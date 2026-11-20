#!/usr/bin/env python3
"""Heuristic static scanner for ABAP source: performance, embedded API
literals, and database CRUD statements.

Pure text analysis. No network access, no credentials, no subprocess calls,
no filesystem writes. Input is ABAP source text (already fetched by the
sap-adt-commands `source` command); output is a JSON report on stdout.

This is a lexical heuristic, not an ABAP parser. It reasons about ABAP
statements one at a time using period (`.`) as a statement terminator and
single quotes (`'`) as string delimiters -- both scoped to a single physical
line, which holds for ABAP because a string literal token cannot span
multiple physical lines. Every rule is documented in
references/analysis-patterns.md alongside its known false-positive and
false-negative risks. Findings are a starting point for human/agent review,
not a verdict.

Usage:
    python adt-client.py --dest DEV_100_DEVELOPER_EN source ZOBJ --type PROG/P \
        | python abap_review_scan.py --stdin

    python abap_review_scan.py --json-file source.json
    python abap_review_scan.py --json-file transport_sources.json   # batch: list or {"objects": [...]}
    python abap_review_scan.py --file myprogram.abap --name ZOBJ --type PROG/P
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Line-level cleanup: strip ABAP comments while respecting string literals.
# ---------------------------------------------------------------------------

def strip_comment(line: str) -> str:
    """Remove the comment portion of a single ABAP source line.

    A line whose first non-blank character is ``*`` is a full-line comment.
    Otherwise a ``"`` outside of a string literal starts a trailing comment.
    ``''`` inside a string is an escaped literal quote, not a close/reopen.
    """
    if line.lstrip().startswith("*"):
        return ""
    in_string = False
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch == "'":
            if in_string and i + 1 < n and line[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
            i += 1
            continue
        if ch == '"' and not in_string:
            return line[:i]
        i += 1
    return line


def extract_string_literals(line: str):
    """Return the unescaped contents of every ``'...'`` literal on the line."""
    literals = []
    buf = []
    in_string = False
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch == "'":
            if in_string:
                if i + 1 < n and line[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                literals.append("".join(buf))
                buf = []
                in_string = False
                i += 1
                continue
            in_string = True
            i += 1
            continue
        if in_string:
            buf.append(ch)
        i += 1
    return literals


def has_statement_terminator(line: str) -> bool:
    """True if a bare ``.`` (outside a string literal) appears on the line."""
    in_string = False
    for ch in line:
        if ch == "'":
            in_string = not in_string
            continue
        if ch == "." and not in_string:
            return True
    return False


def iter_statements(cleaned_lines):
    """Group cleaned lines into logical ABAP statements.

    Yields (start_line, end_line, joined_text). A statement is closed by the
    first line (from its start) that contains a bare period. Text left after
    that period on the same line is folded into the *next* statement's start
    rather than split out precisely -- a documented, low-impact limitation.
    """
    buf = []
    start_line = None
    for lineno, line in enumerate(cleaned_lines, start=1):
        if start_line is None:
            if not line.strip():
                continue
            start_line = lineno
        buf.append(line)
        if has_statement_terminator(line):
            yield start_line, lineno, " ".join(buf)
            buf = []
            start_line = None
    if buf:
        yield start_line, len(cleaned_lines), " ".join(buf)


# ---------------------------------------------------------------------------
# Rule patterns
# ---------------------------------------------------------------------------

_LOOP_AT_RE = re.compile(r"\bLOOP\s+AT\b", re.IGNORECASE)
_ENDLOOP_RE = re.compile(r"\bENDLOOP\b", re.IGNORECASE)
_SELECT_START_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_ENDSELECT_START_RE = re.compile(r"^\s*ENDSELECT\b", re.IGNORECASE)
_SELECT_STAR_RE = re.compile(r"^\s*SELECT\s+(SINGLE\s+|DISTINCT\s+)*\*", re.IGNORECASE)
_INTO_TABLE_RE = re.compile(r"\bINTO\s+(CORRESPONDING\s+FIELDS\s+OF\s+)?TABLE\b", re.IGNORECASE)
_WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)
_UP_TO_ROWS_RE = re.compile(r"\bUP\s+TO\s+\d+\s+ROWS\b", re.IGNORECASE)
_FROM_TABLE_RE = re.compile(r"\bFROM\s+\(?[\w~]+\)?", re.IGNORECASE)

_INSERT_INTO_RE = re.compile(r"^\s*INSERT\s+INTO\s+\(?([\w/]+)\)?", re.IGNORECASE)
_INSERT_FROM_RE = re.compile(r"^\s*INSERT\s+\(?([\w/]+)\)?\s+FROM\b(?!\s+TABLE\s+\w+\s+INTO)", re.IGNORECASE)
_UPDATE_RE = re.compile(r"^\s*UPDATE\s+\(?([\w/]+)\)?", re.IGNORECASE)
_DELETE_FROM_RE = re.compile(r"^\s*DELETE\s+FROM\s+\(?([\w/]+)\)?", re.IGNORECASE)
_DELETE_AMBIGUOUS_RE = re.compile(r"^\s*DELETE\s+(?!TABLE\b|FROM\b)\(?([\w/]+)\)?\s+FROM\b", re.IGNORECASE)
_MODIFY_AMBIGUOUS_RE = re.compile(r"^\s*MODIFY\s+(?!TABLE\b)\(?([\w/]+)\)?\s+FROM\b", re.IGNORECASE)
_EXEC_SQL_RE = re.compile(r"^\s*EXEC\s+SQL\b", re.IGNORECASE)

_URL_RE = re.compile(r"^\s*https?://", re.IGNORECASE)
_IPV4_RE = re.compile(r"^\s*\d{1,3}(\.\d{1,3}){3}\s*$")
_CREDENTIAL_LINE_RE = re.compile(
    r"\b(\w*(?:PASS(?:WORD)?|PWD|SECRET|TOKEN|API_?KEY|BEARER|CREDENTIAL)\w*)\b"
    r"\s*\)?\s*(?:=|TYPE\s+\S+\s+VALUE)\s*'([^']{3,})'",
    re.IGNORECASE,
)

_SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1, "info": 0}


def _finding(rule_id, category, kind, severity, line, message, snippet):
    return {
        "id": rule_id,
        "category": category,
        "kind": kind,
        "severity": severity,
        "line": line,
        "message": message,
        "snippet": snippet.strip()[:300],
    }


def scan_source(source: str):
    """Run every rule over one object's ABAP source and return findings."""
    raw_lines = source.splitlines()
    cleaned_lines = [strip_comment(line) for line in raw_lines]
    findings = []

    # --- structural pass: loop nesting, SELECT-in-LOOP, SELECT/ENDSELECT ---
    loop_stack = []          # line numbers of open LOOP AT statements
    pending_endselect = []   # line numbers of SELECT statements that might be loop-form

    for lineno, line in enumerate(cleaned_lines, start=1):
        if not line.strip():
            continue

        if _LOOP_AT_RE.search(line):
            if loop_stack:
                findings.append(_finding(
                    "nested-loop", "performance", "issue", "medium", lineno,
                    f"Nested LOOP AT inside the loop opened at line {loop_stack[-1]} "
                    "-- verify the inner table is HASHED/SORTED or the read uses "
                    "BINARY SEARCH; otherwise this is O(n²).",
                    raw_lines[lineno - 1],
                ))
            loop_stack.append(lineno)
        if _ENDLOOP_RE.search(line):
            if loop_stack:
                loop_stack.pop()

        if _SELECT_START_RE.search(line):
            if loop_stack:
                findings.append(_finding(
                    "select-in-loop", "performance", "issue", "high", lineno,
                    f"SELECT runs once per iteration of the LOOP opened at line "
                    f"{loop_stack[-1]} -- move it outside the loop (bulk SELECT "
                    "... FOR ALL ENTRIES or JOIN) or replace it with a lookup "
                    "against a table already held in memory.",
                    raw_lines[lineno - 1],
                ))
            if not _INTO_TABLE_RE.search(line):
                pending_endselect.append(lineno)

        if _ENDSELECT_START_RE.search(line) and pending_endselect:
            select_line = pending_endselect.pop()
            findings.append(_finding(
                "select-endselect-loop", "performance", "issue", "medium", select_line,
                "SELECT ... ENDSELECT fetches rows one at a time from the "
                "database. Prefer SELECT ... INTO TABLE (or APPENDING TABLE) "
                "and loop over the internal table instead.",
                raw_lines[select_line - 1],
            ))

    # --- statement-level pass: SELECT shape, CRUD, native SQL ---
    for start_line, _end_line, text in iter_statements(cleaned_lines):
        snippet = raw_lines[start_line - 1] if start_line - 1 < len(raw_lines) else text

        if _SELECT_START_RE.search(text):
            if _SELECT_STAR_RE.search(text):
                findings.append(_finding(
                    "select-star", "performance", "issue", "low", start_line,
                    "SELECT * reads every column. Name only the fields the "
                    "code actually uses.",
                    snippet,
                ))
            if (_FROM_TABLE_RE.search(text) and not _WHERE_RE.search(text)
                    and not _UP_TO_ROWS_RE.search(text)):
                findings.append(_finding(
                    "select-without-where", "performance", "issue", "medium", start_line,
                    "SELECT without a WHERE clause (and no UP TO n ROWS) reads "
                    "the entire table. Confirm this is intentional.",
                    snippet,
                ))

        if _EXEC_SQL_RE.search(text):
            findings.append(_finding(
                "native-sql-block", "crud", "alert", "info", start_line,
                "Native SQL block (EXEC SQL ... ENDEXEC) -- statements inside "
                "bypass Open SQL buffering/authorization checks and are not "
                "visible to this scanner. Inspect manually before changing.",
                snippet,
            ))
            continue

        m = _INSERT_INTO_RE.search(text) or _INSERT_FROM_RE.search(text)
        if m:
            findings.append(_finding(
                "db-insert", "crud", "alert", "info", start_line,
                f"Database INSERT into {m.group(1).upper()}.",
                snippet,
            ))
            continue

        m = _UPDATE_RE.search(text)
        if m:
            findings.append(_finding(
                "db-update", "crud", "alert", "info", start_line,
                f"Database UPDATE on {m.group(1).upper()}.",
                snippet,
            ))
            continue

        m = _DELETE_FROM_RE.search(text)
        if m:
            findings.append(_finding(
                "db-delete", "crud", "alert", "info", start_line,
                f"Database DELETE FROM {m.group(1).upper()}.",
                snippet,
            ))
            continue

        m = _DELETE_AMBIGUOUS_RE.search(text)
        if m:
            findings.append(_finding(
                "db-delete-ambiguous", "crud", "alert", "info", start_line,
                f"DELETE {m.group(1).upper()} FROM ... -- could be a database "
                "table or an internal table; verify the target's declaration.",
                snippet,
            ))
            continue

        m = _MODIFY_AMBIGUOUS_RE.search(text)
        if m:
            findings.append(_finding(
                "db-modify", "crud", "alert", "info", start_line,
                f"MODIFY {m.group(1).upper()} FROM ... -- could be a database "
                "table or an internal table; verify the target's declaration.",
                snippet,
            ))
            continue

    # --- embedded API / hardcoded value pass: per-line string literals ---
    for lineno, (raw_line, cleaned_line) in enumerate(zip(raw_lines, cleaned_lines), start=1):
        if not cleaned_line.strip():
            continue

        for literal in extract_string_literals(cleaned_line):
            if _URL_RE.search(literal):
                findings.append(_finding(
                    "hardcoded-url", "embedded_api", "issue", "high", lineno,
                    f"Hardcoded URL literal ('{literal[:60]}'). Move it to a "
                    "logical destination (SM59 / cl_http_destination_provider) "
                    "so the target can change per system without a code change.",
                    raw_line,
                ))
            elif _IPV4_RE.match(literal):
                findings.append(_finding(
                    "hardcoded-host-ip", "embedded_api", "issue", "medium", lineno,
                    f"Hardcoded IP address literal ('{literal}'). Prefer a "
                    "logical destination or configuration table entry.",
                    raw_line,
                ))

        cred_match = _CREDENTIAL_LINE_RE.search(cleaned_line)
        if cred_match:
            findings.append(_finding(
                "hardcoded-credential", "embedded_api", "issue", "high", lineno,
                f"Literal value assigned to '{cred_match.group(1)}', a "
                "credential-shaped identifier. Move secrets to secure storage "
                "(e.g. a destination's authentication data) -- never in source.",
                raw_line,
            ))

    findings.sort(key=lambda f: (f["line"], -_SEVERITY_RANK.get(f["severity"], 0)))
    return findings


def summarize(findings):
    summary = {"performance": 0, "embedded_api": 0, "crud": 0}
    for f in findings:
        summary[f["category"]] = summary.get(f["category"], 0) + 1
    gate = "REVIEW_NEEDED" if findings else "CLEAN"
    return summary, gate


def review_object(name: str, obj_type: str, source: str) -> dict:
    findings = scan_source(source)
    summary, gate = summarize(findings)
    return {
        "name": name,
        "type": obj_type,
        "findings": findings,
        "summary": summary,
        "gate": gate,
    }


# ---------------------------------------------------------------------------
# Input handling / CLI
# ---------------------------------------------------------------------------

def _normalize_items(payload):
    """Accept a single source object, a list of them, or {"objects": [...]}."""
    if isinstance(payload, dict) and "objects" in payload:
        return payload.get("transport"), payload["objects"]
    if isinstance(payload, list):
        return None, payload
    if isinstance(payload, dict):
        return None, [payload]
    raise ValueError("Expected a JSON object, a list of objects, or {\"objects\": [...]}")


def run_json_payload(payload) -> dict:
    transport, items = _normalize_items(payload)
    results = []
    for item in items:
        if not isinstance(item, dict) or "source" not in item:
            results.append({"error": "Item missing required 'source' field", "item": item})
            continue
        results.append(review_object(
            item.get("name", "UNKNOWN"),
            item.get("type", "UNKNOWN"),
            item["source"],
        ))

    if transport is None and len(results) == 1 and "error" not in results[0]:
        return results[0]

    total_summary = {"performance": 0, "embedded_api": 0, "crud": 0}
    overall_gate = "CLEAN"
    for r in results:
        for cat, count in r.get("summary", {}).items():
            total_summary[cat] = total_summary.get(cat, 0) + count
        if r.get("gate") == "REVIEW_NEEDED":
            overall_gate = "REVIEW_NEEDED"

    out = {"objects": results, "summary": total_summary, "gate": overall_gate}
    if transport:
        out["transport"] = transport
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--json-file", help="Path to a JSON file: one source object, a list, or {\"objects\": [...]}")
    src.add_argument("--stdin", action="store_true", help="Read the same JSON shape from stdin")
    src.add_argument("--file", help="Path to a raw ABAP source file (use with --name/--type)")
    p.add_argument("--name", default="UNKNOWN", help="Object name, only used with --file")
    p.add_argument("--type", default="PROG/P", help="Object type (e.g. PROG/P), only used with --file")
    return p


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = build_parser().parse_args()

    try:
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                source = f.read()
            result = review_object(args.name, args.type, source)
        else:
            if args.stdin:
                raw = sys.stdin.read()
            else:
                with open(args.json_file, encoding="utf-8") as f:
                    raw = f.read()
            payload = json.loads(raw)
            result = run_json_payload(payload)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"error": str(e)}))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Scope a scanner findings report (or a bare diff) to what one transport
actually changed.

`abap_review_scan.py` reports every finding in an object's *current* full
source. When several developers share one object across years of history,
most of those findings usually predate the transport under review. This
script narrows the report down to the lines a specific baseline-vs-current
comparison actually touched, so review attention goes to what the human
asked about, not the object's entire history.

Pure text analysis. No network access, no credentials, no subprocess calls,
no filesystem writes. Inputs are two source snapshots of the *same* object
(the version immediately before the transport's edit, and the current
active source) already fetched via sap-adt-commands `version-source` /
`source` — this script never talks to SAP itself.

Usage:
    python adt-client.py --dest DEV_100_DEVELOPER_EN history ZOBJ --type PROG/P
        # → find the versions[] entry whose "transport" is the task under
        #   review; the entry right after it (older) is the baseline.
    python adt-client.py --dest DEV_100_DEVELOPER_EN version-source ZOBJ \\
        --type PROG/P --version 00042 > before.json
    python adt-client.py --dest DEV_100_DEVELOPER_EN source ZOBJ --type PROG/P > after.json
    python abap_review_scan.py --json-file after.json > findings.json
    python scope_to_transport.py --before before.json --after after.json \\
        --findings findings.json

`--before`/`--after` accept either a raw path to `version-source`/`source`
JSON output (read its "source" field) or a plain .abap text file. Findings
whose line falls inside a changed range are marked
`"in_transport_scope": true`; all others `false` — nothing is dropped, so
the caller still sees the full picture with the relevant lines called out.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys


def _read_source(path: str) -> str:
    """Read a source string from either a JSON {"source": "..."} file
    (as `source`/`version-source` produce) or a plain ABAP text file."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(data, dict) and "source" in data:
            return data["source"]
    return text


def changed_ranges(before: str, after: str) -> list[dict]:
    """1-indexed, inclusive [start, end] line ranges in `after` that this
    diff added or modified. Pure deletions (no corresponding new lines)
    don't touch any line in `after`, so they contribute no range — the
    deletion is still visible in the returned diff text."""
    matcher = difflib.SequenceMatcher(
        a=before.splitlines(), b=after.splitlines(), autojunk=False
    )
    ranges = []
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert") and j2 > j1:
            ranges.append({"start": j1 + 1, "end": j2})
    return ranges


def _line_in_ranges(line: int, ranges: list[dict]) -> bool:
    return any(r["start"] <= line <= r["end"] for r in ranges)


def build_diff_text(before: str, after: str, before_label: str, after_label: str) -> str:
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=before_label,
        tofile=after_label,
    ))


def scope_findings(findings: list[dict], ranges: list[dict]) -> list[dict]:
    scoped = []
    for finding in findings:
        line = finding.get("line")
        tagged = dict(finding)
        tagged["in_transport_scope"] = bool(line is not None and _line_in_ranges(line, ranges))
        scoped.append(tagged)
    return scoped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scope abap_review_scan.py findings (or a bare diff) to what one "
                    "transport's edit actually changed, using a baseline (version before "
                    "the edit) vs current-source comparison.",
    )
    parser.add_argument("--before", required=True,
                        help="Path to the baseline source: version-source JSON output, "
                             "or a plain .abap file")
    parser.add_argument("--after", required=True,
                        help="Path to the current source: `source` JSON output, "
                             "or a plain .abap file")
    parser.add_argument("--findings", default=None,
                        help="Path to abap_review_scan.py's JSON output to tag with "
                             "in_transport_scope (omit to only get the diff/ranges)")
    parser.add_argument("--name", default="", help="Object name, for the report header only")
    parser.add_argument("--type", default="", help="Object type, for the report header only")
    args = parser.parse_args()

    before_src = _read_source(args.before)
    after_src = _read_source(args.after)

    if before_src == after_src:
        result = {
            "name": args.name, "type": args.type,
            "has_changes": False,
            "message": "No difference between baseline and current source — nothing "
                      "in this object changed between the two versions compared.",
        }
        print(json.dumps(result, indent=2))
        return 0

    ranges = changed_ranges(before_src, after_src)
    diff_text = build_diff_text(before_src, after_src, "before", "after")

    result = {
        "name": args.name,
        "type": args.type,
        "has_changes": True,
        "changed_ranges": ranges,
        "diff": diff_text,
    }

    if args.findings:
        with open(args.findings, "r", encoding="utf-8") as f:
            findings_doc = json.load(f)
        findings = findings_doc.get("findings", []) if isinstance(findings_doc, dict) else findings_doc
        scoped = scope_findings(findings, ranges)
        in_scope = [f for f in scoped if f["in_transport_scope"]]
        result["findings"] = scoped
        result["summary"] = {
            "total_findings": len(scoped),
            "in_transport_scope": len(in_scope),
            "outside_transport_scope": len(scoped) - len(in_scope),
        }

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

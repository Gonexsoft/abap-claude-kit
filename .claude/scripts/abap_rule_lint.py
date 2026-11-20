#!/usr/bin/env python3
"""Mekanik kural kontrolu (global kurallar 8c, 12a, 13, 14, 15) - model okumadan, script ile.

Sadece YUKSEK KESINLIKLI kaliplar: yanlis alarm, dogru kodun "duzeltilmesine" yol acar.
Bu yuzden DATA/TYPES bildirimlerinde onek, hard-code, text element gibi baglam isteyen
kurallar burada YOK (model incelemesinde kalir). SAP'ye baglanmaz, dosya yazmaz.

  python -I abap_rule_lint.py --json-file <scan>/objeler.json [--jira <JIRA-NO>]
         [--ranges "OBJE:10-25,40-41;OBJE2:5-9"]

--ranges: mevcut objede DEGISEN satir araliklari. Araligi verilen objede aralik disi bulgular
"mevcut" sayilir (listelenmez); araligi verilmeyen obje yeni kabul edilir (tum satirlar).
--jira: araligi verilen her blokta Jira isareti aranir (kural 15).
Cikti: kisa metin. Her durumda exit 0 (girdi okunamazsa exit 1).
"""

from __future__ import annotations

import argparse
import json
import re
import sys

MAX_LINES = 15

OBSOLETE = [  # (kural, ad, ifade basinda aranan kalip)
    ("12a", "MOVE", re.compile(r"^MOVE\s", re.I)),
    ("12a", "CONCATENATE (string template kullan)", re.compile(r"^CONCATENATE\s+(?!LINES\s+OF\b)", re.I)),
    ("12a", "DESCRIBE TABLE (lines( ) kullan)", re.compile(r"^DESCRIBE\s+TABLE\s", re.I)),
    ("12a", "REFRESH", re.compile(r"^REFRESH\s", re.I)),
    ("12a", "RANGES", re.compile(r"^RANGES\s", re.I)),
    ("12a", "statik CALL METHOD", re.compile(r"^CALL\s+METHOD\s+(?!\()(?![^\s]*[-=]>\()", re.I)),
    ("8c", "CATCH cx_root", re.compile(r"^CATCH\s.*\bCX_ROOT\b", re.I)),
]
ANYWHERE = [
    ("12a", "OCCURS", re.compile(r"\bOCCURS\s+\d", re.I)),
    ("12a", "WITH HEADER LINE", re.compile(r"\bWITH\s+HEADER\s+LINE\b", re.I)),
]
SQL_START = re.compile(r"^(SELECT|WITH)\s", re.I)
ALIAS = re.compile(r"\bAS\s+([A-Za-z])(?=\s|$|\)|,|\.)", re.I)
INLINE_DATA = re.compile(r"(?<![\w-])(?:DATA|FINAL)\(\s*([A-Za-z_][\w]*)\s*\)", re.I)
INLINE_FS = re.compile(r"(?<![\w-])FIELD-SYMBOL\(\s*(<[^>]*>)\s*\)", re.I)
OK_DATA = re.compile(r"^[lg][tsvorcx]_\w", re.I)  # lx_: exception referansi (kural 8c ornegi)
OK_FS = re.compile(r"^<f[st]_\w", re.I)


def clean(line: str) -> str:
    """Yorumu atar, literal iceriklerini bosaltir (uzunluk korunmaz, gerek yok)."""
    if line.startswith("*"):
        return ""
    out, quote = [], ""
    for char in line:
        if quote:
            if char == quote:
                quote = ""
                out.append(char)
            continue
        if char == '"':
            break
        if char in "'`|":
            quote = char
        out.append(char)
    return "".join(out)


def parse_ranges(text: str | None) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    for part in (text or "").split(";"):
        name, _, spans = part.strip().partition(":")
        if not name or not spans:
            continue
        for span in spans.split(","):
            lo, _, hi = span.strip().partition("-")
            if lo.isdigit():
                ranges.setdefault(name.strip().upper(), []).append((int(lo), int(hi) if hi.isdigit() else int(lo)))
    return ranges


def lint(source: str) -> list[tuple[int, str, str]]:
    """-> [(satir, kural, mesaj)]"""
    found: list[tuple[int, str, str]] = []
    start_text, in_sql, at_start = "", False, True
    for lineno, raw in enumerate(source.splitlines(), start=1):
        text = clean(raw).strip()
        if not text:
            continue
        if at_start:
            start_text = text
            in_sql = bool(SQL_START.search(text))
            for rule, name, pattern in OBSOLETE:
                if pattern.search(text):
                    found.append((lineno, rule, f"{name}: yeni kodda kullanilmaz"))
        for rule, name, pattern in ANYWHERE:
            if pattern.search(text):
                found.append((lineno, rule, f"{name}: yeni kodda kullanilmaz"))
        if in_sql or re.search(r"\bJOIN\b", text, re.I):
            for match in ALIAS.finditer(text):
                found.append((lineno, "14", f"tek harfli SQL alias 'AS {match.group(1)}'"))
        for match in INLINE_DATA.finditer(text):
            if not OK_DATA.match(match.group(1)):
                found.append((lineno, "13", f"inline degisken oneksiz/yanlis onek: {match.group(1)}"))
        for match in INLINE_FS.finditer(text):
            if not OK_FS.match(match.group(1)):
                found.append((lineno, "13", f"field-symbol <fs_..>/<ft_..> degil: {match.group(1)}"))
        at_start = text.endswith(".")
    return found


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Mekanik ABAP kural kontrolu")
    parser.add_argument("--json-file", required=True)
    parser.add_argument("--jira")
    parser.add_argument("--ranges")
    args = parser.parse_args()
    try:
        with open(args.json_file, encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload["objects"] if isinstance(payload, dict) and "objects" in payload else payload
        if isinstance(items, dict):
            items = [items]
    except (OSError, ValueError, KeyError) as err:
        print(f"Kural: OKUNAMADI - {err}")
        return 1

    ranges = parse_ranges(args.ranges)
    new: list[str] = []
    existing = 0
    for item in items:
        name, source = str(item.get("name", "?")).upper(), item.get("source") or ""
        spans = ranges.get(name)
        lines = source.splitlines()
        for lineno, rule, message in lint(source):
            if spans and not any(lo <= lineno <= hi for lo, hi in spans):
                existing += 1
                continue
            snippet = lines[lineno - 1].strip()[:70]
            new.append(f"  - {name}:{lineno} — kural {rule} — {message} — {snippet}")
        if args.jira and spans:
            for lo, hi in spans:
                block = "\n".join(lines[max(lo - 2, 0):hi + 1]).upper()
                if args.jira.upper() not in block:
                    new.append(f"  - {name}:{lo}-{hi} — kural 15 — degisen blokta {args.jira} isareti yok")

    print(f"Kural: yeni {len(new)}, mevcut {existing}")
    for line in new[:MAX_LINES]:
        print(line)
    if len(new) > MAX_LINES:
        print(f"  ... +{len(new) - MAX_LINES} bulgu daha")
    return 0


if __name__ == "__main__":
    sys.exit(main())

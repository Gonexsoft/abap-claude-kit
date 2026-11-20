#!/usr/bin/env python3
"""Kullanicinin verdigi belgeleri (xlsx/xlsm, docx, csv/txt/md) duz metne cevirir — ek kutuphane yok.

Neden: belge analizi Gemini'de (gemini-ask.ps1 -Mode doc); Gemini tam metni okur, Claude sadece
bu scriptin stdout'a bastigi ISKELETI (sayfa/kolon adlari, basliklar, satir sayilari) okur ve
Gemini'nin analizini onunla kiyaslar. pdf ve gorseller cevrilmez: Gemini dogrudan okur
(iskelette "dogrudan" diye gecer).

Kullanim:
  python -I .claude/scripts/doc-to-text.py --out-dir <is klasoru>/scan/docs <dosya> [<dosya> ...]
Cikti: <out-dir>/<dosya adi>.txt (UTF-8) + stdout'a iskelet.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
DIRECT = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
PREVIEW_ROWS = 3


def col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def xml_text(node) -> str:
    return "".join(t.text or "" for t in node.iter(f"{{{NS['m']}}}t"))


def convert_xlsx(path: Path) -> tuple[str, list[str]]:
    out, skel = [], []
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = [xml_text(si) for si in root.findall("m:si", NS)]
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels.findall("pr:Relationship", NS)}
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        for sheet in wb.findall("m:sheets/m:sheet", NS):
            name = sheet.get("name")
            target = targets.get(sheet.get(f"{{{NS['r']}}}id"), "")
            target = target.lstrip("/")
            target = target if target.startswith("xl/") else f"xl/{target}"
            if target not in names:
                continue
            root = ET.fromstring(zf.read(target))
            rows = []
            for row in root.iter(f"{{{NS['m']}}}row"):
                cells = {}
                for c in row.findall("m:c", NS):
                    kind, v = c.get("t"), c.find("m:v", NS)
                    if kind == "s" and v is not None:
                        val = shared[int(v.text)]
                    elif kind == "inlineStr":
                        val = xml_text(c)
                    elif kind == "b" and v is not None:
                        val = "TRUE" if v.text == "1" else "FALSE"
                    else:
                        val = v.text if v is not None and v.text else ""
                    if val != "":
                        cells[col_index(c.get("r"))] = val.replace("\t", " ").replace("\n", " / ")
                if cells:
                    rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            width = max((len(r) for r in rows), default=0)
            out.append(f"### Sayfa: {name} ({len(rows)} satir, {width} kolon)")
            out.extend("\t".join(r) for r in rows)
            out.append("")
            skel.append(f"  sayfa '{name}': {len(rows)} satir x {width} kolon")
            for r in rows[: 1 + PREVIEW_ROWS]:
                skel.append("    | " + " | ".join(x[:30] for x in r[:15]))
    skel.append("  not: tarih hucreleri seri sayi olarak gelebilir (or. 45627 = 2024-12-01)")
    return "\n".join(out), skel


def convert_docx(path: Path) -> tuple[str, list[str]]:
    w = NS["w"]
    with zipfile.ZipFile(path) as zf:
        body = ET.fromstring(zf.read("word/document.xml")).find(f"{{{w}}}body")
    out, headings, tables, paras = [], [], 0, 0

    def para_text(p) -> str:
        return "".join(t.text or "" for t in p.iter(f"{{{w}}}t")).strip()

    for el in body:
        if el.tag == f"{{{w}}}p":
            text = para_text(el)
            if not text:
                continue
            style = el.find(f"{{{w}}}pPr/{{{w}}}pStyle")
            level = re.search(r"(\d)$", style.get(f"{{{w}}}val", "")) if style is not None else None
            is_heading = style is not None and re.search(r"heading|baslik|başlık|title", style.get(f"{{{w}}}val", ""), re.I)
            if is_heading:
                depth = int(level.group(1)) if level else 1
                out.append("#" * depth + " " + text)
                headings.append("  " + "  " * (depth - 1) + text[:80])
            else:
                out.append(text)
                paras += 1
        elif el.tag == f"{{{w}}}tbl":
            tables += 1
            out.append(f"[Tablo {tables}]")
            for tr in el.iter(f"{{{w}}}tr"):
                out.append(" | ".join(para_text(tc) for tc in tr.findall(f"{{{w}}}tc")))
            out.append("")
    skel = [f"  {paras} paragraf, {tables} tablo"] + (["  basliklar:"] + headings[:40] if headings else ["  baslik stili yok"])
    return "\n".join(out), skel


def convert_plain(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    lines = text.splitlines()
    skel = [f"  {len(lines)} satir"]
    if path.suffix.lower() == ".csv" and lines:
        dialect = csv.Sniffer().sniff(lines[0]) if lines[0] else csv.excel
        skel.append("    | " + " | ".join(next(csv.reader([lines[0]], dialect))[:15]))
    return text, skel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.stdout.reconfigure(encoding="utf-8")
    rc = 0
    for f in map(Path, args.files):
        ext = f.suffix.lower()
        try:
            if not f.is_file():
                raise FileNotFoundError("dosya yok")
            if ext in DIRECT:
                dst = out_dir / f.name
                if f.resolve() != dst.resolve():
                    shutil.copy2(f, dst)
                print(f"{f.name}: dogrudan (Gemini okur) -> {dst}")
                continue
            if ext in (".xlsx", ".xlsm"):
                text, skel = convert_xlsx(f)
            elif ext == ".docx":
                text, skel = convert_docx(f)
            elif ext in (".csv", ".txt", ".md", ".json", ".xml"):
                text, skel = convert_plain(f)
            else:
                raise ValueError(f"desteklenmeyen tip {ext} (xls/doc ise Excel/Word'de xlsx/docx kaydet)")
            dst = out_dir / (f.name + ".txt")
            dst.write_text(text, encoding="utf-8")
            print(f"{f.name}: {len(text)} karakter -> {dst}")
            print("\n".join(skel))
        except Exception as exc:  # her dosya bagimsiz; biri bozuksa digerleri devam
            print(f"{f.name}: HATA {exc}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

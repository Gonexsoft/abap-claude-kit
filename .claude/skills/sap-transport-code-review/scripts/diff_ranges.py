#!/usr/bin/env python3
"""workspace eki (2026-10-18): MCP `abap_transport_get_unified_diff` ciktisindan, her objenin GUNCEL
kaynagindaki degisen satir araliklarini cikarir.

Neden icerik hizalamasi: bir test transport'unda MCP diff'inin hunk basligindaki (+c,d) satir
numaralari bazi objelerde guncel kaynaga gore 1 satir kaydi (sabit degil). Bu yuzden numaraya
guvenilmez; her hunk'in yeni taraf satirlari difflib ile guncel kaynaga hizalanir.

Offline: ag yok, subprocess yok. Sadece --out ve --extract-new dizinine yazar.

Kullanim:
  python -I diff_ranges.py --diff <mcp_diff.json> --src-dir <dir> --out <ranges.json> [--extract-new]
    --diff        MCP aracinin JSON ciktisi ({"diffResult": "...", ...}) ya da ham diff metni
    --src-dir     <OBJE>.abap guncel kaynak dosyalari (abap_object_read_file ACTIVE)
    --extract-new Diff'te tamamen yeni olan objelerin (@@ -0,0 ...) kaynagini diff'ten
                  <src-dir>/<OBJE>.abap olarak yazar (ayrica okumaya gerek kalmaz)
Cikti: {"<OBJE>": {"type", "new", "ranges": [[bas, son], ...], "notes": [...]}}
Not: degismeyen objeler diff'te ADSIZ "No differences found." olarak gelir; sayisi
"_unchanged_count" alaninda doner.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys


def parse(diff_text: str):
    objs, cur, hunk, unchanged = {}, None, None, 0
    for line in diff_text.splitlines():
        m = re.match(r'^\+\+\+ (\S+) (\S+) \(new\)', line)
        if m:
            cur = {'type': m.group(1), 'hunks': []}
            objs[m.group(2)] = cur
            continue
        if line.startswith('No differences found.'):
            cur = None
            unchanged += 1
            continue
        if cur is None or (line.startswith('--- ') and line.endswith('(old)')):
            continue
        m = re.match(r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
        if m:
            hunk = {'old_empty': m.group(1) == '0' and m.group(2) == '0',
                    'start': int(m.group(3)), 'count': int(m.group(4)), 'new': []}
            cur['hunks'].append(hunk)
            continue
        if hunk is None:
            continue
        if line.startswith('+'):
            hunk['new'].append((line[1:].rstrip(), True))
        elif line.startswith(' ') or line == '':
            hunk['new'].append((line[1:].rstrip() if line else '', False))
    # segment sonundaki bos ayrac satirlari hunk'a ait degil: basliktaki satir sayisiyla kes
    for o in objs.values():
        for h in o['hunks']:
            h['new'] = h['new'][:h['count']]
    return objs, unchanged


def to_ranges(lines):
    out = []
    for x in sorted(set(lines)):
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--diff', required=True)
    p.add_argument('--src-dir', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--extract-new', action='store_true')
    a = p.parse_args()

    raw = open(a.diff, encoding='utf-8').read()
    text = json.loads(raw)['diffResult'] if raw.lstrip().startswith('{') else raw
    objs, unchanged = parse(text)

    result = {'_unchanged_count': unchanged}
    for name, o in objs.items():
        is_new = len(o['hunks']) == 1 and o['hunks'][0]['old_empty']
        path = os.path.join(a.src_dir, name + '.abap')
        if is_new and a.extract_new:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(t for t, _ in o['hunks'][0]['new']) + '\n')
        if not os.path.exists(path):
            result[name] = {'type': o['type'], 'new': is_new, 'ranges': [],
                            'notes': ['guncel kaynak dosyasi yok; once abap_object_read_file ile oku']}
            continue
        src = [x.rstrip() for x in open(path, encoding='utf-8').read().splitlines()]
        added, notes = [], []
        for h in o['hunks']:
            block = [t for t, _ in h['new']]
            sm = difflib.SequenceMatcher(a=block, b=src, autojunk=False)
            mapped = {}
            for i, j, size in sm.get_matching_blocks():
                for k in range(size):
                    mapped[i + k] = j + k + 1
            miss = 0
            for k, (_, is_add) in enumerate(h['new']):
                if is_add:
                    if k in mapped:
                        added.append(mapped[k])
                    else:
                        miss += 1
            if miss:
                notes.append(f"hunk @+{h['start']}: {miss} eklenen satir guncel kaynakta yok "
                             "(transport'tan sonra degismis olabilir)")
        result[name] = {'type': o['type'], 'new': is_new, 'ranges': to_ranges(added), 'notes': notes}

    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=1)
    for name, r in result.items():
        if name.startswith('_'):
            continue
        print(f"{name}\t{'YENI' if r['new'] else 'DEGISEN'}\t{sum(b - x + 1 for x, b in r['ranges'])} satir\t"
              f"{'; '.join(r['notes']) or '-'}")
    print(f"degismeyen (adsiz) obje: {unchanged}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

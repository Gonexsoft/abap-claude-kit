#!/usr/bin/env python3
"""PostToolUse hook: SAP'de her aktivasyondan sonra kontrol + otomatik duzeltme dongusunu
baglama ekler (global kural 3a). Hatirlatmayi hafizaya degil harness'e baglar.
Sadece metin uretir; hicbir SAP cagrisi yapmaz. Her durumda exit 0.
"""

from __future__ import annotations

import json
import sys


def object_names(node, out: list[str]) -> None:
    if isinstance(node, dict):
        for key, val in node.items():
            if key in ("objectName", "name") and isinstance(val, str) and val:
                out.append(val)
            elif key == "affFileName" and isinstance(val, str):
                out.append(val.split(".")[0].upper())
            else:
                object_names(val, out)
    elif isinstance(node, list):
        for item in node:
            object_names(item, out)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    tool_input = payload.get("tool_input") or {}
    names: list[str] = []
    object_names(tool_input, names)
    names = sorted(set(names))
    dest = tool_input.get("destination", "?")

    text = (
        f"[Kural 3a] {dest} uzerinde aktivasyon yapildi"
        + (f" ({', '.join(names)})" if names else "")
        + ". Aktivasyon cevabindaki hata/uyariyi duzelt. CALL FUNCTION tip uyumsuzlugunu "
        "aktivasyon yakalamaz (kural 12b). SADECE ana oturum icin (alt ajansan yok say, "
        "kendi donusunu yap): isin tum objeleri bittiyse /abap-development 'Kontrol' bir kez "
        "(en fazla 3 tur; davranis degisiyorsa sor)."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": text}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass

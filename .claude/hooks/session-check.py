#!/usr/bin/env python3
"""Oturum basi kontrolu (Claude Code SessionStart hook'u).

SAP ADT MCP sunucusu (localhost:2236) cevap veriyor mu, hangi sistemlerde logon var, izinli
listeyle (systems.json) karsilastirir. Stdout oturum baglamina eklenir. Token VS Code
ayarindan okunur, hicbir yere yazilmaz. Sadece abap_destination_list cagrilir (okuma).
Her durumda exit 0: kontrol oturumu asla engellemez.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    systems = json.load(open(os.path.join(HERE, "systems.json"), encoding="utf-8"))["systems"]
    allowed = [s["destination"] for s in systems]
    basis = {s["destination"]: s.get("basis") or "SURUM BILINMIYOR (kod yazmadan once sistemden al, kural 12)"
             for s in systems}
    settings = open(os.path.join(os.environ.get("APPDATA", ""), "Code", "User", "settings.json"),
                    encoding="utf-8").read()
    token = re.search(r'"adt\.mcpServer\.token"\s*:\s*"([^"]+)"', settings)
    port = re.search(r'"adt\.mcpServer\.port"\s*:\s*(\d+)', settings)
    url = f"http://localhost:{port.group(1) if port else '2236'}/mcp"
    if not token:
        print("SAP ADT MCP: VS Code ayarinda adt.mcpServer.token yok — MCP sunucusu kapali olabilir.")
        return

    headers = {"Authorization": f"Bearer {token.group(1)}", "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}

    def post(msg: dict, session: str | None = None):
        h = dict(headers)
        if session:
            h["mcp-session-id"] = session
        req = urllib.request.Request(url, json.dumps(msg).encode(), h, method="POST")
        with urllib.request.urlopen(req, timeout=4) as resp:
            body = resp.read().decode("utf-8")
            return resp.headers.get("mcp-session-id"), body

    try:
        session, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "session-check", "version": "1"}}})
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session)
        _, body = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "abap_destination_list", "arguments": {}}}, session)
    except urllib.error.HTTPError as e:
        if e.code in (400, 401):
            # ADT sunucusu gecersiz/eksik token'a 400 de donuyor (2026-11-03 testinde goruldu)
            print(f"SAP ADT MCP: {e.code} — token gecersiz ya da degismis. Kullaniciya: VS Code'da ADT "
                  "logon'unu kontrol et; surerse 'KURULUM.md'yi uygula' de (token yeniden yazilir), "
                  "sonra Reload Window ya da /mcp -> sap-adt -> Reconnect.")
        else:
            print(f"SAP ADT MCP: HTTP {e.code} — sunucu hata dondu.")
        return
    except Exception:
        print("SAP ADT MCP (localhost:2236) CEVAP VERMIYOR: VS Code'da ADT ile sisteme logon ol, "
              "sonra /mcp -> sap-adt -> Reconnect. Baglanti olmadan SAP islemi yapilamaz.")
        return

    text = ""
    for line in body.splitlines():
        if line.startswith("data:"):
            body = line[5:].strip()
    try:
        content = json.loads(body)["result"]["content"]
        text = " ".join(c.get("text", "") for c in content)
    except Exception:
        pass
    logged_on = re.findall(r"[A-Z0-9]{3}_\d{3}_[A-Z0-9_]+", text)
    usable = [d for d in allowed if d in logged_on]
    missing = [d for d in allowed if d not in logged_on]
    if not usable:
        print("SAP ADT MCP sunucusu acik ama HICBIR izinli sisteme logon YOK "
              f"({', '.join(allowed)}): VS Code'da ADT'den logon olunmadan SAP islemi yapilamaz.")
        return
    msg = ("SAP ADT MCP hazir. Logon + izinli: "
           + ", ".join(f"{d} (SAP_BASIS {basis[d]})" for d in usable) + ".")
    if missing:
        msg += f" Logon OLMAYAN izinli sistem: {', '.join(missing)} (gerekirse VS Code ADT'den logon)."
    msg += " Hatirlatma: hedef sistem her iste kullaniciya sorulur."
    print(msg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # kontrol oturumu bozmasin
        print(f"SAP oturum kontrolu calismadi: {type(e).__name__}")

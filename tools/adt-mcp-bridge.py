#!/usr/bin/env python3
"""SAP ADT MCP (VS Code eklentisi, Streamable HTTP) <-> stdio koprusu — Antigravity icin.

Neden: Antigravity'nin HTTP MCP istemcisi ADT sunucusuna baglanirken "still connecting"de
kaliyor (2026-10-19). Sunucu, oturumdan sonra acilan GET SSE akisina 404 donuyor; istemci bunu
oturum dustu sayip surekli yeniden baglaniyor olabilir. Kopru stdio konusur (en standart yol),
sunucuya sadece POST gonderir — Claude Code'un calisan akisiyla ayni.

Token her baslangicta VS Code ayarindan (adt.mcpServer.token) okunur: Antigravity ayar dosyasinda
token tutulmaz, VS Code token'i degisirse Antigravity'yi yeniden baslatmak yeter.
Ek kutuphane yok. Log: stderr.

  mcp_config.json:  "sap-adt": {"command": "python", "args": ["-I", "<bu dosya>"]}
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

TIMEOUT = 600  # ATC / unit test uzun surebilir


def log(msg: str) -> None:
    sys.stderr.write(f"[adt-mcp-bridge] {msg}\n")
    sys.stderr.flush()


def read_vscode_settings() -> tuple[str, str]:
    path = os.path.join(os.environ.get("APPDATA", ""), "Code", "User", "settings.json")
    text = open(path, encoding="utf-8").read()
    token = re.search(r'"adt\.mcpServer\.token"\s*:\s*"([^"]+)"', text)
    if not token:
        raise RuntimeError("VS Code ayarinda adt.mcpServer.token bulunamadi")
    port = re.search(r'"adt\.mcpServer\.port"\s*:\s*(\d+)', text)
    return token.group(1), f"http://localhost:{port.group(1) if port else '2236'}/mcp"


class Bridge:
    def __init__(self) -> None:
        self.token, self.url = read_vscode_settings()
        self.session: str | None = None
        self.protocol: str | None = None
        self.init_msg: dict | None = None

    def post(self, msg: dict) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["mcp-session-id"] = self.session
        if self.protocol:
            headers["mcp-protocol-version"] = self.protocol
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode("utf-8"),
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if msg.get("method") == "initialize":
                self.session = resp.headers.get("mcp-session-id") or self.session
            if resp.status == 202:
                return []
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
        if "text/event-stream" in ctype:
            out, data = [], []
            for line in body.splitlines():
                if line.startswith("data:"):
                    data.append(line[5:].lstrip())
                elif not line.strip() and data:
                    out.append(json.loads("\n".join(data)))
                    data = []
            if data:
                out.append(json.loads("\n".join(data)))
            return out
        return [json.loads(body)] if body.strip() else []

    def reinitialize(self) -> None:
        # VS Code yeniden yuklenince sunucu oturumu duser: ayni initialize ile yeni oturum ac
        log("oturum dusmus, yeniden baslatiliyor")
        self.token, self.url = read_vscode_settings()
        self.session = None
        self.post(self.init_msg)
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def handle(self, msg: dict) -> list[dict]:
        if msg.get("method") == "initialize":
            self.init_msg = msg
            self.session = None
            replies = self.post(msg)
            for r in replies:
                self.protocol = (r.get("result") or {}).get("protocolVersion", self.protocol)
            return replies
        try:
            return self.post(msg)
        except urllib.error.HTTPError as e:
            if e.code == 404 and self.init_msg:
                self.reinitialize()
                return self.post(msg)
            raise


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    bridge = Bridge()
    log(f"hazir: {bridge.url}")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            log("gecersiz JSON satiri atlandi")
            continue
        try:
            replies = bridge.handle(msg)
        except Exception as e:  # istek cevapsiz kalmasin: istemci asili kalir
            detail = f"{type(e).__name__}: {e}"
            if isinstance(e, urllib.error.HTTPError):
                detail += " " + e.read(300).decode("utf-8", "replace")
            log(f"hata ({msg.get('method')}): {detail}")
            replies = [] if "id" not in msg else [{
                "jsonrpc": "2.0", "id": msg["id"],
                "error": {"code": -32603, "message": f"ADT MCP koprusu: {detail}"}}]
        for r in replies:
            sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

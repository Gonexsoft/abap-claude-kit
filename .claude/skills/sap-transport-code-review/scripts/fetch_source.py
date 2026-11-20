#!/usr/bin/env python3
"""SAP kaynagini MCP'den dogrudan diske indirir (workspace eki, 2026-11-11).

Neden: tarama icin kaynagin once MCP ile okunup sonra dosyaya yeniden yazilmasi ayni kodu
model baglamindan iki kez gecirir. Bu betik kaynagi baglama hic sokmadan dosyaya yazar.

Guvenlik: SADECE `abap_object_read_file` cagrilir (okuma). Hedef, `.claude/hooks/systems.json`
izinli listesinde degilse hicbir ag cagrisi yapilmaz. Token VS Code ayarindan okunur, hicbir
yere yazilmaz. Cikti klasoru workspace `specs` altinda ya da gecici klasorde olmalidir.
Her cagri `.claude/hooks/fetch-source.log`'a yazilir. Ek kutuphane yok.

  python -I fetch_source.py --dest <DESTINATION|SID> --out-dir <klasor> [--version ACTIVE]
         [--json-out objeler.json] [--transport <TR>] <OBJE[:TIP] | aff-dosya-adi> ...

  ZPROG:PROG  ZCL_X:CLAS  zcl_x.clas.locals_imp.abap
Stdout: tek JSON ozet (dosya, satir sayisi, hata). Bir obje bile okunamazsa exit 1.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
SYSTEMS_JSON = os.path.join(WORKSPACE, ".claude", "hooks", "systems.json")
LOG_FILE = os.path.join(WORKSPACE, ".claude", "hooks", "fetch-source.log")
TOOL = "abap_object_read_file"  # bu betigin cagirabildigi TEK arac
PAGE = 2000
TIMEOUT = 60


class FetchError(Exception):
    pass


def resolve_destination(dest: str) -> str:
    """Izinli listedeki tam destination'i doner; SID verildiyse listeden cozer."""
    with open(SYSTEMS_JSON, encoding="utf-8") as handle:
        systems = json.load(handle)["systems"]
    for system in systems:
        if dest in (system["destination"], system.get("sid")):
            return system["destination"]
    raise FetchError(f"'{dest}' izinli sistem listesinde yok (systems.json)")


def is_inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.normcase(path), os.path.normcase(root)]) == os.path.normcase(root)
    except ValueError:  # farkli surucu
        return False


def check_out_dir(out_dir: str) -> str:
    path = os.path.realpath(out_dir)
    allowed = [os.path.realpath(os.path.join(WORKSPACE, "specs")),
               os.path.realpath(tempfile.gettempdir())]
    if not any(is_inside(path, root) for root in allowed):
        raise FetchError("cikti klasoru workspace specs altinda ya da gecici klasorde olmali")
    return path


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.$-]", "_", name)


def parse_spec(spec: str) -> tuple[dict, str, str, str]:
    """-> (objectIdentifier, ad, tip, dosya adi)"""
    if spec.count(".") >= 2 and ":" not in spec:          # AFF dosya adi
        name, kind = spec.split(".")[0].upper(), spec.split(".")[1].upper()
        return {"affFileName": spec}, name, kind, safe_name(spec)
    name, _, kind = spec.partition(":")
    ident = {"objectName": name.upper()}
    if kind:
        ident["objectType"] = kind.upper()
    return ident, name.upper(), kind.upper() or "PROG", safe_name(name.upper()) + ".abap"


class McpClient:
    def __init__(self) -> None:
        path = os.path.join(os.environ.get("APPDATA", ""), "Code", "User", "settings.json")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        token = re.search(r'"adt\.mcpServer\.token"\s*:\s*"([^"]+)"', text)
        if not token:
            raise FetchError("VS Code ayarinda adt.mcpServer.token yok (MCP sunucusu kapali olabilir)")
        port = re.search(r'"adt\.mcpServer\.port"\s*:\s*(\d+)', text)
        self.url = f"http://localhost:{port.group(1) if port else '2236'}/mcp"
        self.headers = {"Authorization": f"Bearer {token.group(1)}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"}
        self.session: str | None = None
        self.next_id = 0

    def post(self, msg: dict) -> dict:
        headers = dict(self.headers)
        if self.session:
            headers["mcp-session-id"] = self.session
        req = urllib.request.Request(self.url, json.dumps(msg).encode("utf-8"), headers,
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                self.session = resp.headers.get("mcp-session-id") or self.session
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            raise FetchError(f"MCP sunucusu HTTP {err.code} dondu (400/401 = token degismis)") from err
        except OSError as err:
            raise FetchError("MCP sunucusu cevap vermiyor (VS Code ADT logon?)") from err
        for line in body.splitlines():                     # SSE cevabi
            if line.startswith("data:"):
                body = line[5:].strip()
        return json.loads(body) if body.strip() else {}

    def connect(self) -> None:
        self.post({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                   "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                              "clientInfo": {"name": "fetch-source", "version": "1"}}})
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def read_page(self, arguments: dict) -> dict:
        self.next_id += 1
        answer = self.post({"jsonrpc": "2.0", "id": self.next_id, "method": "tools/call",
                            "params": {"name": TOOL, "arguments": arguments}})
        if "error" in answer:
            raise FetchError(str(answer["error"].get("message", answer["error"]))[:300])
        result = answer.get("result") or {}
        text = " ".join(c.get("text", "") for c in result.get("content") or [])
        if result.get("isError"):
            raise FetchError(text[:300] or "arac hata dondu")
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
        try:
            return json.loads(text)
        except ValueError as err:
            raise FetchError("beklenmeyen cevap bicimi: " + text[:200]) from err


def fetch(read_page, destination: str, ident: dict, version: str) -> tuple[str, int]:
    """Tum sayfalari okur; (kaynak, totalLines) doner. Satir sayisi tutmazsa hata."""
    parts: list[str] = []
    offset, total = 1, 0
    while True:
        page = read_page({"destination": destination, "objectIdentifier": ident,
                          "version": version, "offset": offset, "limit": PAGE})
        parts.append(page.get("content") or "")
        total = int(page.get("totalLines") or 0)
        if not page.get("truncated"):
            break
        nxt = (page.get("continuation") or {}).get("nextOffset")
        if not nxt or nxt <= offset:
            raise FetchError("sayfalama ilerlemiyor (nextOffset yok)")
        if parts[-1] and not parts[-1].endswith("\n"):
            parts[-1] += "\n"
        offset = nxt
    source = "".join(parts)
    got = len(source.splitlines())
    if got != total:
        raise FetchError(f"satir sayisi tutmuyor: okunan {got}, totalLines {total}")
    return source, total


def log(line: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {line}\n")
    except OSError:
        pass


def run(args: argparse.Namespace, read_page=None) -> dict:
    destination = resolve_destination(args.dest)
    out_dir = check_out_dir(args.out_dir)
    if read_page is None:
        client = McpClient()
        client.connect()
        read_page = client.read_page
    os.makedirs(out_dir, exist_ok=True)
    summary = {"dest": destination, "version": args.version, "files": [], "errors": []}
    objects = []
    for spec in args.objects:
        ident, name, kind, file_name = parse_spec(spec)
        try:
            source, total = fetch(read_page, destination, ident, args.version)
        except FetchError as err:
            summary["errors"].append({"object": spec, "error": str(err)})
            log(f"{destination} {args.version} {spec} HATA {err}")
            continue
        path = os.path.join(out_dir, file_name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(source)
        summary["files"].append({"object": spec, "file": path, "totalLines": total})
        objects.append({"name": name, "type": kind, "source": source})
        log(f"{destination} {args.version} {spec} {total} satir")
    if args.json_out and objects:
        json_path = os.path.join(out_dir, os.path.basename(args.json_out))
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({"transport": args.transport, "objects": objects}, handle, ensure_ascii=False)
        summary["json_out"] = json_path
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAP kaynagini MCP'den diske indirir (sadece okuma)")
    parser.add_argument("--dest", required=True, help="izinli destination ya da SID")
    parser.add_argument("--out-dir", required=True, help="specs altinda scan klasoru ya da gecici klasor")
    parser.add_argument("--version", default="ACTIVE", choices=["ACTIVE", "INACTIVE", "WORKING_AREA"])
    parser.add_argument("--json-out", help="tarayici girdisi (objeler.json) da uretilsin; out-dir'e yazilir")
    parser.add_argument("--transport", help="json-out icindeki transport alani")
    parser.add_argument("objects", nargs="+", help="OBJE[:TIP] ya da AFF dosya adi")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summary = run(args)
    except FetchError as err:
        print(json.dumps({"errors": [{"error": str(err)}]}, ensure_ascii=False))
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

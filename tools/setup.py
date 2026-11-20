#!/usr/bin/env python3
"""SAP ABAP workspace kurulumu — paketi acan gelistiricinin bilgisayarinda calisir.

Normal yol: VS Code'da klasoru acip Claude Code'a "KURULUM.md'yi uygula" demek; Claude
sorulari sohbette sorar ve bu script'i parametreyle calistirir.

  python -I tools\\setup.py --check
      On kosullar + ADT destination listesi + mevcut kurulum durumu (JSON). Hicbir sey yazmaz.
  python -I tools\\setup.py --yes --systems "DEV_100_X:DEV:write,QAS_100_X:QA"
        [--global-rules install|replace|skip] [--git yes|no] [--antigravity yes|no]
        [--mcp-scope project|user]
      Sorusuz kurulum.
  python -I tools\\setup.py
      Etkilesimli kurulum (sorulari script sorar).

Yaptiklari (mevcut dosyalari once yedekler, tekrar calistirilabilir):
  systems.json + CLAUDE.md sistem tablosu + systems\\<SID>.md, hook yollari
  (.claude\\settings.json), VS Code ADT MCP ve sistem/paket kisiti, sap-adt MCP baglantisi
  (varsayilan: workspace .mcp.json — git'e ve pakete girmez), global kodlama kurallari
  (~\\.claude\\CLAUDE.md), istege bagli git init ve Antigravity aktarimi.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
VSCODE_SETTINGS = Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "settings.json"
ADT_DESTINATIONS = HOME / ".adtls" / "destinations.json"
CLAUDE_JSON = HOME / ".claude.json"
GLOBAL_RULES = HOME / ".claude" / "CLAUDE.md"
RULES_SRC = ROOT / "docs" / "global-rules.md"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
ARGS: argparse.Namespace


def say(msg: str = "") -> None:
    print(msg, flush=True)


def ask(question: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    return input(f"{question}{hint}: ").strip() or default


def yes(question: str, default: bool = True) -> bool:
    answer = ask(question + (" (E/h)" if default else " (e/H)"), "e" if default else "h")
    return answer.lower() in ("e", "evet", "y", "yes")


def backup(path: Path) -> None:
    if path.exists():
        shutil.copy2(path, path.with_name(f"{path.name}.bak-{STAMP}"))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def short_path(path: Path) -> str:
    """Bosluk ve Turkce karakterli yollar hook komutunda sorun cikarmasin diye 8.3 kisa yol."""
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 1024):
        return buf.value.replace("\\", "/")
    return str(path).replace("\\", "/")


def rules_text() -> str:
    return re.sub(r"\A<!-- KOPYA.*?-->\s*", "", RULES_SRC.read_text(encoding="utf-8"), flags=re.S)


def load_destinations() -> list[dict]:
    if not ADT_DESTINATIONS.exists():
        return []
    return read_json(ADT_DESTINATIONS).get("destinations", [])


# --- On kosullar ------------------------------------------------------------------------
def prerequisite_problems() -> tuple[list[str], list[str], str]:
    problems, warnings, adt = [], [], ""
    if sys.version_info < (3, 10):
        problems.append(f"Python 3.10+ gerekli (simdi {sys.version.split()[0]})")
    if not shutil.which("git"):
        warnings.append("Git yok — workspace gecmisi tutulamaz (kurulum devam eder)")
    if not shutil.which("powershell.exe"):
        problems.append("powershell.exe yok (erisim korumasi hook'u icin gerekli)")
    if not VSCODE_SETTINGS.exists():
        problems.append(f"VS Code ayar dosyasi yok: {VSCODE_SETTINGS}")
    ext = sorted((HOME / ".vscode" / "extensions").glob("sapse.adt-vscode-*"))
    if not ext:
        problems.append("SAP 'ABAP Development Tools' VS Code eklentisi kurulu degil (sapse.adt-vscode)")
    else:
        adt = ext[-1].name
        version = re.search(r"adt-vscode-(\d+)\.(\d+)", adt)
        if version and (int(version.group(1)), int(version.group(2))) < (1, 2):
            problems.append(f"ADT eklentisi 1.2+ olmali (simdi {adt})")
    if not load_destinations():
        problems.append("ADT'de tanimli sistem yok — VS Code'da ADT'ye sistem ekleyip logon olun")
    return problems, warnings, adt


def vscode_token() -> str:
    try:
        return read_json(VSCODE_SETTINGS).get("adt.mcpServer.token", "")
    except Exception:
        text = VSCODE_SETTINGS.read_text(encoding="utf-8") if VSCODE_SETTINGS.exists() else ""
        found = re.search(r'"adt\.mcpServer\.token"\s*:\s*"([^"]+)"', text)
        return found.group(1) if found else ""


def run_check() -> None:
    """Claude'un kullaniciya soru sormadan once okudugu durum raporu (JSON)."""
    problems, warnings, adt = prerequisite_problems()
    rules_state = "yok"
    if GLOBAL_RULES.exists():
        same = RULES_SRC.exists() and GLOBAL_RULES.read_text(encoding="utf-8").strip() == rules_text().strip()
        rules_state = "ayni" if same else "farkli"
    report = {
        "ok": not problems, "problems": problems, "warnings": warnings, "adt_extension": adt,
        "mcp_token_var": bool(vscode_token()),
        "destinations": [{"id": d["id"], "sid": d.get("properties", {}).get("systemId", ""),
                          "client": d.get("properties", {}).get("client", "")} for d in load_destinations()],
        "global_rules": rules_state, "git_repo_var": (ROOT / ".git").exists(),
        "git_kurulu": bool(shutil.which("git")), "antigravity_var": (HOME / ".gemini").exists(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


# --- Sistemler -----------------------------------------------------------------------------
def build_system(dest: dict, role: str, write: bool) -> dict:
    pr = dest.get("properties", {})
    role = role.upper() if role.upper() in ("DEV", "QA", "PRD") else "DEV"
    return {"destination": dest["id"], "sid": pr.get("systemId") or dest["id"][:3],
            "client": pr.get("client", ""), "role": role, "write": write and role == "DEV",
            "namePattern": "^[ZY]", "packagePattern": "^([ZY]|\\$TMP$)",
            "_lang": pr.get("language", ""), "_user": pr.get("user", "")}


def select_systems() -> list[dict]:
    say("\n== Izinli SAP sistemleri")
    dests = {d["id"]: d for d in load_destinations()}
    chosen = []
    if ARGS.systems:
        # "DEV_100_X:DEV:write,QAS_100_X:QA"
        for item in filter(None, (s.strip() for s in ARGS.systems.split(","))):
            parts = item.split(":")
            if parts[0] not in dests:
                say(f"  uyari: '{parts[0]}' ADT destination'lari arasinda yok, atlandi")
                continue
            chosen.append(build_system(dests[parts[0]], parts[1] if len(parts) > 1 else "DEV",
                                       len(parts) > 2 and parts[2].lower() == "write"))
    else:
        ids = list(dests)
        for i, did in enumerate(ids, 1):
            say(f"  {i}) {did}")
        for token in re.split(r"[,\s]+", ask("Izin verilecek sistemlerin numaralari (or. 1,2)")):
            if token.isdigit() and 1 <= int(token) <= len(ids):
                did = ids[int(token) - 1]
                role = ask(f"  {did} rolu (DEV/QA/PRD)", "DEV").upper()
                chosen.append(build_system(dests[did], role,
                                           role == "DEV" and yes(f"  {did}: Z*/Y* objelere yazma acilsin mi?")))
    if not chosen:
        say("  Sistem secilmedi, kurulum durdu.")
        sys.exit(1)

    # Daha once kaydedilmis SAP_BASIS surumu kurulum tekrarlaninca kaybolmasin (kural 12)
    old_path = ROOT / ".claude" / "hooks" / "systems.json"
    old_basis = {s["destination"]: s.get("basis") for s in
                 (read_json(old_path).get("systems", []) if old_path.exists() else [])}
    for s in chosen:
        s["basis"] = old_basis.get(s["destination"])
    write_json(ROOT / ".claude" / "hooks" / "systems.json", {
        "_aciklama": "Erisime izinli SAP sistemlerinin TEK listesi. Sadece /connect-system ya da "
                     "tools\\setup.py ile degisir. VS Code adt.mcpServer.accessRestrictions.destinations ile ayni tutulur.",
        "systems": [{k: v for k, v in s.items() if not k.startswith("_")} for s in chosen]})
    update_claude_md_table(chosen)
    update_system_files(chosen)
    for s in chosen:
        say(f"  {s['destination']}: {s['role']}, {'Z*/Y* yazma acik' if s['write'] else 'sadece okuma'}")
    return chosen


def update_claude_md_table(systems: list[dict]) -> None:
    path = ROOT / "CLAUDE.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("| SID | Destination")) + 2
    except StopIteration:
        return
    end = start
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    lines[start:end] = [f"| {s['sid']} | {s['destination']} | {s['client']} | {s['role']} | "
                        f"{'Z*, Y*' if s['write'] else 'sadece okuma'} | `systems\\{s['sid']}.md` |"
                        for s in systems]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_system_files(systems: list[dict]) -> None:
    for s in systems:
        path = ROOT / "systems" / f"{s['sid']}.md"
        head = (f"- Destination: `{s['destination']}` (ADT)\n"
                f"- Client: {s['client']}, dil: {s['_lang']}, kullanici: {s['_user']}\n"
                f"- Rol: {s['role']} — " + ("yazma acik, sadece Z* / Y* obje ve paket" if s["write"]
                                             else "sadece okuma") + "\n")
        if path.exists():
            text = re.sub(r"(?m)^- Destination:.*\n- Client:.*\n- Rol:.*\n", head,
                          path.read_text(encoding="utf-8"), count=1)
        else:
            text = (f"# {s['sid']}\n\n{head}- Kurulum: {datetime.date.today()}\n\n"
                    "## Dogrulanmis bilgiler\n- (ilk iste doldurulur: SAP_BASIS surumu, yaratilabilir tipler)\n")
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")


# --- Hook yollari ve proje MCP onayi ------------------------------------------------------
def fix_claude_settings(project_mcp: bool) -> None:
    say("\n== Hook yollari")
    path = ROOT / ".claude" / "settings.json"
    data = read_json(path)
    hooks_dir = short_path(ROOT / ".claude" / "hooks")
    pattern = re.compile(r"[A-Za-z]:/[^\"]*?/\.claude/hooks")
    for groups in data.get("hooks", {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                hook["command"] = pattern.sub(hooks_dir, hook["command"])
    if project_mcp:
        # .mcp.json'daki sap-adt her acilista onay sormadan yuklensin
        enabled = set(data.get("enabledMcpjsonServers", [])) | {"sap-adt"}
        data["enabledMcpjsonServers"] = sorted(enabled)
    write_json(path, data)
    say(f"  {hooks_dir}")


# --- VS Code ayarlari -----------------------------------------------------------------------
def configure_vscode(systems: list[dict]) -> tuple[str, int]:
    say("\n== VS Code ayarlari")
    try:
        settings = read_json(VSCODE_SETTINGS)
    except json.JSONDecodeError:
        say("  settings.json yorum/sondaki virgul iceriyor; otomatik duzenlenemedi. Elle ekleyin:")
        say('    "adt.mcpServer.enabled": true, "adt.mcpServer.accessRestrictionsEnabled": true,')
        say(f'    "adt.mcpServer.accessRestrictions": {{"destinations": "{",".join(s["destination"] for s in systems)}",'
            ' "packages-objectChanges": "Z*,Y*"}')
        return vscode_token(), 2236
    backup(VSCODE_SETTINGS)
    settings["adt.mcpServer.enabled"] = True
    settings["adt.mcpServer.accessRestrictionsEnabled"] = True
    restrictions = settings.get("adt.mcpServer.accessRestrictions") or {}
    restrictions["destinations"] = ",".join(s["destination"] for s in systems)
    restrictions["packages-objectChanges"] = "Z*,Y*"
    settings["adt.mcpServer.accessRestrictions"] = restrictions
    if any(s["write"] for s in systems):
        settings["adt.mcpServer.enableEditFileToolForABAPObjects"] = True
    if "abapfs.mcpServer.autoStart" in settings:
        # ABAP FS'in MCP'si sifresiz ve yazma yetkili acilir, erisim korumasinin disinda kalir
        settings["abapfs.mcpServer.autoStart"] = False
    write_json(VSCODE_SETTINGS, settings, indent=4)
    say("  ADT MCP acik, sistem ve paket kisiti yazildi")
    return settings.get("adt.mcpServer.token", ""), int(settings.get("adt.mcpServer.port", 2236))


# --- sap-adt MCP baglantisi -----------------------------------------------------------------
def register_mcp(token: str, port: int) -> bool:
    say("\n== Claude Code MCP baglantisi (sap-adt)")
    if not token:
        say("  ATLANDI: adt.mcpServer.token yok. VS Code ayarlarinda 'ADT MCP Server' acik olmali; "
            "acip VS Code'u yeniden baslatin ve kurulumu tekrar calistirin.")
        return False
    entry = {"type": "http", "url": f"http://localhost:{port}/mcp",
             "headers": {"Authorization": f"Bearer {token}"}}
    if ARGS.mcp_scope == "user":
        data = read_json(CLAUDE_JSON) if CLAUDE_JSON.exists() else {}
        backup(CLAUDE_JSON)
        data.setdefault("mcpServers", {})["sap-adt"] = entry
        write_json(CLAUDE_JSON, data)
        say("  ~\\.claude.json -> sap-adt (token ekrana yazilmadi)")
    else:
        path = ROOT / ".mcp.json"
        data = read_json(path) if path.exists() else {}
        data.setdefault("mcpServers", {})["sap-adt"] = entry
        write_json(path, data)
        say("  workspace .mcp.json -> sap-adt (git'e ve pakete girmez; token ekrana yazilmadi)")
    return True


# --- Global kurallar -------------------------------------------------------------------------
def install_global_rules() -> None:
    say("\n== Global kodlama kurallari (~\\.claude\\CLAUDE.md)")
    if not RULES_SRC.exists():
        say("  docs\\global-rules.md yok, atlandi")
        return
    text = rules_text()
    mode = ARGS.global_rules
    if GLOBAL_RULES.exists():
        if GLOBAL_RULES.read_text(encoding="utf-8").strip() == text.strip():
            say("  zaten ayni")
            return
        if mode == "ask":
            mode = "replace" if yes("  Zaten global kurallariniz var. Paketteki ile degistireyim mi (eskisi yedeklenir)?", False) else "skip"
        if mode in ("skip", "install"):
            say("  mevcut kurallariniz korundu — paketteki kurallar docs\\global-rules.md'de")
            return
        backup(GLOBAL_RULES)
    elif mode == "skip":
        say("  atlandi")
        return
    GLOBAL_RULES.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_RULES.write_text(text, encoding="utf-8")
    say("  kuruldu")


# --- Son adimlar -------------------------------------------------------------------------------
def choice(value: str, question: str, default: bool) -> bool:
    return value == "yes" or (value == "ask" and yes(question, default))


def finish(mcp_ok: bool) -> None:
    say("\n== Son adimlar")
    if shutil.which("git") and not (ROOT / ".git").exists() and choice(ARGS.git, "  Git deposu acilsin mi?", True):
        subprocess.run(["git", "init", "-q"], cwd=ROOT, check=False)
        say("  git init yapildi")
    sync = ROOT / "tools" / "sync-antigravity.ps1"
    if (HOME / ".gemini").exists() and sync.exists() and choice(ARGS.antigravity, "  Antigravity'ye de aktarilsin mi?", False):
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(sync)],
                       cwd=ROOT, check=False, stdout=subprocess.DEVNULL)
        say("  Antigravity'ye aktarildi")
    say("\n== Baglanti kontrolu")
    subprocess.run([sys.executable, "-I", str(ROOT / ".claude" / "hooks" / "session-check.py")], check=False)
    say("\nKURULUM BITTI." if mcp_ok else "\nKURULUM EKSIK: MCP baglantisi kurulamadi (yukaridaki adimi izleyin).")
    say("Son adim: VS Code'da Ctrl+Shift+P -> 'Developer: Reload Window'. Sonra Claude Code'da /mcp ile "
        "sap-adt'nin bagli oldugunu kontrol edin.")


def main() -> None:
    global ARGS
    p = argparse.ArgumentParser(description="SAP ABAP workspace kurulumu")
    p.add_argument("--check", action="store_true", help="sadece durum raporu (JSON), hicbir sey yazmaz")
    p.add_argument("--yes", action="store_true", help="sorusuz kurulum (Claude bu modu kullanir)")
    p.add_argument("--systems", default="", help='"DEST:ROL[:write],..." or. "DEV_100_X:DEV:write,QAS_100_X:QA"')
    p.add_argument("--global-rules", choices=["ask", "install", "replace", "skip"], default="ask")
    p.add_argument("--git", choices=["ask", "yes", "no"], default="ask")
    p.add_argument("--antigravity", choices=["ask", "yes", "no"], default="ask")
    p.add_argument("--mcp-scope", choices=["project", "user"], default="project")
    ARGS = p.parse_args()

    if ARGS.check:
        run_check()
        return
    if ARGS.yes:
        if not ARGS.systems:
            p.error("--yes ile --systems zorunlu")
        ARGS.git = "no" if ARGS.git == "ask" else ARGS.git
        ARGS.antigravity = "no" if ARGS.antigravity == "ask" else ARGS.antigravity
        ARGS.global_rules = "install" if ARGS.global_rules == "ask" else ARGS.global_rules

    say(f"SAP ABAP workspace kurulumu — {ROOT}")
    problems, warnings, adt = prerequisite_problems()
    for w in warnings:
        say(f"  uyari: {w}")
    if problems:
        say("Kurulum durdu:")
        for prob in problems:
            say(f"  - {prob}")
        sys.exit(1)
    say(f"  on kosullar tamam (ADT: {adt})")

    systems = select_systems()
    fix_claude_settings(project_mcp=ARGS.mcp_scope == "project")
    token, port = configure_vscode(systems)
    mcp_ok = register_mcp(token, port)
    install_global_rules()
    finish(mcp_ok)


if __name__ == "__main__":
    main()

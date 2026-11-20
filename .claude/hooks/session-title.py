"""UserPromptSubmit hook: talepli oturumun basligini Jira numarasiyla koyar.

Mesajda Jira numarasi (PRJ-1234, ABC-56 ...) gecerse baslik:
  - specs\\*\\<NO>\\notes.md varsa: "<NO> <notes.md basligi>" (talebin kendisi, kalici)
  - yoksa: "<NO> <mesajin ilk kelimeleri>" (etiketler temizlenir); notes.md sonraki
    mesajlarda olusunca baslik bir kez notes.md basligina yukseltilir.
Kullanici basligi elle degistirdiyse dokunmaz.
"""
import glob
import json
import os
import re
import sys
import tempfile

JIRA_KEY = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d{1,6})\b")
# Jira numarasina benzeyen ama talep olmayan kaliplar
NOT_JIRA = {"UTF", "ISO", "SHA", "MD", "CP", "RFC", "ABAP", "HTTP", "S4", "EWM"}
# Mesaja eklenen yapistirma/IDE/ajan bloklari basliga girmesin
TAG_BLOCK = re.compile(r"<([a-z_-]+)\b[^>]*>.*?</\1>", re.S)
TAG_SINGLE = re.compile(r"</?[a-z_-]+\b[^>]*>")
WORK_SIZE = re.compile(r"\s*\((?:kucuk|buyuk|küçük|büyük) is\b.*$", re.I)
MAX_TITLE = 60
STATE_DIR = os.path.join(tempfile.gettempdir(), "claude-session-title")


def find_key(text):
    for match in JIRA_KEY.finditer(text):
        key = match.group(1)
        if key.split("-")[0] not in NOT_JIRA:
            return key
    return None


def shorten(title):
    title = " ".join(title.split())
    if len(title) > MAX_TITLE:
        title = title[:MAX_TITLE].rsplit(" ", 1)[0]
    return title.strip(" -_:,.")


def title_from_notes(key, cwd):
    for path in glob.glob(os.path.join(cwd, "specs", "*", key, "notes.md")):
        try:
            with open(path, encoding="utf-8") as notes:
                heading = notes.readline()
        except OSError:
            continue
        heading = heading.lstrip("# ").strip()
        heading = WORK_SIZE.sub("", heading)
        heading = heading.replace(key, " ").strip(" —-:")
        if heading:
            return shorten(f"{key} {heading}")
    return None


def title_from_prompt(key, prompt):
    rest = TAG_SINGLE.sub(" ", TAG_BLOCK.sub(" ", prompt))
    rest = rest.replace(f"[#{key}]", " ").replace(f"[{key}]", " ").replace(key, " ")
    rest = re.sub(r"^\s*/\S+", " ", rest)          # /abap-development gibi komut adi
    rest = " ".join(rest.split()).strip(" -_:#[]")
    return shorten(f"{key} {rest}")


def last_custom_title(transcript_path):
    title = None
    try:
        with open(transcript_path, encoding="utf-8") as transcript:
            for line in transcript:
                if '"custom-title"' in line:
                    try:
                        title = json.loads(line).get("customTitle")
                    except ValueError:
                        pass
    except OSError:
        pass
    return title


def read_state(session_id):
    try:
        with open(os.path.join(STATE_DIR, session_id), encoding="utf-8") as state:
            return json.load(state)
    except (OSError, ValueError):
        return None


def write_state(session_id, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(os.path.join(STATE_DIR, session_id), "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False)


def decide_title(data):
    session_id = data.get("session_id") or ""
    if not session_id:
        return None
    cwd = data.get("cwd") or os.getcwd()
    state = read_state(session_id)

    if state:                                       # baslik daha once konuldu
        if state.get("source") == "notes":
            return None
        current = last_custom_title(data.get("transcript_path") or "")
        if current and current != state.get("title"):
            return None                             # kullanici elle degistirmis
        title = title_from_notes(state["key"], cwd)
        if not title:
            return None
        write_state(session_id, {"key": state["key"], "title": title, "source": "notes"})
        return title

    key = find_key(data.get("prompt") or "")
    if not key:
        return None
    if last_custom_title(data.get("transcript_path") or ""):
        return None                                 # elle adlandirilmis oturum
    title = title_from_notes(key, cwd)
    source = "notes" if title else "prompt"
    title = title or title_from_prompt(key, data.get("prompt") or "")
    write_state(session_id, {"key": key, "title": title, "source": source})
    return title


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    title = decide_title(data)
    if not title:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "sessionTitle": title,
        }
    }
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=True).encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # hook hatasi kullanicinin mesajini asla engellememeli
        pass

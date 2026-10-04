"""Claude Code status line that also saves your usage for DUB.

Claude Code pipes a JSON document to stdin on every update. Only rate_limits
(5-hour and weekly windows) is used here: it is written to ~/.dub/usage.json,
which DUB reads. It makes no requests and never touches credentials.

settings.json:  "statusLine": {"type": "command", "command": "python \"<path>/dub_statusline.py\""}
"""
import json
import os
import sys
import time
from pathlib import Path

DATA = Path(os.environ.get("DUB_HOME") or Path.home() / ".dub")
USAGE = DATA / "usage.json"
WINDOWS = (("five_hour", "5h"), ("seven_day", "7d"))


def save(rate):
    try:
        old = json.loads(USAGE.read_text(encoding="utf-8"))
    except Exception:
        old = {}
    for key, _ in WINDOWS:
        w = rate.get(key) or {}
        if w.get("used_percentage") is not None:
            old[key] = {"used_percentage": float(w["used_percentage"]), "resets_at": w.get("resets_at")}
    old["ts"] = time.time()
    DATA.mkdir(exist_ok=True)
    tmp = DATA / f"usage.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(old), encoding="utf-8")
    for _ in range(3):              # DUB may be reading at that moment
        try:
            os.replace(tmp, USAGE)
            return
        except PermissionError:
            time.sleep(0.05)
    tmp.unlink(missing_ok=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        d = {}
    rate = d.get("rate_limits") or {}
    parts = []
    folder = Path((d.get("workspace") or {}).get("current_dir") or d.get("cwd") or "").name
    if folder:
        parts.append(folder)
    model = (d.get("model") or {}).get("display_name")
    if model:
        parts.append(model)
    for key, label in WINDOWS:
        w = rate.get(key) or {}
        pct = w.get("used_percentage")
        if pct is None:
            continue
        txt = f"{label} {pct:.0f}%"
        if key == "five_hour" and w.get("resets_at"):
            txt += time.strftime(" (reset %H:%M)", time.localtime(w["resets_at"]))
        parts.append(txt)
    if rate:
        try:
            save(rate)
        except Exception:
            pass
    print(" · ".join(parts))


SETTINGS = Path.home() / ".claude" / "settings.json"


def ours(cmd):
    return "dub_statusline" in str(cmd).lower().replace("-", "_")


def our_command():
    if getattr(sys, "frozen", False):          # installed dub-statusline.exe
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{Path(__file__).resolve()}"'


def edit_settings(install):
    """--install turns the status line on in Claude Code's settings.json; --uninstall removes it.
    Never touches a status line that is not this one. Exit: 0 ok, 2 another one exists, 3 error."""
    try:
        if SETTINGS.exists():
            d = json.loads(SETTINGS.read_text(encoding="utf-8"))
        else:
            d = {}
        if not isinstance(d, dict):
            return 3
        cur = (d.get("statusLine") or {}).get("command")
        if install:
            if cur and not ours(cur):
                print("You already have a status line configured; left it alone.")
                return 2
            if cur == our_command():
                return 0
            d["statusLine"] = {"type": "command", "command": our_command()}
        else:
            if cur != our_command():       # only removes this installation's status line, never another DUB one
                return 0
            del d["statusLine"]
        if SETTINGS.exists():
            bak = SETTINGS.with_name("settings.json.bak-dub")
            if not bak.exists():
                bak.write_bytes(SETTINGS.read_bytes())
        SETTINGS.parent.mkdir(exist_ok=True)
        tmp = SETTINGS.with_name(f"settings.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, SETTINGS)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 3


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--install", "--uninstall"):
        sys.exit(edit_settings(sys.argv[1] == "--install"))
    main()

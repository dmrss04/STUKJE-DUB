"""Status line do Claude Code que tambem guarda os consumos para o DUB.

O Claude Code passa um JSON pelo stdin a cada atualizacao. Daqui so se usa
rate_limits (janela de 5h e semanal) e grava-se em ~/.dub/usage.json, que o DUB le.
Nao faz pedidos a lado nenhum e nao toca em credenciais.

settings.json:  "statusLine": {"type": "command", "command": "python \"<caminho>/dub_statusline.py\""}
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
    for _ in range(3):              # o DUB pode estar a ler nesse instante
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
    if getattr(sys, "frozen", False):          # dub-statusline.exe instalado
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{Path(__file__).resolve()}"'


def edit_settings(install):
    """--install liga a status line no settings.json do Claude Code; --uninstall tira-a.
    Nunca mexe numa status line que nao seja esta. Saida: 0 ok, 2 ja existe outra, 3 erro."""
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
                print("Ja tens uma status line configurada; nao lhe mexi.")
                return 2
            if cur == our_command():
                return 0
            d["statusLine"] = {"type": "command", "command": our_command()}
        else:
            if cur != our_command():       # so tira a status line desta instalacao, nunca outra do DUB
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
        print(f"Erro: {e}")
        return 3


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--install", "--uninstall"):
        sys.exit(edit_settings(sys.argv[1] == "--install"))
    main()

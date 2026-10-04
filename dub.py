"""DUB - o Mochi, um blob lofi que vive no canto do teu ecra.
(Irmao da KIK: mesmo comportamento, design abstrato e calmo, secretaria preta.)

Modo musica: abana a cabeca ao som do que esta a tocar no PC.
Modo trabalho: senta-se ao portatil e vai-te dizendo como estao os teus Claudes.

Tudo passivo e so de leitura:
  - audio: le apenas o medidor de volume do Windows (nao grava, nao interceta nada)
  - Claude: le apenas ~/.claude/sessions/*.json (estado que o Claude Code ja escreve)
  - consumo (5h e semanal): le ~/.dub/usage.json, escrito pela status line (dub_statusline.py)
  - Ableton Link: desligado por defeito (opcional no menu)

Abrir:  pythonw dub.py      Fechar: botao direito > Sair
"""
import ctypes
import json
import math
import os
import random
import socket
import struct
import sys
import threading
import time
import wave
from collections import deque
from pathlib import Path

import tkinter as tk

HOME = Path.home()
DATA = Path(os.environ.get("DUB_HOME") or HOME / ".dub")
DATA.mkdir(exist_ok=True)
SESSIONS_DIR = HOME / ".claude" / "sessions"
EVENTS = HOME / ".kik" / "events.jsonl"   # o mesmo hook opcional da KIK serve os dois
STATE = DATA / "state.json"
USAGE = DATA / "usage.json"               # escrito pela status line (dub_statusline.py)
LOG = DATA / "kik.log"


def log(msg):
    try:
        if LOG.exists() and LOG.stat().st_size > 200_000:
            LOG.write_text("")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


# --------------------------------------------------------------------------
# Pixel art
# --------------------------------------------------------------------------
W, H = 32, 34          # grelha logica do sprite (antes do contorno)
KEY = "#ff00fe"        # cor transparente da janela

C = dict(
    body="#f1ebe1", belly="#e2dacc", shine="#fdfbf7", eye="#2a2522", blush="#f2b5a8",
    mouth="#9a4b45", bud="#2c2d33", wire="#4a4b52",
    coral="#e07a5f", red="#e07a5f", laser="#8fc1a9", white="#f7f6f2",
    desk="#3c3d43", desk_edge="#25262b", lid="#4a4c53", lid_dk="#36383e", logo="#73767e",
    glow="#cfe0f5", lamp="#2f3035", bulb_on="#ffd27a", bulb_off="#77705f", pool="#5b5546",
    mug="#ebe5da", tea="#8a5a3c", steam="#a9aeb8", sleeve="#d9c7a6", record="#121214",
    tape="#e7e1d4", tape_win="#2b2c31", walkman="#5b7c99", walkman_dk="#476580",
    phone="#24272c", screen="#cfe9df", zz="#d7dde8", outline="#1a1b1f",
)


# cores do Mochi (nome no menu, cores)
THEMES = {
    "mochi":   ("Mochi (creme)",       dict(body="#f1ebe1", belly="#e2dacc", shine="#fdfbf7", blush="#e6cfc2", cap="#2f3136", brim="#222327")),
    "matcha":  ("Matcha",              dict(body="#cbd8b8", belly="#b6c6a2", shine="#e2ebd5", blush="#bfcaa6", cap="#2f3136", brim="#222327")),
    "hojicha": ("Hojicha (areia)",     dict(body="#dcc0a3", belly="#caa98b", shine="#eedbc6", blush="#d4a993", cap="#2f3136", brim="#222327")),
    "ube":     ("Ube (lavanda)",       dict(body="#d3c8de", belly="#bfb2cc", shine="#e8e1ef", blush="#d2bccb", cap="#2f3136", brim="#222327")),
    "nevoa":   ("Nevoa (cinza-azul)",  dict(body="#ccd4db", belly="#b7c1ca", shine="#e4e9ee", blush="#c9c3c9", cap="#2f3136", brim="#222327")),
    "sesamo":  ("Sesamo preto",        dict(body="#4b4b52", belly="#3e3e45", shine="#6b6b74", blush="#5d5459", eye="#efe9df",
                                            cap="#e6e0d5", brim="#cfc8bb", bud="#9a9aa3", wire="#8a8a92")),
    "sakura":  ("Sakura (rosa palido)", dict(body="#f1dcdc", belly="#e3c8c9", shine="#faeeee", blush="#e6c4c4", cap="#2f3136", brim="#222327")),
    "momo":    ("Momo (pessego)",       dict(body="#f2cfb8", belly="#e4b9a0", shine="#fae4d6", blush="#e8b8a2", cap="#2f3136", brim="#222327")),
    "yuzu":    ("Yuzu (amarelo suave)", dict(body="#efe2a9", belly="#ddcd8f", shine="#f8f0cf", blush="#e2cf94", cap="#2f3136", brim="#222327")),
    "kinako":  ("Kinako (dourado)",     dict(body="#d8c08a", belly="#c4aa72", shine="#eadbb4", blush="#cfb07c", cap="#2f3136", brim="#222327")),
    "menta":   ("Menta",                dict(body="#bfe0d2", belly="#a6cdbd", shine="#dcefe7", blush="#b3d2c2", cap="#2f3136", brim="#222327")),
    "sora":    ("Sora (azul ceu)",      dict(body="#bcd3ea", belly="#a3bfdb", shine="#dbe8f5", blush="#b6c6dc", cap="#2f3136", brim="#222327")),
    "azuki":   ("Azuki (vermelho feijao)", dict(body="#9c5f5a", belly="#87504b", shine="#b97f79", blush="#8e5450", eye="#f3e6df",
                                            cap="#2a2526", brim="#1d1a1b", bud="#2a2526", wire="#5a4645")),
    "cafe":    ("Cafe (mocha)",         dict(body="#7a5c4a", belly="#674c3c", shine="#987a67", blush="#6f5242", eye="#f1e6da",
                                            cap="#e6dccd", brim="#cfc3b1", bud="#2a2422", wire="#4d3c33")),
    "sumi":    ("Sumi (tinta, olhos ambar)", dict(body="#26272c", belly="#1e1f23", shine="#3b3c43", blush="#33302f", eye="#ffb86b",
                                            mouth="#ffb86b", cap="#3a3b41", brim="#4a4b52", bud="#55565e", wire="#55565e", outline="#0a0a0c")),
}


def base_pose(scene="stand"):
    return dict(scene=scene, dx=0, bd=0, ho=0, eyes="open", look=0, mouth="smile",
                arms="type" if scene == "desk" else "down", led=0,
                tp=-1, zz=-1, bang=False,
                deskbottle=scene == "desk", glow=False, prop="none", lamp=False, steam=-1,
                theme="mochi", cap=False, blush=True)


def render_grid(p):
    """Devolve {(x, y): cor} ja com contorno, numa grelha (W+2) x (H+2)."""
    g = {}

    def R(x, y, w, h, c):
        for i in range(x, x + w):
            for j in range(y, y + h):
                if 0 <= i < W and 0 <= j < H:
                    g[(i, j)] = c

    def L(x0, y0, x1, y1, c):
        dx_, dy_ = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx_ + dy_
        while True:
            R(x0, y0, 1, 1, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy_:
                err += dy_; x0 += sx
            if e2 <= dx_:
                err += dx_; y0 += sy

    C = dict(globals()["C"])
    C.update(THEMES.get(p["theme"], THEMES["mochi"])[1])
    desk = p["scene"] == "desk"
    arms = p["arms"]
    asleep = p["zz"] >= 0
    sq = 1 if asleep else min(p["ho"], 2)          # achatar (beat / sono)
    brx, bry, bottom = (8.5, 8.0, 25.5) if desk else (9.0, 8.0, 33.5)
    rx, ry = brx + sq * 0.8, bry - sq * 0.9
    cx, cy = 16.0 + p["dx"], bottom - ry
    icx = int(cx)
    ey = int(round(cy - ry * 0.1))                  # linha dos olhos
    left, right = int(cx - rx + 0.5), int(cx + rx - 0.5)

    # ---- fundo da secretaria: candeeiro ----
    if desk:
        dome = C["bulb_on"] if p["lamp"] else C["bulb_off"]   # candeeiro cogumelo
        R(2, 19, 3, 1, dome); R(1, 20, 5, 2, dome)
        R(3, 22, 1, 3, C["lamp"]); R(2, 25, 3, 1, C["lamp"])

    # ---- fio (por tras do corpo) ----
    if desk:
        L(icx + 3, int(cy) + 2, 21, 24, C["wire"])
    else:
        if arms != "none":
            L(icx + 3, int(cy) + 3, 25, 30, C["wire"])
            R(24, 29, 6, 5, C["walkman"]); R(25, 30, 4, 2, C["tape_win"]); R(24, 33, 6, 1, C["walkman_dk"])

    # ---- corpo ----
    for x in range(W):
        for y in range(H):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                g[(x, y)] = C["belly"] if y + 0.5 > cy + ry * 0.45 else C["body"]
    R(int(cx - rx * 0.55), int(cy - ry * 0.65), 2, 1, C["shine"])

    # ---- bone ----
    if p["cap"]:
        top = int(cy - ry + 0.5)
        band = int(cy - ry * 0.4)
        for x in range(W):
            for y in range(top - 1, band + 1):
                if ((x + 0.5 - cx) / (rx * 0.92)) ** 2 + ((y + 0.5 - (cy - 0.6)) / ry) ** 2 <= 1:
                    g[(x, y)] = C["cap"]
        R(icx + 2, band, right - icx + 3, 1, C["brim"])        # pala
        R(icx + 4, band - 1, right - icx + 1, 1, C["brim"])
        R(icx, top - 2, 1, 1, C["cap"])

    # ---- cara ----
    e, lx = p["eyes"], p["look"]
    exl, exr = icx - 4 + lx, icx + 2 + lx
    if e == "open":
        R(exl, ey, 2, 2, C["eye"]); R(exr, ey, 2, 2, C["eye"])
    elif e == "wide":
        R(exl, ey - 1, 2, 3, C["eye"]); R(exr, ey - 1, 2, 3, C["eye"])
    elif e == "blink":
        R(exl, ey + 1, 2, 1, C["eye"]); R(exr, ey + 1, 2, 1, C["eye"])
    elif e == "closed":
        R(exl - 1, ey + 1, 3, 1, C["eye"]); R(exr, ey + 1, 3, 1, C["eye"])
    elif e == "happy":
        R(exl, ey, 2, 1, C["eye"]); R(exl - 1, ey + 1, 1, 1, C["eye"]); R(exl + 2, ey + 1, 1, 1, C["eye"])
        R(exr, ey, 2, 1, C["eye"]); R(exr - 1, ey + 1, 1, 1, C["eye"]); R(exr + 2, ey + 1, 1, 1, C["eye"])
    if p["blush"]:
        R(icx - 6, ey + 2, 2, 1, C["blush"]); R(icx + 4, ey + 2, 2, 1, C["blush"])
    m = p["mouth"]
    if m in ("smile", "grin", "flat"):
        R(icx - 1, ey + 3, 2, 1, C["eye"])
    elif m == "o":
        R(icx - 1, ey + 2, 2, 2, C["mouth"])
    elif m == "yawn":
        R(icx - 1, ey + 2, 2, 3, C["mouth"])

    # ---- phones de fio ----
    R(left, ey, 2, 2, C["bud"])
    R(right - 1, ey, 2, 2, C["bud"])

    # ---- maozinhas ----
    def nub(x, y):
        R(x, y, 2, 2, C["body"])

    if arms == "thumb":
        nub(right, ey + 1); R(right, ey, 1, 1, C["body"])
    elif arms == "bottle":   # caneca de cha
        R(right + 2, ey, 3, 3, C["mug"]); R(right + 2, ey, 3, 1, C["tea"]); R(right + 5, ey + 1, 1, 1, C["mug"])
        nub(right, ey + 1)
    elif arms == "sign":     # mostra o telemovel
        R(right + 1, ey - 6, 4, 7, C["phone"]); R(right + 2, ey - 5, 2, 5, C["screen"])
        R(right + 2, ey - 4, 1, 2, C["coral"]); R(right + 2, ey - 1, 1, 1, C["coral"])
        nub(right, ey + 1)
    elif arms == "cue":      # ajusta o phone
        nub(right - 1, ey + 2)

    # ---- secretaria (a frente) ----
    if desk:
        if p["glow"]:
            R(11, 21, 10, 1, C["glow"])
        R(10, 22, 12, 3, C["lid"]); R(10, 25, 12, 1, C["lid_dk"]); R(15, 23, 2, 1, C["logo"])
        if arms == "type" and p["tp"] >= 0:
            nub(11, 21 - (1 if p["tp"] == 0 else 0)); nub(19, 21 - (1 if p["tp"] == 1 else 0))
        prop = p["prop"]
        if prop == "tea" and p["deskbottle"]:
            R(26, 23, 3, 3, C["mug"]); R(26, 23, 3, 1, C["tea"]); R(29, 24, 1, 1, C["mug"])
            if p["steam"] >= 0:
                k = p["steam"]
                for (sx, sy) in [(27, 21), (26, 20), (27, 19)][: k + 1]:
                    R(sx, sy, 1, 1, C["steam"])
        elif prop == "vinyl":
            R(24, 19, 6, 7, C["sleeve"]); R(24, 22, 6, 1, C["coral"])
            R(30, 20, 1, 5, C["record"])
        elif prop == "tape":
            R(25, 23, 5, 3, C["tape"]); R(25, 23, 5, 1, C["coral"]); R(26, 24, 3, 1, C["tape_win"])
        R(1, 26, 30, 1, C["pool"] if p["lamp"] else C["desk"])
        if p["lamp"]:
            R(6, 26, 25, 1, C["desk"])
        R(1, 27, 30, 1, C["desk_edge"])
        R(3, 28, 1, 6, C["desk_edge"]); R(28, 28, 1, 6, C["desk_edge"])

    if p["bang"]:
        R(right + 2, 2 if desk else 10, 1, 3, C["coral"]); R(right + 2, (2 if desk else 10) + 4, 1, 1, C["coral"])

    if asleep:
        def Z(x, y):
            R(x, y, 4, 1, C["zz"]); R(x + 2, y + 1, 1, 1, C["zz"]); R(x + 1, y + 2, 1, 1, C["zz"]); R(x, y + 3, 4, 1, C["zz"])
        t = p["zz"]
        top = int(cy - ry)
        Z(22, top - 4 - t)
        if t >= 2:
            Z(27, top - 7 - (t - 2))

    out = {(x + 1, y + 1): c for (x, y), c in g.items()}
    for (x, y) in list(out):
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in out:
                out[(nx, ny)] = C["outline"]
    return out


def grid_to_tk(grid):
    rows = []
    for y in range(H + 2):
        rows.append("{" + " ".join(grid.get((x, y), KEY) for x in range(W + 2)) + "}")
    return " ".join(rows)


def make_ico(path, pose):
    """Escreve um .ico 48x48 com a cara do Mochi recortada do sprite."""
    g = render_grid(pose)
    xs = [x for x, _ in g]; ys = [y for _, y in g]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    N, S = 48, 2
    w, h = x1 - x0 + 1, y1 - y0 + 1
    while w * S > N or h * S > N:
        S -= 1
    ox, oy = (N - w * S) // 2, (N - h * S) // 2
    img = [[None] * N for _ in range(N)]
    for (x, y), c in g.items():
        for a in range(S):
            for b in range(S):
                img[oy + (y - y0) * S + b][ox + (x - x0) * S + a] = c
    pix = bytearray()
    for row in reversed(img):
        for c in row:
            pix += bytes([int(c[5:7], 16), int(c[3:5], 16), int(c[1:3], 16), 255]) if c else bytes(4)
    mask = bytes(((N + 31) // 32) * 4 * N)
    bmp = struct.pack("<IiiHHIIiiII", 40, N, N * 2, 1, 32, 0, len(pix) + len(mask), 0, 0, 0, 0) + pix + mask
    Path(path).write_bytes(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", N, N, 0, 0, 1, 32, len(bmp), 22) + bmp)


def update_shortcut_icon(theme, cap, blush):
    """Gera o icone com o visual atual e aponta o atalho DUB do ambiente de trabalho para ele.
    Usa um ficheiro por combinacao para o Windows nao mostrar o icone antigo em cache."""
    try:
        icons = DATA / "icons"
        icons.mkdir(exist_ok=True)
        pose = base_pose("stand")
        pose.update(theme=theme, cap=cap, blush=blush, eyes="happy")
        pose["arms"] = "none"
        ico = icons / f"dub_{theme}_{'bone' if cap else 'sem'}_{'b' if blush else 'n'}.ico"
        if not ico.exists():
            make_ico(ico, pose)
        import comtypes
        import comtypes.client
        comtypes.CoInitialize()
        from comtypes.client.dynamic import Dispatch
        shell = comtypes.client.CreateObject("WScript.Shell", dynamic=True)
        desktop = shell.SpecialFolders("Desktop")
        if not desktop or not Path(desktop).is_dir():
            return
        lnk = Path(desktop) / "DUB.lnk"
        frozen = getattr(sys, "frozen", False)      # a correr como DUB.exe
        exe = str(Path(sys.executable).resolve())
        installed = frozen and (Path(exe).parent / "unins000.exe").exists()   # o instalador gere o atalho
        if not lnk.exists() and (not frozen or installed):
            return
        created = not lnk.exists()
        sc = shell.CreateShortcut(str(lnk))
        if not hasattr(sc, "IconLocation"):
            sc = Dispatch(sc)
        changed = False
        # com o .exe: cria o atalho na 1a vez e corrige-o se o .exe mudar de pasta
        # (nunca mexe num atalho que aponte para outra coisa, ex. pythonw + dub.py)
        if frozen and (created or sc.TargetPath.lower().endswith("dub.exe")) and sc.TargetPath != exe:
            sc.TargetPath = exe
            sc.WorkingDirectory = str(Path(exe).parent)
            sc.Description = "DUB - o Mochi"
            changed = True
        if sc.IconLocation.split(",")[0] != str(ico):
            sc.IconLocation = str(ico)
            changed = True
        if changed:
            sc.Save()
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        if created:
            global SHORTCUT_CREATED
            SHORTCUT_CREATED = True
    except Exception as e:
        log(f"icone: {e}")


SHORTCUT_CREATED = False


# --------------------------------------------------------------------------
# Ouvir a musica (passivo)
# --------------------------------------------------------------------------
class Meter(threading.Thread):
    """Le o pico do dispositivo de saida do Windows (o mesmo das barrinhas do
    misturador de volume). Nao grava nem interceta audio."""

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.data = dict(active=False, energy=0.0, period=None, last_beat=0.0,
                         beat_index=0, drop_t=-99.0, ok=False)

    def run(self):
        try:
            import comtypes
            comtypes.CoInitialize()
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        except Exception as e:
            log(f"meter indisponivel: {e}")
            return
        meter, acquired = None, 0.0
        slow, loud, prev = 0.0, 0.0, 0.0
        onsets = deque(maxlen=16)
        last_onset = 0.0
        period, last_beat, next_beat, beat_index = None, 0.0, 0.0, 0
        active_until = 0.0
        quiet_start, quiet_end, quiet_len, dropped = None, -99.0, 0.0, True
        drop_t = -99.0
        while True:
            now = time.perf_counter()
            if meter is None or now - acquired > 5:
                try:
                    dev = AudioUtilities.GetSpeakers()
                    raw = getattr(dev, "_dev", dev)
                    meter = raw.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None) \
                        .QueryInterface(IAudioMeterInformation)
                except Exception:
                    meter = None
                acquired = now
            try:
                v = float(meter.GetPeakValue()) if meter else 0.0
            except Exception:
                v, meter = 0.0, None

            slow = slow * 0.985 + v * 0.015
            if v > 0.004:
                if now > active_until:
                    loud = max(loud, slow)
                active_until = now + 2.5
            active = now < active_until
            if active:
                loud = loud * 0.9993 + slow * 0.0007
            energy = max(0.0, min(1.0, slow / (loud * 1.25 + 1e-4))) if active else 0.0

            # deteccao de "drop": volta forte depois de >=3s calmos
            if energy < 0.45:
                if quiet_start is None:
                    quiet_start = now
            else:
                if quiet_start is not None:
                    quiet_len, quiet_end, dropped = now - quiet_start, now, False
                    quiet_start = None
                if not dropped and energy > 0.85 and quiet_len >= 3 and now - quiet_end < 6:
                    drop_t, dropped = now, True

            # onsets (kicks) e tempo
            if active and v > slow * 1.25 + 0.015 and v > prev and now - last_onset > 0.28:
                ioi = now - last_onset
                last_onset = now
                if ioi < 2.0:
                    while ioi < 0.33:
                        ioi *= 2
                    while ioi > 0.75:
                        ioi /= 2
                    onsets.append(ioi)
                    if len(onsets) >= 4:
                        period = sorted(onsets)[len(onsets) // 2]
                if period:
                    err_last, err_next = now - last_beat, now - next_beat
                    err = err_last if abs(err_last) < abs(err_next) else err_next
                    if abs(err) < period * 0.3:
                        last_beat += err * 0.35
                        next_beat += err * 0.35
                    elif now - last_beat > period * 2:
                        last_beat, next_beat = now, now + period
                        beat_index += 1
                else:
                    last_beat = now
                    beat_index += 1
            prev = v
            if period and active and now >= next_beat:
                last_beat = next_beat if now - next_beat < period else now
                next_beat = last_beat + period
                beat_index += 1
            if not active and now - active_until > 10:
                period = None
                onsets.clear()

            with self.lock:
                self.data = dict(active=active, energy=energy, period=period, last_beat=last_beat,
                                 beat_index=beat_index, drop_t=drop_t, ok=meter is not None)
            time.sleep(0.01)

    def read(self):
        with self.lock:
            return dict(self.data)


class LinkThread(threading.Thread):
    """Ableton Link opcional. So le: nunca muda tempo nem faz play/stop."""

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.data = None
        self.want = False   # ligado/desligado pelo menu

    def run(self):
        try:
            import asyncio
            import aalink
        except Exception as e:
            log(f"link indisponivel: {e}")
            return

        async def main():
            link = aalink.Link(120)
            link.quantum = 4
            try:
                link.start_stop_sync_enabled = True
            except Exception:
                pass
            seen = False
            while True:
                if link.enabled != self.want:
                    link.enabled = self.want
                d = None
                if self.want:
                    try:
                        playing = bool(link.playing)
                        seen = seen or playing
                        d = dict(peers=int(link.num_peers), tempo=float(link.tempo), beat=float(link.beat),
                                 t=time.perf_counter(), playing=playing, seen_playing=seen)
                    except Exception:
                        d = None
                with self.lock:
                    self.data = d
                await asyncio.sleep(0.02)

        try:
            asyncio.run(main())
        except Exception as e:
            log(f"link erro: {e}")

    def read(self):
        with self.lock:
            return self.data


class Music:
    def __init__(self):
        self.meter = Meter()
        self.meter.start()
        self.link = LinkThread()
        self.link.start()

    def snapshot(self):
        now = time.perf_counter()
        M = self.meter.read()
        L = self.link.read()
        if L and L["peers"] > 0:
            beat = L["beat"] + (now - L["t"]) * L["tempo"] / 60.0
            if M["active"]:
                active = True
            elif L["seen_playing"]:
                active = L["playing"]
            else:
                active = True
            return dict(active=active, phase=beat % 1.0, beat_index=int(math.floor(beat)),
                        bpm=L["tempo"], energy=M["energy"] if M["active"] else 0.7,
                        drop_ago=now - M["drop_t"], link=True)
        period = M["period"]
        span = period or 0.45
        ph = (now - M["last_beat"]) / span
        bi = M["beat_index"]
        if period and ph >= 1:
            bi += int(ph)
            ph %= 1.0
        return dict(active=M["active"], phase=min(ph, 1.0), beat_index=bi,
                    bpm=(60.0 / period) if period else None, energy=M["energy"],
                    drop_ago=now - M["drop_t"], link=False)


# --------------------------------------------------------------------------
# Claudes (so leitura)
# --------------------------------------------------------------------------
def pid_alive(pid):
    try:
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return k32.GetLastError() == 5   # acesso negado = existe
        code = ctypes.c_ulong()
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return code.value == 259             # STILL_ACTIVE
    except Exception:
        return True


class Claudes:
    NEED_TYPES = ("permission_prompt", "elicitation_dialog")

    def __init__(self):
        self.sessions = {}
        self.primed = False
        self.ev_pos = EVENTS.stat().st_size if EVENTS.exists() else 0

    def busy_count(self):
        return sum(1 for s in self.sessions.values() if s["status"] == "busy")

    def needing(self):
        return [s for s in self.sessions.values() if s["needs"]]

    def poll(self, now):
        events, seen = [], set()
        if SESSIONS_DIR.exists():
            for f in SESSIONS_DIR.glob("*.json"):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                pid, sid = d.get("pid"), d.get("sessionId")
                if not isinstance(pid, int) or not sid or not pid_alive(pid):
                    continue
                seen.add(sid)
                status = str(d.get("status") or "idle")
                s = self.sessions.get(sid)
                if s is None:
                    since = (d.get("statusUpdatedAt") or 0) / 1000 or now
                    s = dict(sid=sid, status=status, since=since, needs=False, needs_ts=0.0,
                             transcript=None, dismissed=False, reminded=0.0)
                    self.sessions[sid] = s
                    if self.primed:
                        events.append(("new", sid))
                s["raw_name"] = d.get("name") or ""
                s["user_named"] = d.get("nameSource") == "user"
                s["cwd"] = d.get("cwd") or ""
                if status != s["status"]:
                    waiting = "wait" in status.lower() or "permission" in status.lower()
                    if s["status"] == "busy" and now - s["since"] >= 4 and not waiting:
                        events.append(("done", sid))      # a espera de ti nao conta como terminado
                    s["status"], s["since"] = status, now
                    s["needs"] = False                    # qualquer mudanca (ex.: waiting -> busy) limpa o aviso
                    if waiting:
                        if not s["needs"]:
                            s.update(needs=True, needs_ts=now, dismissed=False)
                            events.append(("need", sid))
        for sid in list(self.sessions):
            if sid not in seen:
                del self.sessions[sid]
        for s in self.sessions.values():
            if s["needs"] and s["transcript"]:
                try:
                    if os.path.getmtime(s["transcript"]) > s["needs_ts"] + 2:
                        s["needs"] = False
                except OSError:
                    pass
        events += self._hook_events(now)
        self._names()
        self.primed = True
        return events

    def _hook_events(self, now):
        out = []
        try:
            if not EVENTS.exists():
                return out
            size = EVENTS.stat().st_size
            if size < self.ev_pos:
                self.ev_pos = 0
            if size == self.ev_pos:
                return out
            with EVENTS.open("rb") as f:
                f.seek(self.ev_pos)
                chunk = f.read()
            nl = chunk.rfind(b"\n")
            if nl < 0:
                return out
            self.ev_pos += nl + 1
            for line in chunk[:nl].splitlines():
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("hook_event_name") != "Notification":
                    continue
                typ = rec.get("notification_type") or ""
                msg = (rec.get("message") or "").lower()
                if typ in self.NEED_TYPES or (not typ and "permission" in msg):
                    s = self.sessions.get(rec.get("session_id"))
                    if s:
                        s.update(needs=True, needs_ts=rec.get("ts") or now, dismissed=False,
                                 transcript=rec.get("transcript_path"), reminded=now)
                        out.append(("need", s["sid"]))
        except Exception as e:
            log(f"hook events: {e}")
        return out

    def _names(self):
        base = {}
        for s in self.sessions.values():
            s["name"] = s["raw_name"] if s["user_named"] else (Path(s["cwd"]).name or s["raw_name"])
            base.setdefault(s["name"], []).append(s)
        for group in base.values():
            if len(group) > 1:
                for s in group:
                    s["name"] = s["raw_name"] or s["name"]

    def name(self, sid):
        s = self.sessions.get(sid)
        return s["name"] if s else "um Claude"


# --------------------------------------------------------------------------
# Consumo do Claude (so leitura, vem da status line)
# --------------------------------------------------------------------------
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


class Usage:
    WINDOWS = (("five_hour", "5h"), ("seven_day", "semana"))
    WARN = 80
    STALE = 3600     # mais de 1h sem novidades: pode estar desatualizado

    def __init__(self):
        self.data, self.ts, self.mtime = {}, 0.0, None

    def poll(self):
        try:
            mt = USAGE.stat().st_mtime
        except OSError:
            return
        if mt == self.mtime:
            return
        try:
            d = json.loads(USAGE.read_text(encoding="utf-8"))
        except Exception:
            return                     # a meio de uma escrita: tenta no proximo poll
        self.mtime, self.data, self.ts = mt, d, float(d.get("ts") or 0)

    def get(self, key, now):
        """(percentagem, reset) ou None. Depois do reset a janela volta a 0%."""
        w = self.data.get(key)
        if not isinstance(w, dict) or w.get("used_percentage") is None:
            return None
        pct, reset = float(w["used_percentage"]), w.get("resets_at")
        if reset and now >= reset:
            return 0.0, None
        return pct, reset

    def stale(self, now):
        return now - self.ts > self.STALE

    @staticmethod
    def segments(pct):
        return max(0, min(10, math.ceil(pct / 10)))

    @staticmethod
    def when(key, reset):
        t = time.localtime(reset)
        hm = time.strftime("%H:%M", t)
        return hm if key == "five_hour" else f"{DIAS[t.tm_wday]} {hm}"


# --------------------------------------------------------------------------
# Sons (opcionais, muito curtos)
# --------------------------------------------------------------------------
def make_sounds():
    sd = DATA / "sounds"
    sd.mkdir(exist_ok=True)
    specs = {
        "done": [659.3, 987.8],                 # resolve
        "need": [440.0, 587.3, 440.0, 587.3],    # sus4 suspenso
    }
    sr = 22050
    for name, notes in specs.items():
        path = sd / f"{name}.wav"
        if path.exists():
            continue
        frames = bytearray()
        for f in notes:
            n = int(sr * 0.085)
            for i in range(n):
                t = i / sr
                env = min(1.0, i / 60) * (1 - i / n) ** 1.5
                sq = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
                s = math.sin(2 * math.pi * f * t)   # sine puro, mais suave
                frames += struct.pack("<h", int(s * env * 0.22 * 32767))
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(bytes(frames))
    return sd


def play(sd, name):
    try:
        import winsound
        winsound.PlaySound(str(sd / f"{name}.wav"),
                           winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception:
        pass



# --------------------------------------------------------------------------
# Fonte pixel 5x7 (maiusculas, com acentos portugueses)
# --------------------------------------------------------------------------
_G = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#", "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.", "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####", "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####", "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": "###|.#.|.#.|.#.|.#.|.#.|###",             "J": "..###|...#.|...#.|...#.|#..#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#", "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#", "N": "#...#|##..#|#.#.#|#..##|#...#|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.", "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#", "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.", "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.", "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.", "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..", "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.", "1": ".#.|##.|.#.|.#.|.#.|.#.|###",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####", "3": "####.|....#|....#|.###.|....#|....#|####.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.", "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": ".###.|#....|#....|####.|#...#|#...#|.###.", "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.", "9": ".###.|#...#|#...#|.####|....#|....#|.###.",
    ".": ".|.|.|.|.|.|#", ",": ".|.|.|.|.|#|#", "!": "#|#|#|#|#|.|#", ":": ".|.|#|.|.|#|.",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..", "-": "...|...|...|###|...|...|...",
    "'": "#|#|.|.|.|.|.", "(": ".#|#.|#.|#.|#.|#.|.#", ")": "#.|.#|.#|.#|.#|.#|#.",
    "/": "....#|....#|...#.|..#..|.#...|#....|#....", "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "·": ".|.|.|#|.|.|.", "#": ".#.#.|#####|.#.#.|.#.#.|.#.#.|#####|.#.#.",
    "%": "##..#|##..#|...#.|..#..|.#...|#..##|#..##",
    "_": ".....|.....|.....|.....|.....|.....|#####","✓": ".....|....#|...#.|#..#.|.##..|.#...|.....",
    " ": "...|...|...|...|...|...|...",
}
_ACC = {"acute": [(3, -2), (2, -1)], "grave": [(1, -2), (2, -1)], "circ": [(2, -2), (1, -1), (3, -1)],
        "tilde": [(1, -2), (2, -2), (4, -2), (0, -1), (3, -1)], "ced": [(2, 7), (1, 8)]}
_MAP = {"Á": ("A", "acute"), "À": ("A", "grave"), "Â": ("A", "circ"), "Ã": ("A", "tilde"),
        "É": ("E", "acute"), "Ê": ("E", "circ"), "Í": ("I", "acute"), "Ó": ("O", "acute"),
        "Ô": ("O", "circ"), "Õ": ("O", "tilde"), "Ú": ("U", "acute"), "Ç": ("C", "ced")}
FONT_TOP, FONT_LINE = 2, 12   # linhas acima da maiuscula (acentos) e altura de cada linha


def glyph(ch):
    """Devolve (largura, [(x, y), ...]) de um caractere."""
    base, acc = _MAP.get(ch, (ch, None))
    rows = _G.get(base, _G["?"]).split("|")
    w = len(rows[0])
    pts = [(x, y) for y, r in enumerate(rows) for x, v in enumerate(r) if v == "#"]
    if acc:
        off = 1 if w == 3 else 0
        pts += [(x - off, y) for x, y in _ACC[acc]]
    return w, pts


def text_width(t):
    return sum(glyph(ch)[0] + 1 for ch in t) - 1 if t else 0


def wrap_pixel(text, max_units):
    lines, cur = [], ""
    for word in text.upper().split():
        cand = (cur + " " + word).strip()
        if text_width(cand) <= max_units or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# A app
# --------------------------------------------------------------------------
PROPS = ["tea", "tea", "vinyl", "tape", "none"]

DONE_MSGS = ["{n} terminou", "{n} está pronto"]
NEED_MSGS = ["{n} precisa de ti", "{n} está à espera da tua permissão"]


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DUB")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", KEY)
        self.root.config(bg=KEY)

        self.st = self.load_state()
        self.mode = self.st["mode"]
        self.S = self.st["scale"]
        self.music = Music()
        self.music.link.want = self.st["link"]
        self.claudes = Claudes()
        self.usage = Usage()
        self.sd = make_sounds()

        self.cache = {}
        self.cur_key = None
        self.asleep = False
        self.action = None          # (nome, ate, depois)
        self.next_idle = time.time() + 6
        self.next_blink = time.time() + 3
        self.blink_until = 0.0
        self.last_music = time.time()
        self.last_activity = time.time()
        self.last_life = time.time()
        self.last_poll = 0.0
        self.last_save = time.time()
        self.link_peers = 0
        self.bubbles = deque()
        self.bubble = None          # (texto, ate, tipo)
        self.hud_key = None
        self.prop = random.choice(PROPS)
        self.next_prop = time.time() + random.uniform(900, 2400)

        self.canvas = tk.Canvas(self.root, bg=KEY, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.sprite = self.canvas.create_image(0, 0, anchor="s")
        self.font = ("Segoe UI", 9)
        self.small = ("Segoe UI", 8)
        self.layout(first=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_menu)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        h = time.localtime().tm_hour
        self.say("boa noite" if h >= 20 or h < 6 else "bom dia" if h < 12 else "boa tarde", 3)
        self.refresh_icon()
        self.root.after(33, self.tick)

    # ---------------- estado persistente ----------------
    def load_state(self):
        st = dict(mode="work", scale=5, x=None, y=None, energy=80.0, music_seconds=0.0,
                  saved_at=time.time(), snd_work=True, snd_music=False, link=False,
                  theme="mochi", cap=False, blush=True, hud=True,
                  usage_mode="small", usage_warned={})   # usage_warned: janela -> reset ja avisado
        saved = {}
        try:
            saved = json.loads(STATE.read_text(encoding="utf-8"))
            st.update(saved)
        except Exception:
            pass
        if st.pop("usage_hud", True) is False and "usage_mode" not in saved:
            st["usage_mode"] = "off"
        away = max(0.0, time.time() - st["saved_at"])
        st["energy"] = min(100.0, st["energy"] + away / 30.0)   # dormiu enquanto estava fechado
        return st

    def save_state(self):
        try:
            self.st.update(mode=self.mode, scale=self.S, x=self.root.winfo_x(), y=self.root.winfo_y(),
                           saved_at=time.time(), link=self.music.link.want)
            STATE.write_text(json.dumps(self.st), encoding="utf-8")
        except Exception as e:
            log(f"save: {e}")

    # ---------------- janela ----------------
    def window_width(self, big=None):
        big = self.st["usage_mode"] == "big" if big is None else big
        return max(self.sw + (184 if big else 88), 260)    # margens para os quadrados e o consumo

    def layout(self, first=False):
        self.sw, self.sh = (W + 2) * self.S, (H + 2) * self.S
        self.ww = self.window_width()
        self.wh = self.sh + 96
        if first and self.st["x"] is not None:
            x, y = self.st["x"], self.st["y"]
        elif first:
            x = self.root.winfo_screenwidth() - self.ww - 30
            y = self.root.winfo_screenheight() - self.wh - 60
        else:
            x, y = self.root.winfo_x(), self.root.winfo_y()
        self.root.geometry(f"{self.ww}x{self.wh}+{x}+{y}")
        self.canvas.config(width=self.ww, height=self.wh)
        self.canvas.coords(self.sprite, self.ww // 2, self.wh)
        self.sprite_top = self.wh - self.sh
        self.cache.clear()
        self.cur_key = None
        self.hud_key = None
        if self.bubble:
            self.draw_bubble(self.bubble[0], self.bubble[2])

    def frame(self, pose):
        key = tuple(sorted(pose.items()))
        if key == self.cur_key:
            return
        img = self.cache.get(key)
        if img is None:
            small = tk.PhotoImage(width=W + 2, height=H + 2)
            small.put(grid_to_tk(render_grid(pose)))
            img = small.zoom(self.S)
            if len(self.cache) > 400:
                self.cache.clear()
            self.cache[key] = img
        self.canvas.itemconfig(self.sprite, image=img)
        self.cur_key = key

    # ---------------- interacao ----------------
    def on_press(self, e):
        self.drag = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y())
        self.moved = False

    def on_motion(self, e):
        ddx, ddy = e.x_root - self.drag[0], e.y_root - self.drag[1]
        if abs(ddx) + abs(ddy) > 4:
            self.moved = True
        if self.moved:
            self.root.geometry(f"+{self.drag[2] + ddx}+{self.drag[3] + ddy}")

    def on_release(self, e):
        if self.moved:
            self.save_state()
            return
        self.last_activity = time.time()
        if self.asleep:
            self.wake("ha? to acordado!")
            return
        needing = [s for s in self.claudes.needing() if not s["dismissed"]]
        if needing or self.bubble:
            for s in needing:
                s["dismissed"] = True
            self.bubble = None
            self.bubbles.clear()
            self.canvas.delete("bubble")
            if needing:
                self.set_action("thumb", 1.2)
            return
        self.set_mode("music" if self.mode == "work" else "work")

    def set_mode(self, mode):
        self.mode = mode
        self.say("modo música" if mode == "music" else "modo trabalho", 2)
        self.save_state()

    def on_menu(self, e):
        m = tk.Menu(self.root, tearoff=0)
        hours = self.st["music_seconds"] / 3600
        m.add_command(label=f"DUB  ·  {hours:.1f}h de música juntos  ·  energia {int(self.st['energy'])}%",
                      state="disabled")
        m.add_separator()
        if self.claudes.sessions:
            for s in sorted(self.claudes.sessions.values(), key=lambda s: s["name"].lower()):
                mins = int((time.time() - s["since"]) / 60)
                if s["needs"]:
                    txt = f"!  {s['name']}  -  precisa de ti"
                elif s["status"] == "busy":
                    txt = f"●  {s['name']}  -  a trabalhar ({mins} min)"
                else:
                    txt = f"○  {s['name']}  -  livre"
                m.add_command(label=txt, state="disabled")
        else:
            m.add_command(label="(nenhum Claude ativo)", state="disabled")
        m.add_separator()
        now = time.time()
        rows = [(label, key, self.usage.get(key, now)) for key, label in Usage.WINDOWS]
        if any(g for _, _, g in rows):
            old = ""
            if self.usage.stale(now):
                old = f"  ·  há {int((now - self.usage.ts) / 3600)}h"
            for label, key, g in rows:
                if not g:
                    continue
                pct, reset = g
                n = Usage.segments(pct)
                bar = "▓" * n + "░" * (10 - n)
                txt = f"Consumo {label}:  {pct:.0f}%  {bar}"
                if reset:
                    txt += f"  ·  reset {Usage.when(key, reset)}"
                m.add_command(label=txt + old, state="disabled")
        else:
            m.add_command(label="(consumo: aparece depois da próxima resposta de um Claude)", state="disabled")
        um = tk.Menu(m, tearoff=0)
        uvar = tk.StringVar(value=self.st["usage_mode"])
        for val, label in (("off", "Desligado"), ("small", "Barras pequenas"), ("big", "Barras grandes com %")):
            um.add_radiobutton(label=label, variable=uvar, value=val,
                               command=lambda v=val: self.set_usage_mode(v))
        m.add_cascade(label="Consumo no ecrã", menu=um)
        m.add_separator()
        mv = tk.StringVar(value=self.mode)
        m.add_radiobutton(label="Modo musica", variable=mv, value="music", command=lambda: self.set_mode("music"))
        m.add_radiobutton(label="Modo trabalho", variable=mv, value="work", command=lambda: self.set_mode("work"))
        m.add_separator()
        sw = tk.BooleanVar(value=self.st["snd_work"])
        smu = tk.BooleanVar(value=self.st["snd_music"])
        lk = tk.BooleanVar(value=self.music.link.want)
        m.add_checkbutton(label="Som nos avisos (modo trabalho)", variable=sw,
                          command=lambda: self.toggle("snd_work", sw.get()))
        m.add_checkbutton(label="Som nos avisos (modo musica)", variable=smu,
                          command=lambda: self.toggle("snd_music", smu.get()))
        m.add_checkbutton(label="Ableton Link (liga primeiro no Ableton)", variable=lk,
                          command=lambda: self.toggle_link(lk.get()))
        cores = tk.Menu(m, tearoff=0)
        tv = tk.StringVar(value=self.st["theme"])
        for key, (label, _) in THEMES.items():
            cores.add_radiobutton(label=label, variable=tv, value=key,
                                  command=lambda k=key: self.toggle("theme", k))
        m.add_cascade(label="Cor", menu=cores)
        cv = tk.BooleanVar(value=self.st["cap"])
        bv = tk.BooleanVar(value=self.st["blush"])
        m.add_checkbutton(label="Bone", variable=cv, command=lambda: self.toggle("cap", cv.get()))
        m.add_checkbutton(label="Bochechas", variable=bv, command=lambda: self.toggle("blush", bv.get()))
        hv = tk.BooleanVar(value=self.st["hud"])
        m.add_checkbutton(label="Mostrar quadrados dos Claudes", variable=hv,
                          command=lambda: self.toggle("hud", hv.get()))
        size = tk.Menu(m, tearoff=0)
        for label, s in (("Pequeno", 3), ("Medio", 4), ("Grande", 5), ("Enorme", 6)):
            size.add_command(label=label, command=lambda s=s: self.set_scale(s))
        m.add_cascade(label="Tamanho", menu=size)
        m.add_separator()
        m.add_command(label="Sair", command=self.quit)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def toggle(self, k, v):
        self.st[k] = v
        self.save_state()
        if k in ("theme", "cap", "blush"):
            self.refresh_icon()

    def refresh_icon(self):
        args = (self.st["theme"], self.st["cap"], self.st["blush"])
        threading.Thread(target=update_shortcut_icon, args=args, daemon=True).start()

    def toggle_link(self, v):
        self.music.link.want = v
        self.say("Link ligado (so a ouvir)" if v else "Link desligado", 2.5)
        self.save_state()

    def set_usage_mode(self, mode):
        old = self.ww
        self.st["usage_mode"] = mode
        if self.window_width() != old:     # alarga/estreita a janela sem mexer o DUB do sitio
            x = self.root.winfo_x() - (self.window_width() - old) // 2
            self.root.geometry(f"+{x}+{self.root.winfo_y()}")
            self.root.update_idletasks()
            self.layout()
        self.hud_key = None
        self.save_state()

    def set_scale(self, s):
        self.S = s
        self.layout()
        self.save_state()

    def quit(self):
        self.save_state()
        self.root.destroy()

    # ---------------- falas ----------------
    def say(self, text, secs=5, kind="info", urgent=False):
        item = (text, secs, kind)
        if urgent:
            self.bubbles.appendleft(item)
        else:
            self.bubbles.append(item)

    def update_bubble(self, now):
        if self.bubble and now > self.bubble[1]:
            self.bubble = None
            self.canvas.delete("bubble")
        if not self.bubble and self.bubbles:
            text, secs, kind = self.bubbles.popleft()
            self.bubble = (text, now + secs, kind)
            self.draw_bubble(text, kind)

    def draw_bubble(self, text, kind):
        """Balao em pixel art com a fonte 5x7."""
        c = self.canvas
        c.delete("bubble")
        fill, edge = ("#fbe9e3", C["coral"]) if kind == "need" else (C["white"], C["outline"])
        P = 2                                           # tamanho de cada pixel da fonte
        lines = wrap_pixel(text, (self.ww - 40) // P)
        tw = max(text_width(l) for l in lines)
        th = len(lines) * FONT_LINE - 1
        pad = 4
        bw, bh = (tw + 2 * pad) * P, (th + 2 * pad - 4) * P
        cx = self.ww // 2
        bottom = self.sprite_top + (9 if self.mode == "work" else 15) * self.S
        x1 = cx - bw // 2
        x1 -= x1 % P
        y2 = bottom
        y1 = y2 - bh

        def px(x, y, w, h, col):
            c.create_rectangle(x, y, x + w, y + h, fill=col, width=0, tags="bubble")

        px(x1 + P, y1 + P, bw - 2 * P, bh - 2 * P, fill)       # interior
        px(x1 + P, y1, bw - 2 * P, P, edge)                     # bordas (cantos cortados)
        px(x1 + P, y2 - P, bw - 2 * P, P, edge)
        px(x1, y1 + P, P, bh - 2 * P, edge)
        px(x1 + bw - P, y1 + P, P, bh - 2 * P, edge)
        tx = cx + 2 * self.S
        tx -= tx % P
        px(tx + P, y2 - P, 2 * P, P, fill)                      # bico em escada
        px(tx, y2 - P, P, P, edge); px(tx + 3 * P, y2 - P, P, P, edge)
        px(tx + P, y2, P, P, edge); px(tx + 2 * P, y2, P, P, fill); px(tx + 3 * P, y2, P, P, edge)
        px(tx + 2 * P, y2 + P, 2 * P, P, edge)

        ty = y1 + pad * P
        for line in lines:
            lx = cx - text_width(line) * P // 2
            lx -= lx % P
            self.pixel_text(lx, ty, line, P, "#15131c", "bubble")
            ty += FONT_LINE * P

    def pixel_text(self, lx, ty, line, P, col, tag):
        for ch in line:
            w, pts = glyph(ch)
            rows = {}
            for x, y in pts:
                rows.setdefault(y, []).append(x)
            for y, xs in rows.items():          # junta pixels seguidos num so retangulo
                xs.sort()
                start = prev = xs[0]
                for x in xs[1:] + [None]:
                    if x is not None and x == prev + 1:
                        prev = x
                        continue
                    self.canvas.create_rectangle(lx + start * P, ty + y * P, lx + (prev + 1) * P,
                                                 ty + (y + 1) * P, fill=col, width=0, tags=tag)
                    if x is not None:
                        start = prev = x
            lx += (w + 1) * P

    def usage_hud_key(self):
        """O que as barras do consumo mostram agora (None = escondidas)."""
        now = time.time()
        bars = [self.usage.get(key, now) for key, _ in Usage.WINDOWS]
        mode = self.st["usage_mode"]
        if mode == "off" or not any(bars):
            return None
        stale = self.usage.stale(now)
        out = []
        for g in bars:
            pct = g[0] if g else 0.0
            if stale:
                col = "#77738a"
            elif pct >= 95:
                col = C["coral"] if int(now * 2) % 2 else "#a85a46"
            elif pct >= Usage.WARN:
                col = C["coral"]
            else:
                col = C["laser"]
            out.append((Usage.segments(pct), col, round(pct)))
        return tuple(out), stale, mode

    def draw_usage(self, key):
        """Duas barrinhas verticais (5h e 7d) no canto inferior esquerdo, fora do sprite."""
        c = self.canvas
        bars, stale, mode = key
        if mode == "big":
            return self.draw_usage_big(bars, stale)
        pad, cw, gap = 3, text_width("5H"), 4
        seg, bw = max(3, self.S - 1), 7
        bars_h = 10 * (seg + 1) - 1
        x0, y2 = 6, self.wh - 6
        y1 = y2 - (pad + bars_h + 3 + 7 + pad)
        c.create_rectangle(x0, y1, x0 + 2 * pad + 2 * cw + gap, y2, fill="#2b2d31",
                           outline=C["outline"], width=1, tags="hud")
        for i, ((n, col, _), label) in enumerate(zip(bars, ("5H", "7D"))):
            cx = x0 + pad + i * (cw + gap)
            bx = cx + (cw - bw) // 2
            for s in range(10):                       # de baixo para cima
                sy = y1 + pad + bars_h - (s + 1) * (seg + 1) + 1
                c.create_rectangle(bx, sy, bx + bw, sy + seg, width=0,
                                   fill=col if s < n else "#3a3c42", tags="hud")
            self.pixel_text(cx, y2 - pad - 7, label, 1, "#8d8a99" if stale else "#e8e6f0", "hud")

    def draw_usage_big(self, bars, stale):
        """Duas barras horizontais com a percentagem, no canto inferior esquerdo."""
        c = self.canvas
        P, pad, bw, bh = 2, 6, 68, 9
        row = 7 * P + 4 + bh
        x0, y2 = 6, self.wh - 6
        y1 = y2 - (2 * pad + 2 * row + 6)
        c.create_rectangle(x0, y1, x0 + 2 * pad + bw, y2, fill="#2b2d31",
                           outline=C["outline"], width=1, tags="hud")
        for i, ((n, col, pct), label) in enumerate(zip(bars, ("5H", "7D"))):
            ty = y1 + pad + i * (row + 6)
            self.pixel_text(x0 + pad, ty, label, P, "#8d8a99" if stale else "#e8e6f0", "hud")
            txt = f"{pct}%"
            self.pixel_text(x0 + pad + bw - text_width(txt) * P, ty, txt, P,
                            "#8d8a99" if stale else "#e8e6f0", "hud")
            by = ty + 7 * P + 4
            c.create_rectangle(x0 + pad, by, x0 + pad + bw, by + bh, fill="#3a3c42",
                               outline=C["outline"], width=1, tags="hud")
            fill = int((bw - 2) * min(pct, 100) / 100)
            if fill > 0:
                c.create_rectangle(x0 + pad + 1, by + 1, x0 + pad + 1 + fill, by + bh - 1,
                                   fill=col, width=0, tags="hud")

    def update_hud(self, m):
        dots = []
        sessions = self.claudes.sessions.values() if self.st["hud"] else []
        for s in sorted(sessions, key=lambda s: s["sid"]):
            if s["needs"] and not s["dismissed"]:     # depois de lhe tocares deixa de piscar
                dots.append(C["coral"] if int(time.time() * 2) % 2 else "#a85a46")
            elif s["status"] == "busy":
                dots.append(C["laser"])
            else:
                dots.append("#77738a")
        bpm = None   # o BPM continua a ser detetado (m["bpm"]), so nao e mostrado
        usage = self.usage_hud_key()
        key = (tuple(dots), bpm, usage)
        if key == self.hud_key:
            return
        self.hud_key = key
        c = self.canvas
        c.delete("hud")
        if usage:
            self.draw_usage(usage)
        # coluna na margem direita, fora do sprite: nunca fica por cima dos adereços
        d = max(6, int(self.S * 1.6))
        sprite_right = self.ww // 2 + self.sw // 2
        x = self.ww - 8 - (self.ww - self.window_width(False)) // 2   # nao se afastam com as barras grandes
        y = self.wh - 6
        for col in dots:
            c.create_rectangle(x - d, y - d, x, y, fill=col, outline=C["outline"], width=1, tags="hud")
            y -= d + 4
            if y - d < self.sprite_top + self.sh // 3:      # muitos Claudes: nova coluna
                y = self.wh - 6
                x -= d + 4
                if x - d <= sprite_right:
                    break
        if bpm:
            t = c.create_text(14, self.wh - 9, text=bpm, font=self.small, fill="#e8e6f0", anchor="sw", tags="hud")
            x1, y1, x2, y2 = c.bbox(t)
            r = c.create_rectangle(x1 - 4, y1 - 2, x2 + 4, y2 + 2, fill="#2b2d31", outline=C["outline"], tags="hud")
            c.tag_lower(r, t)

    # ---------------- vida ----------------
    def set_action(self, name, secs, after=None):
        self.action = (name, time.time() + secs, after)

    def wake(self, text=None):
        self.asleep = False
        self.last_activity = time.time()
        self.set_action("wake", 1.2)
        if text:
            self.say(text, 3, urgent=True)

    def handle_claude_events(self, events, now):
        for kind, sid in events:
            n = self.claudes.name(sid)
            self.last_activity = now
            if self.asleep:
                self.wake()
            snd = self.st["snd_music"] if self.mode == "music" else self.st["snd_work"]
            if kind == "done":
                self.say(random.choice(DONE_MSGS).format(n=n), 6, "done")
                self.set_action("thumb", 2.0)
                if snd:
                    play(self.sd, "done")
            elif kind == "need":
                self.say(random.choice(NEED_MSGS).format(n=n), 8, "need", urgent=True)
                if snd:
                    play(self.sd, "need")
        for s in self.claudes.needing():
            if not s["dismissed"] and now - s["reminded"] > 120:
                s["reminded"] = now
                self.say(f"{s['name']} continua à tua espera", 6, "need")

    def check_usage(self, now):
        """Avisa uma vez por janela quando o consumo passa dos 80%."""
        self.usage.poll()
        warned = self.st.setdefault("usage_warned", {})
        for key, label in Usage.WINDOWS:
            g = self.usage.get(key, now)
            if not g or not g[1] or g[0] < Usage.WARN:
                continue
            pct, reset = g
            if reset <= warned.get(key, 0) + 60:     # ja avisado nesta janela
                continue
            warned[key] = reset
            self.save_state()
            what = "das 5 horas" if key == "five_hour" else "da semana"
            self.say(f"já usaste {pct:.0f}% {what} · reset {Usage.when(key, reset)}", 8, "need")
            if self.st["snd_music"] if self.mode == "music" else self.st["snd_work"]:
                play(self.sd, "need")

    def update_life(self, now, m):
        dt = min(1.0, now - self.last_life)
        self.last_life = now
        st = self.st
        if m["active"]:
            self.last_music = now
            st["music_seconds"] += dt
        if self.asleep:
            st["energy"] += dt / 6
        elif m["active"] and self.mode == "music":
            st["energy"] -= dt / 120
        else:
            st["energy"] -= dt / 240
        st["energy"] = max(0.0, min(100.0, st["energy"]))

        if self.claudes.busy_count():
            self.last_activity = now
        if self.asleep and m["active"]:
            self.wake("ouvi um kick!")

        needs = any(not s["dismissed"] for s in self.claudes.needing())
        if not self.asleep and not self.action and not needs and not m["active"]:
            idle = now - max(self.last_music, self.last_activity)
            limit = 240 if self.mode == "music" else 600
            if st["energy"] < 15:
                limit = 90
            if idle > limit:
                self.set_action("yawn", 2.0, after="sleep")

        if self.action and now > self.action[1]:
            after = self.action[2]
            self.action = None
            if after == "sleep":
                self.asleep = True

        if now > self.next_prop:
            self.next_prop = now + random.uniform(900, 2400)
            self.prop = random.choice([x for x in PROPS if x != self.prop])

        if now > self.next_blink:
            self.blink_until = now + 0.13
            self.next_blink = now + random.uniform(2.5, 6.0)

        if not self.asleep and not self.action and now > self.next_idle:
            self.next_idle = now + random.uniform(10, 25)
            tired = st["energy"] < 40 or time.localtime().tm_hour in range(1, 7)
            if not m["active"]:
                opts = [("look_l", 1.5, 3), ("look_r", 1.5, 3), ("sip", 2.5, 2),
                        ("yawn", 1.8, 3 if tired else 1)]
                name, secs, _ = random.choices(opts, weights=[o[2] for o in opts])[0]
                self.set_action(name, secs)

    def compute_pose(self, now, m):
        desk = self.mode == "work"
        p = base_pose("desk" if desk else "stand")
        music_on = m["active"] and not self.asleep
        hour = time.localtime().tm_hour
        p.update(prop=self.prop, lamp=desk and (hour >= 19 or hour < 7),
                 theme=self.st["theme"], cap=self.st["cap"], blush=self.st["blush"])
        if desk and self.prop == "tea":
            p["steam"] = int(now * 1.5) % 3

        if self.asleep:
            p.update(eyes="closed", mouth="flat", zz=int(now * 1.5) % 4)
            if desk:
                p.update(ho=4, tp=-1)
            else:
                p.update(ho=2, bd=1)
        else:
            if desk:
                busy = self.claudes.busy_count()
                if busy:
                    rate = 4 + 3 * min(busy, 3)
                    p.update(tp=int(now * rate) % 2, glow=True)
            if music_on:
                self.dance(p, m, desk)

        if not self.asleep and self.action:
            name = self.action[0]
            if name == "look_l":
                p["look"] = -1
            elif name == "look_r":
                p["look"] = 1
            elif name == "sip":
                p.update(arms="bottle", eyes="happy", mouth="o", deskbottle=False)
            elif name == "yawn":
                p.update(eyes="closed", mouth="yawn")
            elif name == "thumb":
                p.update(arms="thumb", eyes="happy")
            elif name == "wake":
                p.update(eyes="wide", mouth="flat")

        if not self.asleep and any(not s["dismissed"] for s in self.claudes.needing()):
            blink = int(now * 2) % 2
            p.update(arms="sign", eyes="wide" if blink else "open", mouth="o", bang=bool(blink))

        if p["eyes"] in ("open", "wide") and now < self.blink_until:
            p["eyes"] = "blink"
        return p

    def dance(self, p, m, desk):
        """Calmo: aceno discreto, olhos fechados quando aquece, mao no headphone no drop."""
        ph, bi, e = m["phase"], m["beat_index"], m["energy"]
        p["ho"] = 1 if ph < 0.35 else 0
        # de 8 em 8 compassos escolhe um groove diferente (sobretudo o aceno normal)
        groove = random.Random(bi // 32).choice(["nod", "nod", "sway", "lean", "look"])
        if groove == "sway":        # balanca de um lado para o outro a cada beat
            side = -1 if bi % 2 == 0 else 1
            p.update(dx=side, look=side)
        elif groove == "lean":      # inclina para um lado durante 2 beats, depois para o outro
            side = -1 if (bi // 2) % 2 == 0 else 1
            p.update(dx=side, look=side)
            p["ho"] = min(p["ho"], 1)
        elif groove == "look":      # fica a olhar para o lado, a acenar devagar
            p["look"] = 1 if (bi // 16) % 2 == 0 else -1
            p["ho"] = 1 if ph < 0.35 and bi % 2 == 0 else 0
        if desk:
            return
        if e > 0.7 and bi % 4 == 0 and ph < 0.3:
            p["bd"] = 1
        if e > 0.75:
            p["eyes"] = "closed"
        if m["drop_ago"] < 8 or (e > 0.85 and (bi // 16) % 2 == 1):
            p["arms"] = "cue"

    # ---------------- loop ----------------
    def tick(self):
        try:
            now = time.time()
            m = self.music.snapshot()
            if now - self.last_poll > 1.0:
                self.last_poll = now
                global SHORTCUT_CREATED
                if SHORTCUT_CREATED:
                    SHORTCUT_CREATED = False
                    self.say("criei um atalho no ambiente de trabalho", 5)
                self.handle_claude_events(self.claudes.poll(now), now)
                self.check_usage(now)
                L = self.music.link.read()
                peers = L["peers"] if L else 0
                if peers and not self.link_peers:
                    self.say(f"ligado ao Ableton Link · {int(round(L['tempo']))} BPM", 4)
                self.link_peers = peers
            self.update_life(now, m)
            self.frame(self.compute_pose(now, m))
            self.update_bubble(now)
            self.update_hud(m)
            if now - self.last_save > 30:
                self.last_save = now
                self.save_state()
        except Exception as e:
            log(f"tick: {e!r}")
        self.root.after(33, self.tick)

    def run(self):
        self.root.mainloop()


def single_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", int(os.environ.get("DUB_PORT", 47812))))
        return s
    except OSError:
        return None


if __name__ == "__main__":
    lock = single_instance()
    if lock is None:
        sys.exit(0)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    App().run()

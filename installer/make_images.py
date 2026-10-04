"""Generates the installer wizard images from DUB's own sprite (uses dub.py)."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
os.environ.setdefault("DUB_HOME", tempfile.mkdtemp(prefix="dub_img_"))   # does not touch ~/.dub

spec = importlib.util.spec_from_file_location("dub", HERE.parent / "dub.py")
dub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dub)

TOP, BOTTOM = (0x3a, 0x3c, 0x45), (0x22, 0x23, 0x28)       # DUB's desk colours
CREAM, SOFT = (0xf1, 0xeb, 0xe1), (0x9a, 0x97, 0xa6)


def mochi(eyes="happy"):
    pose = dub.base_pose("stand")
    pose.update(theme="mochi", cap=False, blush=True, eyes=eyes, mouth="smile", arms="none")
    return dub.render_grid(pose)


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
    return img


def draw_sprite(img, grid, scale, cx, bottom):
    d = ImageDraw.Draw(img)
    xs = [x for x, _ in grid]; ys = [y for _, y in grid]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    ox = cx - (x1 - x0 + 1) * scale // 2
    oy = bottom - (y1 - y0 + 1) * scale
    for (x, y), c in grid.items():
        px, py = ox + (x - x0) * scale, oy + (y - y0) * scale
        d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)


def pixel_text(img, text, x, y, scale, color):
    d = ImageDraw.Draw(img)
    for ch in text.upper():
        w, pts = dub.glyph(ch)
        for gx, gy in pts:
            d.rectangle([x + gx * scale, y + gy * scale, x + (gx + 1) * scale - 1, y + (gy + 1) * scale - 1],
                        fill=color)
        x += (w + 1) * scale


def text_w(text, scale):
    return dub.text_width(text.upper()) * scale


def shadow(img, cx, y, w, h):
    ImageDraw.Draw(img).ellipse([cx - w // 2, y - h // 2, cx + w // 2, y + h // 2], fill=(0x1b, 0x1c, 0x20))


def sidebar(w, h, k):
    """Large image on the left (k = 1 or 2 depending on DPI)."""
    img = gradient(w, h)
    # subtle pixel stars
    d = ImageDraw.Draw(img)
    for sx, sy in ((24, 30), (130, 52), (60, 84), (112, 118), (30, 150), (140, 178), (18, 226), (122, 250)):
        d.rectangle([sx * k, sy * k, sx * k + k, sy * k + k], fill=(0x5c, 0x5e, 0x6a))
    scale = 6 * k
    cx, bottom = w // 2, h - 50 * k
    shadow(img, cx, bottom + 2 * k, 120 * k, 12 * k)
    draw_sprite(img, mochi(), scale, cx, bottom)
    s = 6 * k
    pixel_text(img, "DUB", (w - text_w("DUB", s)) // 2, 34 * k, s, CREAM)
    s2 = 2 * k
    pixel_text(img, "calm blob", (w - text_w("calm blob", s2)) // 2, 34 * k + 7 * s + 10 * k, s2, SOFT)
    return img


def small(w, h, k):
    """Small image in the top-right corner."""
    img = Image.new("RGB", (w, h), TOP)
    img = gradient(w, h)
    draw_sprite(img, mochi(), 1 * k + (k > 1), w // 2, h - 4 * k)
    return img


def save(img, name):
    img.save(HERE / "build" / name, format="BMP")


if __name__ == "__main__":
    (HERE / "build").mkdir(exist_ok=True)
    save(sidebar(164, 314, 1), "wizard.bmp")
    save(sidebar(328, 628, 2), "wizard@2x.bmp")
    save(small(55, 58, 1), "wizard_small.bmp")
    save(small(110, 116, 2), "wizard_small@2x.bmp")
    print("images ok")

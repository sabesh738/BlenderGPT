"""Add the year counter, population counter and captions to rendered Act 1 frames.

Reads act1_timeline.json. Works on:
  - animation frames named f00001.png ... (Blender frame numbers, 24 fps timeline)
      python3 overlay.py frames/ out.mp4            -> encodes an MP4 (needs imageio-ffmpeg)
  - storyboard stills named ..._t012.3.png (time in seconds in the name)
      python3 overlay.py stills/ --stills stills_captioned/

Style follows the reference videos: small-caps serif title + one-line subtitle bottom-right,
large year bottom-left, population with a person glyph top-right.
Fonts: --font path.ttf; otherwise tries Cormorant Garamond (downloaded once from the Google
Fonts GitHub repo into ./fonts), falling back to DejaVu Serif.
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
TL = json.loads((HERE / "act1_timeline.json").read_text())
SRC_FPS = 24
FONT_URLS = {
    "CormorantGaramond-SemiBold.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
}


def font_path(user=None):
    if user:
        return user
    d = HERE / "fonts"
    d.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        p = d / name
        if not p.exists():
            try:
                urllib.request.urlretrieve(url, p)
            except Exception:
                continue
        return str(p)
    for cand in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"):
        if Path(cand).exists():
            return cand
    return None


def interp(pairs, t):
    xs, ys = zip(*pairs)
    return float(np.interp(t, xs, ys))


def year_text(t):
    for d in TL.get("date_label", [])[::-1]:
        if d["from"] <= t < d["to"]:
            return d["text"]
    y = int(round(interp(TL["year_at"], t)))
    if y < 0:
        return f"{-y} BC"
    if y < 1000:
        return f"AD {max(y, 1)}"
    return str(y)


def caption_at(t):
    for b in TL["beats"]:
        t0, t1 = b["t"]
        if t0 <= t < t1 and b.get("caption"):
            fade = min(1.0, (t - t0) / 0.6, (t1 - t) / 0.6)
            return b["caption"], max(0.0, fade)
    return None, 0.0


class Painter:
    def __init__(self, size, font):
        w, h = size
        self.w, self.h = w, h
        s = h / 1080
        self.s = s
        self.f_title = ImageFont.truetype(font, int(58 * s)) if font else ImageFont.load_default()
        self.f_sub = ImageFont.truetype(font, int(30 * s)) if font else ImageFont.load_default()
        self.f_year = ImageFont.truetype(font, int(78 * s)) if font else ImageFont.load_default()
        self.f_pop = ImageFont.truetype(font, int(34 * s)) if font else ImageFont.load_default()
        self.f_est = ImageFont.truetype(font, int(22 * s)) if font else ImageFont.load_default()
        for f in (self.f_title, self.f_sub, self.f_year, self.f_pop, self.f_est):
            try:  # variable fonts (Cormorant) default to Light; use SemiBold like the reference
                f.set_variation_by_axes([600])
            except Exception:
                pass

    def text(self, layer, xy, txt, font, anchor, alpha=1.0):
        """White text with a soft dark shadow (drawn on an RGBA layer)."""
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 2 * self.s, xy[1] + 3 * self.s), txt, font=font, anchor=anchor,
                                fill=(0, 0, 0, int(170 * alpha)))
        sh = sh.filter(ImageFilter.GaussianBlur(4 * self.s))
        layer.alpha_composite(sh)
        ImageDraw.Draw(layer).text(xy, txt, font=font, anchor=anchor, fill=(255, 250, 240, int(255 * alpha)))

    def person(self, layer, x, y, size):
        d = ImageDraw.Draw(layer)
        r = size * 0.22
        d.ellipse([x - r, y - size * 0.95, x + r, y - size * 0.95 + 2 * r], fill=(255, 250, 240, 255))
        d.rounded_rectangle([x - size * 0.3, y - size * 0.5, x + size * 0.3, y], radius=size * 0.15,
                            fill=(255, 250, 240, 255))

    def paint(self, img, t):
        img = img.convert("RGBA")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        s, w, h = self.s, self.w, self.h
        # year, bottom-left
        self.text(layer, (48 * s, h - 44 * s), year_text(t), self.f_year, "ls")
        # population, top-right
        pop = int(round(interp(TL["population_at"], t)))
        txt = f"{pop:,}"
        x = w - 44 * s
        self.text(layer, (x, 70 * s), txt, self.f_pop, "rs")
        tw = ImageDraw.Draw(layer).textlength(txt, font=self.f_pop)
        self.person(layer, x - tw - 20 * s, 66 * s, 34 * s)
        if t < 86:
            self.text(layer, (x, 100 * s), "est.", self.f_est, "rs", alpha=0.8)
        # caption, bottom-right
        cap, a = caption_at(t)
        if cap and a > 0:
            self.text(layer, (w - 48 * s, h - 92 * s), cap["title"], self.f_title, "rs", alpha=a)
            self.text(layer, (w - 48 * s, h - 46 * s), cap["sub"], self.f_sub, "rs", alpha=a)
        img.alpha_composite(layer)
        return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--stills", help="write captioned stills to this folder instead of a video")
    ap.add_argument("--font")
    a = ap.parse_args()
    files = sorted(Path(a.frames).glob("*.png"))
    if not files:
        raise SystemExit("no frames")
    first = Image.open(files[0])
    painter = Painter(first.size, font_path(a.font))
    if a.stills:
        out = Path(a.stills)
        out.mkdir(parents=True, exist_ok=True)
        for f in files:
            m = re.search(r"_t(\d+(?:\.\d+)?)", f.stem)
            t = float(m.group(1)) if m else 0.0
            painter.paint(Image.open(f), t).save(out / (f.stem + ".jpg"), quality=90)
        print("captioned", len(files), "stills ->", out)
        return
    import imageio_ffmpeg
    nums = [int(re.sub(r"\D", "", f.stem)) for f in files]
    step = (nums[1] - nums[0]) if len(nums) > 1 else 1
    fps = SRC_FPS / step
    w, h = first.size
    writer = imageio_ffmpeg.write_frames(a.out or "act1.mp4", (w, h), fps=fps, codec="libx264",
                                         quality=8, macro_block_size=8)
    writer.send(None)
    for f, n in zip(files, nums):
        frame = painter.paint(Image.open(f), (n - 1) / SRC_FPS)
        writer.send(np.asarray(frame).tobytes())
    writer.close()
    print("wrote", a.out or "act1.mp4", f"({len(files)} frames at {fps:g} fps)")


if __name__ == "__main__":
    main()

"""
On-screen HUD for "Miami: Walking Through Time", built in the Video Sequencer
of a separate MIAMI_EDIT scene that plays the 3D scene underneath.

Layout (1920x1080):
  top     era bar (one segment per era, current one lit) + playhead + era name
  bottom-left    running list of events (newest on top), like the Tokyo/London films
  bottom-centre  year (large) and population estimate (small)
  bottom-right   culture captions ("what you're looking at")
  lower-centre   subtitles for spoken lines
"""
import os

import bpy

from mt_common import FILM_END, FPS, RES_X, RES_Y, get_scene, set_interpolation

# Whole-film era list (label, seconds). Matches ERA_BIBLE.md: 23 scenes, 6:56.
ERAS = [
    ("TEQUESTA", 18), ("SPANISH CONTACT", 20), ("SEMINOLE WAR", 18), ("TRADING POST", 16),
    ("GREAT FREEZE", 16), ("A CITY IS BORN", 16), ("CAMP MIAMI", 18), ("MIAMI BEACH", 16),
    ("THE BOOM", 16), ("1926 HURRICANE", 18), ("WORLD WAR II", 18), ("CUBAN EXILE", 16),
    ("COLD WAR", 26), ("MARIEL", 16), ("1980 UNREST", 16), ("HURRICANE ANDREW", 18),
    ("TORNADO", 16), ("2000", 16), ("HURRICANE WILMA", 18), ("KING TIDES", 16),
    ("HURRICANE IRMA", 18), ("SURFSIDE", 16), ("MIAMI NOW", 34),
]


def era_frames():
    out, f = [], 1
    for label, secs in ERAS:
        n = secs * FPS
        out.append((label, f, f + n))  # [start, end)
        f += n
    assert out[-1][2] - 1 == FILM_END, (out[-1][2] - 1, FILM_END)
    return out


# Styling
GOLD = (1.0, 0.80, 0.42)
WHITE = (0.96, 0.94, 0.90)
SHADOW = (0, 0, 0, 0.65)
BOX = (0, 0, 0, 0.32)

BAR_W, BAR_H, BAR_TOP = 1400, 6, 44  # px; BAR_TOP measured from the top edge
BAR_GAP = 3

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_TITLE_FILE = "Cinzel-Regular.ttf"          # Google Fonts, OFL (optional)
FONT_BODY_FILE = "CormorantGaramond-Medium.ttf"  # Google Fonts, OFL (optional)


def _font(fname):
    path = os.path.join(FONT_DIR, fname)
    if os.path.exists(path):
        return bpy.data.fonts.load(path, check_existing=True)
    return None


def _strips(se):
    return se.strips if hasattr(se, "strips") else se.sequences


def _strips_all(se):
    return se.strips_all if hasattr(se, "strips_all") else se.sequences_all


def _new_effect(se, name, type_, channel, f0, f1):
    coll = _strips(se)
    try:
        return coll.new_effect(name=name, type=type_, channel=channel, frame_start=f0, frame_end=f1)
    except TypeError:
        return coll.new_effect(name=name, type=type_, channel=channel, frame_start=f0, length=f1 - f0)


def _set(s, attr, value):
    if hasattr(s, attr):
        try:
            setattr(s, attr, value)
        except (TypeError, ValueError, AttributeError):
            pass


def _alpha_blend(s, alpha=1.0):
    _set(s, "blend_type", "ALPHA_OVER")
    _set(s, "blend_alpha", alpha)


def _fade(s, f0, f1, fin=0, fout=0, alpha=1.0):
    if not (fin or fout) or not hasattr(s, "blend_alpha"):
        return
    pts = []
    if fin:
        pts += [(f0, 0.0), (f0 + fin, alpha)]
    else:
        pts += [(f0, alpha)]
    if fout:
        pts += [(f1 - fout, alpha), (f1 - 1, 0.0)]
    for f, a in pts:
        s.blend_alpha = a
        s.keyframe_insert("blend_alpha", frame=f)


class Hud:
    def __init__(self, src_scene, frame_end):
        self.ed = get_scene("MIAMI_EDIT")
        r, sr = self.ed.render, src_scene.render
        r.resolution_x, r.resolution_y, r.fps = sr.resolution_x, sr.resolution_y, sr.fps
        self.ed.frame_start, self.ed.frame_end = 1, frame_end
        self.se = self.ed.sequence_editor or self.ed.sequence_editor_create()
        for s in list(_strips(self.se)):
            _strips(self.se).remove(s)
        if self.ed.animation_data and self.ed.animation_data.action:
            self.ed.animation_data.action = None
        self.end = frame_end
        self.font_title = _font(FONT_TITLE_FILE)
        self.font_body = _font(FONT_BODY_FILE)
        self.n = 0
        src = _strips(self.se).new_scene(name="SRC_3D", scene=src_scene, channel=1, frame_start=1)
        _set(src, "scene_input", "CAMERA")

    def _name(self, base):
        self.n += 1
        return f"HUD_{self.n:04d}_{base}"[:60]

    # -- primitives ---------------------------------------------------------
    def text(self, text, f0, f1, ch, x, y, size, color=WHITE, ax="LEFT", ay="BOTTOM", font=None,
             box=None, fin=8, fout=8, alpha=1.0, wrap=1.0):
        f0, f1 = max(1, int(f0)), min(self.end + 1, int(f1))
        if f1 <= f0:
            return None
        s = _new_effect(self.se, self._name("txt"), "TEXT", ch, f0, f1)
        s.text = text
        s.font_size = size
        _set(s, "color", (*color, 1.0))
        s.location = (x, y)
        # 4.2/4.3 call the anchor align_x/align_y; 4.4+ call it anchor_x/anchor_y
        for attr, val in (("align_x", ax), ("align_y", ay), ("anchor_x", ax), ("anchor_y", ay),
                          ("alignment_x", ax)):
            _set(s, attr, val)
        _set(s, "wrap_width", wrap)
        _set(s, "use_shadow", True)
        _set(s, "shadow_color", SHADOW)
        _set(s, "shadow_blur", 0.3)
        if box:
            _set(s, "use_box", True)
            _set(s, "box_color", box)
            _set(s, "box_margin", 0.008)
        f = font or self.font_body
        if f is not None:
            _set(s, "font", f)
        _alpha_blend(s, alpha)
        _fade(s, f0, f1, fin, fout, alpha)
        return s

    def rect(self, f0, f1, ch, x, y, w, h, color, alpha=1.0):
        """x, y: bottom-left corner in pixels (y measured from the bottom)."""
        f0, f1 = max(1, int(f0)), min(self.end + 1, int(f1))
        if f1 <= f0:
            return None
        s = _new_effect(self.se, self._name("rect"), "COLOR", ch, f0, f1)
        s.color = color[:3]
        _alpha_blend(s, alpha)
        t = s.transform
        t.scale_x = w / RES_X
        t.scale_y = h / RES_Y
        t.offset_x = x + w / 2 - RES_X / 2
        t.offset_y = y + h / 2 - RES_Y / 2
        return s

    # -- era bar ------------------------------------------------------------
    def era_bar(self, ch0=40):
        eras = era_frames()
        x0 = (RES_X - BAR_W) / 2
        y = RES_Y - BAR_TOP - BAR_H
        total = FILM_END
        for i, (label, fs, fe) in enumerate(eras):
            sx = x0 + BAR_W * (fs - 1) / total
            w = BAR_W * (fe - fs) / total - BAR_GAP
            ch = ch0 + i
            self.rect(1, fs, ch, sx, y, w, BAR_H, WHITE, alpha=0.22)                 # ahead
            self.rect(fs, fe, ch, sx, y - 2, w, BAR_H + 4, GOLD, alpha=0.95)         # now
            self.rect(fe, self.end + 1, ch, sx, y, w, BAR_H, WHITE, alpha=0.70)      # passed
            self.text(label, fs, fe, ch0 + 30, 0.5, (y - 30) / RES_Y, 22, color=WHITE,
                      ax="CENTER", ay="BOTTOM", font=self.font_title, fin=10, fout=10)
        # playhead
        ph = self.rect(1, self.end + 1, ch0 + 31, x0 - 1, y - 6, 2, BAR_H + 12, WHITE, alpha=1.0)
        if ph is not None:
            t = ph.transform
            start = x0 - RES_X / 2
            t.offset_x = start
            t.keyframe_insert("offset_x", frame=1)
            t.offset_x = start + BAR_W * (self.end - 1) / total
            t.keyframe_insert("offset_x", frame=self.end)
            set_interpolation(self.ed, "LINEAR", paths=("offset_x",))

    # -- year and population --------------------------------------------------
    def year(self, label, f0, f1, ch=20, fin=6, fout=6):
        return self.text(label, f0, f1, ch, 0.5, 0.085, 64, color=WHITE, ax="CENTER", ay="BOTTOM",
                         font=self.font_title, fin=fin, fout=fout)

    def year_count(self, y0, y1, f0, f1, ch=20):
        """Rolling year counter from y0 to y1 across [f0, f1). Eases in and out."""
        n = f1 - f0
        prev_val, prev_f = None, None
        for k in range(n + 1):
            u = k / max(1, n)
            u = u * u * (3 - 2 * u)
            v = int(round(y0 + (y1 - y0) * u))
            f = f0 + k
            if v != prev_val:
                if prev_val is not None:
                    self.year(str(prev_val), prev_f, f, ch=ch, fin=0, fout=0)
                prev_val, prev_f = v, f
        self.year(str(prev_val), prev_f, f1, ch=ch, fin=0, fout=0)

    def population(self, label, f0, f1, ch=21):
        return self.text(label, f0, f1, ch, 0.5, 0.058, 22, color=WHITE, ax="CENTER", ay="BOTTOM",
                         fin=10, fout=10, alpha=0.9)

    # -- event list ---------------------------------------------------------
    def event_list(self, events, ch0=24, max_lines=6):
        """events: [(frame, text)]. Newest line on top in gold, older ones fade back."""
        events = sorted(events)
        cuts = [f for f, _ in events] + [self.end + 1]
        for i in range(len(events)):
            f0, f1 = cuts[i], cuts[i + 1]
            active = list(reversed(events[: i + 1]))[:max_lines]
            for slot, (_, txt) in enumerate(active):
                newest = slot == 0
                self.text(txt, f0, f1, ch0 + slot, 0.035, 0.070 + 0.034 * slot, 19,
                          color=GOLD if newest else WHITE, ax="LEFT", ay="BOTTOM",
                          fin=12 if newest else 0, fout=0, alpha=1.0 if newest else max(0.4, 0.85 - 0.1 * slot),
                          wrap=0.62, box=BOX)

    # -- other captions -----------------------------------------------------
    def culture(self, text, f0, f1, ch=32):
        return self.text(text, f0, f1, ch, 0.965, 0.070, 20, color=WHITE, ax="RIGHT", ay="BOTTOM",
                         fin=12, fout=12, wrap=0.34, box=BOX)

    def subtitle(self, speaker, line, translation, f0, f1, ch=34):
        self.text(speaker, f0, f1, ch, 0.5, 0.235, 18, color=GOLD, ax="CENTER", ay="BOTTOM",
                  font=self.font_title, fin=6, fout=6)
        self.text(line, f0, f1, ch + 1, 0.5, 0.195, 30, color=WHITE, ax="CENTER", ay="BOTTOM", fin=6, fout=6)
        if translation:
            self.text(translation, f0, f1, ch + 2, 0.5, 0.165, 22, color=WHITE, ax="CENTER", ay="BOTTOM",
                      fin=6, fout=6, alpha=0.8)

    def title_card(self, title, subtitle, f0, f1, ch=36):
        self.text(title, f0, f1, ch, 0.08, 0.52, 96, color=WHITE, ax="LEFT", ay="BOTTOM",
                  font=self.font_title, fin=18, fout=24)
        self.text(subtitle, f0 + 10, f1, ch + 1, 0.082, 0.47, 30, color=GOLD, ax="LEFT", ay="BOTTOM",
                  font=self.font_title, fin=18, fout=24)

    def markers(self, marks):
        for f, name in marks:
            self.ed.timeline_markers.new(name, frame=f)

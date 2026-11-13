#!/usr/bin/env python3
"""VOLTRO 60-second contest demo: concept motion graphic + native Pleos Connect captures.

Usage: python3 scripts/build_pleos_demo_video_motion.py docs/submission/VOLTRO_Pleos_Demo_Motion.mp4
       python3 scripts/build_pleos_demo_video_motion.py --still <scene> <t> out.png
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = os.environ.get("VOLTRO_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) + "/"
W, H, FPS = 1920, 1080, 30
XF = 0.5

BG = (8, 11, 17)
CARD = (17, 22, 32)
HAIR = (38, 45, 60)
BLUE = (56, 128, 255)
WHITE = (244, 246, 250)
SOFT = (196, 203, 216)
MUTED = (124, 134, 152)
GREEN = (46, 196, 128)

FB = R + "artifacts/user-guide-fonts/AstaSans-Bold.ttf"
FR = R + "artifacts/user-guide-fonts/AstaSans-Regular.ttf"
_fc = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FR, size)
    return _fc[k]

LOCKUP = Image.open(R + "design/brand/voltro-lockup-white.png").convert("RGBA").crop((51, 52, 1539, 263))


def ease(x):  # smootherstep
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (x * 6 - 15) + 10)


def tracked(d, xy, text, font, fill, track=0.0):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + track
    return x


def tracked_len(text, font, track):
    return sum(font.getlength(c) + track for c in text) - track


def wrap(text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if font.getlength(test) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def layer(fn):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(ImageDraw.Draw(l), l)
    bb = l.getbbox() or (0, 0, 1, 1)
    return (l.crop(bb), bb[:2])


def fade(img, a):
    if a >= 0.999:
        return img
    c = img.copy()
    c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
    return c


def make_bg():
    im = Image.new("RGBA", (W, H), BG + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    d.ellipse((-500, -800, 1300, 420), fill=(56, 128, 255, 34))
    d.ellipse((1300, 700, 2500, 1700), fill=(56, 128, 255, 16))
    g = g.filter(ImageFilter.GaussianBlur(180))
    im.alpha_composite(g)
    return im

BASE = make_bg()


class Scene:
    dur = 5.0
    items = ()

    def draw_items(self, im, t):
        for delay, (img, (ox, oy)), rise in self.items:
            a = ease((t - delay) / 0.6)
            if a > 0:
                im.alpha_composite(fade(img, a), (ox, oy + int((1 - a) * rise)))


# ------------------------------------------------------------------ slides
class Slide(Scene):
    def __init__(self, dur, items, bg_fn=None):
        self.dur = dur
        self.items = items
        self.bg = BASE.copy()

    def frame(self, t):
        im = self.bg.copy()
        self.draw_items(im, t)
        return im


def centered(d, y, text, font, fill, track=0.0):
    x = (W - tracked_len(text, font, track)) / 2
    tracked(d, (x, y), text, font, fill, track)


def intro():
    def logo(d, L):
        lw = 640
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 400))
    def tag(d, L):
        centered(d, 560, "YOUR ROUTE. YOUR ENERGY.", F(26, True), BLUE, 6)
    def line(d, L):
        centered(d, 640, "멀리 가는 전기차를 위한, 배터리까지 계산하는 Pleos 앱", F(30), SOFT)
    return Slide(4.5, [(0.15, layer(logo), 20), (0.8, layer(tag), 12), (1.3, layer(line), 12)])


def problem():
    def kick(d, L):
        tracked(d, (160, 250), "THE PROBLEM", F(24, True), BLUE, 5)
    def head(d, L):
        d.text((160, 300), "경로를 고를 때, 시간만 볼 수는 없습니다.", font=F(68, True), fill=WHITE)
    qs = ["얼마나 덜 쓰는가", "몇 분 더 걸리는가", "도착 잔량을 지킬 수 있는가"]
    items = [(0.1, layer(kick), 12), (0.3, layer(head), 18)]
    for i, q in enumerate(qs):
        def f(d, L, i=i, q=q):
            x = 160 + i * 540
            d.line((x, 520, x + 500, 520), fill=HAIR, width=2)
            d.text((x, 545), f"0{i + 1}", font=F(26, True), fill=BLUE)
            d.text((x, 590), q, font=F(38, True), fill=WHITE)
        items.append((1.0 + i * 0.35, layer(f), 14))
    def ans(d, L):
        d.text((160, 760), "VOLTRO는 출발 전과 분기점에서, 이 세 가지를 한 화면으로 답합니다.", font=F(34), fill=SOFT)
    items.append((2.4, layer(ans), 12))
    return Slide(6.2, items)


def tech():
    items = []
    def kick(d, L):
        tracked(d, (160, 190), "UNDER THE HOOD", F(24, True), BLUE, 5)
        d.text((160, 240), "차량 데이터와 실제 도로를 연결했습니다", font=F(60, True), fill=WHITE)
    items.append((0.1, layer(kick), 16))
    rows = [("Pleos Vehicle SDK 2.3.2", "차량에서 SOC를 직접 읽고, 실패하면 그대로 알립니다"),
            ("OpenStreetMap · OSRM", "실제 지도 위에서 도로 거리와 시간을 계산합니다"),
            ("Kotlin · StateFlow · SQLite", "주행 상태를 저장해 중단돼도 이어갑니다")]
    for i, (a, b) in enumerate(rows):
        def f(d, L, i=i, a=a, b=b):
            y = 410 + i * 120
            d.line((160, y, 980, y), fill=HAIR, width=2)
            d.text((160, y + 26), a, font=F(32, True), fill=WHITE)
            d.text((160, y + 72), b, font=F(24), fill=MUTED)
        items.append((0.6 + i * 0.25, layer(f), 12))
    def nxt(d, L):
        x = 1120
        tracked(d, (x, 410), "NEXT", F(22, True), BLUE, 5)
        steps = ["정차 상태에서 사용성 확인", "국내 도로 · 내비 연동", "실차 주행으로 예측 보정"]
        for i, s in enumerate(steps):
            y = 470 + i * 100
            d.ellipse((x, y + 12, x + 16, y + 28), outline=BLUE, width=3)
            if i < 2:
                d.line((x + 8, y + 32, x + 8, y + 104), fill=HAIR, width=2)
            d.text((x + 44, y), s, font=F(32, True), fill=WHITE)
    items.append((1.4, layer(nxt), 12))
    def foot(d, L):
        d.text((160, 860), "실제 차량으로 확인하기 전까지, 절약 효과는 계산값으로만 보여드립니다.", font=F(24), fill=MUTED)
    items.append((2.0, layer(foot), 8))
    return Slide(6.2, items)


def outro():
    def f(d, L):
        lw = 560
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 410))
        centered(d, 560, "경로의 기준에, 에너지를 더하다.", F(36, True), WHITE)
    def g(d, L):
        centered(d, 640, "VOLTRO 1.2.0  ·  Pleos Connect 2.1.0  ·  2026 현대자동차그룹 차량용 앱 개발 공모전", F(22), MUTED, 1)
    return Slide(4.5, [(0.1, layer(f), 14), (0.7, layer(g), 8)])


# ------------------------------------------------------------------ screen scenes
SX0, SX1, SY0, SY1 = 640, 1840, 150, 930   # screen area
TX = 120                                   # text column left
TW = 440


class Screen(Scene):
    def __init__(self, dur, idx, img, title, desc, stat, stat_label, roi, note, full=True):
        self.dur = dur
        src = Image.open(R + img).convert("RGB")
        self.src = src
        iw, ih = src.size
        bw, bh = SX1 - SX0, SY1 - SY0
        sc = min(bw / iw, bh / ih)
        self.fw, self.fh = int(iw * sc), int(ih * sc)
        self.fx = SX0 + (bw - self.fw) // 2
        self.fy = SY0 + (bh - self.fh) // 2
        x0, y0, x1, y1 = roi
        asp = iw / ih
        rw, rh = x1 - x0, y1 - y0
        if rw / rh > asp:
            rh = rw / asp
        else:
            rw = rh * asp
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        x0 = min(max(0, cx - rw / 2), iw - rw); y0 = min(max(0, cy - rh / 2), ih - rh)
        self.roi = (x0, y0, x0 + rw, y0 + rh)
        self.full = (0, 0, iw, ih)

        st = BASE.copy()
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((self.fx, self.fy + 20, self.fx + self.fw, self.fy + self.fh + 30), 24, fill=(0, 0, 0, 170))
        st.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
        d = ImageDraw.Draw(st)
        # bezel
        d.rounded_rectangle((self.fx - 12, self.fy - 12, self.fx + self.fw + 12, self.fy + self.fh + 12), 22, fill=(4, 6, 10), outline=HAIR, width=2)
        # caption under the screen
        cap = "PLEOS CONNECT 2.1.0  ·  NATIVE CAPTURE" if full else "PLEOS CONNECT 2.1.0  ·  APP WINDOW CAPTURE"
        d.ellipse((self.fx, self.fy + self.fh + 36, self.fx + 10, self.fy + self.fh + 46), fill=GREEN)
        tracked(d, (self.fx + 22, self.fy + self.fh + 30), cap, F(17, True), MUTED, 2.5)
        if note:
            for k, ln in enumerate(wrap(note, F(19), SX1 - SX0)):
                d.text((SX0, 990 + k * 28), ln, font=F(19), fill=(98, 108, 126))
        self.static = st

        # text column
        items = []
        def chap(d, L):
            tracked(d, (TX, 300), f"{idx:02d}", F(24, True), BLUE, 3)
            d.line((TX + 52, 314, TX + 112, 314), fill=BLUE, width=2)
            tracked(d, (TX + 128, 300), "/ 06", F(24, True), MUTED, 3)
        items.append((0.15, layer(chap), 10))
        self._y = 360
        def ttl(d, L):
            y = 360
            for ln in title.split("\n"):
                d.text((TX, y), ln, font=F(52, True), fill=WHITE); y += 70
            self._y = y
        items.append((0.3, layer(ttl), 16))
        y0 = self._y + 22
        def dsc(d, L, y0=y0):
            y = y0
            for ln in wrap(desc, F(28), TW):
                d.text((TX, y), ln, font=F(28), fill=SOFT); y += 44
        items.append((0.6, layer(dsc), 12))
        ny = y0 + len(wrap(desc, F(28), TW)) * 44 + 60
        def st_(d, L, ny=ny):
            d.line((TX, ny, TX + TW, ny), fill=HAIR, width=2)
            d.text((TX, ny + 26), stat, font=F(64, True), fill=BLUE)
            d.text((TX, ny + 112), stat_label, font=F(24), fill=MUTED)
        items.append((1.0, layer(st_), 12))
        self.items = items

    def frame(self, t):
        im = self.static.copy()
        a = ease((t - 0.9) / (self.dur * 0.55))
        box = tuple(self.full[i] + (self.roi[i] - self.full[i]) * a for i in range(4))
        im.paste(self.src.resize((self.fw, self.fh), Image.BILINEAR, box=box), (self.fx, self.fy))
        self.draw_items(im, t)
        return im



# ------------------------------------------------------------------ concept motion graphic
import math

ORANGE = (255, 170, 64)
RED = (240, 92, 92)
GRAY = (70, 78, 96)


def catmull(pts, n=24):
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


class Path:
    def __init__(self, pts):
        self.p = catmull(pts)
        self.c = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.c.append(self.c[-1] + math.dist(a, b))
        self.L = self.c[-1]

    def at(self, f):
        s = max(0.0, min(1.0, f)) * self.L
        for i in range(1, len(self.c)):
            if self.c[i] >= s:
                seg = self.c[i] - self.c[i - 1] or 1
                u = (s - self.c[i - 1]) / seg
                a, b = self.p[i - 1], self.p[i]
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        return self.p[-1]

    def sub(self, f0, f1):
        s0, s1 = f0 * self.L, f1 * self.L
        pts = [self.at(f0)] + [q for q, c in zip(self.p, self.c) if s0 < c < s1] + [self.at(f1)]
        return pts


# map area (canvas coordinates)
MX0, MY0, MX1, MY1 = 110, 270, 1150, 960
SS = 2  # supersampling
SEOUL, JUNC, GANG = (230, 720), (560, 640), (1030, 380)
SHARED = Path([SEOUL, (330, 700), (450, 690), JUNC])
FAST = Path([JUNC, (680, 560), (820, 470), (930, 420), GANG])
ECO = Path([JUNC, (660, 720), (800, 700), (900, 600), (980, 480), GANG])


def lerp(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(len(a)))


class Concept(Scene):
    B1, B2, B3 = 0.0, 5.0, 9.6

    def __init__(self, dur=13.6):
        self.dur = dur
        bg = BASE.copy()
        d = ImageDraw.Draw(bg)
        # map card
        d.rounded_rectangle((MX0, MY0, MX1, MY1), 28, fill=(13, 18, 27), outline=HAIR, width=2)
        for gx in range(MX0 + 40, MX1 - 20, 40):
            for gy in range(MY0 + 40, MY1 - 20, 40):
                d.ellipse((gx - 1, gy - 1, gx + 1, gy + 1), fill=(34, 41, 56))
        # coastline hint
        coast = catmull([(1080, MY0 + 10), (1100, 420), (1120, 560), (1135, 720), (1140, MY1 - 10)])
        d.line(coast, fill=(30, 50, 80), width=3)
        tracked(d, (MX0 + 30, MY0 + 26), "SEOUL → GANGNEUNG", F(18, True), MUTED, 3)
        self.bg = bg
        self.titles = [
            ("같은 강릉행, 다른 배터리", "빨리 갈까, 아껴 갈까?"),
            ("주행 중에도", "갈림길에서 다시 물어봅니다"),
            ("출발 전 안전 확인", "모자라면 미리 막습니다"),
        ]
        self.title_layers = []
        for k, (a, b) in enumerate(self.titles):
            def f(d, L, a=a, b=b):
                tracked(d, (MX0, 128), a, F(24, True), BLUE, 2)
                d.text((MX0, 168), b, font=F(54, True), fill=WHITE)
            self.title_layers.append(layer(f))

    # ---------- helpers
    def title(self, im, t):
        bounds = [self.B1, self.B2, self.B3, self.dur]
        for k in range(3):
            a_in = ease((t - bounds[k] - 0.15) / 0.5)
            a_out = 1 - ease((t - bounds[k + 1] + 0.35) / 0.35) if k < 2 else 1
            a = min(a_in, a_out)
            if a > 0:
                img, (ox, oy) = self.title_layers[k]
                im.alpha_composite(fade(img, a), (ox, oy + int((1 - a_in) * 14)))

    def draw_map(self, t):
        w, h = (MX1 - MX0) * SS, (MY1 - MY0) * SS
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        tr = lambda pts: [((x - MX0) * SS, (y - MY0) * SS) for x, y in pts]

        draw = ease((t - 0.4) / 1.8)
        low = ease((t - self.B3 - 0.3) / 0.6)          # beat 3: everything goes red/gray
        switched = ease((t - 7.7) / 0.5) if t < self.B3 else 1.0

        fast_col = lerp(lerp(ORANGE, GRAY, switched * 0.75), RED, low)
        eco_col = lerp(BLUE, RED, low)
        shared_col = lerp(WHITE, RED, low)
        wf = int(9 * SS)
        # base routes drawn progressively
        d.line(tr(SHARED.sub(0, min(1, draw * 2.2))), fill=shared_col, width=wf, joint="curve")
        if draw > 0.45:
            u = (draw - 0.45) / 0.55
            d.line(tr(FAST.sub(0, u)), fill=fast_col, width=wf, joint="curve")
            d.line(tr(ECO.sub(0, u)), fill=eco_col, width=wf, joint="curve")
        # nodes
        for (x, y), name, (dx, dy) in ((SEOUL, "서울", (-22, 22)), (GANG, "강릉", (-90, -16))):
            if draw > 0.05:
                X, Y = (x - MX0) * SS, (y - MY0) * SS
                r = 13 * SS
                d.ellipse((X - r, Y - r, X + r, Y + r), fill=(13, 18, 27), outline=WHITE, width=4 * SS)
                d.text((X + dx * SS, Y + dy * SS), name, font=F(26 * SS, True), fill=SOFT)
        # route labels
        la = ease((t - 2.0) / 0.5) * (1 - low)
        if la > 0:
            fx, fy = FAST.at(0.45); ex, ey = ECO.at(0.4)
            d.text(((fx - MX0 - 120) * SS, (fy - MY0 - 66) * SS), "빠른 경로", font=F(26 * SS, True),
                   fill=lerp(ORANGE, GRAY, switched * 0.7) + (int(255 * la),))
            ex, ey = ECO.at(0.7)
            d.text(((ex - MX0 + 34) * SS, (ey - MY0 + 6) * SS), "절전 경로", font=F(26 * SS, True),
                   fill=BLUE + (int(255 * la),))

        # beat 2: junction pulse + car
        if self.B2 <= t < self.B3:
            tb = t - self.B2
            X, Y = (JUNC[0] - MX0) * SS, (JUNC[1] - MY0) * SS
            ph = (tb % 1.0)
            if tb < 3.0:
                rr = (14 + 34 * ph) * SS
                d.ellipse((X - rr, Y - rr, X + rr, Y + rr), outline=BLUE + (int(200 * (1 - ph)),), width=3 * SS)
            d.ellipse((X - 9 * SS, Y - 9 * SS, X + 9 * SS, Y + 9 * SS), fill=WHITE)
            # car position
            if tb < 1.4:
                pos = SHARED.at(ease(tb / 1.4) * 0.86)
            elif tb < 2.9:
                pos = SHARED.at(0.86)
            elif tb < 3.2:
                pos = SHARED.at(0.86 + 0.14 * ease((tb - 2.9) / 0.3))
            else:
                pos = ECO.at(ease((tb - 3.2) / 1.35))
            cx, cy = (pos[0] - MX0) * SS, (pos[1] - MY0) * SS
            g = 26 * SS
            d.ellipse((cx - g, cy - g, cx + g, cy + g), fill=BLUE + (60,))
            d.ellipse((cx - 14 * SS, cy - 14 * SS, cx + 14 * SS, cy + 14 * SS), fill=WHITE, outline=BLUE, width=5 * SS)

        # beat 3: lock badge on Gangneung
        if low > 0:
            X, Y = (GANG[0] - MX0) * SS, (GANG[1] - MY0) * SS
            r = 30 * SS
            d.ellipse((X - r, Y - r, X + r, Y + r), fill=RED + (int(230 * low),))
            d.text((X - 11 * SS, Y - 18 * SS), "!", font=F(34 * SS, True), fill=WHITE + (int(255 * low),))
        return L.resize((MX1 - MX0, MY1 - MY0), Image.LANCZOS)

    def card(self, d, x, y, name, col, minutes, kwh, soc0, soc1, prog, highlight, alpha, low):
        a = int(255 * alpha)
        if a <= 0:
            return
        fill = (17, 22, 32, a) if not highlight else (18, 34, 64, a)
        d.rounded_rectangle((x, y, x + 600, y + 250), 24, fill=fill, outline=(col if highlight else HAIR) + (a,), width=3 if highlight else 2)
        d.ellipse((x + 34, y + 38, x + 50, y + 54), fill=col + (a,))
        d.text((x + 66, y + 28), name, font=F(30, True), fill=WHITE + (a,))
        d.text((x + 34, y + 82), minutes, font=F(44, True), fill=WHITE + (a,))
        kv = kwh * prog
        txt = f"{kv:.1f} kWh"
        d.text((x + 566 - F(44, True).getlength(txt), y + 82), txt, font=F(44, True), fill=col + (a,))
        # battery bar
        bx0, by0, bx1, by1 = x + 34, y + 168, x + 566, y + 196
        d.rounded_rectangle((bx0, by0, bx1, by1), 14, fill=(30, 36, 50, a))
        soc = soc0 + (soc1 - soc0) * prog
        frac = max(0.0, soc) / 100
        under = soc < 15
        bc = RED if under else (GREEN if not low else RED)
        if frac > 0.004:
            d.rounded_rectangle((bx0, by0, bx0 + max(28, (bx1 - bx0) * frac), by1), 14, fill=bc + (a,))
        tx = bx0 + (bx1 - bx0) * 0.15
        d.line((tx, by0 - 10, tx, by1 + 10), fill=WHITE + (int(a * 0.8),), width=3)
        lab = f"도착 {soc:.1f}%" if soc >= 0 else "최소 잔량 미달"
        d.text((x + 34, y + 206), "최소 15%", font=F(20), fill=MUTED + (a,))
        d.text((x + 566 - F(22, True).getlength(lab), y + 204), lab, font=F(22, True), fill=(RED if under else SOFT) + (a,))

    def frame(self, t):
        im = self.bg.copy()
        self.title(im, t)
        im.alpha_composite(self.draw_map(t), (MX0, MY0))
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        X0 = 1220
        low = t >= self.B3
        if not low:
            prog = ease((t - 2.2) / 1.8)
            sw = ease((t - 7.7) / 0.5) if t >= self.B2 else 0
            a1 = ease((t - 1.4) / 0.5); a2 = ease((t - 1.7) / 0.5)
            fade_out = 1 - ease((t - self.B3 + 0.4) / 0.4)
            self.card(d, X0, 300, "빠른 경로", ORANGE, "130분", 34.6, 68, 18.6, prog, t >= self.B2 and sw < 0.5, min(a1, fade_out) * (1 - 0.45 * sw), False)
            self.card(d, X0, 580, "절전 경로", BLUE, "145분", 31.7, 68, 22.7, prog, sw >= 0.5, min(a2, fade_out), False)
            # difference chip after bars finish
            ca = ease((t - 4.0) / 0.5) * fade_out * (1 - ease((t - self.B2) / 0.4))
            if ca > 0:
                a = int(255 * ca)
                txt = "절전 경로: 2.9 kWh 덜 쓰고 15분 더"
                tw_ = F(26, True).getlength(txt)
                d.rounded_rectangle((X0, 862, X0 + tw_ + 60, 920), 29, fill=(18, 40, 80, a), outline=BLUE + (a,), width=2)
                d.text((X0 + 30, 873), txt, font=F(26, True), fill=WHITE + (a,))
            # beat 2 prompt card
            pa = ease((t - self.B2 - 1.2) / 0.5) * (1 - ease((t - 8.6) / 0.5))
            if pa > 0:
                a = int(255 * pa)
                px, py = 520, 752 + int((1 - pa) * 16)
                d.rounded_rectangle((px, py, px + 560, py + 190), 22, fill=(250, 251, 253, a))
                d.text((px + 30, py + 18), "앞 분기점에서 절전 경로로 바꾸면", font=F(24), fill=(70, 78, 96, a))
                d.text((px + 30, py + 50), "2.9 kWh 절약 · 15분 추가", font=F(38, True), fill=(30, 100, 240, a))
                press = ease((t - self.B2 - 2.5) / 0.25)
                d.rounded_rectangle((px + 30, py + 112, px + 270, py + 170), 14, fill=(232, 235, 241, a))
                d.text((px + 92, py + 125), "그대로 가기", font=F(24, True), fill=(60, 66, 80, a))
                bcol = lerp((40, 44, 56), (30, 100, 240), press)
                d.rounded_rectangle((px + 290, py + 112, px + 530, py + 170), 14, fill=bcol + (a,))
                d.text((px + 358, py + 125), "바꾸기", font=F(24, True), fill=(255, 255, 255, a))
                # pointer tap
                if 0 < press < 1 or (t - self.B2 - 2.5) < 0.6 and press >= 1:
                    rr = 10 + 30 * press
                    cx, cy = px + 410, py + 141
                    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255, int(a * (1 - press * 0.6))), width=4)
        else:
            tb = t - self.B3
            prog = ease((tb - 0.4) / 1.6)
            a1 = ease(tb / 0.5)
            self.card(d, X0, 300, "빠른 경로", ORANGE, "130분", 34.6, 20, 20 - 49.4, prog, False, a1, True)
            self.card(d, X0, 580, "절전 경로", BLUE, "145분", 31.7, 20, 20 - 45.3, prog, False, ease((tb - 0.2) / 0.5), True)
            ba = ease((tb - 2.0) / 0.5)
            if ba > 0:
                a = int(255 * ba)
                d.rounded_rectangle((X0, 862, X0 + 600, 940), 20, fill=(60, 20, 26, a), outline=RED + (a,), width=2)
                d.text((X0 + 30, 872), "출발 SOC 20% · 시작 버튼 잠김", font=F(24, True), fill=WHITE + (a,))
                d.text((X0 + 30, 904), "절전 경로도 60.4% 이상 충전해야 출발할 수 있어요", font=F(20), fill=(240, 200, 200, a))
        im.alpha_composite(L)
        # footnote
        fa = ease((t - 1.0) / 0.5)
        if fa > 0:
            n = Image.new("RGBA", (W, 40), (0, 0, 0, 0))
            ImageDraw.Draw(n).text((MX0, 6), "강릉 오프라인 데모 시나리오의 계산값입니다. 출발 SOC 68%, 전비 5.2 km/kWh, 배터리 70 kWh 가정.",
                                   font=F(19), fill=(98, 108, 126))
            im.alpha_composite(fade(n, fa), (0, 990))
        return im


S = "docs/submission/screenshots/"
G = "docs/user-guide/screenshots/"
SIM = "데모 차량값으로 계산한 수치이며 실차 측정값이 아닙니다. 주행은 좌표 재생입니다."
MAP = "지도 © OpenStreetMap contributors (ODbL) · 도로 경로 OSRM. 소비량은 계산값이고 주행은 좌표 재생입니다."
D = 6.3

SCENES = [
    intro(),
    Concept(),
    Screen(D, 1, G + "pleos-full-road.png", "Pleos 화면에서\n바로 씁니다", "차 안 디스플레이에서 실제 지도와 도로 경로를 펼쳐 놓고 비교합니다.",
           "2개 경로", "서울 시청에서 강릉역까지", (840, 0, 2560, 967), MAP),
    Screen(D, 2, G + "pleos-sdk.png", "배터리 잔량은\n차에서 읽어옵니다", "Vehicle SDK로 SOC를 가져오고, 어디서 온 값인지 함께 표시합니다.",
           "SOC 100%", "Pleos 에뮬레이터에서 읽은 값", (860, 360, 1670, 1060),
           "SOC는 Pleos Connect 에뮬레이터에서 읽은 값이며 실차 측정값이 아닙니다.", full=False),
    Screen(D, 3, S + "pleos-comparison.png", "왜 이 경로인지\n알려줍니다", "도착 잔량과 늘어나는 시간을 기준으로 고르고, 전비가 20% 나빠질 때의 결과도 같이 보여줍니다.",
           "−2.9 kWh", "절전 경로, 대신 15분 더", (870, 250, 2530, 1000), SIM),
    Screen(D, 4, G + "pleos-junction-demo.png", "갈림길에서\n한 번 더 묻습니다", "아낄 수 있는 에너지와 늘어나는 시간을 보여주고, 운전자가 고를 때까지 기다립니다.",
           "1.2 km 앞", "분기점 안내", (0, 180, 1682, 700), SIM, full=False),
    Screen(D, 5, S + "pleos-low-soc.png", "모자라면\n출발 전에 막습니다", "어느 경로로도 최소 잔량을 못 지키면 시작 버튼이 잠기고, 얼마나 충전해야 하는지 알려줍니다.",
           "SOC 20%", "기준은 자동으로 낮추지 않습니다", (1180, 230, 2560, 1006), SIM),
    Screen(D, 6, S + "pleos-report.png", "도착하면\n결과를 남깁니다", "처음 고른 경로와 무엇이 달라졌는지 기록합니다. 앱이 꺼져도 멈춘 곳부터 이어집니다.",
           "31.7 kWh", "이번 주행의 계산상 소비량", (870, 260, 2530, 1000), SIM),
    tech(),
    outro(),
]


def timeline():
    starts, t = [], 0.0
    for i, s in enumerate(SCENES):
        starts.append(t)
        t += s.dur - (XF if i < len(SCENES) - 1 else 0)
    return starts, t


def render_at(tt, starts, total):
    act = [(i, tt - starts[i]) for i, s in enumerate(SCENES) if starts[i] <= tt < starts[i] + s.dur]
    if not act:
        act = [(len(SCENES) - 1, SCENES[-1].dur - 1e-3)]
    img = SCENES[act[0][0]].frame(act[0][1])
    if len(act) > 1:
        img = Image.blend(img, SCENES[act[1][0]].frame(act[1][1]), ease(act[1][1] / XF))
    # progress hairline
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 4, W, H), fill=(20, 26, 38))
    d.rectangle((0, H - 4, int(W * tt / total), H), fill=BLUE)
    if tt < 0.6 or tt > total - 0.9:
        a = max(0.0, min(1.0, min(tt / 0.6, (total - tt) / 0.9)))
        img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, a)
    return img


def main(out):
    starts, total = timeline()
    n = int(round(total * FPS))
    print("total", round(total, 2), "s, frames", n, file=sys.stderr)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(render_at(k / FPS, starts, total).convert("RGB").tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "--still":
        starts, total = timeline()
        i, tt = int(sys.argv[2]), float(sys.argv[3])
        render_at(starts[i] + tt, starts, total).convert("RGB").save(sys.argv[4])
    else:
        main(sys.argv[1])

#!/usr/bin/env python3
"""VOLTRO ~1-minute contest demo: 3D concept motion graphic + native Pleos Connect captures with animated callouts.
Requires scripts/voltro_terrain3d.py next to this file.

Usage: python3 scripts/build_pleos_demo_video_3d.py docs/submission/VOLTRO_Pleos_Demo_3D.mp4
       python3 scripts/build_pleos_demo_video_3d.py --still <scene> <t> out.png
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



import math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voltro_terrain3d as T3

ORANGE = (255, 166, 60)
RED = (240, 92, 92)


def lerpc(a, b, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(a[k] + (b[k] - a[k]) * u) for k in range(len(a)))


def mix(a, b, u):
    return a + (b - a) * max(0.0, min(1.0, u))


def glow_line(L, pts, col, width, alpha=255, glow=True):
    """Draw a line with soft glow onto RGBA layer L."""
    if len(pts) < 2:
        return
    if glow:
        g = Image.new("RGBA", L.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).line(pts, fill=col + (int(alpha * 0.55),), width=width * 3, joint="curve")
        g = g.filter(ImageFilter.GaussianBlur(width * 1.4))
        L.alpha_composite(g)
    ImageDraw.Draw(L).line(pts, fill=col + (alpha,), width=width, joint="curve")


class Slide(Scene):
    def __init__(self, dur, items, motion=None):
        self.dur = dur
        self.items = items
        self.motion = motion
        self.bg = BASE.copy()

    def frame(self, t):
        im = self.bg.copy()
        if self.motion:
            self.motion(im, t)
        self.draw_items(im, t)
        return im


def centered(d, y, text, font, fill, track=0.0):
    x = (W - tracked_len(text, font, track)) / 2
    tracked(d, (x, y), text, font, fill, track)


# ---------------------------------------------------------------- intro / outro route motif
MOTIF = None


def motif_path():
    global MOTIF
    if MOTIF is None:
        MOTIF = T3.Route([(-40, 820), (300, 760), (620, 800), (960, 720), (1300, 760), (1600, 690), (1960, 720)])
    return MOTIF


def draw_motif(im, t, t0, t1, y_off=0, alpha=1.0):
    r = motif_path()
    f = ease((t - t0) / (t1 - t0))
    if f <= 0:
        return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pts = [(x, y + y_off) for x, y in r.sub(0, f)]
    glow_line(L, pts, BLUE, 4, int(220 * alpha))
    # faint full track
    tr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tr).line([(x, y + y_off) for x, y in r.p], fill=(56, 128, 255, int(28 * alpha)), width=2)
    im.alpha_composite(tr)
    im.alpha_composite(L)
    x, y = r.at(f); y += y_off
    d = ImageDraw.Draw(im)
    for rr, a in ((22, 40), (12, 90)):
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(56, 128, 255, int(a * alpha)))
    d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=WHITE)
    # waypoint ticks passed by the dot
    for k, wp in enumerate((0.22, 0.5, 0.78)):
        if f >= wp:
            wx, wy = r.at(wp); wy += y_off
            a = ease((f - wp) / 0.08)
            d.ellipse((wx - 6, wy - 6, wx + 6, wy + 6), outline=(56, 128, 255, int(255 * a * alpha)), width=3)


def intro():
    def logo(d, L):
        lw = 640
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 330))
    def tag(d, L):
        centered(d, 490, "YOUR ROUTE. YOUR ENERGY.", F(26, True), BLUE, 6)
    def line(d, L):
        centered(d, 570, "멀리 가는 전기차를 위한, 배터리까지 계산하는 Pleos 앱", F(30), SOFT)
    return Slide(4.8, [(0.5, layer(logo), 24), (1.1, layer(tag), 12), (1.6, layer(line), 12)],
                 motion=lambda im, t: draw_motif(im, t, 0.0, 3.6))


def outro():
    def f(d, L):
        lw = 560
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 360))
        centered(d, 510, "경로의 기준에, 에너지를 더하다.", F(36, True), WHITE)
    def g(d, L):
        centered(d, 590, "VOLTRO 1.2.0  ·  Pleos Connect 2.1.0  ·  2026 현대자동차그룹 차량용 앱 개발 공모전", F(22), MUTED, 1)
    return Slide(4.8, [(0.3, layer(f), 14), (0.9, layer(g), 8)],
                 motion=lambda im, t: draw_motif(im, t, 0.0, 3.2, y_off=40, alpha=0.8))


# ---------------------------------------------------------------- tech: animated data-flow diagram
def tech():
    items = []
    def kick(d, L):
        tracked(d, (160, 150), "UNDER THE HOOD", F(24, True), BLUE, 5)
        d.text((160, 200), "차량 데이터와 실제 도로를 연결했습니다", font=F(58, True), fill=WHITE)
    items.append((0.1, layer(kick), 16))
    NODES = {
        "sdk": ((160, 360, 560, 470), "Pleos Vehicle SDK", "배터리 SOC · 전비"),
        "map": ((160, 600, 560, 710), "OpenStreetMap · OSRM", "실제 도로 거리 · 시간"),
        "core": ((700, 470, 1000, 600), "VOLTRO", "Kotlin · StateFlow · SQLite"),
        "out": ((700, 760, 1000, 860), "추천 · 분기점 · 리포트", ""),
    }
    for k, (key, (box, a, b)) in enumerate(NODES.items()):
        def f(d, L, box=box, a=a, b=b, key=key):
            core = key == "core"
            d.rounded_rectangle(box, 20, fill=(22, 52, 110) if core else CARD, outline=BLUE if core else HAIR, width=2)
            x0, y0, x1, y1 = box
            ty = y0 + (22 if b else (y1 - y0 - 34) / 2)
            d.text((x0 + 26, ty), a, font=F(30 if core else 26, True), fill=WHITE)
            if b:
                d.text((x0 + 26, ty + 44), b, font=F(21), fill=SOFT if core else MUTED)
        items.append(({"sdk": 0.5, "map": 0.7, "core": 1.0, "out": 1.4}[key], layer(f), 12))
    EDGES = [((560, 415), (640, 415), (640, 515), (700, 515)),
             ((560, 655), (640, 655), (640, 555), (700, 555)),
             ((850, 600), (850, 760))]

    def motion(im, t):
        d = ImageDraw.Draw(im)
        for i, e in enumerate(EDGES):
            a = ease((t - 0.9 - i * 0.25) / 0.5)
            if a <= 0:
                continue
            d.line(e, fill=(56, 128, 255, int(110 * a)), width=3)
            # travelling packets
            segs = list(zip(e, e[1:]))
            lens = [math.dist(p, q) for p, q in segs]
            tot = sum(lens)
            for k in range(2):
                s = ((t * 0.55 + k * 0.5 + i * 0.17) % 1.0) * tot
                for (p, q), l in zip(segs, lens):
                    if s <= l:
                        u = s / l
                        x, y = p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
                        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(56, 128, 255, int(60 * a)))
                        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255, int(255 * a)))
                        break
                    s -= l
        # next-step timeline progress
        x = 1240
        steps = ["정차 상태에서 사용성 확인", "국내 도로 · 내비 연동", "실차 주행으로 예측 보정"]
        for i, s_ in enumerate(steps):
            y = 440 + i * 120
            a = ease((t - 1.8 - i * 0.35) / 0.4)
            if i < 2:
                seg = ease((t - 2.0 - i * 0.35) / 0.4)
                d.line((x + 9, y + 34, x + 9, y + 34 + 86 * seg), fill=(56, 128, 255, 200), width=3)
            if a > 0:
                d.ellipse((x, y + 12, x + 18, y + 30), outline=(56, 128, 255, int(255 * a)), width=3,
                          fill=(56, 128, 255, int(255 * a)) if i == 0 else None)
                d.text((x + 44, y + 2 + (1 - a) * 10), s_, font=F(32, True), fill=WHITE + (int(255 * a),))
    def nxt(d, L):
        tracked(d, (1240, 380), "NEXT", F(22, True), BLUE, 5)
    items.append((1.6, layer(nxt), 8))
    def foot(d, L):
        d.text((160, 960), "실제 차량으로 확인하기 전까지, 절약 효과는 계산값으로만 보여드립니다.", font=F(24), fill=MUTED)
    items.append((2.4, layer(foot), 8))
    return Slide(6.6, items, motion=motion)


# ---------------------------------------------------------------- 3D concept
class Concept3D(Scene):
    B2, B3 = 6.6, 11.4
    SS = 1.5
    X0 = 1300     # cards column
    CW = 580

    def __init__(self, dur=15.4):
        self.dur = dur
        self.bg = BASE.copy()
        self.titles = [("같은 강릉행, 다른 배터리", "빨리 갈까, 아껴 갈까?"),
                       ("주행 중에도", "갈림길에서 한 번 더 묻습니다"),
                       ("출발 전 안전 확인", "모자라면 미리 막습니다")]
        self.tl = []
        for a, b in self.titles:
            def f(d, L, a=a, b=b):
                tracked(d, (90, 84), a, F(24, True), BLUE, 2)
                d.text((90, 124), b, font=F(56, True), fill=WHITE)
            self.tl.append(layer(f))
        fl, fs = T3.lengths()
        self.Lf, self.Ls = fl, fs     # world lengths incl. shared

    # camera keyframes: (t, target(x,y,z), dist, yaw, pitch)
    KEYS = [(0.0, (50, 27, 0), 175, -0.55, 0.45),
            (2.4, (52, 27, 0), 125, -0.22, 0.86),
            (6.2, (52, 27, 0), 120, -0.05, 0.92),
            (7.6, (36, 30, 0), 92, -0.12, 0.98),
            (10.6, (52, 28, 0), 112, 0.02, 0.95),
            (12.2, (52, 27, 0), 128, 0.08, 1.06),
            (15.4, (52, 27, 0), 132, 0.14, 1.08)]

    def cam(self, t):
        K = self.KEYS
        for i in range(len(K) - 1):
            if K[i][0] <= t <= K[i + 1][0]:
                u = ease((t - K[i][0]) / (K[i + 1][0] - K[i][0]))
                a, b = K[i], K[i + 1]
                tgt = tuple(mix(a[1][j], b[1][j], u) for j in range(3))
                return T3.Camera(tgt, mix(a[2], b[2], u), mix(a[3], b[3], u), mix(a[4], b[4], u), 1300, 690, 640)
        a = K[-1]
        return T3.Camera(a[1], a[2], a[3], a[4], 1300, 690, 640)

    def car_pos(self, route, s):
        """s: world distance from Seoul along shared+route."""
        if s <= T3.SHARED.L:
            return T3.SHARED.at(s / T3.SHARED.L)
        return route.at((s - T3.SHARED.L) / route.L)

    def card(self, d, y, name, sub, col, km, mins, kwh, soc, hl, a, low=False):
        A = int(255 * a)
        if A <= 0:
            return
        x = self.X0
        d.rounded_rectangle((x, y, x + self.CW, y + 236), 22, fill=(18, 36, 70, int(A * 0.92)) if hl else (14, 19, 29, int(A * 0.9)),
                            outline=(col if hl else HAIR) + (A,), width=3 if hl else 2)
        d.ellipse((x + 30, y + 34, x + 46, y + 50), fill=col + (A,))
        d.text((x + 60, y + 24), name, font=F(28, True), fill=WHITE + (A,))
        d.text((x + 60 + F(28, True).getlength(name) + 14, y + 30), sub, font=F(20), fill=MUTED + (A,))
        d.text((x + 30, y + 76), f"{km:.0f} km", font=F(38, True), fill=WHITE + (A,))
        d.text((x + 200, y + 76), f"{mins:.0f}분", font=F(38, True), fill=SOFT + (A,))
        kt = f"{kwh:.1f} kWh"
        d.text((x + self.CW - 30 - F(38, True).getlength(kt), y + 76), kt, font=F(38, True), fill=col + (A,))
        bx0, by0, bx1, by1 = x + 30, y + 152, x + self.CW - 30, y + 178
        d.rounded_rectangle((bx0, by0, bx1, by1), 13, fill=(32, 38, 52, A))
        frac = max(0.0, soc) / 100
        under = soc < 15
        if frac > 0.005:
            d.rounded_rectangle((bx0, by0, bx0 + max(26, (bx1 - bx0) * frac), by1), 13, fill=(RED if under else GREEN) + (A,))
        tx = bx0 + (bx1 - bx0) * 0.15
        d.line((tx, by0 - 9, tx, by1 + 9), fill=(255, 255, 255, int(A * 0.85)), width=3)
        d.text((x + 30, y + 190), "최소 15%", font=F(19), fill=MUTED + (A,))
        lab = f"배터리 {soc:.1f}%" if soc >= 0 else "최소 잔량 미달"
        d.text((x + self.CW - 30 - F(22, True).getlength(lab), y + 188), lab, font=F(22, True), fill=(RED if under else SOFT) + (A,))

    def frame(self, t):
        im = self.bg.copy()
        cam = self.cam(t)
        ss = self.SS
        hs = mix(0.05, 1.7, ease((t - 0.2) / 2.0))
        low = ease((t - self.B3 - 0.3) / 0.6) if t >= self.B3 else 0.0
        # terrain
        TL = Image.new("RGBA", (int(W * ss), int(H * ss)), (0, 0, 0, 0))
        T3.draw_terrain(ImageDraw.Draw(TL), cam, hs, ss, 0, 0)
        TL = TL.resize((W, H), Image.BILINEAR)
        ta = ease(t / 0.8)
        im.alpha_composite(fade(TL, ta))

        P = lambda pts: [(p[0], p[1]) for p in pts]
        RL = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ease((t - 0.9) / 1.6)
        sw = ease((t - self.B2 - 3.0) / 0.5) if t >= self.B2 else 0.0
        if t >= self.B3:
            sw = 1.0
        fast_col = lerpc(lerpc(ORANGE, (110, 100, 90), sw * 0.8), RED, low)
        eco_col = lerpc(BLUE, RED, low)
        sh_col = lerpc(WHITE, RED, low)
        if draw > 0:
            glow_line(RL, P(T3.route3d(T3.SHARED, 0, min(1, draw * 2.5), cam, hs)), sh_col, 7)
            if draw > 0.4:
                u = (draw - 0.4) / 0.6
                glow_line(RL, P(T3.route3d(T3.FAST, 0, u, cam, hs)), fast_col, 7)
                glow_line(RL, P(T3.route3d(T3.ECO, 0, u, cam, hs)), eco_col, 7)
        im.alpha_composite(RL)
        d = ImageDraw.Draw(im)

        # city pins
        for xy, name, dx in ((T3.SEOUL, "서울", -70), (T3.GANG, "강릉", 20)):
            a = ease((t - 0.8) / 0.5)
            if a <= 0:
                continue
            bx, by, _ = T3.point3d(xy, cam, hs, 0.5)
            tx, ty, _ = T3.point3d(xy, cam, hs, 5.5)
            d.line((bx, by, tx, ty), fill=(255, 255, 255, int(160 * a)), width=2)
            d.ellipse((bx - 8, by - 8, bx + 8, by + 8), fill=(255, 255, 255, int(255 * a)))
            d.text((tx + (dx if dx > 0 else -F(28, True).getlength(name) - 10), ty - 18), name, font=F(28, True), fill=WHITE + (int(255 * a),))
            if name == "강릉" and low > 0:
                r = 26
                d.ellipse((tx - r, ty - r, tx + r, ty + r), fill=RED + (int(240 * low),))
                d.text((tx - 6, ty - 21), "!", font=F(32, True), fill=WHITE + (int(255 * low),))

        # route labels
        la = ease((t - 2.2) / 0.5) * (1 - low)
        if la > 0:
            for route, f_, txt, col, off in ((T3.FAST, 0.42, "고속도로  180 km", lerpc(ORANGE, (140, 130, 120), sw), -64),
                                             (T3.ECO, 0.5, "국도  165 km", BLUE, 30)):
                x, y, _ = T3.point3d(route.at(f_), cam, hs, 0.5)
                tw_ = F(26, True).getlength(txt)
                d.rounded_rectangle((x - tw_ / 2 - 16, y + off - 6, x + tw_ / 2 + 16, y + off + 38), 20,
                                    fill=(8, 11, 17, int(200 * la)), outline=col + (int(255 * la),), width=2)
                d.text((x - tw_ / 2, y + off), txt, font=F(26, True), fill=col + (int(255 * la),))

        # ---- beat 1: race
        if t < self.B2:
            mins = 145 * ease_lin((t - 2.6) / 3.0)
            pf, pe = min(1, mins / 130), min(1, mins / 145)
            sf, se = pf * self.Lf, pe * self.Ls
            for route, s, col, done in ((T3.FAST, sf, ORANGE, pf >= 1), (T3.ECO, se, BLUE, pe >= 1)):
                if mins <= 0:
                    break
                x, y, _ = T3.point3d(self.car_pos(route, s), cam, hs, 0.9)
                d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=col + (70,))
                d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=WHITE, outline=col, width=4)
            a1, a2 = ease((t - 1.6) / 0.5), ease((t - 1.9) / 0.5)
            fo = 1 - ease((t - self.B2 + 0.35) / 0.35)
            km_f, km_e = 180 * pf, 165 * pe
            self.card(d, 250, "빠른 경로", "고속도로", ORANGE, km_f, min(mins, 130), km_f / 5.2, 68 - km_f / 5.2 / 70 * 100, False, min(a1, fo))
            self.card(d, 510, "절전 경로", "국도", BLUE, km_e, mins, km_e / 5.2, 68 - km_e / 5.2 / 70 * 100, pe >= 1, min(a2, fo))
            ca = ease((t - 2.2) / 0.5) * fo
            if ca > 0:
                A = int(255 * ca)
                d.text((self.X0, 780), "소비량 = 거리 ÷ 전비 (5.2 km/kWh)", font=F(22), fill=MUTED + (A,))
            cb = ease((t - 5.7) / 0.4) * fo
            if cb > 0:
                A = int(255 * cb)
                d.rounded_rectangle((self.X0, 822, self.X0 + self.CW, 922), 20, fill=(18, 40, 80, A), outline=BLUE + (A,), width=2)
                d.text((self.X0 + 26, 836), "국도가 15 km 짧아 2.9 kWh 덜 씁니다", font=F(26, True), fill=WHITE + (A,))
                d.text((self.X0 + 26, 876), "대신 도착은 15분 늦어요", font=F(22), fill=SOFT + (A,))
        # ---- beat 2: junction prompt
        elif t < self.B3:
            tb = t - self.B2
            fo = 1 - ease((t - self.B3 + 0.35) / 0.35)
            ai = ease(tb / 0.4)
            self.card(d, 250, "빠른 경로", "고속도로", ORANGE, 180, 130, 34.6, 18.6, sw < 0.5, min(ai, fo) * (1 - 0.45 * sw))
            self.card(d, 510, "절전 경로", "국도", BLUE, 165, 145, 31.7, 22.7, sw >= 0.5, min(ai, fo))
            jx, jy, _ = T3.point3d(T3.JUNC, cam, hs, 0.6)
            ph = tb % 1.0
            if tb < 3.0:
                rr = 12 + 40 * ph
                d.ellipse((jx - rr, jy - rr, jx + rr, jy + rr), outline=(56, 128, 255, int(220 * (1 - ph))), width=3)
            if tb < 1.4:
                s = ease(tb / 1.4) * T3.SHARED.L * 0.86
                pos = T3.SHARED.at(s / T3.SHARED.L)
            elif tb < 3.0:
                pos = T3.SHARED.at(0.86)
            elif tb < 3.3:
                pos = T3.SHARED.at(0.86 + 0.14 * ease((tb - 3.0) / 0.3))
            else:
                pos = T3.ECO.at(ease((tb - 3.3) / 1.4))
            x, y, _ = T3.point3d(pos, cam, hs, 0.9)
            d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(56, 128, 255, 70))
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=WHITE, outline=BLUE, width=4)
            pa = ease((tb - 1.2) / 0.45) * (1 - ease((tb - 4.0) / 0.4))
            if pa > 0:
                A = int(255 * pa)
                px, py = 150, 760 + int((1 - pa) * 18)
                d.rounded_rectangle((px, py, px + 560, py + 196), 22, fill=(250, 251, 253, A))
                d.text((px + 30, py + 20), "앞 갈림길에서 국도로 바꾸면", font=F(24), fill=(70, 78, 96, A))
                d.text((px + 30, py + 54), "2.9 kWh 절약 · 15분 추가", font=F(38, True), fill=(30, 100, 240, A))
                press = ease((tb - 2.55) / 0.25)
                d.rounded_rectangle((px + 30, py + 118, px + 270, py + 176), 14, fill=(232, 235, 241, A))
                d.text((px + 92, py + 132), "그대로 가기", font=F(24, True), fill=(60, 66, 80, A))
                d.rounded_rectangle((px + 290, py + 118, px + 530, py + 176), 14, fill=lerpc((40, 44, 56), (30, 100, 240), press) + (A,))
                d.text((px + 376, py + 132), "바꾸기", font=F(24, True), fill=(255, 255, 255, A))
                if 0 < tb - 2.55 < 0.7:
                    u = (tb - 2.55) / 0.7
                    rr = 10 + 34 * u
                    cx, cy = px + 410, py + 147
                    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255, int(A * (1 - u))), width=4)
        # ---- beat 3: low SOC
        else:
            tb = t - self.B3
            prog = ease((tb - 0.5) / 1.6)
            a1, a2 = ease(tb / 0.45), ease((tb - 0.15) / 0.45)
            self.card(d, 250, "빠른 경로", "고속도로", ORANGE, 180, 130, 34.6, 20 - 49.4 * prog, False, a1)
            self.card(d, 510, "절전 경로", "국도", BLUE, 165, 145, 31.7, 20 - 45.3 * prog, False, a2)
            ba = ease((tb - 2.1) / 0.45)
            if ba > 0:
                A = int(255 * ba)
                d.rounded_rectangle((self.X0, 790, self.X0 + self.CW, 900), 20, fill=(62, 20, 26, A), outline=RED + (A,), width=2)
                d.text((self.X0 + 26, 806), "출발 SOC 20% · 시작 버튼 잠김", font=F(26, True), fill=WHITE + (A,))
                d.text((self.X0 + 26, 848), "국도로 가도 60.4% 이상 충전해야 출발할 수 있어요", font=F(21), fill=(240, 200, 200, A))

        # titles
        bounds = [0.0, self.B2, self.B3, self.dur]
        for k in range(3):
            ain = ease((t - bounds[k] - 0.2) / 0.5)
            aout = 1 - ease((t - bounds[k + 1] + 0.35) / 0.35) if k < 2 else 1
            a = min(ain, aout)
            if a > 0:
                img, (ox, oy) = self.tl[k]
                im.alpha_composite(fade(img, a), (ox, oy + int((1 - ain) * 14)))
        fa = ease((t - 1.0) / 0.5)
        if fa > 0:
            d.text((90, 1010), "강릉 오프라인 데모의 계산값입니다. 소비량은 거리 ÷ 전비로 계산하며 고도와 교통은 반영하지 않습니다. 지형은 설명용 그래픽입니다.",
                   font=F(19), fill=(98, 108, 126, int(255 * fa)))
        return im


def ease_lin(x):
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------- Pleos screen scenes with callouts
SX0, SX1, SY0, SY1 = 640, 1840, 150, 930
TX, TW = 120, 440
NUM = re.compile(r"(\d+(?:\.\d+)?)")


class Screen(Scene):
    def __init__(self, dur, idx, img, title, desc, stat, stat_label, roi, note, hl, full=True):
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
        self.hl = hl
        self.stat, self.stat_label = stat, stat_label

        st = BASE.copy()
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((self.fx, self.fy + 20, self.fx + self.fw, self.fy + self.fh + 30), 24, fill=(0, 0, 0, 170))
        st.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
        d = ImageDraw.Draw(st)
        d.rounded_rectangle((self.fx - 12, self.fy - 12, self.fx + self.fw + 12, self.fy + self.fh + 12), 22, fill=(4, 6, 10), outline=HAIR, width=2)
        cap = "PLEOS CONNECT 2.1.0  ·  NATIVE CAPTURE" if full else "PLEOS CONNECT 2.1.0  ·  APP WINDOW CAPTURE"
        d.ellipse((self.fx, self.fy + self.fh + 36, self.fx + 10, self.fy + self.fh + 46), fill=GREEN)
        tracked(d, (self.fx + 22, self.fy + self.fh + 30), cap, F(17, True), MUTED, 2.5)
        if note:
            for k, ln in enumerate(wrap(note, F(19), SX1 - SX0)):
                d.text((SX0, 990 + k * 28), ln, font=F(19), fill=(98, 108, 126))
        self.static = st

        items = []
        def chap(d, L):
            tracked(d, (TX, 300), f"{idx:02d}", F(24, True), BLUE, 3)
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
        self.ny = y0 + len(wrap(desc, F(28), TW)) * 44 + 60
        self.items = items
        self.zoom_end = 0.9 + self.dur * 0.5

    def stat_text(self, u):
        m = NUM.search(self.stat)
        if not m:
            return self.stat
        v = float(m.group(1)) * u
        dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
        return self.stat[:m.start()] + f"{v:.{dec}f}" + self.stat[m.end():]

    def frame(self, t):
        im = self.static.copy()
        a = ease((t - 0.9) / (self.zoom_end - 0.9))
        box = tuple(self.full[i] + (self.roi[i] - self.full[i]) * a for i in range(4))
        im.paste(self.src.resize((self.fw, self.fh), Image.BILINEAR, box=box), (self.fx, self.fy))
        d = ImageDraw.Draw(im)
        # chapter line grows
        g = ease((t - 0.15) / 0.6)
        d.line((TX + 52, 314, TX + 52 + 60 * g, 314), fill=BLUE, width=2)
        self.draw_items(im, t)
        # stat with count-up
        sa = ease((t - 0.9) / 0.5)
        if sa > 0:
            A = int(255 * sa)
            ny = self.ny
            d.line((TX, ny, TX + TW * ease((t - 0.9) / 0.8), ny), fill=HAIR, width=2)
            txt = self.stat_text(ease((t - 1.0) / 1.2))
            d.text((TX, ny + 26 + (1 - sa) * 12), txt, font=F(64, True), fill=BLUE + (A,))
            d.text((TX, ny + 112), self.stat_label, font=F(24), fill=MUTED + (A,))
        # highlight box on the screenshot + connector to the stat
        ha = ease((t - self.zoom_end + 0.1) / 0.5)
        if ha > 0 and self.hl:
            bx0, by0, bx1, by1 = box
            sx = lambda x: self.fx + (x - bx0) / (bx1 - bx0) * self.fw
            sy = lambda y: self.fy + (y - by0) / (by1 - by0) * self.fh
            x0, y0, x1, y1 = sx(self.hl[0]), sy(self.hl[1]), sx(self.hl[2]), sy(self.hl[3])
            x0, y0 = max(self.fx + 4, x0), max(self.fy + 4, y0)
            x1, y1 = min(self.fx + self.fw - 4, x1), min(self.fy + self.fh - 4, y1)
            grow = 1 + 0.06 * (1 - ha)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            hw, hh = (x1 - x0) / 2 * grow + 8, (y1 - y0) / 2 * grow + 8
            G = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(G)
            gd.rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), 14, outline=(56, 128, 255, int(200 * ha)), width=10)
            G = G.filter(ImageFilter.GaussianBlur(10))
            im.alpha_composite(G)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), 14, outline=(56, 128, 255, int(255 * ha)), width=4)
        return im


S = "docs/submission/screenshots/"
G = "docs/user-guide/screenshots/"
SIM = "데모 차량값으로 계산한 수치이며 실차 측정값이 아닙니다. 주행은 좌표 재생입니다."
MAP = "지도 © OpenStreetMap contributors (ODbL) · 도로 경로 OSRM. 소비량은 계산값이고 주행은 좌표 재생입니다."
D = 6.4

SCENES = [
    intro(),
    Concept3D(),
    Screen(D, 1, G + "pleos-full-road.png", "Pleos 화면에서\n바로 씁니다", "차 안 디스플레이에서 실제 지도와 도로 경로를 펼쳐 놓고 비교합니다.",
           "2개 경로", "서울 시청에서 강릉역까지", (840, 0, 2560, 967), MAP, hl=(1700, 262, 2516, 620)),
    Screen(D, 2, G + "pleos-sdk.png", "배터리 잔량은\n차에서 읽어옵니다", "Vehicle SDK로 SOC를 가져오고, 어디서 온 값인지 함께 표시합니다.",
           "SOC 100%", "Pleos 에뮬레이터에서 읽은 값", (860, 360, 1670, 1060),
           "SOC는 Pleos Connect 에뮬레이터에서 읽은 값이며 실차 측정값이 아닙니다.", hl=(1150, 420, 1370, 640), full=False),
    Screen(D, 3, S + "pleos-comparison.png", "왜 이 경로인지\n알려줍니다", "도착 잔량과 늘어나는 시간을 기준으로 고르고, 전비가 20% 나빠질 때의 결과도 같이 보여줍니다.",
           "2.9 kWh", "절전 경로가 아끼는 양, 대신 15분 더", (870, 250, 2530, 1000), SIM, hl=(1700, 745, 2516, 985)),
    Screen(D, 4, G + "pleos-junction-demo.png", "갈림길에서\n한 번 더 묻습니다", "아낄 수 있는 에너지와 늘어나는 시간을 보여주고, 운전자가 고를 때까지 기다립니다.",
           "1.2 km 앞", "분기점 안내", (0, 180, 1682, 700), SIM, hl=(26, 195, 1660, 425), full=False),
    Screen(D, 5, S + "pleos-low-soc.png", "모자라면\n출발 전에 막습니다", "어느 경로로도 최소 잔량을 못 지키면 시작 버튼이 잠기고, 얼마나 충전해야 하는지 알려줍니다.",
           "SOC 20%", "기준은 자동으로 낮추지 않습니다", (1180, 230, 2560, 1006), SIM, hl=(1690, 262, 2530, 345)),
    Screen(D, 6, S + "pleos-report.png", "도착하면\n결과를 남깁니다", "처음 고른 경로와 무엇이 달라졌는지 기록합니다. 앱이 꺼져도 멈춘 곳부터 이어집니다.",
           "31.7 kWh", "이번 주행의 계산상 소비량", (870, 260, 2530, 1000), SIM, hl=(880, 780, 1460, 880)),
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

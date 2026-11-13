#!/usr/bin/env python3
"""VOLTRO 60-second contest demo: concise explanation + native Pleos Connect captures.

Usage: python3 scripts/build_pleos_demo_video_60s.py docs/submission/VOLTRO_Pleos_Demo_60s.mp4
       python3 scripts/build_pleos_demo_video_60s.py --still <scene> <t> out.png
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
        centered(d, 640, "전기차 에너지 경로 비교 · Pleos 차량용 앱", F(30), SOFT)
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
        d.text((160, 240), "실제 차량 데이터와 실제 도로 위에서", font=F(60, True), fill=WHITE)
    items.append((0.1, layer(kick), 16))
    rows = [("Pleos Vehicle SDK 2.3.2", "SOC 읽기 · 미지원/timeout은 오류로 표시"),
            ("OpenStreetMap · OSRM", "실제 지도와 도로 거리 · 시간"),
            ("Kotlin · StateFlow · SQLite", "재생 체크포인트와 기기 내 이력")]
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
        steps = ["정차 상태 사용성 검증", "국내 도로 · 내비 연동", "실차 소비량으로 예측 보정"]
        for i, s in enumerate(steps):
            y = 470 + i * 100
            d.ellipse((x, y + 12, x + 16, y + 28), outline=BLUE, width=3)
            if i < 2:
                d.line((x + 8, y + 32, x + 8, y + 104), fill=HAIR, width=2)
            d.text((x + 44, y), s, font=F(32, True), fill=WHITE)
    items.append((1.4, layer(nxt), 12))
    def foot(d, L):
        d.text((160, 860), "실측 근거를 확보하기 전에는 실차 절약 성능이나 예측 정확도를 주장하지 않습니다.", font=F(24), fill=MUTED)
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


S = "docs/submission/screenshots/"
G = "docs/user-guide/screenshots/"
SIM = "데모 차량값과 거리×전비 계산값이며 실차 측정값이 아닙니다. 주행은 좌표 재생입니다."
MAP = "지도 © OpenStreetMap contributors (ODbL) · 도로 경로 OSRM. 소비량은 추정값, 주행은 도로 좌표 재생입니다."
D = 7.3

SCENES = [
    intro(),
    problem(),
    Screen(D, 1, G + "pleos-full-road.png", "Pleos 차량\n디스플레이에서", "Pleos Connect 앱 영역에서 실행되며, 실제 OSM 지도와 OSRM 도로 경로를 비교합니다.",
           "2 경로", "서울 시청 → 강릉역 실제 도로 후보", (840, 0, 2560, 967), MAP),
    Screen(D, 2, G + "pleos-sdk.png", "차량 상태를\nSDK로 읽습니다", "공식 Vehicle SDK로 SOC를 읽고, 입력 출처를 구분해 표시합니다.",
           "SOC 100%", "Pleos 에뮬레이터 SDK 읽기 값", (860, 360, 1670, 1060),
           "SOC는 Pleos Connect 에뮬레이터의 Vehicle SDK 값이며 실차 측정값이 아닙니다.", full=False),
    Screen(D, 3, S + "pleos-comparison.png", "추천에는\n근거가 있습니다", "최소 도착 잔량과 허용 추가 시간으로 추천하고, 전비 20% 저하 가정도 함께 보여줍니다.",
           "−2.9 kWh", "절전 경로 · 15분 추가", (870, 250, 2530, 1000), SIM),
    Screen(D, 4, G + "pleos-junction-demo.png", "분기점에서\n다시 제안합니다", "같은 분기점 이후의 시간과 에너지를 비교하고, 운전자가 승인할 때만 경로를 바꿉니다.",
           "1.2 km", "전방 분기점 · 선택까지 재생 일시정지", (0, 180, 1682, 700), SIM, full=False),
    Screen(D, 5, S + "pleos-low-soc.png", "부족하면\n출발을 막습니다", "모든 경로가 최소 도착 잔량에 못 미치면 시작을 막고, 필요한 출발 SOC를 안내합니다.",
           "SOC 20%", "안전 조건을 자동으로 낮추지 않음", (1180, 230, 2560, 1006), SIM),
    Screen(D, 6, S + "pleos-report.png", "결과는\n리포트로 남깁니다", "출발 경로 대비 계산상 변화를 기록하고, 중단돼도 마지막 체크포인트에서 복구합니다.",
           "31.7 kWh", "완료 경로의 계산상 소비량", (870, 260, 2530, 1000), SIM),
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

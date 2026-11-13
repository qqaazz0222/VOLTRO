#!/usr/bin/env python3
"""VOLTRO contest demo video renderer: explanation slides + native Pleos Connect captures."""
import subprocess, sys, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Repository root (default: parent of scripts/). Usage: python3 scripts/build_pleos_demo_video.py docs/submission/VOLTRO_Pleos_Demo.mp4
R = os.environ.get("VOLTRO_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) + "/"
W, H, FPS = 1920, 1080, 30
XF = 0.6  # crossfade seconds

BG = (11, 15, 23)
PANEL = (20, 26, 38)
LINE = (44, 52, 68)
BLUE = (47, 120, 255)
WHITE = (240, 243, 248)
MUTED = (150, 160, 178)
GREEN = (40, 190, 120)
RED = (240, 96, 96)

FB = R + "artifacts/user-guide-fonts/AstaSans-Bold.ttf"
FRG = R + "artifacts/user-guide-fonts/AstaSans-Regular.ttf"
_fc = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FRG, size)
    return _fc[k]

LOCKUP = Image.open(R + "design/brand/voltro-lockup-white.png").convert("RGBA").crop((51, 52, 1539, 263))
ICON = Image.open(R + "design/brand/voltro-app-icon.png").convert("RGBA")


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def text_layer(draw_fn):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), layer)
    bb = layer.getbbox() or (0, 0, 1, 1)
    return (layer.crop(bb), bb[:2])


def with_alpha(layer, a):
    if a >= 0.999:
        return layer
    l = layer.copy()
    al = l.getchannel("A").point(lambda v: int(v * a))
    l.putalpha(al)
    return l


def wrap(text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        test = cur + ch
        if font.getlength(test) > maxw and cur:
            # break at last space if possible
            sp = cur.rfind(" ")
            if sp > 0:
                lines.append(cur[:sp]); cur = cur[sp + 1:] + ch
            else:
                lines.append(cur); cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def base_bg():
    im = Image.new("RGB", (W, H), BG)
    # subtle top glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((-400, -700, 1400, 500), fill=(47, 120, 255, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im.paste(glow, (0, 0), glow)
    return im.convert("RGBA")

BASE = base_bg()


# ---------------------------------------------------------------- slide scenes
class Slide:
    """Static text slide with staggered fade-ins. items: list of (delay, layer)."""
    def __init__(self, dur, build):
        self.dur = dur
        self.bg = BASE.copy()
        self.items = build(self)

    def frame(self, t):
        im = self.bg.copy()
        for delay, layer, rise in self.items:
            a = smooth((t - delay) / 0.5)
            if a <= 0:
                continue
            dy = int((1 - a) * rise)
            img, (ox, oy) = layer
            im.alpha_composite(with_alpha(img, a), (ox, oy + dy))
        return im


def lay(fn, delay=0.0, rise=18):
    return (delay, text_layer(fn), rise)


def build_intro(s):
    def logo(d, L):
        lw = 760
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 330))
    def tag(d, L):
        t = "Your Route. Your Energy."
        f = F(46)
        d.text(((W - f.getlength(t)) / 2, 520), t, font=f, fill=BLUE)
    def sub(d, L):
        t = "전기차 배터리와 도로를 함께 보는 Pleos 주행 의사결정 앱"
        f = F(38, True)
        d.text(((W - f.getlength(t)) / 2, 620), t, font=f, fill=WHITE)
        t2 = "2026 현대자동차그룹 차량용 앱 개발 공모전 출품 · 데모 영상"
        f2 = F(28)
        d.text(((W - f2.getlength(t2)) / 2, 690), t2, font=f2, fill=MUTED)
    return [lay(logo, 0.2, 0), lay(tag, 0.9), lay(sub, 1.5)]


def heading(d, kicker, title, y=150):
    d.text((160, y), kicker, font=F(28, True), fill=BLUE)
    d.text((160, y + 48), title, font=F(60, True), fill=WHITE)


def build_problem(s):
    items = [lay(lambda d, L: heading(d, "PROBLEM", "장거리 전기차 운전자가 출발 전 묻는 질문"), 0.2)]
    qs = [("01", "어떤 경로가 에너지를 얼마나 덜 쓰는가?"),
          ("02", "그 대신 몇 분이 더 걸리는가?"),
          ("03", "도착했을 때 내가 정한 잔량을 지킬 수 있는가?")]
    for i, (n, q) in enumerate(qs):
        def f(d, L, n=n, q=q, i=i):
            y = 380 + i * 130
            d.rounded_rectangle((160, y, 1760, y + 104), 22, fill=PANEL, outline=LINE, width=2)
            d.text((210, y + 26), n, font=F(42, True), fill=BLUE)
            d.text((320, y + 26), q, font=F(42, True), fill=WHITE)
        items.append(lay(f, 1.0 + i * 0.7))
    def tail(d, L):
        d.text((160, 800 + 10), "지금은 거리·시간·SOC를 따로 확인해야 합니다. VOLTRO는 세 질문을 한 화면에서 답합니다.",
               font=F(32), fill=MUTED)
    items.append(lay(tail, 3.4))
    return items


def build_overview(s):
    items = [lay(lambda d, L: heading(d, "SOLUTION", "VOLTRO가 하는 일"), 0.2)]
    cards = [("출발 전 비교", "경로별 시간 · 거리 · 소비 kWh · 도착 SOC를 한 번에 비교"),
             ("안전 조건 추천", "최소 도착 잔량과 허용 추가 시간으로 추천하고 근거를 설명"),
             ("분기점 안내", "주행 중 분기점에서 절약 에너지와 추가 시간을 비교해 제안"),
             ("리포트 · 이력", "완료 후 계산상 변화와 여정 기록을 기기에 저장")]
    cw, gap = 380, 26
    for i, (t, b) in enumerate(cards):
        def f(d, L, t=t, b=b, i=i):
            x = 160 + i * (cw + gap); y = 380
            d.rounded_rectangle((x, y, x + cw, y + 420), 26, fill=PANEL, outline=LINE, width=2)
            d.rounded_rectangle((x + 36, y + 40, x + 100, y + 104), 16, fill=BLUE)
            d.text((x + 52, y + 50), str(i + 1), font=F(40, True), fill=WHITE)
            d.text((x + 36, y + 140), t, font=F(40, True), fill=WHITE)
            yy = y + 210
            for ln in wrap(b, F(29), cw - 72):
                d.text((x + 36, yy), ln, font=F(29), fill=MUTED); yy += 44
        items.append(lay(f, 0.9 + i * 0.5))
    def foot(d, L):
        d.text((160, 860), "Pleos Vehicle SDK의 SOC · 전비와 OpenStreetMap 지도 · OSRM 실제 도로 경로를 연결합니다.",
               font=F(30), fill=MUTED)
    items.append(lay(foot, 3.2))
    return items


def build_divider(s):
    def f(d, L):
        t = "Pleos Connect 실제 구동 화면"
        d.text(((W - F(72, True).getlength(t)) / 2, 440), t, font=F(72, True), fill=WHITE)
        t2 = "Pleos Connect 2.1.0 · Android 14 (API 34) · 2560×1440 차량 디스플레이에서 앱을 실행해 촬영"
        d.text(((W - F(30).getlength(t2)) / 2, 560), t2, font=F(30), fill=MUTED)
        d.rounded_rectangle((W / 2 - 60, 400, W / 2 + 60, 408), 4, fill=BLUE)
    return [lay(f, 0.1)]


def build_tech(s):
    items = [lay(lambda d, L: heading(d, "TECHNOLOGY", "구현 기술"), 0.2)]
    rows = [("Pleos Vehicle SDK 2.3.2", "SOC capability 확인과 읽기 snapshot · 미지원/timeout은 오류로 표시"),
            ("OpenStreetMap · OSRM", "실제 지도 타일과 도로 geometry · 거리 · 시간, 출처 표시와 요청 간격 제한"),
            ("Kotlin Android", "ViewModel · StateFlow · Coroutines · SQLite · 재생 체크포인트"),
            ("FastAPI 검증 서버", "에너지 계산 · 분기점 평가 · 멱등 완료 저장 API와 자동 테스트")]
    for i, (a, b) in enumerate(rows):
        def f(d, L, a=a, b=b, i=i):
            y = 360 + i * 125
            d.rounded_rectangle((160, y, 1760, y + 100), 20, fill=PANEL, outline=LINE, width=2)
            d.text((205, y + 30), a, font=F(36, True), fill=WHITE)
            d.text((700, y + 34), b, font=F(29), fill=MUTED)
        items.append(lay(f, 0.8 + i * 0.5))
    return items


def build_next(s):
    items = [lay(lambda d, L: heading(d, "NEXT", "다음 검증 단계"), 0.2)]
    steps = [("정차 상태 사용성", "운전자 10명이 비교 · 전환 과제 수행"),
             ("도로 · 내비 연동", "국내 교통 데이터와 공식 내비 연동 검증"),
             ("실차 소비량 보정", "경로별 예측과 실측을 짝지어 오차 공개")]
    for i, (a, b) in enumerate(steps):
        def f(d, L, a=a, b=b, i=i):
            x = 160 + i * 540; y = 400
            d.rounded_rectangle((x, y, x + 500, y + 300), 26, fill=PANEL, outline=LINE, width=2)
            d.text((x + 40, y + 40), f"STEP {i + 1}", font=F(28, True), fill=BLUE)
            d.text((x + 40, y + 100), a, font=F(42, True), fill=WHITE)
            yy = y + 175
            for ln in wrap(b, F(30), 420):
                d.text((x + 40, yy), ln, font=F(30), fill=MUTED); yy += 44
            if i < 2:
                d.polygon([(x + 512, y + 135), (x + 530, y + 150), (x + 512, y + 165)], fill=BLUE)
        items.append(lay(f, 0.8 + i * 0.6))
    def foot(d, L):
        d.text((160, 790), "충분한 실측 근거를 확보하기 전에는 실차 절약 성능이나 AI 예측 정확도를 주장하지 않습니다.",
               font=F(30), fill=MUTED)
    items.append(lay(foot, 2.8))
    return items


def build_outro(s):
    def f(d, L):
        lw = 620
        lk = LOCKUP.resize((lw, int(LOCKUP.height * lw / LOCKUP.width)), Image.LANCZOS)
        L.alpha_composite(lk, ((W - lw) // 2, 380))
        t = "Your Route. Your Energy."
        d.text(((W - F(44).getlength(t)) / 2, 545), t, font=F(44), fill=BLUE)
        t2 = "경로의 기준에, 에너지를 더하다."
        d.text(((W - F(36, True).getlength(t2)) / 2, 630), t2, font=F(36, True), fill=WHITE)
    return [lay(f, 0.2, 0)]


# ---------------------------------------------------------------- screen scenes
BOX_L, BOX_R, BOX_T, BOX_B = 60, 1420, 130, 940


class Screen:
    def __init__(self, dur, img, step, title, bullets, roi=None, note=None, kind="full"):
        self.dur = dur
        src = Image.open(R + img).convert("RGB")
        self.src = src
        iw, ih = src.size
        bw, bh = BOX_R - BOX_L, BOX_B - BOX_T
        sc = min(bw / iw, bh / ih)
        self.fw, self.fh = int(iw * sc), int(ih * sc)
        self.fx = BOX_L + (bw - self.fw) // 2
        self.fy = BOX_T + (bh - self.fh) // 2
        self.full = (0, 0, iw, ih)
        if roi:
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
        else:
            self.roi = None
        # static layer: frame, header chip, panel
        st = BASE.copy()
        d = ImageDraw.Draw(st)
        # shadow
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((self.fx - 6, self.fy + 6, self.fx + self.fw + 6, self.fy + self.fh + 18), 18, fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        st.alpha_composite(sh)
        d = ImageDraw.Draw(st)
        d.rounded_rectangle((self.fx - 3, self.fy - 3, self.fx + self.fw + 3, self.fy + self.fh + 3), 10, outline=LINE, width=3)
        # header
        d.text((60, 52), step, font=F(26, True), fill=BLUE)
        sw = F(26, True).getlength(step)
        d.text((60 + sw + 20, 52), "VOLTRO DEMO", font=F(26), fill=MUTED)
        badge = "Pleos Connect 2.1.0 실제 구동 화면" if kind == "full" else "Pleos Connect 2.1.0 · 앱 창 캡처"
        bwid = F(24, True).getlength(badge) + 70
        d.rounded_rectangle((1860 - bwid, 44, 1860, 92), 24, fill=(18, 40, 80), outline=BLUE, width=2)
        d.ellipse((1860 - bwid + 22, 61, 1860 - bwid + 36, 75), fill=GREEN)
        d.text((1860 - bwid + 48, 54), badge, font=F(24, True), fill=WHITE)
        # small icon
        if note:
            d.text((60, 975), note, font=F(23), fill=MUTED)
        self.static = st
        # panel layers
        px = 1470; pw = 1860 - px
        self.layers = []
        def tl(d, L):
            yy = 200
            for ln in wrap(title, F(46, True), pw):
                d.text((px, yy), ln, font=F(46, True), fill=WHITE); yy += 62
            d.rounded_rectangle((px, yy + 20, px + 70, yy + 26), 3, fill=BLUE)
            self._ty = yy + 70
        self.layers.append((0.4, text_layer(tl), 16))
        yy = self._ty
        for i, b in enumerate(bullets):
            def bl(d, L, b=b, y0=yy):
                d.ellipse((px, y0 + 14, px + 12, y0 + 26), fill=BLUE)
                y = y0
                for ln in wrap(b, F(30), pw - 30):
                    d.text((px + 28, y), ln, font=F(30), fill=(214, 220, 230)); y += 44
            lines = len(wrap(b, F(30), pw - 30))
            self.layers.append((1.1 + i * 0.9, text_layer(bl), 14))
            yy += lines * 44 + 30

    def view(self, t):
        if not self.roi:
            z = smooth(t / self.dur) * 0.04
            iw, ih = self.src.size
            return (iw * z / 2, ih * z / 2, iw * (1 - z / 2), ih * (1 - z / 2))
        a = smooth((t - self.dur * 0.38) / (self.dur * 0.22))
        f, r = self.full, self.roi
        return tuple(f[i] + (r[i] - f[i]) * a for i in range(4))

    def frame(self, t):
        im = self.static.copy()
        box = self.view(t)
        crop = self.src.resize((self.fw, self.fh), Image.BILINEAR, box=box)
        im.paste(crop, (self.fx, self.fy))
        for delay, layer, rise in self.layers:
            a = smooth((t - delay) / 0.5)
            if a <= 0:
                continue
            img, (ox, oy) = layer
            im.alpha_composite(with_alpha(img, a), (ox, oy + int((1 - a) * rise)))
        return im


S = "docs/submission/screenshots/"
G = "docs/user-guide/screenshots/"
SIM = "차량값·소비량은 시뮬레이터 입력과 거리×전비 계산값이며 실차 측정값이 아닙니다. 주행은 좌표 재생입니다."
MAPN = "지도 © OpenStreetMap contributors (ODbL) · 도로 경로 OSRM. 소비량은 거리×전비 추정, 주행은 도로 좌표 재생입니다."

SCENES = [
    Slide(7.5, build_intro),
    Slide(9.5, build_problem),
    Slide(10, build_overview),
    Slide(4, build_divider),
    Screen(9, G + "pleos-full-road.png", "01", "Pleos에서 실행",
           ["차량 디스플레이 앱 영역에서 VOLTRO 실행", "실제 도로 모드: OSM 지도 + OSRM 도로 경로", "큰 버튼 · 회색 기반 Pleos 디자인 가이드 적용"],
           roi=(840, 0, 2560, 967), note=MAPN),
    Screen(9, G + "pleos-sdk.png", "02", "Vehicle SDK로 차량 상태 읽기",
           ["공식 Pleos Vehicle SDK 2.3.2로 SOC 읽기", "입력 출처를 'Pleos SOC'로 구분 표시", "미지원 · timeout은 오류로 표시하고 기존 값 보존"],
           roi=(860, 360, 1670, 1060), kind="app",
           note="SOC 100%는 Pleos Connect 에뮬레이터 Vehicle SDK의 읽기 값이며 실차 측정값이 아닙니다."),
    Screen(9, G + "pleos-comparison.png", "03", "실제 도로 경로 비교",
           ["서울 시청 → 강릉역, OSRM 실제 도로 후보", "경로별 시간 · 거리 · 소비 kWh · 도착 SOC", "지도 드래그 · 확대 · 전체 보기 지원"],
           roi=(0, 60, 1682, 720), kind="app", note=MAPN),
    Screen(8.5, G + "pleos-driving.png", "04", "도로 좌표 주행 재생",
           ["선택 경로의 실제 도로 좌표를 재생", "남은 여정 · 현재 배터리 · 예상 도착 잔량 갱신", "차량 내비게이션은 제어하지 않음"],
           roi=(0, 150, 1682, 760), kind="app", note=MAPN),
    Screen(10, S + "pleos-comparison.png", "05", "추천과 그 근거까지",
           ["빠른 130분 · 34.6 kWh vs 절전 145분 · 31.7 kWh", "최소 도착 잔량 · 허용 추가 시간 기준 추천", "전비 20% 저하 가정 시 도착 잔량도 표시"],
           roi=(870, 250, 2530, 1000), note=SIM + " 20% 저하는 민감도 가정입니다."),
    Screen(10, G + "pleos-junction-demo.png", "06", "분기점에서 더 효율적인 경로 안내",
           ["전방 1.2 km 분기점: 2.9 kWh 절약 · 15분 추가", "선택을 기다리며 재생 일시정지", "운전자가 승인해야만 경로 변경"],
           roi=(0, 180, 1682, 700), kind="app", note=SIM),
    Screen(8.5, S + "pleos-report.png", "07", "완료 리포트",
           ["출발 경로 대비 계산상 2.9 kWh 감소 · 15분 추가", "총 거리 · 주행 시간 · 도착 배터리 요약", "실측 소비량이 아닌 계산값임을 명시"],
           roi=(870, 260, 2530, 1000), note=SIM),
    Screen(10, S + "pleos-low-soc.png", "08", "잔량이 부족하면 출발을 막습니다",
           ["SOC 20%: 모든 경로가 최소 도착 잔량 미달", "필요한 최소 출발 SOC · 추가 배터리 에너지 안내", "안전 조건을 자동으로 완화하지 않음"],
           roi=(1180, 230, 2560, 1006), note=SIM),
    Screen(9, S + "pleos-recovery.png", "09", "중단돼도 이어서 재생",
           ["앱 프로세스가 종료돼도 마지막 체크포인트 복구", "복구 후 항상 일시정지 · 분기점 승인 대기 보존", "24시간 유효한 기기 내 임시 기록"],
           roi=(860, 120, 2540, 640), note="복구 화면은 저장/복구 자동 검사의 고정 입력으로 촬영했습니다. " + "실차 주행 세션 복구가 아닌 시연 재생 복구입니다."),
    Screen(8, G + "pleos-settings.png", "10", "운전자 기준 설정",
           ["출발 SOC · 전비 · 사용 가능 용량", "최소 도착 잔량 · 허용 추가 시간", "경로 변경 실패 시나리오: 실패 시 기존 경로 유지"],
           roi=(1240, 210, 2150, 1180)),
    Screen(7, G + "pleos-history.png", "11", "주행 이력",
           ["최근 50개 여정을 기기에 저장", "정밀 위치 이력은 저장하지 않음"],
           roi=(0, 0, 1682, 800), kind="app"),
    Slide(10, build_tech),
    Slide(9, build_next),
    Slide(6, build_outro),
]


def main(out):
    starts, t = [], 0.0
    for i, s in enumerate(SCENES):
        starts.append(t)
        t += s.dur - (XF if i < len(SCENES) - 1 else 0)
    total = t
    n = int(round(total * FPS))
    print("total", total, "frames", n, file=sys.stderr)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for k in range(n):
        tt = k / FPS
        act = [(i, tt - starts[i]) for i, s in enumerate(SCENES) if starts[i] <= tt < starts[i] + s.dur]
        if not act:
            act = [(len(SCENES) - 1, SCENES[-1].dur - 1e-3)]
        img = SCENES[act[0][0]].frame(act[0][1])
        if len(act) > 1:
            nxt = SCENES[act[1][0]].frame(act[1][1])
            img = Image.blend(img, nxt, smooth(act[1][1] / XF))
        # global fade in/out
        if tt < 0.5 or tt > total - 0.8:
            a = min(tt / 0.5, (total - tt) / 0.8)
            img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, max(0, min(1, a)))
        p.stdin.write(img.convert("RGB").tobytes())
        if k % 300 == 0:
            print(k, file=sys.stderr, flush=True)
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--still":
        # --still sceneIndex t out.png
        i, tt, o = int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        SCENES[i].frame(tt).convert("RGB").save(o)
    else:
        main(sys.argv[1])

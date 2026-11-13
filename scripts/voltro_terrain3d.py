# 3D terrain concept scene for VOLTRO demo (imported by the video builder).
import math

# ---------------- world
WX, WY = 100.0, 56.0
NX, NY = 44, 26


def height(x, y):
    h = 0.0
    # Taebaek-like ridge running north-south near the east coast
    h += 8.5 * math.exp(-((x - 70) ** 2) / 90 - ((y - 30) ** 2) / 900)
    h += 5.5 * math.exp(-((x - 60) ** 2) / 60 - ((y - 12) ** 2) / 80)
    h += 6.0 * math.exp(-((x - 58) ** 2) / 70 - ((y - 48) ** 2) / 70)
    h += 3.2 * math.exp(-((x - 40) ** 2) / 120 - ((y - 40) ** 2) / 90)
    h += 2.6 * math.exp(-((x - 30) ** 2) / 80 - ((y - 14) ** 2) / 70)
    h += 0.6 * math.sin(x * 0.35) * math.cos(y * 0.4)
    # coastal drop toward the sea
    if x > 90:
        h -= (x - 90) * 0.5
    return max(-1.5, h)


def catmull(pts, n=30):
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


class Route:
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
        return [self.at(f0)] + [q for q, c in zip(self.p, self.c) if s0 < c < s1] + [self.at(f1)]


SEOUL, JUNC, GANG = (8.0, 30.0), (30.0, 31.0), (93.0, 24.0)
SHARED = Route([SEOUL, (16, 31.5), (24, 30.5), JUNC])
# highway: longer, sweeps north around the ridge
FAST = Route([JUNC, (40, 36), (52, 40.5), (66, 41.5), (80, 37), (88, 30), GANG])
# local road: shorter and straighter, crosses the same terrain
ECO = Route([JUNC, (44, 29), (58, 27), (72, 25), (84, 24.5), GANG])


def lengths():
    return SHARED.L + FAST.L, SHARED.L + ECO.L


# ---------------- camera
def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1
    return tuple(c / l for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class Camera:
    def __init__(self, target, dist, yaw, pitch, fl, cx, cy):
        tx, ty, tz = target
        cp = math.cos(pitch)
        self.pos = (tx + dist * cp * math.sin(yaw), ty - dist * cp * math.cos(yaw), tz + dist * math.sin(pitch))
        f = norm((tx - self.pos[0], ty - self.pos[1], tz - self.pos[2]))
        r = norm(cross(f, (0, 0, 1)))
        u = cross(r, f)
        self.f, self.r, self.u = f, r, u
        self.fl, self.cx, self.cy = fl, cx, cy

    def proj(self, p):
        d = (p[0] - self.pos[0], p[1] - self.pos[1], p[2] - self.pos[2])
        z = dot(d, self.f)
        return (self.cx + self.fl * dot(d, self.r) / z, self.cy - self.fl * dot(d, self.u) / z, z)


LIGHT = norm((-0.5, -0.6, 0.75))


def build_mesh():
    xs = [WX * i / NX for i in range(NX + 1)]
    ys = [WY * j / NY for j in range(NY + 1)]
    H = [[height(x, y) for x in xs] for y in ys]
    quads = []
    for j in range(NY):
        for i in range(NX):
            p = [(xs[i], ys[j], H[j][i]), (xs[i + 1], ys[j], H[j][i + 1]),
                 (xs[i + 1], ys[j + 1], H[j + 1][i + 1]), (xs[i], ys[j + 1], H[j + 1][i])]
            a = (p[1][0] - p[0][0], p[1][1] - p[0][1], p[1][2] - p[0][2])
            b = (p[3][0] - p[0][0], p[3][1] - p[0][1], p[3][2] - p[0][2])
            n = norm(cross(a, b))
            shade = max(0.0, dot(n, LIGHT))
            hm = sum(q[2] for q in p) / 4
            sea = all(q[0] > 94 for q in p)
            quads.append((p, shade, hm, sea))
    return quads

MESH = build_mesh()


def lerpc(a, b, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(a[k] + (b[k] - a[k]) * u) for k in range(3))


def draw_terrain(d, cam, hs, ss, ox, oy):
    """Painter-sorted shaded low-poly terrain. ox, oy: canvas offset of layer; ss: supersample factor."""
    polys = []
    for p, shade, hm, sea in MESH:
        pts = [cam.proj((q[0], q[1], q[2] * hs)) for q in p]
        z = sum(q[2] for q in pts) / 4
        polys.append((z, pts, shade, hm, sea))
    polys.sort(key=lambda r: -r[0])
    for z, pts, shade, hm, sea in polys:
        if sea:
            col, edge = (9, 24, 48), (14, 36, 68)
        else:
            u = (hm * hs) / 9.0
            base = lerpc((20, 30, 46), (52, 70, 98), u)
            k = 0.55 + 0.6 * shade
            col = tuple(min(255, int(c * k)) for c in base)
            edge = tuple(min(255, int(c * 1.25 + 8)) for c in col)
        xy = [((q[0] - ox) * ss, (q[1] - oy) * ss) for q in pts]
        d.polygon(xy, fill=col, outline=edge, width=max(1, ss // 2))


def route3d(route, f0, f1, cam, hs, lift=0.5):
    return [cam.proj((x, y, height(x, y) * hs + lift)) for x, y in route.sub(f0, f1)]


def point3d(xy, cam, hs, lift=0.5):
    x, y = xy
    return cam.proj((x, y, height(x, y) * hs + lift))

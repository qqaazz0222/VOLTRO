#!/usr/bin/env python3
"""Build the original VOLTRO vector identity and Android icons from one 48-unit mark.

Requires CairoSVG 2.8.2, fonttools 4.68.0, and Pillow 13.0.0.
SVG lettering is outlined with the app's OFL-licensed Asta Sans font.
"""
from io import BytesIO
from pathlib import Path
import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/brand"
RES = ROOT / "VOLTRO/app/src/main/res"
INK, BLUE, PAPER = "#131417", "#0064FF", "#F7F8FA"
# A continuous V silhouette. The offset cut on the right is a route branch / energy pulse.
MARK = ("M8.8 8 H16 C16.8 8 17.2 8.4 17.6 9.4 L24.2 27.5 L30.8 9.4 "
        "C31.2 8.4 31.6 8 32.4 8 H39.2 C40 8 40.4 8.7 40 9.6 "
        "L36.5 18.5 H29.8 L27.5 24.5 H34.3 L29.3 37.5 "
        "C28.7 39.1 27.4 40 25.8 40 H22.1 C20.5 40 19.3 39.2 18.7 37.6 "
        "L8 9.6 C7.6 8.7 8 8 8.8 8 Z")
font = instantiateVariableFont(TTFont(RES / "font/asta_sans.ttf"), {"wght": 600}, inplace=True)
glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
units = font["head"].unitsPerEm


def lettering(text, x, baseline, size, color=INK, tracking=0):
    paths = []
    scale = size / units
    for char in text:
        name = cmap[ord(char)]
        pen = SVGPathPen(glyphs); glyphs[name].draw(pen)
        paths.append(f'<path transform="translate({x:.4f} {baseline}) scale({scale:.6f} {-scale:.6f})" d="{pen.getCommands()}" fill="{color}"/>')
        x += glyphs[name].width * scale + tracking
    return "".join(paths), x


def mark(color=INK, transform=""):
    return f'<path d="{MARK}" fill="{color}" transform="{transform}"/>'


def svg(width, height, content, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{content}</svg>\n')


def save(name, width, height, content, title, pixels):
    data = svg(width, height, content, title)
    (OUT / f"{name}.svg").write_text(data)
    cairosvg.svg2png(bytestring=data.encode(), write_to=str(OUT / f"{name}.png"), output_width=pixels)


def lockup(color):
    letters, end = lettering("VOLTRO", 58, 40, 42, color, 3.36)
    return mark(color) + letters, round(end + 4, 2)


OUT.mkdir(parents=True, exist_ok=True)
for suffix, color in [("ink", INK), ("white", "#FFFFFF"), ("blue", BLUE)]:
    save(f"voltro-mark-{suffix}", 48, 48, mark(color), f"VOLTRO {suffix} symbol", 1024)
for suffix, color in [("ink", INK), ("white", "#FFFFFF")]:
    content, width = lockup(color)
    save(f"voltro-lockup-{suffix}", width, 48, content, f"VOLTRO {suffix} logo", 1600)
icon = f'<rect width="72" height="72" rx="18" fill="{BLUE}"/>' + mark("#FFFFFF", "translate(3.6 3.6) scale(1.35)")
save("voltro-app-icon", 72, 72, icon, "VOLTRO app icon preview", 1024)

# Brand overview: the same source mark at presentation and small display sizes.
board = [f'<rect width="1600" height="1000" fill="{PAPER}"/>']
board.append(lettering("VOLTRO identity", 80, 84, 36)[0])
board.append(lettering("V / ROUTE / ENERGY", 80, 124, 16, "#686A72", 1.1)[0])
board.append('<rect x="64" y="174" width="720" height="300" rx="28" fill="#FFFFFF"/>')
board.append(f'<rect x="808" y="174" width="728" height="300" rx="28" fill="{INK}"/>')
content, _ = lockup(INK)
board.append(f'<g transform="translate(130 275) scale(2.05)">{content}</g>')
content, _ = lockup("#FFFFFF")
board.append(f'<g transform="translate(880 275) scale(2.05)">{content}</g>')
board.append(lettering("LIGHT", 100, 220, 15, "#686A72", 1.3)[0])
board.append(lettering("DARK", 844, 220, 15, "#C7C9CE", 1.3)[0])
board.append(lettering("APP ICON", 80, 554, 18, INK, 1.2)[0])
board.append(f'<g transform="translate(80 590) scale(3.6)">{icon}</g>')
board.append(f'<circle cx="526" cy="720" r="112" fill="{BLUE}"/>')
board.append(mark("#FFFFFF", "translate(425.2 619.2) scale(4.2)"))
board.append(f'<rect x="698" y="608" width="224" height="224" rx="46" fill="{BLUE}"/>')
board.append(mark("#FFFFFF", "translate(709.2 619.2) scale(4.2)"))
board.append(lettering("48 / 32 / 24", 1040, 614, 16, "#686A72", 1)[0])
for x, size in [(1030, 96), (1162, 64), (1260, 48)]:
    board.append(mark(INK, f"translate({x} 658) scale({size/48})"))
for x, color, label in [(1040, INK, "131417"), (1200, BLUE, "0064FF"), (1360, "#FFFFFF", "FFFFFF")]:
    board.append(f'<rect x="{x}" y="804" width="108" height="42" rx="12" fill="{color}" stroke="#E0E1E6"/>')
    board.append(lettering(label, x, 876, 16, "#686A72")[0])
board.append(lettering("Asta Sans  /  Original vector artwork  /  VOLTRO", 80, 944, 18, "#686A72")[0])
save("voltro-brand-overview", 1600, 1000, "".join(board), "VOLTRO logo, light and dark variants, and app icon", 1600)

# Native VectorDrawables: no raster logo in the app, so all densities share the silhouette.
header = ('<vector xmlns:android="http://schemas.android.com/apk/res/android" '
          'android:width="48dp" android:height="48dp" android:viewportWidth="48" android:viewportHeight="48">\n'
          f'    <path android:fillColor="{INK}" android:pathData="{MARK}" />\n</vector>\n')
(RES / "drawable/ic_voltro.xml").write_text(header)
foreground = ('<vector xmlns:android="http://schemas.android.com/apk/res/android" '
              'android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">\n'
              '    <group android:scaleX="1.35" android:scaleY="1.35" android:translateX="21.6" android:translateY="21.6">\n'
              f'        <path android:fillColor="#FFFFFF" android:pathData="{MARK}" />\n'
              '    </group>\n</vector>\n')
(RES / "drawable/ic_launcher_foreground.xml").write_text(foreground)
(RES / "drawable/ic_launcher_background.xml").write_text(
    f'<shape xmlns:android="http://schemas.android.com/apk/res/android"><solid android:color="{BLUE}" /></shape>\n')
for density, pixels in [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]:
    for is_round in [False, True]:
        background = (f'<circle cx="24" cy="24" r="22" fill="{BLUE}"/>' if is_round else
                      f'<rect x="2" y="2" width="44" height="44" rx="11" fill="{BLUE}"/>')
        source = svg(48, 48, background + mark("#FFFFFF", "translate(4.2 4.2) scale(.825)"), "VOLTRO legacy icon")
        raster = cairosvg.svg2png(bytestring=source.encode(), output_width=pixels*4, output_height=pixels*4)
        with Image.open(BytesIO(raster)) as image:
            image.resize((pixels, pixels), Image.Resampling.LANCZOS).save(
                RES / f"mipmap-{density}" / ("ic_launcher_round.webp" if is_round else "ic_launcher.webp"),
                format="WEBP", lossless=True)
print(f"Brand SVG/PNG and Android resources: {OUT}")

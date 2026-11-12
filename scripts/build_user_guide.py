#!/usr/bin/env python3
"""Create the illustrated Korean guide from preserved, unmodified app screenshots.

Requires python-docx, Pillow, fonttools, and lxml. PDF/render QA is a separate step.
"""
from pathlib import Path
import json
import uuid
from io import BytesIO
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from lxml import etree
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/user-guide"
SHOTS = OUT / "screenshots"
RELEASE = json.loads((ROOT / "apk/VOLTRO_VOLTRO_release.json").read_text())
METRICS = json.loads((OUT / "DEMO_CAPTURE.json").read_text())
FONT = "Asta Sans"
doc = Document()
doc.core_properties.title = "VOLTRO 사용자 가이드"
doc.core_properties.subject = "실제 실행 화면으로 따라 하는 목적지 선택과 에너지 경로 비교"
doc.core_properties.author = "VOLTRO"
doc.core_properties.keywords = "VOLTRO, 사용자 가이드, Pleos, 데모"
for name, size in [("Normal", 12), ("Title", 30), ("Subtitle", 13), ("Heading 1", 23), ("Heading 2", 15), ("Caption", 9)]:
    style = doc.styles[name]
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    style.paragraph_format.space_after = Pt(8)
    style.paragraph_format.line_spacing = 1.18
    if name in ("Title", "Subtitle", "Heading 1", "Heading 2"):
        style.font.bold = name != "Subtitle"
        style.paragraph_format.keep_with_next = True
for name in ("Heading 1", "Heading 2"):
    doc.styles[name].paragraph_format.space_before = Pt(0)
doc.styles["Normal"].paragraph_format.widow_control = True
doc.styles["Caption"].paragraph_format.space_after = Pt(0)
for style in doc.styles:
    for border in style.element.xpath(".//w:pBdr"):
        border.getparent().remove(border)


def setup(section, columns=False):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Inches(11.6929), Inches(8.2677)
    section.left_margin = section.right_margin = Inches(.6)
    section.top_margin = Inches(.52)
    section.bottom_margin = Inches(.58)
    section.footer_distance = Inches(.22)
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols"); section._sectPr.append(cols)
    cols.clear()
    cols.set(qn("w:num"), "2" if columns else "1")
    if columns:
        cols.set(qn("w:equalWidth"), "0")
        cols.set(qn("w:space"), "500")
        for width, space in [(4250, 500), (10360, 0)]:
            item = OxmlElement("w:col"); item.set(qn("w:w"), str(width)); item.set(qn("w:space"), str(space)); cols.append(item)
    section.footer.is_linked_to_previous = True


setup(doc.sections[0])
footer = doc.sections[0].footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.paragraph_format.space_after = Pt(0)
r = footer.add_run(f"VOLTRO 사용자 가이드   |   {RELEASE["version_name"]}   |   ")
r.font.size = Pt(8)
field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"), "PAGE"); footer._p.append(field)


def p(text, style=None, bold=False):
    paragraph = doc.add_paragraph(style=style)
    run = paragraph.add_run(text)
    if bold: run.bold = True
    return paragraph


def heading(text, level=1):
    return doc.add_paragraph(text, style=f"Heading {level}")


def steps(items):
    for i, text in enumerate(items, 1):
        paragraph = p(f"{i}  {text}")
        paragraph.paragraph_format.left_indent = Inches(.23)
        paragraph.paragraph_format.first_line_indent = Inches(-.23)
        paragraph.paragraph_format.space_after = Pt(11)


def note(title, text):
    heading(title, 2); p(text)


def picture(filename, width, caption):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shape = paragraph.add_run().add_picture(str(SHOTS / filename), width=Inches(width))
    shape._inline.docPr.set("descr", caption)
    paragraph = p(caption, "Caption")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def page():
    section = doc.add_section(WD_SECTION_START.NEW_PAGE); setup(section)


def screen_page(filename, title, intro, caption, width=8.0):
    page(); heading(title); p(intro)
    picture(filename, width, caption)


def table(headers, rows, widths):
    result = doc.add_table(rows=1, cols=len(headers))
    result.alignment = WD_TABLE_ALIGNMENT.LEFT
    result.autofit = False
    for column, width in zip(result.columns, widths): column.width = Inches(width)
    for i, title in enumerate(headers): result.rows[0].cells[i].text = title
    for row in rows:
        for cell, value in zip(result.add_row().cells, row): cell.text = str(value)
    borders = OxmlElement("w:tblBorders")
    for side in ["top", "bottom", "left", "right", "insideH", "insideV"]:
        e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "5"); e.set(qn("w:color"), "D9D9D9"); borders.append(e)
    result._tbl.tblPr.append(borders)
    for ri, row in enumerate(result.rows):
        for ci, cell in enumerate(row.cells):
            cell.width = Inches(widths[ci]); cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            margins = OxmlElement("w:tcMar")
            for side in ["top", "bottom", "left", "right"]:
                e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "95"); e.set(qn("w:type"), "dxa"); margins.append(e)
            cell._tc.get_or_add_tcPr().append(margins)
            if ri == 0:
                fill = OxmlElement("w:shd"); fill.set(qn("w:fill"), "EDEEF2"); cell._tc.get_or_add_tcPr().append(fill)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.1
                for run in paragraph.runs:
                    run.font.size = Pt(10.5); run.bold = ri == 0
                    run.font.color.rgb = RGBColor(0, 0, 0)
    return result


# 1 Cover
p("VOLTRO 사용자 가이드", "Title")
p("Pleos 실제 화면으로 따라 하는 지도와 도로 경로 비교", "Subtitle")
p("Pleos Connect에서 실제 지도를 보고 도로 경로의 시간·소비량을 비교한 뒤 주행 재생 결과를 확인하는 방법입니다. 주행 위치와 소비량은 재생·추정값입니다.")
picture("pleos-full-road.png", 9.2, "Pleos Connect 2.1.0의 실제 전체 화면 · OpenStreetMap 지도와 OSRM 도로 경로")
p(f"앱 {RELEASE['version_name']} · 모든 화면은 Pleos에서 직접 촬영 · 지도 데이터 © OpenStreetMap contributors / ODbL · 경로 OSRM", "Caption")

# 2 Preparation
page(); heading("01 설치와 시연 준비")
p("저장소 apk 폴더의 VOLTRO_VOLTRO_release.apk를 설치합니다. Android API 28 이상을 지원하며, 이 가이드는 Pleos Connect 2.1.0 / Android 14에서 촬영한 화면을 기준으로 합니다.")
steps([
    "에뮬레이터에 APK를 설치한 뒤 VOLTRO 아이콘을 선택합니다. Android Studio 에뮬레이터에서는 APK를 창에 끌어 놓아 설치할 수 있습니다.",
    "Home에서 실제 도로를 선택합니다. 출발지는 서울 시청이며 목적지는 강릉역·속초해수욕장·양양 서피비치 중에서 선택합니다.",
    "차량 잔량을 확인합니다. 기본 SOC 68%, 전비 5.2 km/kWh, 용량 70 kWh이며 최소 도착 잔량은 15%입니다. 강릉 실도로 재생 예시는 SDK가 반환한 SOC 100%를 사용했습니다. SDK를 사용할 수 없다면 설정에서 시연용 SOC 100을 입력할 수 있습니다.",
])
table(["모드", "지도와 경로", "네트워크", "주행"], [
    ["실제 도로", "OSM 지도 + OSRM 도로 1~3개", "인터넷 필요", "실도로 좌표 재생"],
    ["오프라인 데모", "격자 모식도 + 합성 경로 3개", "서버 없이 사용", "합성 좌표 재생"],
], [1.6, 4.1, 2.25, 2.2])
p("")
note("화면과 실제 차량값의 구분", "SOC 100% 화면은 Pleos 에뮬레이터의 실제 SDK 응답입니다. 실차 측정값이 아닙니다. 전비 5.2와 용량 70은 설정값이며, SDK 읽기는 계속 갱신되는 계측값이 아닌 한 번의 snapshot입니다.")
note("가이드 화면의 기준", "모든 이미지는 Pleos 개발 빌드의 실제 화면입니다. 전체 화면은 2560×1440px, 앱 창은 Android PixelCopy로 직접 캡처한 1682×1210px입니다. 휴대폰 화면이나 합성 UI는 포함하지 않았습니다. 배포용 release APK에서는 개발 서버 항목이 비활성화됩니다.")

# 3 Home
screen_page("pleos-home.png", "02 목적지를 선택하기",
    "실제 도로가 선택되어 있는지 확인하고 강릉역을 누른 뒤 경로 분석하기를 선택합니다. 지도와 경로 조회에는 인터넷이 필요하며 출발지·목적지 좌표가 외부 서비스로 전송됩니다.",
    "화면 1  Pleos Home · 기본 SOC 68% · 보조 문구 22sp와 버튼 24sp 적용")

# 4 Vehicle SDK
screen_page("pleos-sdk.png", "03 Pleos 차량 상태를 읽기",
    "Pleos 차량 상태 읽기를 누르면 지원되는 SOC·전비를 한 번 가져옵니다. 아래 화면은 SOC 100%를 읽은 결과입니다. 실패하면 기존 값을 유지하며 설정값으로도 경로를 분석할 수 있습니다.",
    "화면 2  SDK SOC 100% · 전비와 용량의 출처는 설정값 · 에뮬레이터 응답")

# 5 Actual routes
route_summary = " / ".join(f"{r['label']} {r['distance_km']:.1f}km·{r['minutes']:.0f}분·{r['energy_kwh']:.1f}kWh" for r in METRICS['routes'])
screen_page("pleos-comparison.png", "04 실제 도로 경로를 비교하기",
    "카드를 눌러 경로를 선택합니다. 지도는 드래그와 +·−·전체 보기를 지원합니다. 반환된 실제 경로만 표시하며, 최소 도착 잔량을 충족해야 주행 재생을 시작할 수 있습니다.",
    "화면 3  OpenStreetMap 지도와 OSRM 도로 2개 · SOC 100% 기준")

# 6 Replay
screen_page("pleos-driving.png", "05 도로 위의 주행을 재생하기",
    "선택한 경로로 주행 재생을 누르면 도로 좌표를 따라 위치·잔량·남은 시간을 갱신합니다. 일시정지·데모 계속과 배속 1×·4×·12×를 사용할 수 있으며, 주행 중 지도 조작은 제한됩니다.",
    "화면 4  실제 도로 좌표를 재생하다 일시정지한 화면 · GPS 추적과 차량 내비 제어는 미연동")

# 7 Report
screen_page("pleos-report.png", "06 완료 리포트를 확인하기",
    "목적지에 도착하면 리포트를 자동으로 저장합니다. 거리와 가상 시간, 출발 시 예상 소비량, SOC 변화를 확인하세요. 실측 소비량과 예측 오차는 제공하지 않습니다.",
    f"화면 5  {METRICS['completed_route']} 재생 완료 · {METRICS['completed_km']:.1f}km · 약 {METRICS['completed_energy_kwh']:.1f}kWh 추정")

# 8 History
screen_page("pleos-history.png", "07 지난 주행 결과를 다시 보기",
    "주행 이력을 눌러 최근 50개 완료 기록을 확인합니다. 기록을 누르면 리포트가 다시 열립니다. 기기 주행 이력 삭제는 확인 후 기기의 모든 기록을 지우며, 취소한 주행은 완료 기록에 저장되지 않습니다.",
    "화면 6  Pleos 기기의 실제 주행 이력 · 도로 재생과 Mock 기록을 구분")

# 9 Settings: full display includes the native dialog
screen_page("pleos-settings.png", "08 차량값과 조건을 설정하기",
    "Home의 설정에서 SOC·전비·사용 가능 용량·최소 도착 잔량·허용 추가 시간을 입력하고 적용합니다. 기존 분석이 지워지므로 다시 분석해야 합니다. 필요한 경우 설정창을 아래로 스크롤하세요.",
    "화면 7  Pleos 전체 화면에 열린 실제 설정창 · 개발 빌드 화면", width=9.4)
p("입력 범위: SOC·최소 잔량 0~100%, 전비 0 초과~30, 용량 0 초과~300kWh, 추가 시간 0~120분.")

# 10 Safety
screen_page("pleos-soc-blocked.png", "09 도착 잔량이 부족한 경우",
    "SOC 68%로 같은 실도로를 분석하면 도착 잔량이 최소 15%에 미달해 시작 버튼이 비활성화됩니다. 실제 출발 SOC·전비·용량을 확인하고 재분석하세요. 기준을 자동으로 낮추지 않습니다.",
    "화면 8  실제 도로와 같은 차량 용량 · SOC 68%에서 최소 도착 잔량 미달 차단")

# 11 Branch decision example
screen_page("pleos-junction-demo.png", "10 분기점 안내를 시연하기",
    "Home에서 오프라인 데모를 선택하고 기본값 68%·5.2·70으로 강릉역의 빠른 경로를 재생합니다. 분기점 안내에서 절전 경로로 변경 또는 기존 경로 유지를 선택합니다. 선택 동안 재생은 멈춥니다.",
    "화면 9  Pleos의 오프라인 분기점 시연 · 합성 경로의 2.9kWh·15분 예시")

# 12 Troubleshooting and scope
page(); heading("11 문제 해결과 숫자 읽기")
table(["보이는 상황", "확인할 내용과 조작"], [
    ["도로 경로 조회 실패", "인터넷 연결을 확인한 뒤 다시 분석합니다. 마지막 분석은 유지되며 오프라인 데모로 자동 전환하지 않습니다."],
    ["배경 지도 연결 실패", "화면의 재시도 안내를 누릅니다. 이미 받은 도로 경로는 유지되며 타일 로딩과 경로 응답을 구분합니다."],
    ["후보가 한 개만 나옴", "공급자가 대안을 반환하지 않은 경우입니다. 없는 경로를 임의로 추가하지 않습니다."],
    ["두 경로의 kWh가 같아 보임", "현재 모델은 거리÷전비입니다. 거리 차이가 작으면 소수점 한 자리 반올림값이 같을 수 있습니다."],
    ["분기점 안내가 나오지 않음", "같은 분기점·절약량·추가 시간·도착 잔량 조건을 충족할 때만 표시합니다. 도로 경로에 항상 대안이 있는 것은 아닙니다."],
    ["Pleos 읽기 실패 또는 timeout", "기존 설정값으로 진행합니다. 서비스·지원 여부를 확인하고 재설치 직후라면 에뮬레이터 cold boot 후 다시 읽습니다."],
    ["앱으로 돌아오니 일시정지", "데모 계속을 누릅니다. 프로세스가 종료된 경우 진행 중 재생은 복원되지 않으며 완료 이력만 유지됩니다."],
], [2.35, 7.8])
p("")
note("실제 도로와 추정 소비량", "지도와 경로 geometry·거리·ETA는 실제 공개 서비스의 응답입니다. 소비량은 같은 baseline 모델의 추정이며 실시간 교통·고도·날씨는 반영하지 않습니다. 주행은 좌표 재생으로 실제 GPS 추적·차량 내비 변경·음성 안내는 제공하지 않습니다.")
p(f"촬영 당시 경로 예시: {route_summary}. 조회 시점에 따라 거리·시간·후보 수가 달라집니다. 분기점 시연 페이지의 2.9kWh는 합성 데모 수치입니다.")
p("지도 데이터 © OpenStreetMap contributors / ODbL · https://www.openstreetmap.org/copyright · 경로 OSRM · https://routing.openstreetmap.de/about.html", "Caption")
p(f"앱 {RELEASE['version_name']} / release APK SHA-256 앞자리 {RELEASE['sha256'][:16]} · 촬영 빌드와 원본 이미지 정보: CAPTURE_INFO.json", "Caption")

OUT.mkdir(parents=True, exist_ok=True)
# Embed OFL-licensed Asta Sans regular/bold fonts so Korean stays readable across machines.
font_directory = ROOT / "artifacts/user-guide-fonts"
font_directory.mkdir(parents=True, exist_ok=True)
font_source = ROOT / "VOLTRO/app/src/main/res/font/asta_sans.ttf"
font_table = next(rel.target_part for rel in doc.part.rels.values() if rel.reltype.endswith("/fontTable"))
font_xml = etree.fromstring(font_table.blob)
family = OxmlElement("w:font"); family.set(qn("w:name"), FONT)
for face, weight in [("Regular", 400), ("Bold", 600)]:
    font = instantiateVariableFont(TTFont(font_source), {"wght": weight}, inplace=True, updateFontNames=True)
    stream = BytesIO(); font.save(stream)
    data = stream.getvalue()
    (font_directory / f"AstaSans-{face}.ttf").write_bytes(data)
    key = uuid.uuid4()
    mask = key.bytes[::-1]
    encoded = bytearray(data)
    for i in range(32): encoded[i] ^= mask[i % 16]
    part = Part(PackURI(f"/word/fonts/AstaSans{face}.odttf"),
        "application/vnd.openxmlformats-officedocument.obfuscatedFont", bytes(encoded), doc.part.package)
    rid = font_table.relate_to(part, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font")
    embed = OxmlElement("w:embedRegular" if face == "Regular" else "w:embedBold")
    embed.set(qn("r:id"), rid); embed.set(qn("w:fontKey"), "{" + str(key).upper() + "}")
    family.append(embed)
font_xml.append(family)
font_table._blob = etree.tostring(font_xml, xml_declaration=True, encoding="UTF-8", standalone=True)
doc.settings.element.append(OxmlElement("w:embedTrueTypeFonts"))
doc.save(OUT / "VOLTRO_User_Guide.docx")
print(OUT / "VOLTRO_User_Guide.docx")

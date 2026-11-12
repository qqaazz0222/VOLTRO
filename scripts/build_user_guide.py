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
r = footer.add_run("VOLTRO 사용자 가이드   |   1.0.0-mvp   |   ")
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


def screen_page(filename, title, caption):
    section = doc.add_section(WD_SECTION_START.NEW_PAGE); setup(section, True)
    picture(filename, 2.83, caption)
    doc.add_paragraph().add_run().add_break(WD_BREAK.COLUMN)
    heading(title)


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


# 1 Overview and installation
p("VOLTRO 사용자 가이드", "Title")
p("실제 실행 화면으로 따라 하는 에너지 경로 비교와 주행 데모", "Subtitle")
p("처음 사용하는 참가자와 시연자가 서버 없이 목적지를 선택하고, 경로별 소비량을 비교한 뒤 주행 결과를 확인하는 방법을 안내합니다. 현재 경로와 주행은 시뮬레이션입니다.")
picture("pleos-home.png", 8.4, "화면 1  Pleos Connect 2.1.0 에뮬레이터의 실제 Home 화면  |  개발 빌드  |  2560 × 1440 px")
p("가이드 기준  2026년 11월 12일  ·  앱 1.0.0-mvp  ·  기본 시나리오 68% / 5.2 km/kWh / 70 kWh", "Caption")

# 2 Getting ready
page(); heading("01 사용 전 준비")
p("기본 데모는 로그인, 차량 연결, 서버 실행 없이 사용할 수 있습니다. 아래 값으로 시작하면 이 가이드의 수치와 같은 결과를 확인할 수 있습니다.")
heading("설치와 실행", 2)
steps([
    "저장소의 apk 폴더에서 VOLTRO_VOLTRO_release.apk를 받습니다. Android API 28 이상 기기 또는 에뮬레이터가 필요합니다.",
    "에뮬레이터에 APK를 설치한 뒤 VOLTRO 아이콘을 선택합니다. Android Studio 에뮬레이터에서는 APK 파일을 창에 끌어 놓아 설치할 수 있습니다.",
    "Home 오른쪽 위의 설정을 열어 SOC 68, 전비 5.2, 용량 70, 최소 도착 잔량 15, 허용 추가 시간 15로 확인합니다. 적용을 누르면 Home으로 돌아갑니다.",
])
table(["차량 입력", "기본값", "의미"], [
    ["SOC", "68%", "출발할 때의 배터리 잔량"], ["평균 전비", "5.2 km/kWh", "1 kWh로 이동하는 예상 거리"],
    ["사용 가능 배터리 용량", "70 kWh", "에너지 소비량을 잔량으로 환산할 때 사용하는 설정값"],
], [2.25, 1.65, 6.25])
p("")
note("가장 빠른 시연 순서", "강릉역 선택 → 경로 분석하기 → 빠른 경로 선택 → Mock 주행 → 분기점에서 절전 경로로 변경 → 리포트 → 주행 이력. 기본 4배속에서는 조작 시간을 제외하고 약 30초 안팎의 주행을 재생합니다.")
note("화면을 읽는 방법", "작은 창에서는 항목이 세로로 이어집니다. 아래로 스크롤해 카드와 조작부를 확인하세요. 넓은 Pleos 창에서는 목적지와 차량 정보, 지도와 경로 카드가 나란히 표시됩니다.")
p("아래 단계별 세로 화면은 배포용 release APK를 Android API 37에서 직접 실행해 캡처했습니다. Pleos 화면은 같은 기능의 개발 빌드를 실제 에뮬레이터에서 캡처했습니다.", "Caption")

# 3 Home
screen_page("home.png", "02 목적지를 선택하기", "화면 2  release APK의 Home  |  세로 창에서는 차량 카드가 아래에 이어집니다")
p("Home에서 데모 목적지를 선택합니다. 현재 출발지는 서울 시청이며, 일반 장소 검색 대신 제공된 세 곳의 목적지를 사용할 수 있습니다.")
steps([
    "강릉역을 누릅니다. 또는 검색창에 강릉을 입력합니다.",
    "화면 아래의 경로 분석하기를 누릅니다.",
    "경로 비교 화면이 열리면 거리, 시간, 소비량과 도착 잔량을 확인합니다.",
])
heading("선택할 수 있는 목적지", 2)
p("강릉역  ·  속초해수욕장  ·  양양 서피비치")
note("차량 정보 확인", "화면을 아래로 스크롤하면 현재 SOC, 평균 전비와 사용 가능 용량을 볼 수 있습니다. 기본 상태는 Demo EV입니다. Pleos 차량 상태 읽기는 선택 기능이며 기본 데모를 시작하는 데 필요하지 않습니다.")
note("목적지를 찾을 수 없다면", "세 곳 중 하나의 이름을 입력하거나 추천 목록에서 직접 선택하세요. 현재 버전은 실제 장소 검색과 실도로 경로 탐색을 제공하지 않습니다.")

# 4 Compare
screen_page("routes-list.png", "03 경로를 비교하고 선택하기", "화면 3  실제 경로 카드  |  지도 아래로 스크롤한 화면")
p("지도는 경로 좌표를 연결한 데모 모식도입니다. 경로 카드가 아래에 더 있다면 스크롤해 빠른 경로, 균형 경로와 절전 경로를 비교합니다.")
table(["경로", "시간", "소비량", "도착 잔량"], [
    ["빠른 경로", "130분", "34.6 kWh", "18.5%"],
    ["균형 경로", "137분", "33.5 kWh", "20.2%"],
    ["절전 경로", "145분", "31.7 kWh", "22.7%"],
], [1.6, 1.1, 1.6, 1.55])
p("위 값은 강릉역과 기본 차량 입력을 사용한 예시입니다. 절전 경로는 빠른 경로보다 15분 더 걸리고 약 2.9 kWh를 덜 소비합니다.")
steps([
    "카드를 눌러 원하는 경로를 선택합니다. 선택한 카드는 테두리와 표시 색이 바뀝니다.",
    "분기점 안내를 시연하려면 빠른 경로를 선택합니다. 기본 추천인 절전 경로로 출발하면 불필요한 전환 안내가 나오지 않을 수 있습니다.",
    "선택한 경로로 Mock 주행을 누릅니다.",
])
note("선택할 수 없는 경로", "도착 잔량이 설정한 최소값보다 낮은 경로는 선택할 수 없습니다. 모든 경로가 부족하면 시작 버튼이 비활성화됩니다. 설정을 확인하고 다시 분석하세요.")

# 5 driving
screen_page("junction.png", "04 분기점 안내에 응답하기", "화면 4  빠른 경로 주행 중 실제로 표시된 분기점 안내")
p("주행 화면은 위치를 순서대로 재생하며 잔량과 남은 거리·시간을 갱신합니다. 빠른 경로에서는 분기점 약 1.2 km 전에 절전 대안이 표시됩니다.")
steps([
    "안내의 절약량과 추가 시간을 확인합니다. 기본 예시는 약 2.9 kWh 절약, 15분 추가입니다.",
    "절전 경로로 변경을 누르면 승인을 반영해 ECO 경로로 시뮬레이션을 이어갑니다.",
    "기존 경로 유지를 누르면 빠른 경로를 계속 재생합니다. 선택할 동안 데모는 일시정지됩니다.",
])
table(["주행 조작", "동작"], [
    ["일시정지 또는 데모 계속", "재생을 멈추거나 이어갑니다"],
    ["배속", "1배속 → 4배속 → 12배속 순으로 바뀝니다"],
    ["주행 취소", "확인 후 데모를 종료하며 완료 이력으로 저장하지 않습니다"],
], [2.1, 3.75])
p("작은 창에서는 조작부가 아래에 있을 수 있습니다. 다른 앱으로 이동하면 데모가 멈추므로 돌아온 뒤 데모 계속을 누르세요.")
note("실제 내비게이션과의 차이", "이 버튼은 VOLTRO 시뮬레이터의 경로만 바꿉니다. 차량 내비게이션을 변경하거나 실제 분기점의 회전 지시를 제공하지 않습니다.")

# 6 report
screen_page("report.png", "05 주행 결과 확인하기", "화면 5  절전 경로로 변경한 뒤 도착한 실제 리포트")
p("목적지에 도착하면 리포트가 자동으로 열리고 기기에 저장됩니다. 기본 예시에서 빠른 경로로 출발한 뒤 절전 경로를 승인하면 아래 결과를 확인할 수 있습니다.")
table(["표시 항목", "예시 결과"], [
    ["완료 경로", "절전 경로"], ["총 주행 거리", "165.0 km"], ["가상 주행 시간", "145분"],
    ["시뮬레이션 소비량", "31.7 kWh"], ["출발 시 예상 소비량", "34.6 kWh"], ["배터리 변화", "68.0% → 22.7%"],
], [2.75, 3.1])
p("")
note("두 소비량이 다른 이유", "출발 시 예상 소비량은 처음 선택한 빠른 경로의 값입니다. 완료 소비량은 전환 후 실제로 재생한 데모 경로의 계산값이므로 서로 다를 수 있습니다.")
note("실측값으로 해석하지 않기", "실측 소비량은 측정되지 않음으로 표시되고 예측 오차는 계산하지 않습니다. 시뮬레이션 소비량과 SOC 변화는 같은 기본 모델로 계산한 값입니다.")

# 7 history
screen_page("history.png", "06 지난 주행을 다시 보기", "화면 6  기기에 저장된 실제 주행 이력")
p("리포트의 새로운 여정 시작하기로 Home에 돌아갑니다. 오른쪽 위의 주행 이력을 누르면 이 기기에 저장된 최근 50개의 완료 기록을 확인할 수 있습니다.")
steps([
    "목적지, 선택 경로, 거리와 시뮬레이션 소비량을 확인합니다.",
    "원하는 기록을 누르면 해당 주행의 리포트가 다시 열립니다.",
    "기록을 지우려면 기기 주행 이력 삭제를 누르고 확인창에서 삭제를 선택합니다.",
])
note("삭제 범위", "확인 후 이 기기의 모든 주행 기록이 삭제됩니다. 별도 개발 서버에 전송한 기록은 기기 삭제 버튼으로 지워지지 않습니다.")
note("저장되는 기록", "완료된 주행만 이력에 남습니다. 취소한 주행은 완료 기록으로 저장되지 않으며, 앱 프로세스가 종료되면 진행 중인 데모를 복원하지 않습니다.")
note("기록이 없다면", "주행이 목적지까지 완료됐는지 확인하세요. 기본 데모를 한 번 끝까지 재생하면 목록에 기록이 추가됩니다.")

# 8 settings
screen_page("settings.png", "07 차량값과 데모 조건 설정하기", "화면 7  release APK의 실제 설정 화면  |  개발 서버 항목은 비활성화됩니다")
p("Home의 설정에서 입력값을 바꾼 뒤 적용을 누릅니다. 적용하면 기존 분석을 지우고 Home으로 돌아가므로 경로를 다시 분석해야 합니다.")
table(["항목", "기본값", "입력 범위"], [
    ["출발 배터리 SOC", "68%", "0~100%"], ["평균 전비", "5.2 km/kWh", "0 초과, 30 이하"],
    ["사용 가능 용량", "70 kWh", "0 초과, 300 이하"], ["최소 도착 잔량", "15%", "0~100%"],
    ["허용 추가 시간", "15분", "0~120분"],
], [2.65, 1.45, 1.75])
p("")
note("경로 변경 실패 시나리오", "이 스위치를 켜고 빠른 경로로 주행하면, 분기점에서 변경을 승인해도 실패 메시지와 함께 기존 경로를 유지하는 동작을 시연할 수 있습니다. 정상 데모를 다시 하려면 스위치를 끄고 적용하세요.")
note("개발 서버 항목", "공모전용 release APK에서는 개발 서버 사용과 서버 연결 확인이 비활성화됩니다. 서버 없이 기본 사용자 흐름을 사용할 수 있습니다. 개발 빌드의 서버 설정은 저장소 README를 참고하세요.")
p("차량값과 선호값은 기기에 저장됩니다. 숫자 입력 오류가 나오면 입력 범위를 확인하세요. 가이드의 예시 수치를 재현하려면 위 기본값으로 복원합니다.")

# 9 SDK full width
page(); heading("08 Pleos 차량 정보를 불러오기")
p("Pleos Connect의 Home에서 Pleos 차량 상태 읽기를 누릅니다. SOC와 지원되는 누적 전비를 한 번 읽으며, 성공하면 차량 카드의 출처 표시가 바뀝니다.")
picture("pleos-sdk.png", 7.8, "화면 8  Pleos Vehicle SDK가 SOC 100%를 반환한 실제 실행 화면  |  개발 빌드  |  에뮬레이터 값")
p("이 화면에서는 SOC만 SDK snapshot이며 전비 5.2와 용량 70은 설정값입니다. 전비가 지원되는 환경에서는 전비도 SDK 값으로 표시됩니다. 용량은 설정값으로 유지됩니다.")
p("읽은 SOC가 기본값 68%와 다르면 경로별 도착 잔량도 달라집니다. 이 가이드와 같은 수치가 필요하면 설정에서 기본값으로 돌린 뒤 다시 분석하세요. snapshot은 계속 갱신되는 실시간 계측값이 아닙니다.")

# 10 troubleshooting
page(); heading("09 문제가 생겼을 때")
p("먼저 화면의 안내 문구를 확인하세요. 오류가 나도 기존 경로 또는 차량 입력값을 유지하도록 동작합니다.")
table(["보이는 상황", "확인할 내용", "사용자가 할 일"], [
    ["목적지 오류", "데모 목적지 외의 장소를 입력했는지 확인", "강릉역, 속초해수욕장, 양양 서피비치 중 선택"],
    ["시작 버튼 비활성", "예상 도착 SOC가 최소 잔량 미달인지 확인", "차량값과 최소 도착 잔량을 확인한 뒤 재분석"],
    ["분기점 안내가 없음", "이미 절전 경로로 출발했거나 추천 조건 미충족", "안내를 시연하려면 기본값과 빠른 경로로 시작"],
    ["Pleos 값을 읽지 못함", "일반 Android이거나 서비스·권한·capability 미지원", "기존 설정값으로 데모 진행 또는 Pleos 환경 확인"],
    ["Pleos 응답 시간 초과", "재설치 직후 서비스 응답 지연 여부", "기존 값으로 진행하고 에뮬레이터 cold boot 후 재시도"],
    ["앱으로 돌아오니 정지", "다른 앱으로 이동해 데모가 일시정지됨", "주행 화면의 데모 계속 선택"],
    ["APK 업데이트 설치 실패", "개발용 debug 앱과 release의 서명이 다른지 확인", "이력 보존이 필요하면 별도 에뮬레이터에서 release 실행"],
], [2.2, 3.65, 4.3])
p("")
note("현재 사용할 수 있는 범위", "현재 버전은 합성 경로를 비교하고 주행을 재생하는 시연용 앱입니다. 실제 도로 검색, GPS 주행 추적, 차량 내비게이션 경로 변경과 음성 안내는 제공하지 않습니다. Pleos SDK snapshot을 읽어도 경로와 주행은 데모로 유지됩니다.")
note("숫자와 단위", "kWh는 소비 전력량, km/kWh는 전비, %는 배터리 잔량입니다. SOC 변화는 %p로 표기합니다. 예를 들어 68.0%에서 22.7%로 줄어든 차이는 45.3%p입니다.")
p(f"화면과 기능 기준  앱 {RELEASE['version_name']} / release APK SHA-256 앞자리 {RELEASE['sha256'][:16]}  |  원본 화면과 캡처 정보는 같은 폴더의 screenshots 및 CAPTURE_INFO.json에서 확인할 수 있습니다.", "Caption")

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

# Pleos에 맞춘 VOLTRO UI

2026-11-12 확인한 공개 Pleos 가이드와 Pleos Connect 2.1.0 에뮬레이터를 기준으로 구현했다. Pleos UI SDK를 사용한 구현이나 플랫폼 심사 통과를 뜻하지 않는다.

## 기준 문서

- [디자인 원칙](https://document.pleos.ai/docs/connect/guide/docs-design/Introduction/intro): 일관된 패턴, 짧은 문구, 명확한 대비, 주야간 대응.
- [Colors](https://document.pleos.ai/docs/connect/guide/docs-design/foundations/colors): grayscale와 informative 색상의 공개 표.
- [Typography](https://document.pleos.ai/docs/connect/guide/docs-design/foundations/typography): Asta Sans, 중립적인 서체와 최소 18px 가독성 권장.
- [Iconography](https://document.pleos.ai/docs/connect/guide/docs-design/foundations/contents-creation/iconography): 48×48dp 기반 선형/채움 아이콘.
- [App Icon](https://document.pleos.ai/docs/connect/guide/docs-design/foundations/contents-creation/app-icon): foreground/background 분리와 adaptive icon.
- [Basic Button](https://document.pleos.ai/docs/connect/guide/docs-design/components/actions/basic-button): 기본·눌림·비활성·로딩 상태.

## 적용

| 역할 | Light | Dark |
|---|---|---|
| 앱 배경 | `#F7F8FA` | `#1D1E21` |
| 카드 | `#FFFFFF` | `#313236` |
| 본문 | `#131417` | `#FFFFFF` |
| 보조 글자 | `#686A72` | `#C7C9CE` |
| Filled 버튼 | `#44464E` | `#EDEEF2` |
| 선택/긍정 정보 | `#0064FF` | `#86B6FF` |
| 배터리 상태 | `#008347` | `#00E074` |

Grayscale 원색은 공식 표에 따른다. Light 배터리 green과 Dark 정보 blue는 일반 텍스트 대비 4.5:1을 만족하도록 공식 informative 색상에서 조정한 앱 전용 변형이다. 청색은 선택/정보에만, 녹색은 배터리 상태에 사용한다. 자율주행 의미의 보라색은 사용하지 않는다.

- `PleosDesign.kt`와 `values[-night]/colors.xml`에 색상과 글꼴을 모은다. 시스템 night mode에 따라 전환한다.
- Asta Sans 가변 폰트를 앱에 포함한다. 라이선스는 `licenses/AstaSans-OFL.txt`와 앱 assets에 있다.
- 넓은 차량 창에서는 보조 문구·입력값을 최소 22sp, 버튼은 24sp로 표시한다. 좁은 창의 최소 18sp는 유지한다. 핵심 수치는 30–48sp, 기본 버튼은 64dp 높이를 사용한다. 지도 출처·로딩 안내는 18sp, 배경 지도 타일은 차량 화면에서 1.5배 크기로 그려 지명을 읽기 쉽게 했다.
- 흑백 filled 주요 버튼, 중립색 보조 버튼, Ripple·haptic 피드백, 선택 카드 테두리를 적용한다.
- VectorDrawable을 사용해 VOLTRO 고유 V/에너지 마크, 이력, 설정, 이동 아이콘을 구성한다. 시스템 로고나 타사 아이콘 파일은 복사하지 않는다. 로고는 경로가 합쳐지는 V와 에너지 꺾임을 연결한 채움형으로 새로 제작했다. 주야간 단색 로고와 청색 adaptive 앱 아이콘의 원본·사용법은 [브랜드 자산](../design/brand/README.md)에 있다.
- adaptive launcher icon을 별도의 배경·전경으로 제공한다.
- 차량의 넓은 화면에서는 2열, 작은 창에서는 1열로 전환한다. 시스템 바와 분할 창의 inset을 반영한다.
- 실제 도로 모드는 OSM 배경 지도와 OSRM 도로 geometry를 표시한다. 지도 출처를 항상 표시하고 주행이 좌표 재생임을 구분한다. 별도 오프라인 모드의 합성 경로 그림은 모식도라고 표시한다.
- 주행 화면에서 목적지 검색·설정·이력 접근을 차단한다. Mock 조작부는 시뮬레이터 기능이다. 승인 판단 동안 시뮬레이터를 멈춘다.

## 검증 범위

`DesignContrastTest`는 주간/야간 본문·보조 글자·선택 표시·CTA·오류 표시의 대비를 검사한다. Pleos 실차의 물리적 글자 크기, 운전 중 조작 허용 여부, 각 제조사 마스킹, 런처 캐시와 차량별 폰트 렌더링은 실차 검증이 필요하다.

# VOLTRO

전기차의 SOC와 전비로 경로별 예상 소비량·도착 잔량을 비교하고 절전 경로 선택을 돕는 Pleos용 주행 의사결정 보조 앱입니다.

Your Route. Your Energy.

## 제출 정보 (2026-11-15)

| 항목 | 제출 내용 |
|---|---|
| 팀명 / 앱 이름 | 김현수 / VOLTRO |
| GitHub 저장소 | https://github.com/qqaazz0222/VOLTRO |
| 소스 코드 | Android 앱: `VOLTRO/`, 선택적 개발 서버: `backend/` |
| APK 파일 경로 | [`apk/김현수_VOLTRO_release.apk`](apk/김현수_VOLTRO_release.apk) |
| GitHub Release | [VOLTRO 1.2.0 MVP 제출본](https://github.com/qqaazz0222/VOLTRO/releases/tag/v1.2.0-mvp-submission) |
| 버전 / 지원 OS | `1.2.0-mvp` / Android 9(API 28) 이상 |
| 공개 상태 | Public (2026-11-15 확인). 제출 안내에 따라 2026-11-23까지 공개 상태를 유지해야 합니다. |

APK는 약 4.56MB이며 소스 코드와 함께 저장소의 `apk/`에 포함합니다. 제출 페이지에는 위 저장소 주소와 APK 파일 경로를 입력합니다. 접수 메일에는 저장소 주소와 **최종 제출 커밋 전체 해시**를 기재합니다. Release 본문에 기록한 최종 제출 커밋을 사용하며, 로컬에서는 아래 명령으로 확인할 수 있습니다.

```sh
git fetch origin tag v1.2.0-mvp-submission
git rev-parse 'v1.2.0-mvp-submission^{commit}'
```

APK JSON의 `source_commit`은 빌드에 사용한 소스 커밋입니다. 최종 제출 커밋에는 그 소스와 완성된 APK·JSON·체크섬이 모두 포함되므로 빌드 소스 커밋과 다를 수 있습니다.

## APK 설치 및 빠른 실행

Android 9(API 28) 이상 또는 Pleos Connect 에뮬레이터에 APK를 설치합니다. Android SDK의 `platform-tools`를 PATH에 추가한 환경에서는 다음과 같이 실행합니다.

```sh
adb install -r 'apk/김현수_VOLTRO_release.apk'
adb shell am start -n com.qqaazz0222.voltro/.MainActivity
```

- 인터넷 없이 실행: **Home → 오프라인 데모 → 강릉역 → 경로 분석하기 → 빠른 경로 → Mock 주행 → 분기점 승인 → 리포트**.
- 실제 지도 실행: 인터넷을 연결한 뒤 **Home → 실제 도로 → 목적지 → 경로 분석하기**. 지도·경로 API 키와 별도 서버는 필요 없습니다. SOC가 부족하면 차량 입력을 조정한 뒤 다시 분석합니다.
- Pleos 차량 상태 읽기는 Pleos Vehicle Service가 제공되는 에뮬레이터에서 사용합니다. 일반 Android에서는 수동 입력과 오프라인 데모를 사용할 수 있습니다.
- 같은 앱 ID의 debug APK가 설치되어 있으면 서명이 달라 업데이트 설치가 실패할 수 있습니다. 별도 에뮬레이터를 사용해 기존 데이터를 보존합니다.

## 테스트 환경 및 필요한 설정

| 항목 | 확인된 환경 / 설정 |
|---|---|
| 개발 에뮬레이터 | Pleos Connect **2.1.0**, Android **14/API 34**, arm64 |
| Pleos 화면 규격 | 전체 **2560×1440 px / 160 dpi**, 확장 앱 영역 관찰값 **1682×1210 px** |
| 일반 Android 검증 | **API 37**, **1080×2400 px / 420 dpi** |
| Vehicle SDK / Service | SDK **2.3.2** / Pleos Vehicle Service **2.3.22** (선택적 차량 상태 읽기) |
| 앱 빌드 | Android Studio bundled JDK, 포함된 Gradle wrapper, Android SDK **37**, SDK Build Tools |
| 개발 서버 | Python **3.11 이상**, FastAPI. Release의 지도·오프라인 시연에는 불필요 |
| 네트워크 | 실제 지도·도로: HTTPS OSM/OSRM 연결 필요. 오프라인 데모: 불필요 |
| SDK 경로 | Android Studio에서 설정하거나 `VOLTRO/local.properties`의 `sdk.dir` 또는 `ANDROID_HOME` 지정 |

빌드 명령과 개발 서버 설정은 아래 개발 환경 및 서버 연동 항목을 참고합니다. Release 빌드에서는 로컬 HTTP 개발 서버가 비활성화됩니다.

## 1.2.0 제출 버전

[신규 signed release APK](apk/김현수_VOLTRO_release.apk) · [2분 30초 시연 영상](docs/submission/VOLTRO_Demo.mp4) · [기획 원고·시연 대본·제출 안내](docs/submission/README.md) · [APK 버전·소스 커밋·서명](apk/김현수_VOLTRO_release.json)

- Home의 **심사 시연 시나리오**에서 절전 전환·잔량 부족·경로 변경 실패를 준비한다. 데모 입력은 저장된 프로필과 완료 이력을 바꾸지 않는다.
- 비교 화면에 추천 근거·최소 잔량 여유·전비 20% 저하 가정과 잔량 부족 시 최소 출발 SOC·추가 배터리 에너지를 표시한다. 저하 가정은 통계적 오차 범위가 아니다.
- 재생 중 프로세스가 종료되면 Home의 **이전 재생 복구**로 마지막 체크포인트를 불러온다. 복구 후에는 항상 일시정지하며 분기점 승인도 보존한다. 24시간 유효한 기기 내 임시 기록이다.
- 경로 변경 실패는 기존 경로를 유지하고 재생을 정지한다. 완료 리포트는 출발 경로 대비 계산상 에너지·시간 변화를 표시한다.

제출 소스와 APK는 `main`에 커밋·푸시하며 제출 태그로 고정한다. 최신 APK의 정확한 빌드 소스 커밋·SHA-256·서명은 JSON에 기록한다. 기존 1.1.0 배포본은 [보관 폴더](apk/archive/1.1.0/)에 보존했으며 기존 사용자 가이드는 해당 버전 기준이다.

전기차의 SOC와 전비로 경로별 예상 소비량·도착 잔량을 비교하고 분기점의 에너지 절약 효과를 안내하는 Pleos용 주행 의사결정 보조 앱입니다. OpenStreetMap 실제 지도와 OSRM 도로 경로를 연결하며, 주행은 도로 좌표 재생입니다. 차량 SOC·전비는 선택적으로 공식 Vehicle SDK에서 읽을 수 있습니다.

**기존 1.1.0 시연용 release:** [VOLTRO_VOLTRO_release.apk](apk/archive/1.1.0/VOLTRO_VOLTRO_release.apk) · [소스 커밋/해시/서명 정보](apk/archive/1.1.0/VOLTRO_VOLTRO_release.json). 이전 파일명은 보관용이며 제출본은 등록 팀명 `김현수`를 사용합니다. 정식 Pleos Market 배포 인증을 받은 APK는 아닙니다.

**기존 1.1.0의 실제 Pleos 화면 10개를 담은 12쪽 사용자 가이드:** [PDF](docs/user-guide/VOLTRO_User_Guide.pdf) · [Word](docs/user-guide/VOLTRO_User_Guide.docx) · [캡처 정보와 문서 재생성](docs/user-guide/README.md).

**로고와 앱 아이콘:** [브랜드 자산 및 SVG·PNG](design/brand/README.md).

`MVP_SPEC.md` 기반의 전기차 에너지 경로 비교 앱. 기존 Android Studio 프로젝트는 `VOLTRO/`, FastAPI 서버는 `backend/`에 있다.

## 개발 환경

- Android Studio의 bundled JDK, 프로젝트에 포함된 Gradle wrapper, Android SDK 37
- Python 3.11 이상

검증 디스플레이: Pleos Connect **2.1.0**, Android **14/API 34**, **2560×1440 px / 160 dpi**, 확장 앱 영역 관찰값 **1682×1210 px**. 일반 Android **API 37**, **1080×2400 px / 420 dpi**에서도 검사한다. 설정·실제 SDK 지원 범위와 평가 항목별 대응은 [공모전 기준](docs/CONTEST_ALIGNMENT.md)에 정리했다.

```sh
python3 -m venv .venv
.venv/bin/pip install -e './backend[test]'
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

API 확인: `http://127.0.0.1:8000/health`, OpenAPI: `http://127.0.0.1:8000/docs`.

Android Studio에서 `VOLTRO/`를 열어 `app` 실행. 터미널 빌드는 macOS 기준:

```sh
(cd VOLTRO && JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew :app:assembleDebug :app:testDebugUnitTest)
```

```sh
.venv/bin/python -m pytest backend/tests -q
```

## 실제 지도와 도로 경로 실행

1. Home의 기본 **실제 도로** 모드에서 목적지를 선택하고 **경로 분석하기**를 누른다. 출발지는 서울 시청이며 목적지는 현재 제공된 세 곳으로 제한된다.
2. OSRM 공개 데모 서버의 실제 경로 1~3개와 OpenStreetMap 지도를 표시한다. 인터넷이 필요하며 별도 API 키·개발 서버는 필요 없다.
3. 지도 드래그·확대/축소·전체 보기로 확인한 뒤 카드를 눌러 경로를 선택한다. 소비량·잔량은 실제 거리와 현재 차량 입력으로 계산한다. 교통·고도는 미반영이다.
4. 기본 SOC 68%는 강릉 실도로에서 최소 도착 잔량에 미달할 수 있다. 충분한 SOC를 입력하거나 Pleos 값을 읽고 재분석한다. 안전 조건을 자동 완화하지 않는다.
5. **선택한 경로로 주행 재생**을 누르면 도로 좌표를 재생하고 완료 리포트·이력을 저장한다. 실제 GPS·차량 내비게이션은 제어하지 않는다.

공급자·캐시·출처·요청 제한·서버 교체 방법은 [실제 지도 연동](docs/REAL_MAPS.md)을 참고한다. 공개 서비스 기반 공모전 시연 모드이며 운영용 공급자 계약·인증·국내 통행 검증은 별도다.

## 오프라인 데모 실행

서버 없이도 전체 흐름을 실행할 수 있다.

1. Android Studio에서 **VOLTRO/**를 열고 `app`을 Pleos Connect 2.1.0 또는 API 28 이상 에뮬레이터에서 실행한다.
2. Home에서 **오프라인 데모**를 선택하고 **강릉역**을 선택한 뒤 **경로 분석하기**를 누른다.
3. 3개 경로의 시간·거리·kWh·도착 SOC를 비교한다. 기본 추천은 절전 경로다.
4. 분기점 시연을 보려면 **빠른 경로**를 선택하고 **Mock 주행**을 시작한다.
5. 기본 4배속에서 약 6초 후 분기점 안내와 함께 데모가 일시정지된다. **절전 경로로 변경** 또는 **기존 경로 유지**를 선택한다.
6. 끝까지 주행하면 리포트를 생성하고 기기에 저장한다. 배속 버튼은 1×/4×/12×를 순환한다.
7. **주행 이력**에서 완료 기록을 확인한다. 설정의 **경로 변경 실패 시나리오**로 실패 시 기존 경로 유지도 시연할 수 있다.

설정에서 최소 도착 SOC·허용 추가 시간·차량 SOC/전비/용량을 변경할 수 있다. 모든 경로의 도착 잔량이 부족하면 시작 버튼이 비활성화된다. 차량값은 실제 측정값이 아닌 시뮬레이터 입력이다.

## 서버 연동 모드

위 명령으로 FastAPI를 실행한 뒤 앱 **설정 → 개발 서버 사용 → 적용**을 선택한다. **서버 연결 확인**으로 `/health` 및 차량 API를 확인할 수 있다. 경로 비교·분기점 분석·완료 저장이 실제 HTTP로 동작한다.

에뮬레이터에서 개발 서버는 `10.0.2.2:8000`으로 접근한다. HTTP는 debug의 로컬 주소에만 허용한다. Android 17(API 37)에서는 서버를 사용하는 시점에 로컬 네트워크 권한을 요청한다. Release는 HTTPS 실제 지도·도로 경로와 오프라인 Mock 데모를 제공하며 로컬 HTTP 개발 서버는 비활성화한다.

서버를 끄고 재분석하면 오류를 표시하고 마지막 검증 경로를 유지한다. 완료 전송 실패 때도 기기 리포트가 남으며 **리포트 다시 저장**으로 재시도할 수 있다. 개발 서버에는 공개 배포용 인증·HTTPS가 아직 없다.

## 검증

```sh
# Python API/계산 테스트
.venv/bin/python -m pytest backend/tests -q

# Android 빌드/계산 테스트/lint
(cd VOLTRO && JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew :app:assembleDebug :app:testDebugUnitTest :app:lintDebug)
```

저장소 루트에서 에뮬레이터를 켠 상태로:

```sh
# 서버 없이 Mock 여정·저장·안전 조건·색상 대비 검사 (8 tests)
python3 scripts/check_android.py --serial emulator-5554

# FastAPI가 실행 중일 때 서버 왕복까지 포함 (9 tests)
python3 scripts/check_android.py --serial emulator-5554 --backend

# Pleos Vehicle Service가 있는 에뮬레이터에서 SDK 읽기만 검사 (1 test)
python3 scripts/check_android.py --serial emulator-5554 --pleos-vehicle

# 인터넷으로 실제 OSM/OSRM 도로 여정 검사 (1 test)
python3 scripts/check_android.py --serial emulator-5554 --roads

# 넓은 Pleos 창의 글자·버튼 검사 (1 test)
python3 scripts/check_android.py --serial emulator-5554 --pleos-layout

# Pleos SDK·실도로 여정을 실행하여 가이드용 native 원본 촬영 (1 test)
python3 scripts/check_android.py --serial emulator-5554 --capture-guide
```

장치 ID는 `adb devices`로 확인한다. 스크립트는 테스트 APK 설치, 선언된 테스트용 runtime 권한 허용, 현재 Android 사용자로 instrumentation 실행, 실제 runner의 테스트 수·성공 여부를 확인한다. 결과는 Git에서 제외한 `artifacts/instrumentation-<serial>.txt`에 저장한다.

Backend 재현용 잠금 파일은 `backend/requirements.lock`이다. 필요하면 `.venv/bin/pip install -r backend/requirements.lock`으로 검증된 버전을 설치한다. 소스 checkout 상태의 개발 실행을 기준으로 한다.

## 구현 범위

Mock 차량 조회, 목적지 선택, 3개 후보 경로 비교, baseline 예측, 안전 추천, 좌표 주행 재생, 분기점 절약 안내/명시적 승인, 리포트와 최근 50개 이력 저장을 구현했다. Pleos 공개 디자인 가이드에 맞춰 Asta Sans, 회색 기반 주야간 테마, 큰 버튼과 vector/adaptive 아이콘을 적용했다.

**Home → Pleos 차량 상태 읽기**는 공식 Vehicle SDK 2.3.2로 SOC와 지원되는 누적 전비를 가져온다. Pleos Connect 2.1.0의 Vehicle Service 2.3.22에서 직접 읽기 통합 테스트를 통과했다. 입력 출처를 구분하며 용량은 설정값으로 유지한다. 에뮬레이터가 아닌 일반 Android에서는 실패를 표시하고 기존 값을 보존한다. 지속적인 telemetry가 아닌 읽기 snapshot이다.

Pleos에서 APK 재설치 직후 SDK capability 응답 timeout도 관찰했다. cold boot 후 읽기는 성공했으며, 연결 안정성과 실차 동작은 추가 검증이 필요하다. timeout을 mock 성공값으로 바꾸지 않는다.

**OSM 지도·OSRM 도로 경로를 연결했으며 Pleos 위치·내비·TTS는 미연동**이다. 도로 경로 모드도 주행 위치와 소비량은 재생·추정값이다. 별도 오프라인 모드에는 합성 경로를 유지한다. 실측 소비량과 예측 정확도는 제공하지 않는다. 프로세스 종료 후 재생은 마지막 체크포인트에서 명시적으로 복구할 수 있다. 실시간 차량 주행 세션 복구가 아닌 시연 재생 복구다.

개발용 APK: `VOLTRO/app/build/outputs/apk/debug/app-debug.apk`.

공모전용 APK는 `apk/김현수_VOLTRO_release.apk`이며 release 빌드·zipalign·v3 서명·non-debuggable 확인 후 패키징한다. 서명키와 암호는 저장소 밖에 보관한다. 소스 커밋이 확정된 상태에서 `python3 scripts/build_submission.py --team 김현수`로 다시 만들 수 있다. [패키징 설명](apk/README.md)을 참고한다.

서명된 release의 실제 UI 시연 검사는 `python3 scripts/smoke_submission.py --serial <장치ID>`로 실행한다. `--roads`를 추가하면 실제 OSM/OSRM 도로 모드를 검사한다. debug 앱과 서명이 다르므로 기존 앱을 삭제하지 말고 별도 에뮬레이터 데이터를 사용한다. 스크립트는 설치 실패 시 데이터 삭제를 시도하지 않는다.

- [API 계약](docs/API_SPEC.md)
- [Pleos 디자인 적용](docs/DESIGN.md)
- [SDK 지원 범위 및 미연동 항목](docs/SDK_INTEGRATION.md)
- [테스트 계획과 결과](docs/TEST_PLAN.md)
- [외부 자료와 라이선스](docs/THIRD_PARTY.md)

진행 내역과 남은 제약은 [구현 기록](docs/IMPLEMENTATION_LOG.md)에 기록한다.

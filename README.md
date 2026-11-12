# VOLTRO

Your Route. Your Energy.

전기차의 SOC와 전비로 경로별 예상 소비량·도착 잔량을 비교하고 분기점의 에너지 절약 효과를 안내하는 Pleos용 주행 의사결정 보조 앱입니다. OpenStreetMap 실제 지도와 OSRM 도로 경로를 연결하며, 주행은 도로 좌표 재생입니다. 차량 SOC·전비는 선택적으로 공식 Vehicle SDK에서 읽을 수 있습니다.

**공모전 시연용 release:** [VOLTRO_VOLTRO_release.apk](apk/VOLTRO_VOLTRO_release.apk) · [소스 커밋/해시/서명 정보](apk/VOLTRO_VOLTRO_release.json). 팀명 파일 라벨 `VOLTRO`는 실제 등록 팀명에 맞춰 바꿀 수 있습니다. 정식 Pleos Market 배포 인증을 받은 APK는 아닙니다.

**실제 실행 화면 사용자 가이드:** [PDF](docs/user-guide/VOLTRO_User_Guide.pdf) · [Word](docs/user-guide/VOLTRO_User_Guide.docx) · [캡처 정보와 문서 재생성](docs/user-guide/README.md).

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
cd VOLTRO
JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew :app:assembleDebug :app:testDebugUnitTest
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
cd VOLTRO
JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

저장소 루트에서 에뮬레이터를 켠 상태로:

```sh
# 서버 없이 Mock 여정·저장·안전 조건·색상 대비 검사 (4 tests)
python3 scripts/check_android.py --serial emulator-5554

# FastAPI가 실행 중일 때 서버 왕복까지 포함 (5 tests)
python3 scripts/check_android.py --serial emulator-5554 --backend

# Pleos Vehicle Service가 있는 에뮬레이터에서 SDK 읽기만 검사 (1 test)
python3 scripts/check_android.py --serial emulator-5554 --pleos-vehicle
```

장치 ID는 `adb devices`로 확인한다. 스크립트는 테스트 APK 설치, 선언된 테스트용 runtime 권한 허용, 현재 Android 사용자로 instrumentation 실행, 실제 runner의 테스트 수·성공 여부를 확인한다. 결과는 Git에서 제외한 `artifacts/instrumentation-<serial>.txt`에 저장한다.

Backend 재현용 잠금 파일은 `backend/requirements.lock`이다. 필요하면 `.venv/bin/pip install -r backend/requirements.lock`으로 검증된 버전을 설치한다. 소스 checkout 상태의 개발 실행을 기준으로 한다.

## 구현 범위

Mock 차량 조회, 목적지 선택, 3개 후보 경로 비교, baseline 예측, 안전 추천, 좌표 주행 재생, 분기점 절약 안내/명시적 승인, 리포트와 최근 50개 이력 저장을 구현했다. Pleos 공개 디자인 가이드에 맞춰 Asta Sans, 회색 기반 주야간 테마, 큰 버튼과 vector/adaptive 아이콘을 적용했다.

**Home → Pleos 차량 상태 읽기**는 공식 Vehicle SDK 2.3.2로 SOC와 지원되는 누적 전비를 가져온다. Pleos Connect 2.1.0의 Vehicle Service 2.3.22에서 직접 읽기 통합 테스트를 통과했다. 입력 출처를 구분하며 용량은 설정값으로 유지한다. 에뮬레이터가 아닌 일반 Android에서는 실패를 표시하고 기존 값을 보존한다. 지속적인 telemetry가 아닌 읽기 snapshot이다.

Pleos에서 APK 재설치 직후 SDK capability 응답 timeout도 관찰했다. cold boot 후 읽기는 성공했으며, 연결 안정성과 실차 동작은 추가 검증이 필요하다. timeout을 mock 성공값으로 바꾸지 않는다.

**OSM 지도·OSRM 도로 경로를 연결했으며 Pleos 위치·내비·TTS는 미연동**이다. 도로 경로 모드도 주행 위치와 소비량은 재생·추정값이다. 별도 오프라인 모드에는 합성 경로를 유지한다. 실측 소비량과 예측 정확도는 제공하지 않는다. 프로세스가 종료되면 진행 중인 주행을 복원하지 않으며 완료된 이력만 유지한다.

개발용 APK: `VOLTRO/app/build/outputs/apk/debug/app-debug.apk`.

공모전용 APK는 `apk/VOLTRO_VOLTRO_release.apk`이며 release 빌드·zipalign·v3 서명·non-debuggable 확인 후 패키징한다. 서명키와 암호는 저장소 밖에 보관한다. 소스 커밋이 확정된 상태에서 `python3 scripts/build_submission.py --team VOLTRO`로 다시 만들 수 있다. [패키징 설명](apk/README.md)을 참고한다.

서명된 release의 실제 UI 시연 검사는 `python3 scripts/smoke_submission.py --serial <장치ID>`로 실행한다. debug 앱과 서명이 다르므로 기존 앱을 삭제하지 말고 별도 에뮬레이터 데이터를 사용한다. 스크립트는 설치 실패 시 데이터 삭제를 시도하지 않는다.

- [API 계약](docs/API_SPEC.md)
- [Pleos 디자인 적용](docs/DESIGN.md)
- [SDK 지원 범위 및 미연동 항목](docs/SDK_INTEGRATION.md)
- [테스트 계획과 결과](docs/TEST_PLAN.md)
- [외부 자료와 라이선스](docs/THIRD_PARTY.md)

진행 내역과 남은 제약은 [구현 기록](docs/IMPLEMENTATION_LOG.md)에 기록한다.

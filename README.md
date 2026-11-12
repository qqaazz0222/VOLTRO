# VOLTRO

Your Route. Your Energy.

`MVP_SPEC.md` 기반의 전기차 에너지 경로 비교 앱. 기존 Android Studio 프로젝트는 `VOLTRO/`, FastAPI 서버는 `backend/`에 있다.

## 개발 환경

- Android Studio의 bundled JDK, 프로젝트에 포함된 Gradle wrapper, Android SDK 37
- Python 3.11 이상

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

## 데모 실행

서버 없이도 전체 흐름을 실행할 수 있다.

1. Android Studio에서 **VOLTRO/**를 열고 `app`을 Pleos Connect 2.1.0 또는 API 28 이상 에뮬레이터에서 실행한다.
2. Home에서 **강릉역**을 선택한 뒤 **경로 분석하기**를 누른다.
3. 3개 경로의 시간·거리·kWh·도착 SOC를 비교한다. 기본 추천은 절전 경로다.
4. 분기점 시연을 보려면 **빠른 경로**를 선택하고 **Mock 주행**을 시작한다.
5. 기본 4배속에서 약 6초 후 분기점 안내와 함께 데모가 일시정지된다. **절전 경로로 변경** 또는 **기존 경로 유지**를 선택한다.
6. 끝까지 주행하면 리포트를 생성하고 기기에 저장한다. 배속 버튼은 1×/4×/12×를 순환한다.
7. **주행 이력**에서 완료 기록을 확인한다. 설정의 **경로 변경 실패 시나리오**로 실패 시 기존 경로 유지도 시연할 수 있다.

설정에서 최소 도착 SOC·허용 추가 시간·차량 SOC/전비/용량을 변경할 수 있다. 모든 경로의 도착 잔량이 부족하면 시작 버튼이 비활성화된다. 차량값은 실제 측정값이 아닌 시뮬레이터 입력이다.

## 서버 연동 모드

위 명령으로 FastAPI를 실행한 뒤 앱 **설정 → 개발 서버 사용 → 적용**을 선택한다. **서버 연결 확인**으로 `/health` 및 차량 API를 확인할 수 있다. 경로 비교·분기점 분석·완료 저장이 실제 HTTP로 동작한다.

에뮬레이터에서 개발 서버는 `10.0.2.2:8000`으로 접근한다. HTTP는 debug의 로컬 주소에만 허용한다. Android 17(API 37)에서는 서버를 사용하는 시점에 로컬 네트워크 권한을 요청한다. 기본 오프라인 데모는 권한이 필요 없다. Release는 로컬 HTTP 서버 연동을 제공하지 않는 Mock 데모다.

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
```

장치 ID는 `adb devices`로 확인한다. 스크립트는 테스트 APK 설치, 선언된 테스트용 runtime 권한 허용, 현재 Android 사용자로 instrumentation 실행, 실제 runner의 테스트 수·성공 여부를 확인한다. 결과는 Git에서 제외한 `artifacts/instrumentation-<serial>.txt`에 저장한다.

Backend 재현용 잠금 파일은 `backend/requirements.lock`이다. 필요하면 `.venv/bin/pip install -r backend/requirements.lock`으로 검증된 버전을 설치한다. 소스 checkout 상태의 개발 실행을 기준으로 한다.

## 구현 범위

Mock 차량 조회, 목적지 선택, 3개 후보 경로 비교, baseline 예측, 안전 추천, 좌표 주행 재생, 분기점 절약 안내/명시적 승인, 리포트와 최근 50개 이력 저장을 구현했다. Pleos 공개 디자인 가이드에 맞춰 Asta Sans, 회색 기반 주야간 테마, 큰 버튼과 vector/adaptive 아이콘을 적용했다.

**Home → Pleos 차량 상태 읽기**는 공식 Vehicle SDK 2.3.2로 SOC와 지원되는 누적 전비를 가져온다. Pleos Connect 2.1.0의 Vehicle Service 2.3.22에서 직접 읽기 통합 테스트를 통과했다. 입력 출처를 구분하며 용량은 설정값으로 유지한다. 에뮬레이터가 아닌 일반 Android에서는 실패를 표시하고 기존 값을 보존한다. 지속적인 telemetry가 아닌 읽기 snapshot이다.

**실제 도로 공급자와 Pleos 위치·내비·TTS는 미연동**이다. SDK 차량값을 불러와도 경로와 주행은 synthetic 시뮬레이션이다. 실측 소비량과 예측 정확도는 제공하지 않는다. 프로세스가 종료되면 진행 중인 주행을 복원하지 않으며 완료된 이력만 유지한다.

APK: `VOLTRO/app/build/outputs/apk/debug/app-debug.apk`.

- [API 계약](docs/API_SPEC.md)
- [Pleos 디자인 적용](docs/DESIGN.md)
- [SDK 지원 범위 및 미연동 항목](docs/SDK_INTEGRATION.md)
- [테스트 계획과 결과](docs/TEST_PLAN.md)
- [외부 자료와 라이선스](docs/THIRD_PARTY.md)

진행 내역과 남은 제약은 [구현 기록](docs/IMPLEMENTATION_LOG.md)에 기록한다.

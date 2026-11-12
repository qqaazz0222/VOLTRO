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

실차 SDK 연동은 아직 없으며 기본 차량은 MOCK(68%, 5.2 km/kWh, 70 kWh)이다. 에뮬레이터에서 개발 서버는 `10.0.2.2:8000`으로 접근한다. HTTP는 debug의 로컬 주소에만 허용한다.

진행 내역과 남은 제약은 [구현 기록](docs/IMPLEMENTATION_LOG.md)에 기록한다.

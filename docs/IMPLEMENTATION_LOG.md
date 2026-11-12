# 구현 기록

## Phase 1 — 기반 구축

- 기존 `VOLTRO/` Android Studio 프로젝트, 패키지명, Gradle 구성을 유지했다.
- 차량 모델·Repository·Mock 구현, Home 진입점, 비동기 HTTP 클라이언트, FastAPI `/health`, `/api/v1/vehicle`을 추가했다.
- Android `assembleDebug`, `testDebugUnitTest` 성공. Backend 기초 테스트 1개 통과.
- 실제 차량 SDK 의존성은 없으며 모든 차량 데이터는 MOCK이다. Android UI는 기존 View 기반 프로젝트에 맞춰 구현한다.

후속 Phase의 검증 결과와 제약은 아래에 추가한다.

## Phase 2 — 에너지 예측

- UI와 독립된 Kotlin/Python baseline 엔진과 입력 검증, `/api/v1/energy/predict`를 추가했다.
- 거리/전비, 도착 SOC 공식을 공통 적용한다. 도달 불가능한 음수 도착 SOC는 그대로 유지해 추천에서 제외한다.
- Backend 12개 테스트 통과. Kotlin의 정상·0거리·음수·0전비·0용량·비유한 값 검증 테스트 통과.
- 속도·고도 보정은 적용하지 않는다. 실측 예측 정확도는 검증하지 않았다.

## Phase 3 — 공통 시나리오와 경로 비교

- `mock-data/scenario.json`을 Android assets와 Backend가 공통으로 사용한다.
- 서울 출발 데모 목적지 3곳, 빠른/균형/절전 3개 경로, 거리 기반 에너지 및 SOC 계산, 안전 추천, 서버 경로 비교 API를 구현했다.
- Backend 경로 비교·선호 조건·미지원 목적지·데이터 일관성 테스트 통과.

## Phase 4 — 실제 도로 경로: 미연동

- 실제 도로 공급자 계약·키·통행 검증 자료가 없어 MockRouteProvider를 유지한다. 임의의 실도로/고도 데이터는 생성하지 않는다.
- 국내 경로 공급자·라이선스 확보 후 교체할 Repository 경계를 구성했다. 현재 경로는 synthetic graph이며 통행 가능성을 보증하지 않는다.

## Phase 5 — Mock 분기점 분석 엔진

- 공통 prefix 이후 분기점 탐지, 경로 매칭, 분기점 이후 동일 출발점 에너지/시간 비교, 위치 정확도·SOC·capability·중복 안내 제한을 구현했다.
- 모든 경로가 공통 35 km 구간에 25분을 사용하여 경로 전환 때 위치·소비량·가상 시간이 연속적이다.
- Backend 전체 26개 테스트 통과. Android 계산·추천·분기점 단위 테스트 통과. 화면 및 실제 에뮬레이터 주행 검증은 후속 커밋에 기록한다.

## Phase 6 — Pleos SDK: capability gate만 구현

- `PleosNavigationRepository`는 미지원 결과만 반환한다. 실제 차량 SDK API를 추측하지 않았다.
- 설치된 Pleos Connect 2.1.0 에뮬레이터에서 기본 앱 실행과 개발 서버 연결을 확인했다. SDK 차량 데이터·내비 변경·TTS 기능 검증과 차량 배포 인증은 미완료다.

## Phase 7 — 저장 기반

- Android 기기 전용 SQLite 이력 저장소와 Backend 완료 API·멱등 SQLite 저장을 추가했다.
- Mock 소비량과 실측값을 구분하며 실측값이 없으면 오차는 null이다. 정확한 좌표 이력은 저장하지 않는다.

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

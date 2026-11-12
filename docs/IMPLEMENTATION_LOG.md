# 구현 기록

## Phase 1 — 기반 구축

- 기존 `VOLTRO/` Android Studio 프로젝트, 패키지명, Gradle 구성을 유지했다.
- 차량 모델·Repository·Mock 구현, Home 진입점, 비동기 HTTP 클라이언트, FastAPI `/health`, `/api/v1/vehicle`을 추가했다.
- Android `assembleDebug`, `testDebugUnitTest` 성공. Backend 기초 테스트 1개 통과.
- 실제 차량 SDK 의존성은 없으며 모든 차량 데이터는 MOCK이다. Android UI는 기존 View 기반 프로젝트에 맞춰 구현한다.

후속 Phase의 검증 결과와 제약은 아래에 추가한다.

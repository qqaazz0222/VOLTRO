# 공모전 기준과 개발 방향

확인일: 2026-11-12 (KST). 공모전 안내가 바뀌면 공식 페이지를 재확인한다.

## 공식 근거

- [개발 환경](https://appdevchallenge.auto-hmg.io/guide/development): API 28 이상, Gradle 8 이상, Kotlin/Java 및 Pleos SDK 활용.
- [제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission): `apk/`의 실행 가능한 release APK, 정해진 파일명, README의 실행·환경·에뮬레이터 버전·화면 규격·APK 경로.
- [평가 항목](https://appdevchallenge.auto-hmg.io/guide/judging-awards): 차량 특화성, 창의성, 기술 활용성, 사업성. 시연 영상과 저장소/APK는 선택 개발 산출물이다.
- [SDK 신청/제공 상태](https://document.pleos.ai/docs/pleos-only/create-my-project): 공개 문서상 Vehicle State·NaviHelper 사용 가능, FusedLocation·TTS 등 준비 중. 개별 프로젝트/차량의 실제 지원 범위는 별도 확인한다.

## VOLTRO에 적용

| 기준 | 구현/방향 | 구분 |
|---|---|---|
| 차량 특화성 | SOC·전비로 시간과 kWh·도착 잔량 비교 | SDK snapshot 및 OSRM 도로/Mock 경로 |
| 주요 선택 순간 | 같은 분기점 이후 두 경로의 소비량·추가 시간 비교 | 실제 도로 prefix와 별도 Mock 그래프 |
| Pleos 기술 활용 | 공식 Vehicle 2.3.2 capability/get 기반 배터리 snapshot | Pleos 에뮬레이터 직접 읽기 테스트 |
| 안전한 UI | 정차 전 검색, 단순한 주행 표시, 명시적 전환 승인 | 데모 구현, 실차 주행 정책 미검증 |
| 개발 산출물 | Kotlin 앱/FastAPI/테스트/README/release 패키징 | 제출용 검토 가능 자료 |

## 확인한 디스플레이

Pleos Connect 2.1.0, Android 14(API 34), arm64. 전체 디스플레이 **2560×1440 px / 160 dpi**, Driving view와 시스템 영역을 제외한 확장 앱 영역 **1682×1210 px** (테스트 시 관찰한 bounds). 다른 차량/window 배치에서는 바뀔 수 있다. 앱은 800dp 미만에서 1열, 이상에서 2열로 구성한다. 일반 Android API 37의 1080×2400 px / 420dpi에서도 검증한다.

## 다음 개발 우선순위

1. 현재 OSM·OSRM 공개 데모 연결을 운영 규모에 맞는 공급자로 전환하고 국내 통행·교통·고도 및 정확도를 검증한다.
2. 확인된 NaviHelper SDK로 목적지·옵션 요청과 결과 이벤트를 검증한다. 임의 좌표 경로가 실제 내비에서 선택 가능하다고 가정하지 않는다.
3. 위치/TTS SDK 제공 상태를 확인한 후 권한·오디오 포커스·차량 주행 제약을 적용한다.
4. 실차 에너지 누적 측정값을 확보한 후 예측 오차와 순위를 평가한다.

팀명·참가자 개인정보·동의서·사업 지표는 임의로 작성하지 않는다. 공모전 접수 메일 발송, 저장소 공개 범위 변경, 계정 초대는 수행하지 않는다. 제출 시 개발한 범위와 미검증 범위를 구분한다.

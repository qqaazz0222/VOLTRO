# 플랫폼 연동 상태

## 개발 환경

[공모전 개발 환경](https://appdevchallenge.auto-hmg.io/guide/development)과 [Pleos 공식 설치 문서](https://document.pleos.ai/docs/connect/guide/getting-started/application-development/setup-connect-sdk-emulator)를 참고했다. 최소 API 28, Gradle 8 이상 요구에 맞춰 기존 프로젝트의 minSdk를 28로 올렸다. 기존 compile/target SDK 37, AGP 9.5.1, Gradle 9.6을 유지한다.

확인 환경: macOS arm64, Android Studio bundled JDK, Pleos Connect 2.1.0 / Android 14(API 34) 에뮬레이터, 일반 Android API 37 에뮬레이터.

## 구현과 미지원의 구분

| 기능 | 상태 |
|---|---|
| Mock 차량 SOC·전비·용량 | 구현 |
| 사용자 입력 차량 프로필 | 구현, 소비량 예측·주행 재생 입력에 적용 |
| Mock 경로·위치 재생 | 구현 |
| Mock 목적지·경로 전환 | 운전자 명시적 승인 후 시뮬레이션에 적용 |
| Pleos 차량 데이터 읽기 | Vehicle 2.3.2 SOC 및 누적 전비 snapshot 구현, Pleos 에뮬레이터 직접 읽기 통합 테스트 통과 |
| Pleos 위치 읽기 | 미연동, 기기 위치 권한 요청 안 함 |
| NaviHelper 목적지/경로 전환 | 미연동, capability=false |
| TTS | 음성 권한·오디오 포커스·차량 정책 검증 전 비활성 |
| 실제 지도·도로 경로 | OSM raster 지도와 OSRM 자동차 경로 연결, 공개 데모 서비스 기반 |
| 도로 고도·실시간 교통 | 미연동, 거리÷전비 baseline 유지 |
| 차량 주행 UX 제한 | 실차 상태 수신 미연동, 도로 좌표 재생·Mock 화면 제공 |

`PleosNavigationRepository`는 명시적인 Unsupported 결과를 반환하며 내비게이션 API를 호출하지 않는다. `PleosVehicleRepository`는 공식 SDK로 읽기만 수행한다. Location adapter는 아직 없으며 Mock 위치는 노드 사이를 보간한 값이다.

## 확인한 Vehicle SDK 연동

2026-11-12 공개 [Vehicle SDK 설정](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/Vehicle/project-setup), [capability](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/Vehicle/check-capability), [권한](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/Vehicle/vehicle-permission) 문서 및 Maven 배포본의 소스를 확인했다.

- Maven: `ai.pleos.playground:Vehicle:2.3.2`, 공식 `nexus-playground.pleos.ai` 저장소만 사용.
- `pleos.car.permission.CAR_ENERGY`: normal 읽기 권한. 차량 제어 권한은 선언하지 않는다. SDK 자체 manifest의 service binding 권한과 query도 병합된다.
- `Vehicle.initialize()` → `getEvBattery()` → SOC capability 확인 → SOC 읽기. 누적 전비는 별도 capability와 get으로 읽는다. 완료·실패·timeout에서 `release()`한다.
- 공식 소스에 명시된 단위: SOC %, 누적 전비 km/kWh. null/범위 밖 값은 사용하지 않는다.
- 누적 전비가 없으면 기존 설정값을 사용하고 출처를 구분한다. 사용 가능 용량은 설정값이다. deprecated capacity/level API는 호출하지 않는다.
- Home의 ‘Pleos 차량 상태 읽기’로만 호출한다. snapshot이며 주행 중 실시간 telemetry를 구독하지 않는다. 다른 기기나 미지원 capability에서는 입력값을 유지한다.
- Pleos Connect 2.1.0, Vehicle Service **2.3.22 / code 74**에서 공식 SDK 직접 읽기 테스트 1개 통과. 이는 에뮬레이터 검증이며 실차 검증이 아니다.
- cold boot 환경에서는 동일 프로세스 내 두 번의 initialize/read/release를 확인했다. SDK만 검사할 때 `scripts/check_android.py --serial <ID> --pleos-vehicle`을 사용한다.
- APK를 재설치한 직후 capability 콜백이 6초 내에 오지 않는 경우를 재현했다. 같은 에뮬레이터를 cold boot한 후에는 읽기에 성공했다. 기존 값 유지와 명시적 timeout 처리를 적용했으며, 이를 SDK/서비스 연결의 안정성 검증 완료로 표시하지 않는다. 설치 후 SDK 테스트가 timeout이면 공식 권장 cold boot 환경에서 다시 확인한다. 앱에서 시스템 서비스를 강제 종료하지 않는다.
- NaviHelper는 공개 SDK 정보를 확인했지만 합성 데모 경로를 실제 내비게이션 경로로 보내지 않는다. FusedLocation/TTS는 공식 프로젝트 신청 문서상 준비 중으로 안내되어 있어 임의 API를 구현하지 않는다.

실차 연동 전 SDK 계약, 권한, 데이터 최신성, 정확도, `navigationSelectable`와 변경 결과 확인을 검증해야 한다. 분석 성공이 실제 내비게이션 경로 변경 성공을 의미하지 않는다.

## 기술 선택

기존 프로젝트의 Android Views를 유지했다. StateFlow/ViewModel/Coroutines를 사용하며 Repository를 생성자에서 연결한다. 외부 SDK 검증 전 DI 프레임워크와 코드 생성 도구는 추가하지 않았다. HTTP는 비동기 HttpURLConnection, 이력은 SQLiteOpenHelper로 구현했다. Retrofit/Hilt/Room/Compose는 이번 Mock 버전의 필수 의존성이 아니며 명세 권장 스택에서의 차이로 기록한다.

## 안전한 실패

- 유효한 경로 분석 결과는 서버 요청 실패 때 보존한다. Home의 ‘마지막 경로 분석 보기’에서 확인 가능하다.
- 분기점 분석 실패나 Mock 경로 변경 실패는 활성 경로를 바꾸지 않는다.
- 분기점 접근 1.5km 이내·정확도 50m 이내·경로 offset 75m 이내·정책 조건을 모두 검사한다.
- 위치를 통과하거나 경로가 바뀌면 기존 알림을 제거한다. 중복 알림은 앱과 서버 모두 제한한다.
- 백그라운드 진입 때 Mock 주행을 정지한다. Activity 재생성은 ViewModel이 유지한다. 프로세스 종료 후 진행 중 주행의 복원은 아직 지원하지 않으며 완료 이력만 복원한다.
- 완료 리포트는 서버 전송 전에 기기에 저장한다. 서버 전송 실패는 다시 저장으로 재시도한다.

Android 17/API 37에서는 로컬 개발 서버 TCP 접속에도 [로컬 네트워크 runtime 권한](https://developer.android.com/privacy-and-security/local-network-permission)이 필요하다. 이 권한은 debug manifest에만 선언하고 서버 기능 사용 때 요청한다. Release는 공개 HTTPS 실제 지도·도로 경로와 별도 오프라인 Mock 모드를 제공한다. 지도·요청 제한·외부 전송 범위는 [실제 지도 연동](REAL_MAPS.md)에 정리했다.

# 플랫폼 연동 상태

## 개발 환경

[공모전 개발 환경](https://appdevchallenge.auto-hmg.io/guide/development)과 [Pleos 공식 설치 문서](https://document.pleos.ai/docs/connect/guide/getting-started/application-development/setup-connect-sdk-emulator)를 참고했다. 최소 API 28, Gradle 8 이상 요구에 맞춰 기존 프로젝트의 minSdk를 28로 올렸다. 기존 compile/target SDK 37, AGP 9.5.1, Gradle 9.6을 유지한다.

확인 환경: macOS arm64, Android Studio bundled JDK, Pleos Connect 2.1.0 / Android 14(API 34) 에뮬레이터, 일반 Android API 37 에뮬레이터.

## 구현과 미지원의 구분

| 기능 | 상태 |
|---|---|
| Mock 차량 SOC·전비·용량 | 구현 |
| 사용자 입력 차량 프로필 | 구현, 시뮬레이션에만 적용 |
| Mock 경로·위치 재생 | 구현 |
| Mock 목적지·경로 전환 | 운전자 명시적 승인 후 시뮬레이션에 적용 |
| Pleos 차량 데이터 읽기 | SDK 권한·artifact·시그니처 미검증 |
| Pleos 위치 읽기 | 미연동, 기기 위치 권한 요청 안 함 |
| NaviHelper 목적지/경로 전환 | 미연동, capability=false |
| TTS | 음성 권한·오디오 포커스·차량 정책 검증 전 비활성 |
| 실제 도로 경로/고도 | 공급자 키·라이선스·국내 통행 검증 필요 |
| 차량 주행 UX 제한 | 실차 상태 수신 미연동, 현재 Mock 화면만 제공 |

`PleosNavigationRepository`는 명시적인 Unsupported 결과를 반환하며 실차 API를 호출하지 않는다. 실제 Vehicle/Location adapter는 SDK 확보 후 `domain/repository` 경계에 추가한다. 현재 Mock 위치는 경로 노드 사이를 보간한 값이며 실제 GPS가 아니다.

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

# 검증 계획과 결과

## 자동 검사

| 영역 | 검사 |
|---|---|
| Python 에너지 | 정상/0거리/음수/0전비/0용량/범위 밖 SOC/NaN·무한대 |
| Python 경로 | 목적지 3곳/3개 후보/동일 전비 공식/추가 시간/최소 SOC/동일 소비량 |
| Python 분기점 | 공통 prefix/합류 제외/접근 거리/통과/낮은 정확도/이탈/미지원 내비/중복 알림/경로 변경 |
| Python 완료 | 실측과 Mock 구분/오차 null/멱등성/내용 충돌/완료 후 안내 방지 |
| Kotlin domain | 차량 모델/에너지 경계값/추천 제약/분기점 위치·에너지/전환 시 위치와 시간 연속성 |
| Instrumentation Mock | Home→비교→빠른 경로→분기점→승인→완료→DB 기록, Activity 재생성 |
| Instrumentation 실패 | Mock 변경 실패 시 기존 경로 유지, 취소 주행 미저장, SOC 부족 주행 차단 |
| Instrumentation 디자인 | Light/Dark 본문·보조 글자·선택 표시·CTA·배터리·오류 대비 4.5:1 이상 |
| Instrumentation Backend | 실제 HTTP 경로 비교·분기점·승인 전환·완료 SQLite 저장 왕복 |

실행 명령은 README를 참조한다. 로컬 서버 검사는 `--backend`, 공개 도로 서비스 검사는 `--roads`, Pleos 가이드 촬영은 `--capture-guide`를 명시한다. 기본 모음은 네트워크 없이 실행한다.

## 1.2.0 검증 (2026-11-13)

- Python **26개 통과**, Kotlin JVM **18개 통과**(출발 SOC·부족 에너지·완충 도달 여부·전비 저하 민감도 4개 추가).
- 일반 Android API 37에서 오프라인 **8개 통과** 및 공개 도로 통합 **1개 통과**. Pleos Connect 2.1.0에서도 오프라인 **8개 통과**, 큰 글자·버튼 **1개 통과**, Vehicle SDK 직접 읽기 **1개 통과**.
- 신규 자동 검사는 세 시나리오 준비 시 저장 프로필 보존, 중단 체크포인트의 미결 승인·중복 안내 상태 보존, 항상 일시정지 복구, 손상 파일의 안전한 제거, 완료 이력 우선 처리와 멱등 저장을 검사한다. 경로 변경 실패 후 정지와 기존 경로 유지, 완료·취소 후 다음 여정 활성화 전에 체크포인트가 제거되는지도 확인한다.
- `assembleRelease`, `testDebugUnitTest`, `lintDebug` 성공. lint error **0**, warning **32**(기존 SDK 권장·View 할당·리소스 등 권장 사항 포함). warning을 해소 완료로 집계하지 않는다.
- Pleos native 화면 4개를 직접 확인해 리포트 구분선 높이와 잔량 부족 안내 대비를 보완했다. [촬영 출처](submission/screenshots/CAPTURE_INFO.json)는 test fixture와 실제 SDK·실차 측정을 구분한다.
- signed release의 실제 강제 종료·재실행·명시적 복구·승인·완료와 잔량 부족·전환 실패는 `scripts/check_contest_release.py`로 별도 검증한다. 최종 APK와 검사 결과의 해시는 [출품 검토 자료](submission/README.md)에 기록한다.

## 기존 1.0/1.1 확인된 결과

- Python: **26 tests passed**.
- Android JVM: **14 tests passed** (기존 8개와 실도로 geometry·거리·시간·좌표 검증 6개).
- Android API 37: **5 instrumented tests passed** (Mock 3, 디자인 1, Backend 1).
- Pleos Connect 2.1.0: **Vehicle SDK 직접 읽기 통합 테스트 1개 통과**, Vehicle Service 2.3.22. `PleosVehicleIntegrationTest`는 일반 Android의 기본 테스트 모음과 분리한다.
- `assembleDebug`, `testDebugUnitTest`, `lintDebug` 성공. lint error 0. SDK 업데이트 권장·View draw 할당·다국어 리소스 등 warning은 남아 있다.
- 1.1.0 실도로: Android API 37의 명시적 `RoadJourneyTest` 1개 통과. 실제 OSRM geometry·거리·에너지와 재생 진입을 확인했다. 공개 서비스 호출은 기본 오프라인 모음에 포함하지 않는다.
- Pleos 2.1.0: `WideLayoutTest` 1개 통과. Home 글자 최소 22sp, 이력 버튼 한 줄 표시와 터치 높이를 검사했다. 지도 출처 18sp, 경로 카드 핵심 수치 32sp, 버튼 24sp, 설정·확인창 확대를 적용했다.
- Pleos 가이드 캡처 테스트 1개 통과: 실제 Vehicle SDK SOC 100% → OSRM 도로 2개 → OSM viewport 로딩 → 주행 재생 → 완료·이력 → SOC 부족 차단 → 실제 설정창 → 오프라인 분기점 안내. 10개 native 창/전체 화면을 보존한다.
- 서명된 1.1.0 release에서 `smoke_submission.py --roads`와 오프라인 smoke 모두 통과. 실제 지도 타일·도로 geometry·완료 리포트·이력 출처 및 기본 프로필 복원, 기존 분기점 승인 흐름을 확인했다. 두 결과의 APK 해시가 최종 배포본과 일치한다.
- 공모전용 release: `assembleRelease`·zipalign·v3 서명·non-debuggable 확인. 별도의 일반 Android API 37 에뮬레이터 데이터에서 서명된 APK를 직접 설치해 Home → SDK 미지원 fallback → 비교 → 분기점 승인 → 리포트 → 기기 이력 저장까지 UI smoke 테스트 통과.
- 초기 1.0 검증 당시 Pleos Connect 2.1.0에서 기본 앱 실행, 차량 Mock/API 상태 표시, Home/경로 비교/분기점 화면을 직접 확인했다. 5개 연속 테스트 중 4개(미지원 전환, SOC, 대비, Backend 왕복)는 통과했으며 UI 전체 여정 테스트는 시스템 focus/lifecycle 문제로 실패했다. 당시 결과를 전체 5개 통과로 집계하지 않는다. 위 1.1.0 가이드 캡처 검사는 host GPU cold boot 환경에서 별도로 통과한 결과다.

## 수동 시연

아래 고정 수치 시나리오는 Home에서 **오프라인 데모**를 선택한 경우다. 실제 도로 모드의 거리·시간·경로 개수는 공급자 응답에 따라 달라진다.

1. 기본 강릉 예측: 180/174/165 km, 130/137/145분, 약 34.6/33.5/31.7 kWh.
2. 빠른 경로로 시작: 33.8 km 위치(분기점 1.2 km 전)에서 약 2.9 kWh / 15분 안내. 같은 출발점 이후의 소비량을 비교한다.
3. 승인: 공통 구간에서 ECO로 변경, 최종 165 km, 가상 145분, 약 31.7 kWh.
4. 유지 또는 변경 실패: FASTEST 유지, 180 km, 가상 130분, 약 34.6 kWh.
5. 기본 ECO 출발: 이미 효율적인 경로이므로 불필요한 전환 알림이 없다.
6. SOC 20% 설정: 모든 후보가 최소 15% 도착 잔량 미달이므로 선택/시작 불가.
7. 서버 중지: 분석 오류 표시, 마지막 검증 경로 유지. 서버 재시작 후 재시도.
8. Dark mode, 좁은 창, 큰 글꼴에서 겹침·클리핑·터치 영역 확인.

## 남은 검증

OSM·OSRM의 국내 도로 데이터·통행 제한·교통 정확도, 실차 SDK 필드·위치 정확도·내비 capability, 실차 계측 에너지, TTS 정책, 제조사별 UI·런처 마스킹·주행 안전 심사, 운영 API 인증·부하·개인정보 정책은 미검증이다. 지도·geometry를 정상 표시한 결과를 실차 정확도 검증으로 확대하지 않는다.

Pleos emulator의 system DrivingView/CarSystemUI가 headless 환경에서 crash하거나 instrumentation Activity의 lifecycle에 영향을 줄 수 있다. Gradle의 `BUILD SUCCESSFUL`만으로 테스트를 통과 처리하지 않고 `check_android.py`가 실제 runner 결과를 검사한다.

software GPU의 DrivingView가 화면 전체를 덮는 InputSink를 남겨 터치를 가로채는 현상도 관찰했다. 이 Mac에서는 `-gpu host`로 cold boot하고 Pleos 런처에서 앱을 열어 정상 입력과 가이드 촬영을 확인했다. 이 실행 옵션은 로컬 에뮬레이터 검증 조건이며 앱이 시스템 서비스를 종료하거나 입력 보호를 해제하지 않는다.

SDK 검사만 실행하려면 `check_android.py --serial <Pleos ID> --pleos-vehicle`을 사용한다. APK 재설치 직후 capability callback timeout도 관찰되었으며 cold boot 후 재확인한다. 실패를 숨기거나 mock 응답을 SDK 성공으로 반환하지 않는다.

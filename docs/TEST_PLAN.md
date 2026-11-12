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

실행 명령은 README를 참조한다. 네트워크가 필요한 테스트는 `--backend`를 명시하고 로컬 서버를 먼저 실행한다.

## 확인된 결과

- Python: **26 tests passed**.
- Android JVM: **8 tests passed**.
- Android API 37: **5 instrumented tests passed** (Mock 3, 디자인 1, Backend 1).
- Pleos Connect 2.1.0: **Vehicle SDK 직접 읽기 통합 테스트 1개 통과**, Vehicle Service 2.3.22. `PleosVehicleIntegrationTest`는 일반 Android의 기본 테스트 모음과 분리한다.
- `assembleDebug`, `testDebugUnitTest`, `lintDebug` 성공. lint error 0. SDK 업데이트 권장·View draw 할당·다국어 리소스 등 warning은 남아 있다.
- Pleos Connect 2.1.0: 기본 앱 실행, 차량 Mock/API 상태 표시, Home/경로 비교/분기점 화면을 직접 확인했다. 5개 연속 테스트 중 4개(미지원 전환, SOC, 대비, Backend 왕복)는 통과했으며 UI 전체 여정 테스트는 시스템 focus/lifecycle 문제로 실패했다. 전체 5개 통과로 집계하지 않는다.

## 수동 시연

1. 기본 강릉 예측: 180/174/165 km, 130/137/145분, 약 34.6/33.5/31.7 kWh.
2. 빠른 경로로 시작: 33.8 km 위치(분기점 1.2 km 전)에서 약 2.9 kWh / 15분 안내. 같은 출발점 이후의 소비량을 비교한다.
3. 승인: 공통 구간에서 ECO로 변경, 최종 165 km, 가상 145분, 약 31.7 kWh.
4. 유지 또는 변경 실패: FASTEST 유지, 180 km, 가상 130분, 약 34.6 kWh.
5. 기본 ECO 출발: 이미 효율적인 경로이므로 불필요한 전환 알림이 없다.
6. SOC 20% 설정: 모든 후보가 최소 15% 도착 잔량 미달이므로 선택/시작 불가.
7. 서버 중지: 분석 오류 표시, 마지막 검증 경로 유지. 서버 재시작 후 재시도.
8. Dark mode, 좁은 창, 큰 글꼴에서 겹침·클리핑·터치 영역 확인.

## 남은 검증

실제 국내 도로 및 경로 공급자, SDK 차량 필드·위치 정확도·내비 capability, 실차 계측 에너지, TTS 정책, 제조사별 UI·런처 마스킹·주행 안전 심사, production API 인증·부하·개인정보 정책은 미검증이다. 실차 정확도 목표를 달성했다고 주장하지 않는다.

Pleos emulator의 system DrivingView/CarSystemUI가 headless 환경에서 crash하거나 instrumentation Activity의 lifecycle에 영향을 줄 수 있다. Gradle의 `BUILD SUCCESSFUL`만으로 테스트를 통과 처리하지 않고 `check_android.py`가 실제 runner 결과를 검사한다.

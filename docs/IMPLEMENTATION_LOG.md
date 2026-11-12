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

## 화면 통합 및 Pleos 디자인 적용

- Home → 경로 비교 → Mock 주행 → 분기점 승인/유지 → 완료 리포트 → 이력을 ViewModel/StateFlow로 연결했다.
- Pleos 공개 grayscale, Asta Sans, 48dp 기반 vector 아이콘, adaptive launcher, 주야간 테마, 큰 버튼·Ripple·haptic 피드백을 적용했다. 출처와 접근성 조정은 `DESIGN.md`에 기록했다.
- 최소 API 28로 조정했다. API 37의 개발 서버 통신은 debug 전용 `ACCESS_LOCAL_NETWORK`와 사용 시 권한 요청으로 처리한다. 권한 거부 때 오프라인 데모를 유지한다.
- Android API 37 에뮬레이터에서 5개 instrumented test 통과: 전체 Mock 여정/승인 전환/화면 재생성/DB 저장, 미지원 전환 유지, SOC 부족 차단, 주야간 대비, 실제 개발 서버와 경로·분기점·완료 API 왕복.
- `assembleDebug`, Kotlin 단위 테스트, `lintDebug` 성공. lint 오류 0, 권장 사항 warning은 남아 있다.
- Pleos 2.1.0 화면에서 Home/경로 비교/분기점 화면을 확인했다. Gradle connected test가 instrumentation crash에도 성공으로 끝나는 환경 문제가 있어 실제 runner의 테스트 개수와 OK 출력을 검증하는 `scripts/check_android.py`를 추가했다.

## 최종 안정화

- 개발 서버 기능은 debug에만 허용하며 Release에서는 설정을 비활성화한다. Android 17 로컬 네트워크 권한은 실제 API 테스트에서 확인했다.
- 차량 입력과 선호값을 기기에 저장한다. 전비 소수점 정밀도를 보존하기 위해 문자열로 저장하고 기존 Float 저장값도 읽을 수 있다.
- 주행 표시 계산은 domain usecase로 분리했다. 서버의 계산 시각·모델·목적지·에너지 수학 일관성을 검증한 후 화면에 반영한다.
- Pleos에서 5개 연속 테스트 중 4개가 통과했다. UI 전체 여정 테스트는 CarSystemUI/DrivingView의 focus·Activity lifecycle 영향을 받아 실패했다. 별도 UI 테스트에서도 FASTEST 탭이 반영되지 않는 현상을 재현했고 당시 `mCurrentFocus`가 DrivingView인 것을 확인했다. 이를 정상 통과로 처리하지 않는다. 일반 Android API 37에서는 전체 5개가 통과한다.
- 외부 도로 경로·실차 SDK·TTS·실차 UX 인증은 여전히 미연동/미검증이다. 전체 production MVP 완료로 선언하지 않는다.
- 주야간 테마를 Pleos 에뮬레이터에서 시각 확인했으며 테스트 후 주간 모드로 복원했다. 설정 변경은 기존 분석을 무효화하고 Home으로 돌아오도록 처리해 빈 비교 화면을 방지한다.

## 공모전 가이드 재점검 — Vehicle SDK 실제 연결

- 2026-11-12 공모전 개발 환경·제출·심사 안내 및 Pleos 공개 SDK 문서를 재확인했다. 공개 Vehicle State 사용 가능 안내와 Maven 배포본을 확인하여 이전의 ‘SDK 미확보’ 제약을 해소했다.
- Vehicle 2.3.2 공식 소스의 capability/get/normal permission/%/km·kWh 단위를 확인하고 읽기 snapshot 어댑터를 구현했다.
- Pleos 2.1.0 / Vehicle Service 2.3.22에서 SDK 직접 읽기 테스트 1개 통과. debug build·JVM 8개·lint 통과. 누적 전비/용량 fallback의 출처를 분리한다.
- Navi/위치/TTS 및 실차 검증은 미완료다. 기존 합성 경로를 실제 내비에 보내지 않는다. 다음 작업은 제출 규격에 맞춘 release APK 패키징이다.

## 공모전용 release 검증

- 공식 제출 안내에 따라 `apk/팀명_VOLTRO_release.apk`, 소스 커밋·SHA-256·공개 서명 fingerprint 메타데이터, 재생성 스크립트를 준비했다. 서명 비밀정보는 저장소 밖의 로컬 데모 키로 관리한다.
- 원본 프로젝트의 `optimization.packageScope` 설정으로 release가 AndroidX Startup에서 `IllegalAccessError`를 내는 것을 발견했다. Kotlin collection 상속 접근 오류를 로그/매핑으로 확인하고 부분 scope를 제거해 전체 R8 최적화로 전환했다.
- 수정된 release APK(약 4.3MiB)는 별도 Android API 37 userdata에서 실행·SDK 미지원 fallback·경로 비교·분기점 승인·완료 리포트·이력 저장 UI 검사를 통과했다. 서명 및 실행 검증 전 APK를 정상 산출물로 처리하지 않았다.
- Pleos SDK는 첫 읽기와 cold boot 후 읽기에 성공했다. 앱 재설치 직후 capability callback timeout도 재현했으므로 반복 연결 안정성은 제약으로 남긴다. 실패 시 차량 입력을 유지한다.
- cold boot 후 같은 프로세스에서 `initialize → 읽기 → release`를 두 차례 연속 수행하는 SDK 테스트도 통과했다. 재설치 직후의 서비스 응답 지연과 구분한다.

## 로고 개편과 실행 화면 갱신

- Pleos의 48dp iconography와 adaptive icon 전경·배경 구조를 확인하고, 합쳐지는 경로 V와 에너지 꺾임을 연결한 자체 채움형 심볼을 제작했다. 앱 헤더·adaptive/monochrome·모든 밀도별 WebP 아이콘을 같은 원본에서 생성한다.
- Asta Sans 워드마크와 ink/white/blue 심볼, 투명 PNG·SVG, 앱 아이콘과 브랜드 미리보기를 `design/brand/`에 제공한다. Word 가이드의 APK 해시는 패키징 메타데이터에서 가져오도록 변경했다.
- Android debug 빌드·기존 단위 테스트·lint 성공. versionCode 3의 non-debuggable release를 같은 데모 키로 다시 서명하고 zipalign·v3 서명을 검증했다. 서명된 새 APK의 실제 UI 검사 6개 항목을 모두 통과했다.
- Pleos Connect 2.1.0에서 새 헤더와 시스템 GNB 앱 아이콘, 주간·야간 로고를 확인했다. 재부팅 후 SDK SOC 100% 읽기도 성공했다. 캡처는 에뮬레이터 값이며 실차 측정값이 아니다.
- 사용자 가이드의 실제 화면 8개를 모두 다시 캡처했다. 원본 이미지·빌드 유형·APK SHA-256·소스 커밋을 `docs/user-guide/CAPTURE_INFO.json`에 보존한다.
- Word/PDF 10페이지를 다시 렌더링하여 한글·표·새 로고 배치를 확인했다. DOCX에 포함된 8개 이미지가 새 캡처의 SHA-256과 정확히 일치하고, 가이드 마지막 페이지의 APK 해시도 새 배포본과 일치한다.

## 실제 지도·도로 경로와 Pleos 가독성 보완

- Phase 4의 미연동 상태를 해소했다. 기본 실제 도로 모드에 OSM raster 지도와 OSRM 공개 도로 경로를 연결하고, 기존 합성 시나리오는 별도 오프라인 데모로 유지한다. 출발지는 서울 시청, 목적지는 기존 세 곳이다. 실제로 반환된 서로 다른 후보 1~3개만 표시한다.
- 도로 geometry·거리·시간 annotation과 출발/도착 좌표를 검증하고 실제 도로 거리를 에너지 baseline에 적용한다. 실제 node와 시간 보간으로 위치를 재생하며, 서로 다른 전방 분기점을 별도로 처리한다. 실시간 교통·고도·날씨·GPS·차량 내비 변경은 미연동이다.
- 현재 viewport 타일만 요청하고 HTTP 만료·ETag 캐시와 식별 가능한 User-Agent를 사용한다. OSRM 요청 간격·목적지 캐시·출처 링크를 적용한다. 조회 실패 때 마지막 분석을 보존하며 합성 경로로 자동 대체하지 않는다. 정책·공급자 교체법은 `REAL_MAPS.md`에 기록했다.
- 넓은 차량 창의 본문·보조 문구·입력값을 최소 22sp, 버튼을 24sp, 경로 카드의 시간·소비량을 32sp로 키웠다. 설정창·확인창은 제목 26sp, 본문·동작 22sp를 사용하고 이력 버튼의 한 줄 표시와 입력 높이를 보완했다. 지도 출처는 18sp, 지도 타일은 차량 창에서 1.5배로 표시한다.
- JVM 14개, API 37의 오프라인 instrumentation 4개와 명시적 실도로 통합 검사 1개를 통과했다. debug 빌드·lint·test APK 빌드 성공. Pleos의 큰 글자·버튼 검사 1개와 실제 SDK·도로 재생·리포트·설정·분기점 캡처 검사 1개를 통과했다. software GPU에서 DrivingView가 입력을 가로채는 현상은 host GPU cold boot로 해소해 촬영했다.
- versionCode 4 / 1.1.0-mvp의 non-debuggable release를 같은 로컬 데모 키로 서명했다. zipalign·v3 서명과 실제 도로/오프라인 두 smoke 검사를 통과했다. 검증 결과와 정확한 소스 커밋·해시는 `apk/` 메타데이터에 기록한다.
- 휴대폰 가이드 이미지를 모두 제거하고 Pleos 원본 10개로 교체했다. 앱 창 8개는 native PixelCopy 1682×1210px, 전체 디스플레이 2개는 2560×1440px로 촬영했으며 사후 크롭·UI 합성을 하지 않았다. SDK SOC 100%는 에뮬레이터 snapshot이고 실차 측정값이 아니다.
- Word/PDF를 12페이지로 재편집하고 전체 페이지의 한글·지도·표·캡션을 렌더링 검수했다. DOCX 이미지 10개의 SHA-256을 원본과 대조하고 Asta Sans regular/bold를 포함했다. 캡처 출처·촬영 경로 수치·release 해시를 가이드에 보존했다.

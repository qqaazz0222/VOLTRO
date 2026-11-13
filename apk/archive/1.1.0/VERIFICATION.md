# Release 검증 기록

빌드 규격: release, version **1.1.0-mvp / code 4**, application ID `com.qqaazz0222.voltro`, min API 28. 실제 OSM 지도·OSRM 도로 경로와 확대된 Pleos 글자를 반영한 빌드다.

`VOLTRO_VOLTRO_release.json`에 이 APK의 정확한 소스 커밋·SHA-256·서명 인증서 fingerprint가 있다. APK는 zipalign과 apksigner 검증을 통과했으며 non-debuggable이다. 빌드 성공만으로 실행 성공을 판단하지 않았다.

검증한 APK의 SHA-256은 `5b2172a26a0df69b1187729bdb803fe9ce6eb6d3ca62fa64d74c42f515a62a1c`, 앱 소스 커밋은 `96c2154b97558f8ec0b1ef7b51dc4d115d1053c0`이다. 일반 Android API 37, 1080×2400px/420dpi, 별도 userdata에 이 서명된 APK를 설치하여 두 모드를 확인했다.

실제 도로 검사 (`scripts/smoke_submission.py --serial <ID> --roads`):

1. 정상 Home 실행과 실제 도로 모드 선택.
2. OSRM이 반환한 실제 도로 geometry·거리·시간과 경로 카드 표시.
3. 현재 지도 영역의 OSM 타일 로딩 및 출처 표시.
4. 도로 좌표 재생 완료 후 리포트 저장.
5. 이력에 도로 재생 출처 표시.
6. 검사 후 기본 프로필 복원.

오프라인 회귀 검사 (`scripts/smoke_submission.py --serial <ID>`):

1. 정상 Home 실행.
2. Pleos 서비스가 없는 환경에서 읽기 실패를 표시하고 기존 차량 설정 보존.
3. 오프라인 데모에서 강릉 목적지와 FASTEST 경로 선택, 약 34.6kWh / 도착 18.5% 표시.
4. 분기점의 절약 정보 안내, 사용자 승인 후 ECO 전환.
5. 주행 완료 리포트 및 로컬 이력 표시.

두 검사 모두 **PASSED**, 각각의 `result.json`에 기록된 APK SHA-256이 위 배포본과 일치한다. 원본 runtime 로그·UI dump·스크린샷은 Git에서 제외한 `artifacts/road-release-smoke/`와 `artifacts/release-smoke/`에 기록한다.

같은 앱 소스의 debug 빌드로 Pleos Connect 2.1.0에서 큰 글자·버튼 배치 검사 1개와 실제 SDK SOC 100% → 도로 분석 → 재생 → 리포트·이력 → 잔량 부족 차단 → 설정 → 오프라인 분기점의 캡처 검사 1개를 통과했다. [사용자 가이드](../../../docs/user-guide/README.md)는 실제 Pleos 화면 10개를 사용한 12페이지 Word/PDF로 교체했다. 캡처의 debug 빌드와 배포 release의 해시는 별도로 기록한다.

지도·도로 정보는 공개 서비스 응답이며 주행은 좌표 재생, 소비량은 거리/전비 추정이다. 이 검증은 실차 GPS·에너지 정확도·내비 제어·Pleos Market 심사 통과를 인증하지 않는다.

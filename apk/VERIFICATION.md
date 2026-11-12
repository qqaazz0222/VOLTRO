# Release 검증 기록

빌드 규격: release, version 1.0.0-mvp / code 2, application ID `com.qqaazz0222.voltro`, min API 28.

`VOLTRO_VOLTRO_release.json`에 이 APK의 정확한 소스 커밋·SHA-256·서명 인증서 fingerprint가 있다. APK는 zipalign과 apksigner 검증을 통과했으며 non-debuggable이다. 빌드 성공만으로 실행 성공을 판단하지 않았다.

일반 Android API 37, 1080×2400px/420dpi, 별도 초기 userdata에 이 APK를 설치하여 다음 UI 흐름을 확인했다.

1. 정상 Home 실행.
2. Pleos 서비스가 없는 환경에서 읽기 실패를 표시하고 기존 차량 설정 보존.
3. 강릉 목적지와 FASTEST 경로 선택, 약 34.6kWh / 도착 18.5% 표시.
4. 분기점의 절약 정보 안내, 사용자 승인 후 ECO 전환.
5. 주행 완료 리포트 및 로컬 이력 표시.

검사 스크립트: `scripts/smoke_submission.py`. 원본 runtime 로그·UI dump·스크린샷은 Git에서 제외한 `artifacts/release-smoke/`에 기록한다. 이 파일은 실차 SDK·실도로·Pleos Market 심사 통과를 인증하지 않는다.

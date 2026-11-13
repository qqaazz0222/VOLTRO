# VOLTRO 1.2.0 release 검증 기록

검증일: 2026-11-13 KST. **1.2.0-mvp / versionCode 5**, application ID `com.qqaazz0222.voltro`, min API 28.

- 앱 소스 커밋: `66927c93e3e4a4b3acc202efe40d4a9e17974145`
- APK SHA-256: `0371726acdffeda1828dbf568cc7143bc8fea35509e4630e7b2e48505479ed4e`
- 파일: `VOLTRO_VOLTRO_release.apk` / 4,562,012 bytes
- non-debuggable release, zipalign 및 v3 서명 검증 통과. 공개 인증서 fingerprint와 상세 정보는 [메타데이터](VOLTRO_VOLTRO_release.json)에 있다.

## 실제 release UI 검증

별도 Android API 37 에뮬레이터 userdata에서 서명 APK를 실행했다. 구현 검토 경로의 APK를 검사한 뒤 소스를 커밋하고 정식 제출 경로로 재패키징했으며, **두 파일의 전체 바이트와 SHA-256이 정확히 일치**함을 확인했다.

1. 절전 전환 시나리오와 추천 근거 표시.
2. 분기점 승인 화면에서 실제 `am force-stop` → 재실행 → 사용자의 복구 선택 → 미결 승인을 보존한 일시정지 복구.
3. 승인 후 완료 리포트: 계산상 약 2.9 kWh 감소·15분 추가.
4. SOC 20%에서 시작 비활성화, 최소 출발 SOC와 부족 배터리 에너지 표시.
5. 경로 변경 실패 시 기존 빠른 경로를 유지하고 정지.
6. 명시적 취소 후 Home 복귀.

모두 **PASSED**. [원본 runner/UI 로그·요약](../docs/submission/validation/), [2분 30초 실제 화면 녹화](../docs/submission/VOLTRO_Demo.mp4), [영상 해시·출처](../docs/submission/VIDEO_INFO.json)를 보존한다.

## 계산·플랫폼 확인

Python 26개, Kotlin JVM 18개 통과. Pleos Connect 2.1.0의 오프라인 여정/안전/대비/시나리오/복구 8개와 글자·버튼 1개, 공식 Vehicle SDK 직접 읽기 1개 통과. 일반 Android의 명시적 공개 도로 통합 검사 1개도 통과했다. build·lint 성공이며 lint error 0, warning 32개는 남아 있다. 완료/취소가 승인된 뒤 재생 체크포인트가 남지 않는 회귀 검사도 포함한다.

[기존 1.1.0 APK와 검증 기록](archive/1.1.0/) 및 해당 버전의 사용자 가이드는 보존했다. 신규 Pleos 화면은 [출품 자료](../docs/submission/README.md)의 원본 캡처 정보를 따른다.

지도·도로는 공개 공급자 응답, 주행은 재생, 에너지는 추정이다. 실차 GPS·실측 에너지 정확도·차량 내비 제어·Pleos Market 인증을 완료했다는 뜻은 아니다. 최종 접수에는 등록 팀명·참가자 동의/서명·저장소 및 영상 공유 경로를 확정한다. 원격 푸시·공개 설정 변경·접수는 수행하지 않았다.

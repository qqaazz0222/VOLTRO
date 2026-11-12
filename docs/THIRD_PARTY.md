# 외부 자료 및 라이선스

- **Asta Sans**: https://github.com/google/fonts/tree/main/ofl/astasans · SIL Open Font License 1.1. 원본 `AstaSans[wght].ttf`를 `asta_sans.ttf`로 이름만 바꿔 포함했다. 저작권·전체 조건은 `licenses/AstaSans-OFL.txt`에 보존하며 APK assets에도 포함한다.
- **Pleos 디자인 가이드**: `DESIGN.md`에 링크한 공개 문서를 참고하여 색상·가독성·아이콘 구조를 자체 구현했다. 공식 Figma 파일·원본 로고·시스템 아이콘 파일은 번들하지 않았다. Pleos 인증이나 승인된 SDK 컴포넌트라고 표시하지 않는다.
- **경로/좌표 데이터**: `mock-data/scenario.json`은 VOLTRO의 합성 데모 fixture다. 도시·목적지 좌표는 시연용 기준점이며 실제 도로·고도·통행 데이터를 포함하지 않는다. 외부 지도 tile이나 상용 경로 API 데이터는 사용하지 않는다.
- **앱 UI 아이콘**: 자체 VectorDrawable. 기존 Android Studio 기본 adaptive icon을 VOLTRO 마크로 교체했다.
- **Pleos Vehicle SDK 2.3.2**: 공식 Maven 저장소에서 Gradle로 참조한다. 벤더 SDK 및 전이 의존성의 이용 조건이 적용된다. 원본 AAR와 sources JAR는 저장소에 재배포하지 않는다. SDK source의 실제 API·단위·permission 정의를 확인해 읽기 어댑터를 구현했다.
- **AndroidX / Material / Kotlin Coroutines**: 프로젝트의 Gradle 의존성. 각 배포 패키지의 라이선스가 적용된다. AndroidX/Material/Coroutines는 Apache 2.0 계열이다.
- **FastAPI / Uvicorn / Pydantic / pytest / HTTPX**: Python 패키지 원본 라이선스가 적용된다. 정확한 설치 버전은 `backend/requirements.lock`을 참조한다. 배포 시 transitive dependency 라이선스 고지는 별도 점검한다.

공모전 제출용 문구는 Mock 경로/주행과 SDK snapshot 범위를 구분해야 한다. Vehicle SDK 에뮬레이터 읽기 테스트를 실차 정확도·실도로 통행 가능성·전체 SDK 검증 완료로 확대해 소개하면 안 된다.

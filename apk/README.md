# 공모전 시연용 release APK

공식 [제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission)의 `apk/` 위치·`팀명_앱이름_release.apk` 파일명·실행 가능한 release 빌드 규격에 맞춘다.

- 파일명 기본 팀 라벨은 `VOLTRO`다. 등록한 실제 팀명이 다르면 빌드 스크립트의 `--team`으로 변경한다.
- APK는 non-debuggable release이며 지원 기기(API 28 이상)에 대한 v3 서명을 검증한다. 동봉 JSON에는 소스 커밋, SHA-256, 공개 인증서 fingerprint를 기록한다.
- 기본 서명키는 이 PC의 `~/.local/share/voltro/contest-signing/`에만 저장하는 **공모전 데모 전용** 키다. 키·암호는 Git에 넣지 않는다. Pleos Market 등록용 신원이나 제조사 서명이 아니다.
- 동일 application ID의 debug APK가 설치되어 있다면 서명이 달라 업데이트 설치가 되지 않는다. 해당 테스트 앱의 이력을 보존해야 한다면 별도 에뮬레이터에서 실행한다.
- 기본 시연은 서버 없이 가능하다. Home → 강릉역 → 경로 분석 → 빠른 경로 → Mock 주행 → 분기점 승인 → 리포트 순서다.
- Pleos Vehicle SDK snapshot은 실제 에뮬레이터 서비스와 연동하지만 경로/주행은 합성 데이터다. 일반 Android에서도 오프라인 데모를 실행할 수 있다.
- 디버그용 로컬 HTTP 서버 옵션은 release에서 비활성화된다.

재생성 (소스가 커밋된 상태, JDK와 Android SDK 필요):

```sh
python3 scripts/build_submission.py --team VOLTRO
```

별도 서명키가 있으면 `VOLTRO_SIGNING_KEYSTORE`, `VOLTRO_SIGNING_ALIAS`, `VOLTRO_SIGNING_PASSWORD_FILE` 세 환경변수를 지정한다. 이 스크립트는 keystore와 private key의 암호가 같은 키를 지원한다. 암호 값 자체를 명령행이나 저장소에 넣지 않는다. 기존 키를 잃어버리면 같은 서명으로 업데이트할 수 없으므로 로컬 키는 본인이 안전하게 보관해야 한다.

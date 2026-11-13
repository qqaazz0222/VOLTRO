# VOLTRO 1.2.0 출품 검토 자료

2026-11-13 KST. 사용 가능한 앱과 설명 자료를 검토하는 묶음이다. 외부 접수·저장소 공개 변경·개인정보 및 동의서 서명은 수행하지 않는다.

## 자료

- [접수양식에 옮길 기획 원고](ENTRY_BRIEF.md): 고객 문제, 차량 가치, 기술, 사업 검증 목표, 현재 제약.
- [3분 심사 시연 대본](DEMO_SCRIPT.md): 절전 전환·잔량 부족·전환 실패, 복구 보조 시연.
- [1.2.0 검토용 signed release APK](../../apk/VOLTRO_VOLTRO_release.apk): 신규 기능이 포함된 non-debuggable 빌드.
- [APK 메타데이터](../../apk/VOLTRO_VOLTRO_release.json): 정확한 앱 소스 커밋·SHA-256·서명 인증서 fingerprint.
- 기존 [Pleos 사용자 가이드](../user-guide/VOLTRO_User_Guide.pdf)는 1.1.0 화면 기준이다. 신규 기능은 이 문서와 시연 대본을 함께 확인한다.

## 1.2.0 시연 방법

Home → **심사 시연 시나리오**에서 다음을 선택한다. 적용 확인 후 비교 화면으로 이동한다. 차량 입력은 데모값이며 저장된 프로필과 완료 이력을 덮어쓰지 않는다.

| 시나리오 | 기대 결과 |
|---|---|
| 절전 전환 | 빠른 경로가 선택됨 → 주행 → 분기점 승인 → 약 2.9 kWh 감소·15분 추가 리포트 |
| 배터리 부족 | SOC 20%, 모든 경로 시작 차단, 최소 출발 SOC·추가 배터리 에너지 표시 |
| 경로 변경 실패 | 빠른 경로 → 분기점 승인 시 실패 표시, 기존 경로 유지 |

비교 화면의 **전비 20% 저하**는 민감도 확인용 가정이다. 추천을 자동으로 바꾸는 확률 모델이나 실차 안전 보증이 아니다. 음수 SOC는 해당 조건에서 도착 불가임을 보여주기 위해 그대로 표시한다.

## 제출 빌드와 재생성

현재 `apk/VOLTRO_VOLTRO_release.apk`는 1.2.0 signed release다. 기존 1.1.0은 [보관 폴더](../../apk/archive/1.1.0/)에 원본 메타데이터와 함께 남겼다. 로컬 `codex/contest-readiness-1.2` 브랜치에 소스·자료와 APK 산출물을 분리해 커밋한다. 메타데이터의 앱 소스 커밋과 접수 메일의 최종 제출 커밋(APK 포함)을 구분한다. 원격에는 푸시하지 않는다.

```sh
# 구현·스크립트가 커밋된 상태에서 재생성
python3 scripts/build_submission.py --team 실제팀명

# 앞으로의 미커밋 변경을 검토할 때만 사용: 별도 apk/review/ 생성
python3 scripts/build_submission.py --team 실제팀명 --review
```

기본 명령은 소스가 미커밋이면 중단한다. `--review`만 미커밋 소스를 허용하며 정확한 파일별 해시를 기록하고 `source_commit`은 `null`로 표시한다. 최종 접수에는 기본 명령의 빌드를 사용한다. 서명 키·암호·참가자 개인 문서는 저장소에 추가하지 않는다.

## 재검증

```sh
.venv/bin/python -m pytest backend/tests -q
cd VOLTRO
JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

저장소 루트에서 `python3 scripts/check_android.py --serial <ID>`는 오프라인 8개 검사를 실행한다. `--roads`, `--pleos-layout`, `--pleos-vehicle`은 네트워크·기기 조건에 따라 별도 실행한다. `python3 scripts/check_contest_release.py --serial <별도 에뮬레이터 ID> --record`는 signed release의 실제 강제 종료·복구·세 가지 시나리오를 검사하고 화면 녹화를 생성한다. 최종 APK를 검사할 때는 `--apk apk/VOLTRO_VOLTRO_release.apk`를 지정한다. debug 서명이 이미 설치된 장치에서는 설치가 실패하며 앱 데이터를 삭제하지 않는다.

## 접수 시 참가자가 확정할 항목

공식 접수 기간은 **2026-10-21–2026-11-15**다. 팀·대표자·참가부문·연락처와 참가자 전원의 개별 동의·서명·날짜를 실제 정보로 작성한다. 등록 팀명에 맞춘 APK 파일명, 저장소 주소와 최종 커밋, 영상 링크·공유 권한을 확인한다. 비공개 저장소는 공식 안내에 따른 공개 일정 또는 소스·APK 압축 다운로드 대안을 선택한다. 현재 MAU·Retention·매출 실적이 있는 것처럼 기재하지 않는다.

근거: [공식 제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission), [공식 평가 항목](https://appdevchallenge.auto-hmg.io/guide/judging-awards). 2026-11-13 재확인.

## 신규 Pleos 화면

[추천과 전비 저하 가정](screenshots/pleos-comparison.png) · [SOC 부족과 필요 출발 잔량](screenshots/pleos-low-soc.png) · [일시정지 복구·미결 승인](screenshots/pleos-recovery.png) · [계산상 변화 리포트](screenshots/pleos-report.png)

Pleos Connect 2.1.0 / API 34의 native 2560×1440 전체 화면이다. 앱 실행 화면을 그대로 촬영했으며 크롭·확대·합성을 하지 않았다. 비교·SOC 부족은 오프라인 시나리오, 복구·리포트는 저장/복구 자동 검사의 고정 입력이다. 차량값과 소비량은 실차 측정값이 아니다. [촬영 출처와 원본 SHA-256](screenshots/CAPTURE_INFO.json)에 debug APK 해시도 기록한다. 별도 signed release 영상·검사와 빌드 출처를 혼용하지 않는다.

## 실제 signed release 시연 영상과 검증

[2분 35초 시연 영상](VOLTRO_Demo.mp4)은 Android API 37 일반 에뮬레이터의 실제 앱 화면 녹화다. 성공 시나리오 → 분기점에서 프로세스 강제 종료 → Home에서 명시적 복구 → 승인·완료 → SOC 부족 → 변경 실패·일시정지·취소 흐름을 담았다. 720×1600, 무음이며 프레임 합성·컷 편집 없이 MP4 컨테이너만 정리했다. [영상 출처·APK 해시](VIDEO_INFO.json)를 함께 제공한다. Pleos 실차나 실제 차량 소비량을 촬영한 영상은 아니다.

검사 원본과 요약은 [validation/](validation/)에 보존한다. release UI 검사의 APK SHA-256과 최종 배포본 해시가 일치하는지 확인한다. [앱 검증 기록](../../apk/VERIFICATION.md)에는 정확한 source commit과 서명 정보가 있다.

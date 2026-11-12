# VOLTRO 사용자 가이드

실제 실행 화면 8개로 설치부터 목적지 선택, 경로 비교, 분기점 승인, 리포트·이력 확인과 설정까지 설명하는 10페이지 가이드입니다.

- [PDF로 보기](VOLTRO_User_Guide.pdf)
- [Word 원본 내려받기](VOLTRO_User_Guide.docx)
- [원본 화면 및 캡처 정보](CAPTURE_INFO.json)

기준 버전은 **1.0.0-mvp**, 작성일은 **2026년 11월 12일**입니다. 세로 화면은 저장소의 서명된 [release APK](../../apk/VOLTRO_VOLTRO_release.apk)를 Android API 37에서 실행해 캡처했습니다. 가로 화면은 Pleos Connect 2.1.0의 개발 빌드입니다. 모든 화면은 `adb exec-out screencap -p`로 수집한 수정 없는 실제 화면입니다.

경로·주행은 시뮬레이션이며, Pleos SDK의 SOC 100% 화면도 에뮬레이터의 응답입니다. 문서에서 개발 빌드와 release, SDK 값과 설정값을 구분합니다. 기본 시연은 로그인과 개발 서버 없이 진행합니다.

## 문서 재생성

문서 본문과 레이아웃은 [build_user_guide.py](../../scripts/build_user_guide.py), 이미지 원본은 [screenshots](screenshots)에 있습니다. Python 3.12 환경에서 다음 의존성으로 생성했습니다.

```sh
python -m pip install python-docx==1.2.0 Pillow==13.0.0 fonttools==4.68.0 lxml==6.1.3
python scripts/build_user_guide.py
```

생성된 DOCX를 LibreOffice 또는 Microsoft Word에서 PDF로 내보냅니다. 배포 파일은 LibreOffice 26.8.2와 Asta Sans를 사용해 변환하고, 10페이지 전체를 이미지로 렌더링해 한글·표·화면 배치를 확인했습니다. 다른 변환기의 줄바꿈은 달라질 수 있습니다.

DOCX에는 앱과 같은 Asta Sans의 regular/bold 글꼴을 포함했습니다. 글꼴 출처 및 재배포 조건은 [OFL 라이선스](../../licenses/AstaSans-OFL.txt)를 참고하세요. 생성 과정의 임시 글꼴과 검토 이미지는 Git에서 제외한 `artifacts/`에 저장됩니다.

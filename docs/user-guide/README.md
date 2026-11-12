# VOLTRO Pleos 사용자 가이드

실제 지도·도로 경로 비교, 주행 재생, 리포트·이력, 설정과 분기점 시연을 설명하는 **12페이지** 가이드입니다. 휴대폰 화면을 모두 교체하고 **Pleos에서 직접 촬영한 10개 화면**을 사용했습니다.

- [PDF로 보기](VOLTRO_User_Guide.pdf)
- [Word 원본 내려받기](VOLTRO_User_Guide.docx)
- [캡처별 환경·방법·APK 해시](CAPTURE_INFO.json)
- [촬영 당시 실제 도로 경로 수치](DEMO_CAPTURE.json)

기준 버전은 **1.1.0-mvp / versionCode 4**, 작성일은 **2026년 11월 12일**입니다. 모든 이미지는 Pleos Connect 2.1.0 / Android 14(API 34), 2560×1440px / 160dpi 환경에서 촬영했습니다. 전체 화면 2개는 시스템 UI를 포함하며, 앱 창 8개는 Android PixelCopy로 실제 창의 GPU 픽셀을 직접 캡처한 1682×1210px 원본입니다. 이미지에 합성 UI를 넣거나 촬영 후 잘라내지 않았습니다.

촬영은 같은 앱 소스의 개발 빌드로 진행했습니다. 캡처된 APK의 SHA-256과 정확한 소스 커밋은 `CAPTURE_INFO.json`에 있습니다. [서명된 release APK](../../apk/VOLTRO_VOLTRO_release.apk)는 같은 사용자 흐름을 제공하며 개발 HTTP 서버 항목은 비활성화됩니다.

실제 도로 페이지는 OSM 지도와 OSRM 응답을 사용합니다. SOC 100%는 실제 Pleos 에뮬레이터 SDK 응답이며, 전비 5.2와 용량 70은 설정값입니다. 주행은 도로 좌표 재생으로, 실차 GPS·소비량 계측을 뜻하지 않습니다. 분기점 알림 페이지의 2.9kWh·15분 수치는 별도 오프라인 합성 데모입니다.

## 캡처와 문서 재생성

[캡처 테스트](../../VOLTRO/app/src/androidTest/java/com/qqaazz0222/voltro/PleosGuideCaptureTest.kt)는 실제 앱의 모드·분석·SDK 읽기·재생을 실행해 창을 촬영합니다. 공개 지도 서버를 훑거나 타일을 사전 다운로드하지 않으며, 하나의 경로 조회와 현재 보이는 지도 영역을 사용합니다.

```sh
python3 scripts/check_android.py --serial emulator-5554 --capture-guide
```

Pleos 에뮬레이터와 Vehicle Service, 인터넷이 필요합니다. 원본 PNG와 `metrics.json`은 앱의 `files/pleos-guide/`에 생성됩니다. 현재 Android 사용자 ID는 `adb shell am get-current-user`로 확인합니다. 예를 들어 사용자 10의 원본을 가져오는 명령은 다음과 같습니다.

```sh
adb -s emulator-5554 exec-out run-as com.qqaazz0222.voltro --user 10 \
  cat files/pleos-guide/pleos-comparison.png > pleos-comparison.png
```

가이드의 `screenshots/`와 `DEMO_CAPTURE.json`을 새 촬영본으로 교체하고 캡처 메타데이터를 갱신한 뒤 생성합니다. 본문과 레이아웃 원본은 [build_user_guide.py](../../scripts/build_user_guide.py)입니다.

```sh
python -m pip install python-docx==1.2.0 Pillow==13.0.0 fonttools==4.68.0 lxml==6.1.3
python scripts/build_user_guide.py
```

생성된 DOCX를 LibreOffice 또는 Word에서 PDF로 내보냅니다. 배포 파일은 LibreOffice 26.8.2로 변환하고 12페이지 전체를 이미지로 렌더링해 한글·지도·표·페이지 배치를 확인했습니다. Asta Sans regular/bold를 DOCX에 포함했으며 [OFL 라이선스](../../licenses/AstaSans-OFL.txt)를 보존합니다. 임시 글꼴과 검토 이미지는 Git에서 제외한 `artifacts/`에 저장합니다.

지도 데이터: [© OpenStreetMap contributors / ODbL](https://www.openstreetmap.org/copyright). 경로: [OSRM](https://routing.openstreetmap.de/about.html). 공급자·캐시·요청 제한은 [실제 지도 연동](../REAL_MAPS.md)을 참고하세요.

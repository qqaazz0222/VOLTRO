# 실제 지도와 도로 경로

VOLTRO 1.1.0-mvp의 기본 모드는 **실제 도로**다. OpenStreetMap 배경 지도에 OSRM이 반환한 자동차 도로 경로를 표시하고, 그 경로의 거리와 ETA를 후보 카드에 연결한다. 소비량은 `도로 거리 ÷ 설정/SDK 전비`, 도착 SOC는 소비량과 사용 가능 용량으로 계산한다. 실시간 교통·고도·운전자별 전비 보정은 적용하지 않는다.

## 사용자 흐름

1. Home에서 **실제 도로**를 선택하고 강릉역·속초해수욕장·양양 서피비치 중 목적지를 선택한다. 출발지는 서울 시청으로 고정되어 있다.
2. **경로 분석하기**를 누르면 출발지·목적지 좌표를 OSRM 공개 데모 서버로 전송한다. API 키나 별도 개발 서버 없이 HTTPS로 호출한다.
3. 실제 지도에서 경로를 비교한다. 지도는 드래그와 `+` / `−` / **전체** 조작을 지원한다. 지도 아래의 출처를 누르면 OSM 저작권·OSRM 서비스·지도 오류 신고 링크를 열 수 있다.
4. 도착 잔량이 최소값 이상인 경로를 선택해 **주행 재생**을 시작한다. 이 재생은 실도로 좌표를 따라가며, 실제 GPS·차량 내비게이션을 제어하지 않는다. 주행 재생 중에는 지도 드래그·확대 조작을 제공하지 않는다.
5. 리포트·이력에는 도로 경로 재생과 기존 Mock 기록을 구분해 저장한다. 기존 이력 JSON에는 새 출처 필드가 없어도 기본값으로 읽힌다.

기본 SOC 68% / 전비 5.2 / 용량 70으로 강릉 실도로를 조회하면 최소 도착 잔량 15%에 미달할 수 있다. 시작 차단은 정상 동작이며 임계값을 자동으로 낮추지 않는다. 재생을 시연하려면 충분한 SOC를 입력하거나 Pleos 차량 상태를 읽어 다시 분석한다.

## 경로 검증과 에너지 계산

- `alternatives=2`로 요청하고 응답의 서로 다른 경로 **1~3개**만 사용한다. 공급자가 대안을 반환하지 않을 수 있으므로 임의로 2~3개의 경로를 생성하지 않는다. [OSRM Route API](https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#route-service)
- GeoJSON은 `[경도, 위도]` 순서로 읽는다. 시작·끝 snap 거리, 좌표 범위, segment annotation 수, 누적 거리·시간, 지리적 길이와 공급자 거리의 일관성을 확인한다. 잘못된 응답은 캐시에 저장하지 않는다.
- 가장 빠른 경로와 더 짧은 대안을 구분하고, 현재 전비와 SOC로 후보별 소비량·잔량을 매번 다시 계산한다. 추천은 반환된 후보 안에서 최소 잔량·허용 추가 시간·최소 절약량 정책을 적용한 결과다. 모든 도로에 대한 에너지 최적해를 뜻하지 않는다.
- 상세 좌표를 보존해 지도 선과 재생 위치를 같은 도로 geometry에 맞춘다. 공통 경로 prefix의 실제 분기점을 사용하고, 앞선 분기점을 처리한 뒤 다음 분기점을 검사한다.
- OSRM segment duration은 회전 시간을 제외한다. 재생의 구간 시간은 annotation 비율에 공급자 전체 ETA를 배분한 보간값이며 실측 시간이 아니다. 기존 합성 경로의 35km/25분 가정은 실도로 경로에 적용하지 않는다. [Annotation 정의](https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#annotation-object)
- 내부 `confidence`는 유효성 검사에 통과한 geometry를 정책에서 사용할지를 구분하는 값이다. 소비량 예측 정확도나 실차 검증 수치로 표시하지 않는다.

## 지도와 네트워크

지도는 Android Canvas의 Web Mercator 좌표계에서 OSM raster tile과 도로 선을 함께 그린다. SDK/웹 페이지를 띄우는 방식이 아니며, 외부 JavaScript를 실행하지 않는다.

- 실제로 보이는 viewport의 타일만 요청한다. 사전 다운로드·오프라인 지도 저장 기능은 제공하지 않는다.
- 앱 이름과 저장소 연락 URL을 담은 User-Agent를 사용한다. `HttpResponseCache` 64MiB와 메모리 캐시 24MiB로 서버의 캐시 만료·ETag·조건부 요청을 처리한다. 캐시를 우회하는 헤더를 보내지 않는다.
- 타일 다운로드는 최대 두 작업, OSRM 요청은 앱 인스턴스에서 1.1초 이상 간격으로 직렬화한다. 동일 목적지 응답은 5분간 재사용하며 차량 입력이 바뀌면 에너지를 재계산한다.
- 지도 타일에 오류가 나면 연결 실패와 재시도 안내를 표시한다. 경로 조회에 실패해도 마지막 분석을 보존하며 Mock 경로로 자동 전환하지 않는다.
- OSM 저작권 표시를 지도 위에 계속 표시한다. 지도 데이터는 [OpenStreetMap contributors / ODbL](https://www.openstreetmap.org/copyright), 경로는 OSRM 출처를 표시한다.

OSM 타일 서버는 캐시·식별·출처 표시와 viewport 요청 조건을 요구한다. 공개 OSRM 서비스는 최대 초당 1회 요청과 출처 표시 등을 요구하며 가용성을 보장하지 않는다. 현재 기본 주소는 공모전 시연용 공개 서비스다. 서비스 운영·상용 배포에는 운영 규모와 해당 이용 조건에 맞는 공급자 또는 자체 서버를 사용해야 한다. [OSM Tile Policy](https://operations.osmfoundation.org/policies/tiles/), [OSRM 서버 안내](https://routing.openstreetmap.de/about.html), [FOSSGIS 이용 조건](https://www.fossgis.de/arbeitsgruppen/osm-server/nutzungsbedingungen/)

## 공급자 교체

호환되는 HTTPS OSRM 서버와 OSM raster tile endpoint를 Gradle 속성으로 교체할 수 있다. 별도 키가 필요한 서비스는 비밀 키를 APK에 넣지 않고 인증된 백엔드 어댑터를 추가해야 한다. 공급자를 바꾸면 출처 표시·캐시 조건도 해당 조건에 맞게 검토한다.

```sh
cd VOLTRO
./gradlew :app:assembleDebug \
  -PvoltroRoutingUrl=https://routing.example.org \
  '-PvoltroTileUrl=https://tiles.example.org/{z}/{x}/{y}.png'
```

개발용 FastAPI는 기존 합성 경로·완료 저장 테스트를 위한 별도 모드다. 앱의 실제 도로 모드는 현재 `OsrmRouteRepository`에서 공급자와 직접 통신한다. Pleos 위치·NaviHelper·TTS 연동은 이 작업에 포함되지 않는다.

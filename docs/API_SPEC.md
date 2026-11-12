# VOLTRO 개발 API

로컬 전용 FastAPI, `/api/v1`, WGS84, kWh/km/min 단위. Swagger와 전체 스키마는 `/docs`에서 확인한다. 현재 경로 제공자는 항상 synthetic MOCK이다.

| Method | 경로 | 용도 |
|---|---|---|
| GET | `/health` | 서버/모델/모드 확인 |
| GET | `/api/v1/vehicle` | Mock 차량 초기 상태 |
| GET | `/api/v1/destinations` | 지원하는 데모 목적지 |
| POST | `/api/v1/energy/predict` | 입력 검증 후 baseline 예측 |
| POST | `/api/v1/routes/compare` | 3개 경로와 추천, trip_id 발급 |
| POST | `/api/v1/junctions/evaluate` | 동일 세션의 분기점 접근 평가 |
| POST | `/api/v1/trips/complete` | 완료 결과 멱등 저장 |

## 예시

```sh
curl -X POST http://127.0.0.1:8000/api/v1/routes/compare \
  -H 'Content-Type: application/json' \
  -d '{"origin":{"latitude":37.5665,"longitude":126.9780},"destination":{"latitude":37.7644,"longitude":128.8995},"vehicle":{"soc_percent":68,"usable_capacity_kwh":70,"efficiency_km_per_kwh":5.2},"preferences":{"min_arrival_soc_percent":15,"max_extra_minutes":15}}'
```

강릉 시나리오 기본 결과:

| 경로 | 거리 | 시간 | 소비량 | 도착 SOC |
|---|---:|---:|---:|---:|
| FASTEST | 180 km | 130분 | 34.6154 kWh | 18.5495% |
| BALANCED | 174 km | 137분 | 33.4615 kWh | 20.1978% |
| ECO | 165 km | 145분 | 31.7308 kWh | 22.6703% |

기본 공식은 `distance / efficiency`이며 보정 계수를 사용하지 않는다. 명세의 21.6/16.2 예시는 이 거리와 기본 전비로 재현되지 않아 사용하지 않았다.

## 응답과 오류

경로 응답에는 노드·polyline, 출처, 계산 시각, 모델 버전, 추천 ID(없으면 null), trip_id를 포함한다. 세션은 최대 1,000개, 2시간 유효, 메모리에만 존재하며 서버 재시작 후 경로를 다시 분석해야 한다.

분기점 요청은 명세 필드 외에 `accuracy_meters`(기본 5), `navigation_selectable`(기본 false)을 받는다. Mock 내비 capability를 클라이언트가 명시할 때만 추천한다. 이미 안내한 활성경로/분기점 조합은 `should_notify=false`로 응답한다.

완료 요청은 `actual_energy_kwh=null`, `simulated_energy_kwh`, `energy_source="MOCK_SOC_ESTIMATE"`를 사용한다. 실측 데이터가 있을 때만 `energy_source="MEASURED"`와 actual 값을 함께 전달한다. Mock 결과를 실측값으로 저장하는 요청은 거부한다. 실측값이 없거나 예측값이 0이면 상대오차는 null이다. 동일 trip_id와 같은 내용은 같은 응답을 반환하며 다른 내용은 409이다.

검증 실패 등 예상 오류는 `{"error":{"code":"INVALID_INPUT","message":"...","retryable":false}}` 형태다. 입력 범위를 벗어나는 좌표, 비유한 수, 0 용량/전비를 거부한다. 정밀 위치를 DB에 보관하지 않는다.

## 운영 한계

기본 바인딩은 `127.0.0.1`이며 인증 없는 개발 서버다. 외부 공개 배포는 아직 구현 범위에 포함하지 않는다. 공개 배포 전 HTTPS, 인증, 요청 빈도 제한, 세션 공유 저장소, 운영 모니터링과 데이터 보관/삭제 정책을 추가해야 한다. Android에 서버 비밀키를 포함하지 않는다.

`VOLTRO_DB`로 SQLite 파일 위치, `VOLTRO_SCENARIO`로 공통 fixture 파일 위치를 지정할 수 있다. 패키지 wheel을 단독 설치하는 경우에는 fixture를 따로 제공해야 한다. 기본 실행은 저장소 checkout 기준이다.

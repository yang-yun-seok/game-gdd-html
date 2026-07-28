# Game Business Plan (`business`)

게임의 시장·고객·수익·출시 가설을 사업 의사결정에 맞게 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `business-objectives` | 의사결정과 범위 | 승인할 가설, 독자, 지역·기간, 제외 범위 |
| 02 | `market` | 시장 맥락 | 범주, 규모·성장 주장, 플랫폼·지역; 최신 출처 |
| 03 | `audience` | 고객과 수요 | 세그먼트, 문제·욕구, 지불·플레이 맥락 |
| 04 | `competitive-positioning` | 경쟁과 포지셔닝 | 비교축, 대체재, 차별점, 진입 장벽 |
| 05 | `business-model` | 제품·수익 구조 | 제품 형태, 채널, 비용·수익 가설 |
| 06 | `monetization` | 상품과 가격 전략 | 상품군, 가격 논리, 전환 경로, 공정성 |
| 07 | `go-to-market` | 출시·유통 전략 | 지역, 채널, 단계, 파트너, 일정·의존성 |
| 08 | `business-kpis` | KPI와 시나리오 | 퍼널, 목표·하한, 가정, 민감도 |
| 09 | `business-risks` | 리스크와 검증 | 법·플랫폼·시장·운영 리스크, 검증 계획 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `business-objectives`, `market`, `audience`, `business-model`, `business-risks`

| facet | 추가 section ID |
|---|---|
| `positioning` | `competitive-positioning` |
| `research` | `competitive-positioning` |
| `monetization` | `monetization` |
| `pricing` | `monetization` |
| `launch` | `go-to-market` |
| `operations` | `go-to-market` |
| `telemetry` | `business-kpis` |
| `scenarios` | `business-kpis` |

dependency:

- `monetization` → `business-model`
- `go-to-market` → `competitive-positioning`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 화면별 UI, 시스템 상태표, 레벨 상세는 넣지 않는다.
- 최신 외부 사실은 직접 출처와 확인일이 필수다.
- 근거 있는 KPI·매출 시나리오가 있으면 Chart.js를 권장하며, 없는 수치를 만들지 않는다.

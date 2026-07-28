# Economy Design (`economy`)

게임 안 자원의 가치가 생성·소비·교환되는 구조와 운영 레버를 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `economy-objectives` | 경제 목표와 경계 | 목표 행동, 시간축, 유·무료 경계, 금지 경험 |
| 02 | `currencies` | 재화 정의 | 재화별 목적, 획득·보유·만료·거래 규칙 |
| 03 | `sources-sinks` | 소스·싱크 지도 | 주기·양·조건, 순증감, 폐쇄 루프 Mermaid |
| 04 | `exchange-pricing` | 교환과 가격 | 환율, 가격 앵커, 할인, 상·하한, 반올림 |
| 05 | `economy-progression` | 성장과 소비 단계 | 구간별 수요, 해금, 저축·소비 목표 |
| 06 | `monetization` | 상품·과금 경계 | 상품 역할, 가치 구성, 구매 제한, 공정성 |
| 07 | `abuse-prevention` | 인플레이션·악용 방지 | 파밍, 다계정, 환불, 교환 루프, 대응 |
| 08 | `economy-telemetry` | 지표와 운영 레버 | 잔액·유입·소비·가격 지표, 알람, 롤백 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `economy-objectives`, `currencies`, `sources-sinks`, `economy-telemetry`

| facet | 추가 section ID |
|---|---|
| `pricing` | `exchange-pricing` |
| `progression` | `economy-progression` |
| `rewards` | `economy-progression` |
| `monetization` | `monetization` |
| `exceptions` | `abuse-prevention` |
| `insufficient-resource` | `abuse-prevention` |
| `telemetry` | `economy-telemetry` |

dependency:

- `monetization` → `exchange-pricing`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 전투 공식 상세, 화면 배치, 전체 운영 일정과 시장 전략은 넣지 않는다.
- 소스·싱크 Mermaid 1개가 필수다.
- 실제 또는 명시된 예시값이 있으면 Chart.js를 권장한다.

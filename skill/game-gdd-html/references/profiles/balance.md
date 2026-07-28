# Balance Design (`balance`)

목표 경험을 만드는 변수, 공식, 곡선과 검증 가능한 튜닝 절차를 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `balance-objectives` | 목표와 원칙 | 목표 체감, 대상 구간, 허용 편차, 금지 결과 |
| 02 | `variables` | 변수와 단위 | 심볼, 의미, 단위, 기본값, 범위, 데이터 출처 |
| 03 | `formulas` | 공식과 계산 순서 | 수식, 반올림, 캡, 우선순위, 예외 |
| 04 | `curves` | 목표 곡선 | 성장·난이도·효율 곡선과 구간별 의도 |
| 05 | `scenarios` | 기준 시나리오 | 최소·기준·최대 케이스와 기대 결과 |
| 06 | `simulation` | 시뮬레이션 결과 | 입력 세트, 반복 수, 분포, 민감도 |
| 07 | `tuning` | 조정 레버와 절차 | 변경 가능 값, 영향 범위, 롤백 기준 |
| 08 | `balance-validation` | 검증과 텔레메트리 | 테스트 케이스, 표본, 지표, 합격 범위 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `balance-objectives`, `variables`, `formulas`, `balance-validation`

| facet | 추가 section ID |
|---|---|
| `curves` | `curves` |
| `progression` | `curves` |
| `difficulty` | `curves` |
| `scenarios` | `scenarios` |
| `simulation` | `scenarios`, `simulation` |
| `tuning` | `tuning` |
| `telemetry` | `balance-validation` |

dependency:

- `simulation` → `scenarios`, `curves`
- `tuning` → `curves`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 화면 명세, 세계관, 제작 일정, BM 전략은 넣지 않는다.
- 근거 있는 실제·목표·제안값을 보여 주는 Chart.js 1개가 필수다.
- 흐름 관계가 없으면 Mermaid를 억지로 넣지 않는다.

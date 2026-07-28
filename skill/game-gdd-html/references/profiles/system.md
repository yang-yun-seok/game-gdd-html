# System Specification (`system`)

특정 기능의 사용자 경험, 게임 규칙, 상태와 기획 데이터를 개발·QA 협업에서 같은 의미로 해석하고 검증할 수 있게 작성한다. 기획서는 관찰 가능한 결과와 수용 기준을 결정하며 구현 구조는 확정하지 않는다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `definition` | 정의와 범위 | 목적, 사용자 가치, 인·아웃 스코프, 용어 |
| 02 | `flow` | 사용자·상태 흐름 | 진입, 성공, 실패, 취소, 재진입 Mermaid |
| 03 | `rules` | 상세 규칙 | 발동 조건, 입력 의미, 우선순위, 상태 변화, 관찰 결과 |
| 04 | `data` | 상태와 기획 데이터 | 상태 전이, 데이터 항목 의미, 단위·기본값·범위, 갱신·복구 조건 |
| 05 | `exceptions` | 예외와 악용 방지 | 조건→시스템 반응→사용자 피드백 5개 이상 |
| 06 | `balance` | 파라미터와 조정 | 공식, 변수 의미, 기본값, 범위, 상·하한, 조정 기준 |
| 07 | `qa` | QA·텔레메트리 | 수용 조건, 테스트 케이스, 관찰 이벤트, 성공·실패 기준 |

## 권장 표

- 규칙: `Rule ID | 발동 조건 | 입력 의미 | 우선순위 | 상태 변화 | 사용자 관찰 결과 | 실패 피드백`
- 데이터: `Data ID | 의미 | 단위 | 기본값 | 허용 범위 | 갱신·복구 조건 | 관련 상태 | 책임 kind`

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `definition`, `flow`, `rules`, `qa`

| facet | 추가 section ID |
|---|---|
| `data` | `data` |
| `states` | `data` |
| `exceptions` | `exceptions` |
| `insufficient-resource` | `exceptions` |
| `result-feedback` | `exceptions` |
| `formulas` | `balance` |
| `curves` | `balance` |
| `simulation` | `balance` |
| `scenarios` | `balance` |
| `tuning` | `balance` |
| `economy-loop` | `balance` |
| `telemetry` | `qa` |

dependency:

- `balance` → `data`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 화면 배치·컴포넌트는 쓰지 않고 `Screen ID`와 필요한 피드백만 UI 문서로 넘긴다.
- `balance`는 시스템이 소비하는 파라미터 계약까지만 다룬다. 곡선·시뮬레이션·다구간 튜닝은 밸런스 문서로 넘긴다.
- 클라이언트·서버 분담, API, 저장소, 물리 스키마·타입, 트랜잭션·멱등·롤백 방식, 프레임·틱 처리 순서는 이 기획서가 확정하지 않는다. 필요한 사용자 결과, 상태 보존 조건, 일관성·복구 기준만 적고 구현 방식은 `개발 협의 조건`으로 넘긴다.
- 시장·사업, 콘텐츠 카탈로그, 제작 로드맵은 넣지 않는다.
- 사용자 행동 또는 게임 상태 흐름 Mermaid 1개가 필수다. 다이어그램은 역할별 관찰 결과를 보여 주되 런타임 배치나 내부 처리 순서를 설계하지 않는다.

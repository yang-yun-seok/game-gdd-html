# UI / UX Specification (`ui-ux`)

화면 구조, 상호작용, 상태, 접근성과 개발 핸드오프를 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `ui-objectives` | UX 목표와 범위 | 사용자·상황·핵심 과업, 성공 기준, 제외 화면 |
| 02 | `information-architecture` | 정보 구조 | 메뉴 계층, 정보 우선순위, 전역 탐색 규칙 |
| 03 | `user-flow` | 화면 흐름 | 시작·성공·취소·실패·재진입 Mermaid |
| 04 | `screen-specs` | 화면별 명세 | Screen ID, 목적, 진입, 요소, 액션, 종료 조건 |
| 05 | `interaction-rules` | 조작과 피드백 | 입력, 포커스, 전환, 확인, 되돌리기, 피드백 |
| 06 | `ui-states` | 상태와 예외 화면 | 기본·로딩·빈·오류·잠김·오프라인 상태 |
| 07 | `accessibility` | 접근성·현지화 | 키보드·패드·터치, 색·텍스트·자막, 확장성 |
| 08 | `handoff-qa` | 에셋·개발 핸드오프 | 컴포넌트 상태, 문자열, 이벤트, 수용 조건 |

## 권장 표

`Screen ID | 진입 조건 | 목적 | 요소·데이터 | 사용자 액션 | 시스템 반응 | 종료·다음 화면`

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `ui-objectives`, `user-flow`, `screen-specs`, `handoff-qa`

| facet | 추가 section ID |
|---|---|
| `navigation` | `information-architecture` |
| `flow` | `user-flow` |
| `batch-action` | `screen-specs`, `interaction-rules` |
| `interaction` | `interaction-rules` |
| `result-feedback` | `interaction-rules`, `ui-states` |
| `states` | `ui-states` |
| `exceptions` | `ui-states` |
| `insufficient-resource` | `ui-states` |
| `accessibility` | `accessibility` |
| `mobile-touch` | `interaction-rules`, `accessibility` |
| `data` | `handoff-qa` |
| `telemetry` | `handoff-qa` |

dependency:

- `interaction-rules` → `screen-specs`
- `ui-states` → `screen-specs`
- `accessibility` → `interaction-rules`

dependency는 전이적으로 추가한다. 예를 들어 `accessibility`를 선택하면 `interaction-rules`와 그 dependency인 `screen-specs`도 포함한다. core 섹션은 제외할 수 없으며, 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 시스템 공식과 데이터 소유권은 재작성하지 않고 `Rule ID`·`Field`를 참조한다.
- 경제 튜닝, 콘텐츠 카탈로그, 시장 분석은 넣지 않는다.
- 화면 흐름 Mermaid 1개가 필수다. 수치 비교가 실제 UX 결정에 필요할 때만 Chart.js를 쓴다.

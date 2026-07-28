# Game Production Plan (`production`)

개발 범위, 일정, 담당, 의존성, 완료 조건을 실행 가능한 제작 계획으로 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `production-objectives` | 제작 목표와 기준 | 문서 목적, 대상 단계, 승인 독자, 성공 기준 |
| 02 | `scope-roadmap` | 범위와 로드맵 | 포함·제외, 단계별 산출물, 변경 기준 |
| 03 | `milestones` | 마일스톤 | 날짜·기간, 진입·완료 조건, 승인 게이트 |
| 04 | `work-breakdown` | 작업 분해 | 작업 ID, 우선순위, 예상 공수, 산출물 |
| 05 | `ownership` | 담당과 협업 | 책임자, 검토자, 협업팀, 의사결정 권한 |
| 06 | `dependencies` | 의존성과 블로커 | 선행 작업, 외부 입력, 차단 조건, 해소 계획 |
| 07 | `risks` | 일정·품질 리스크 | 발생 가능성, 영향, 완화책, 대체안 |
| 08 | `acceptance` | 완료·인수 조건 | 검수 항목, QA 조건, 승인자, 인계 자료 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 dependency만 더해 `core + triggered + dependency` 범위로 작성한다.

- `core_ids`: `production-objectives`, `scope-roadmap`, `milestones`, `ownership`, `acceptance`

| facet | 추가 section ID |
|---|---|
| `production` | `work-breakdown` |
| `dependencies` | `dependencies` |
| `risks` | `risks` |
| `handoff` | `dependencies`, `ownership` |
| `qa` | `acceptance` |
| `updates` | `scope-roadmap`, `milestones`, `work-breakdown`, `acceptance` |
| `operations` | `milestones`, `ownership` |
| `launch` | `milestones`, `risks` |

dependency:

- `work-breakdown` → `scope-roadmap`
- `dependencies` → `work-breakdown`
- `risks` → `milestones`

core 섹션은 제외할 수 없다. 명시 포함 또는 dependency와 제외가 충돌하면 질문한다. 시스템·UI·콘텐츠 규칙 자체는 이 문서에 복제하지 않고 해당 문서 ID와 승인 상태만 연결한다.

## 경계와 시각화

- 실제 기능 규칙, 화면 상세, 수치 밸런스는 소유 문서로 넘긴다.
- 마일스톤과 의존성 흐름 Mermaid 1개가 필수다.
- 근거 없는 정밀 일정이나 공수를 확정값처럼 쓰지 않는다.

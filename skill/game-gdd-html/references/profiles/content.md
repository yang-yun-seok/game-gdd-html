# Content Design (`content`)

콘텐츠 단위의 구조, 반복·해금·보상, 난이도와 제작 공급 방식을 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `content-definition` | 콘텐츠 정의와 범위 | 콘텐츠 단위, 대상 플레이어, 인·아웃 스코프 |
| 02 | `content-loop` | 참여·완료·반복 루프 | 진입, 준비, 플레이, 완료, 재도전 흐름 |
| 03 | `content-structure` | 구조와 카탈로그 | 타입, 단계, 해금, 선후행, 변형 규칙 |
| 04 | `content-rules` | 콘텐츠 규칙 | 입장, 성공·실패, 제한, 매칭, 재진입 |
| 05 | `rewards-progression` | 보상과 성장 연결 | 보상 티어, 최초·반복 보상, 성장 연결 |
| 06 | `difficulty-pacing` | 난이도와 페이싱 | 단계별 목표, 학습·숙련, 실패 비용 |
| 07 | `content-production` | 제작 템플릿과 공급 | 제작 단위, 데이터 템플릿, 에셋, 작업량 |
| 08 | `content-qa` | QA와 성과 측정 | 수용 조건, 플레이테스트, 완료·이탈 지표 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `content-definition`, `content-loop`, `content-structure`, `content-qa`

| facet | 추가 section ID |
|---|---|
| `rules` | `content-rules` |
| `exceptions` | `content-rules` |
| `rewards` | `rewards-progression` |
| `progression` | `rewards-progression` |
| `economy-loop` | `rewards-progression` |
| `difficulty` | `difficulty-pacing` |
| `curves` | `difficulty-pacing` |
| `production` | `content-production` |
| `telemetry` | `content-qa` |

dependency:

- `difficulty-pacing` → `content-structure`
- `rewards-progression` → `content-structure`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 플레이어가 관찰하는 콘텐츠 상태와 전이 조건만 정의하며, 엔진 수준 구현 구조는 `개발 협의`로 남긴다.
- 화면별 UI, 게임 전체 경제, 라이브 캘린더는 넣지 않는다.
- 콘텐츠 루프 Mermaid 1개가 필수다.

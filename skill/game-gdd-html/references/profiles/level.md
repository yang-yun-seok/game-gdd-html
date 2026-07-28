# Level Design (`level`)

레벨·스테이지·맵의 공간 동선, 조우, 페이싱과 재도전 구조를 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `level-objectives` | 목표 경험과 제약 | 학습·도전 목표, 플레이 시간, 공간·기술 제약 |
| 02 | `player-flow` | 플레이어 동선 | 시작, 분기, 목표, 실패, 복귀 Mermaid |
| 03 | `layout` | 공간 구조 | 구역, 연결, 크기, 시야, 랜드마크, 이동 수치 |
| 04 | `encounters` | 조우 배치 | 적·퍼즐·자원·휴식 배치와 트리거 |
| 05 | `pacing` | 긴장과 휴식 | 구간별 시간, 강도, 학습, 변주 |
| 06 | `checkpoints` | 체크포인트와 재도전 | 저장, 리스폰, 손실, 숏컷, 이탈 복귀 |
| 07 | `level-rewards` | 탐험·완료 보상 | 필수·선택 보상, 발견, 재방문 동기 |
| 08 | `playtest` | 플레이테스트 계획 | 경로, 사망, 시간, 길찾기 지표와 합격 기준 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `level-objectives`, `player-flow`, `layout`, `playtest`

| facet | 추가 section ID |
|---|---|
| `encounters` | `encounters` |
| `difficulty` | `pacing` |
| `flow` | `pacing` |
| `checkpoints` | `checkpoints` |
| `exceptions` | `checkpoints` |
| `rewards` | `level-rewards` |
| `economy-loop` | `level-rewards` |
| `telemetry` | `playtest` |

dependency:

- `encounters` → `layout`
- `checkpoints` → `player-flow`
- `pacing` → `encounters`

dependency는 전이적으로 추가한다. 예를 들어 `difficulty` 또는 `flow`가 `pacing`을 선택하면 `encounters`와 그 dependency인 `layout`도 포함한다. core 섹션은 제외할 수 없으며, 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 게임 전체 성장·경제, 화면별 UI, 전체 서사는 넣지 않는다.
- 동선 Mermaid 1개가 필수다.
- 실제 공간 도면이 필요하면 HTML의 한계를 밝히고 별도 레벨 에디터 산출물을 참조한다.

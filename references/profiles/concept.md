# Concept Document (`concept`)

아이디어 승인, 피치, 프리프로덕션 검증에 사용한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `vision` | 콘셉트와 플레이어 약속 | 한 줄 피치, 판타지, 필러, 차별점 |
| 02 | `player-experience` | 타깃 경험과 코어 루프 | 페르소나, 5분 경험, 코어 루프 |
| 03 | `market` | 포지셔닝 가설 | 비교작, 차별 축, 시장 가설 |
| 04 | `scope` | 프로토타입·MVP 범위 | 핵심 기능, 제외 기능, 팀·기간 가정 |
| 05 | `risks` | 가설과 검증 계획 | 프로토타입, 성공·중단 기준 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `vision`, `player-experience`, `scope`, `risks`

| facet | 추가 section ID |
|---|---|
| `research` | `market` |
| `positioning` | `market` |
| `launch` | `market` |

- dependency: 없음
- core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다.
- 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 상세 데이터 스키마, 화면별 UI, 운영 런북, 근거 없는 매출 차트는 넣지 않는다.
- 코어 루프 Mermaid 1개가 필수다.
- 사업 수치가 없으면 수익화는 가설과 검증 방법으로 적는다.

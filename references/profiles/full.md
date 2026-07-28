# Full GDD (`full`)

전체·통합·마스터 GDD를 명시적으로 요청한 경우에만 사용한다. 상세 명세의 복사본이 아니라 하위 문서의 의사결정 지도다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `vision` | 비전과 디자인 필러 | 한 줄 콘셉트, 플레이어 약속, 필러 3~5개, 금지 원칙 |
| 02 | `player-experience` | 타깃과 플레이 경험 | 페르소나, 세션 맥락, 코어·메타 루프 |
| 03 | `market` | 포지셔닝 | 비교축, 차별점, 제품 형태; 필요할 때만 포함 |
| 04 | `systems` | 시스템 지도 | 핵심 시스템의 책임과 의존성, 승패·실패 규칙 |
| 05 | `content-progression` | 콘텐츠와 성장 | 성장축, 해금, 난이도, 공급 템포, 엔드게임 |
| 06 | `ux-flow` | 주요 사용자 흐름 | 핵심 화면과 진입·완료·취소·복귀 흐름 |
| 07 | `economy-balance` | 경제·보상·밸런스 요약 | 핵심 소스·싱크, 목표 곡선, 조정 레버 |
| 08 | `live-data` | 라이브·데이터 요약 | KPI, 이벤트, 콘텐츠 주기; 필요할 때만 포함 |
| 09 | `production` | 제작 범위와 로드맵 | MVP, 우선순위, 의존성, 마일스톤, 제외 범위 |
| 10 | `risks` | 리스크와 검증 | 리스크·신호·완화책, 플레이테스트, 결정 로그 |

필수 ID는 `market`, `live-data`를 제외한 8개다.

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `vision`, `player-experience`, `systems`, `content-progression`, `ux-flow`, `economy-balance`, `production`, `risks`

| facet | 추가 section ID |
|---|---|
| `research` | `market` |
| `positioning` | `market` |
| `operations` | `live-data` |
| `telemetry` | `live-data` |

- dependency: 없음
- core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다.
- 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 화면별 요소, 규칙별 상세 데이터, 전체 수치표는 별도 프로필 문서로 넘긴다.
- Mermaid 1개는 필수이며 시스템 관계를 포함한 2개를 권장한다.
- 근거 있는 수치 모델이 있으면 Chart.js를 권장한다.

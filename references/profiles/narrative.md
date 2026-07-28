# Narrative Design (`narrative`)

세계, 캐릭터, 플롯·퀘스트·대사와 상태 정합성을 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `narrative-objectives` | 서사 목표와 톤 | 주제, 감정 곡선, 대상, 금지 원칙 |
| 02 | `world` | 세계관과 규칙 | 시대·공간, 세력, 세계 규칙, 용어 |
| 03 | `characters` | 캐릭터와 관계 | 욕망, 갈등, 변화, 관계, 플레이 역할 |
| 04 | `story-structure` | 플롯과 분기 | 막·챕터·비트, 분기·합류 Mermaid |
| 05 | `quests` | 퀘스트 구조 | Quest ID, 조건, 목표, 단계, 결과, 실패 |
| 06 | `dialogue` | 대사와 선택 | 화자, 맥락, 선택지, 조건, 톤, 현지화 |
| 07 | `narrative-delivery` | 전달 방식 | 컷신, 환경, UI, 보이스, 스킵·재생 규칙 |
| 08 | `continuity` | 정합성과 검수 | 시간선, 상태 플래그, 금칙, 검수 체크 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `narrative-objectives`, `story-structure`, `continuity`

| facet | 추가 section ID |
|---|---|
| `world` | `world` |
| `characters` | `characters` |
| `quests` | `quests` |
| `dialogue` | `dialogue` |
| `delivery` | `narrative-delivery` |
| `flow` | `story-structure` |

dependency:

- `quests` → `story-structure`
- `dialogue` → `characters`
- `narrative-delivery` → `story-structure`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 전투 공식, 경제 튜닝, 픽셀 UI, 전체 아트 바이블은 넣지 않는다.
- 플롯 또는 퀘스트 분기 Mermaid 1개가 필수다.
- 시스템 보상 공식은 `Reward ID`로 참조한다.

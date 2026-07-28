# 2단계 문서 라우팅

## 목차

1. 프로필과 kind 2단계 라우팅
2. 프로필 파일 선택
3. kind 계약 선택
4. 복수 문서 요청
5. 입력 정리와 질문
6. 정보 상태
7. 내부 커버리지와 문서 협업
8. 공통 작성 규칙

## 1. 프로필과 kind 2단계 라우팅

먼저 게임의 주제가 아니라 사용자가 요청한 **산출물의 종류(kind)**를 판별하고, 그 kind가
속한 **broad profile**을 선택한다. `full`은 기본값이 아니다.

자연어는 먼저 `scripts/interpret_request.py`로 GDDQL과 후보 근거로 정규화한다. 명시 표현이 없거나 경계가 남을 때만 의미 라우팅 프롬프트로 보완하며, 직접 입력된 GDDQL의 구문 오류를 자연어로 재해석하지 않는다.
사용자는 kind ID나 GDDQL을 배울 필요가 없으며 자연어 요청이 기본이다.

```text
자연어/GDDQL
  → kind 후보와 명시 문서명 판별
  → kind 계약에서 broad profile 도출
  → 문서별 default facet + 요청 facet
  → 문서별 section plan
  → kind마다 독립 HTML
```

### 판별 우선순위

1. 출시된 게임을 조사해 구조를 복원하는 역분석이면 `game-reverse-gdd`를 우선한다.
2. 사용자가 명시한 41개 문서 유형이 주제명보다 우선한다. 한국어 대표명과 alias를 canonical kind로 정규화한다.
3. kind가 정해지면 `kind_contracts.py`의 `profile`을 사용한다. 주제 키워드로 다른 프로필을 덮어쓰지 않는다.
4. `전체`, `통합`, `마스터 GDD`가 명시된 경우에만 `master-gdd`/`full`을 선택한다.
5. 구체 kind 없이 `시스템 기획서`, `UI·UX 문서`처럼 broad 산출물만 요청하면 `kind: null`인 일반 프로필 문서를 허용한다. 이것이 기존 호환 경로다.
6. 문서 유형이 없으면 요청 동사, 독자, 필요한 의사결정으로 kind를 추론한다. 충분한 근거가 없으면 broad profile까지만 선택하거나 한 질문으로 확인한다.
7. `게임 기획서`라고만 하면 `full`이나 특정 kind로 추정하지 않는다.

예:

- `강화 시스템 UI 기획서` → `ui-spec` → `ui-ux`; 주제는 제작·강화
- `제작·강화 시스템 기획서` → `crafting-enhancement-system` → `system`
- `전투 밸런스 기획서` → `combat-balance` → `balance`
- `던전 기획서` → `dungeon-design` → `level`
- `게임 경제 기획서` → `game-economy` → `economy`
- `개발 일정 기획서` → `development-plan` → `production`
- `업데이트 명세서` → `update-spec` → `production`
- `게임 전체 통합 GDD` → `master-gdd` → `full`
- `길드 시스템 기획서` → 등록된 세부 kind가 없으므로 일반 `system` 문서 또는 확인 질문

### 경계 판별

- 명시 kind가 있으면 아래 의미 경계보다 명시 문서명이 우선한다.
- `content` 대 `system`: 종류·구조·공급·해금·보상은 `content`, 한 기능의 처리 규칙·상태·데이터·예외는 `system`
- `balance` 대 `economy`: 전투·성장·난이도의 수치 관계는 `balance`, 재화의 생성·소비·교환·가격은 `economy`
- `content` 대 `live-ops`: 콘텐츠 자체 설계는 `content`, 캘린더·세그먼트·배포·롤백은 `live-ops`
- `production` 대 `live-ops`: 작업·마일스톤·의존성·릴리스 변경 명세는 `production`, 시즌·이벤트 캘린더와 운영 판단은 `live-ops`
- `economy` 대 `business`: 게임 안 가치 순환은 `economy`, 시장·상품·매출·출시 전략은 `business`
- 데이터·규칙·로그·예외 협업 문서는 각각 `data-table-spec`, `logic-rule-spec`, `logging-spec`, `exception-spec` kind이며 broad profile은 `system`이다.

## 2. 프로필 파일 선택

프로필을 선택한 뒤에는 **해당 프로필 파일만** 읽는다. 복수 문서를 만들 때만 선택된 프로필 파일을 각각 읽는다.

| 프로필 | 대표 요청 표현 | 프로필 계약 파일 |
|---|---|---|
| `full` | 전체, 통합, 마스터 GDD | `profiles/full.md` |
| `concept` | 컨셉·콘셉트, 제안서, 피치, 아이디어 검토 | `profiles/concept.md` |
| `system` | 시스템 기획서, 기능 명세, 규칙·상태·데이터 | `profiles/system.md` |
| `ui-ux` | UI 기획서, UX 설계, 화면 기획서, HUD·메뉴 | `profiles/ui-ux.md` |
| `content` | 콘텐츠 기획서, 모드·던전·미션 구조 | `profiles/content.md` |
| `balance` | 밸런스 기획서, 수치 기획, 공식·곡선·튜닝 | `profiles/balance.md` |
| `economy` | 경제·재화·보상 기획서, 소스·싱크, 가격 | `profiles/economy.md` |
| `level` | 레벨·스테이지·맵·던전 기획서, 조우 배치 | `profiles/level.md` |
| `narrative` | 세계관·시나리오·퀘스트·대사 기획서 | `profiles/narrative.md` |
| `live-ops` | 라이브서비스·운영·이벤트 기획서 | `profiles/live-ops.md` |
| `business` | 사업 기획서, 시장성, BM, 매출·출시 전략 | `profiles/business.md` |
| `production` | 개발 일정, 마일스톤, 의존성, 업데이트 명세 | `profiles/production.md` |

프로필 파일의 canonical section ID, 완료 조건, 기본 제외 범위, 시각화 조건을 그대로 적용한다. 단, allowed section 전체를 매번 작성하지 않는다. 각 파일의 `자동 범위 조합`에 따라 `core_ids + facet-triggered section + dependency`만 선택하고, 선택 결과를 `document.scope`에 고정한다.

kind 문서라면 broad profile 파일과 해당 category reference 파일만 읽는다. kind가 없는 일반
프로필 문서는 기존처럼 프로필 파일만 읽는다.

## 3. kind 계약 선택

canonical kind와 계약은 `scripts/kind_contracts.py`가 단일 소스다. 각 계약은 다음 필드를 가진다.

| 필드 | 역할 |
|---|---|
| `label` | 표지와 사용자 전달에 쓰는 한국어 문서명. canonical 코드는 노출하지 않음 |
| `category` | 9개 실무 문서군 중 하나 |
| `profile` | canonical section과 시각화 정책을 제공하는 broad profile |
| `aliases` | 자연어에서 kind를 찾기 위한 충돌 최소화 별칭 |
| `default_facets` | 해당 kind가 기본으로 발동해야 하는 profile facet |
| `required_outputs` | 이 문서가 소유·참조·N/A로 반드시 처리할 결과 계약 |
| `default_excludes` | 이 kind에서 기본적으로 다루지 않는 범위 |
| `handoffs` | 상세를 복제하지 않고 넘길 downstream kind ID |
| `reference` | category 문서의 kind별 질문·산출물·완료 조건 |

category별 상세 계약:

| category | 참조 파일 |
|---|---|
| 프로젝트 전체 기획 | `kinds/project.md` |
| 시스템 기획 | `kinds/system.md` |
| 전투 기획 | `kinds/combat.md` |
| 레벨·콘텐츠 기획 | `kinds/level-content.md` |
| 경제·밸런스 기획 | `kinds/economy-balance.md` |
| UI·UX 기획 | `kinds/ui-ux.md` |
| 세계관·스토리 기획 | `kinds/narrative.md` |
| 데이터·기술 협업 기획 | `kinds/data-tech.md` |
| 운영·마케팅 기획 | `kinds/operations-marketing.md` |

범위는 `kind.default_facets + 사용자 facet`을 프로필 계약에 적용해 계산한다.
kind 기본 facet은 선택 사항이 아니라 최소 범위다. 사용자 제외가 기본 facet, core section 또는
dependency와 충돌하면 본문을 쓰기 전에 질문한다. `required_outputs`는 section ID가 아니므로
필요한 표·규칙·참조로 충족하고, `handoffs`는 다른 kind의 상세를 현재 문서에 복사하지 않게 한다.

kind가 선택됐으면 렌더러 JSON에 `document.kind`를 기록하고 HTML에 `gdd-kind`를 남긴다.
kind가 없는 일반 profile plan에는 두 값을 넣지 않는다.

## 4. 복수 문서 요청

복수 영역을 한 통합본으로 조용히 합치지 않는다.

- `filter.documents`와 `scope.document_plans`의 각 항목마다 독립 HTML을 생성한다.
- 사용자가 `각각`, `별도`라고 하면 kind마다 독립 HTML을 생성한다.
- 분리 여부가 불명확해도 기본은 kind별 독립 HTML이다. 결과 수와 일정이 크게 달라질 때만 한 번 확인한다.
- `ui-spec`과 `wireframe`처럼 broad profile이 같아도 별도 문서다. 같은 프로필이라는 이유로 section plan이나 본문을 합치지 않는다.
- 공통 용어와 가정은 공유하되 본문을 복제하지 않는다.
- 문서 간 연결은 `System Rule ID`, `Screen ID`, `Content ID`, `Metric ID`처럼 안정적인 식별자로 참조한다.
- kind 목록에 합본을 요청하면 독립 HTML은 유지하고 색인·전달 패키지만 묶는다. 여러 kind 계약을 하나의 `document.kind`로 위장하지 않는다.
- `KIND`가 없는 기존 프로필 단위 요청에서만 사용자가 명시한 하나의 합본 본문을 허용한다. 선택된 영역만 묶고 `full`의 시장·제작·경제 섹션을 자동 추가하지 않는다.
- 전체 GDD와 상세 문서를 함께 요청하면 `full`은 요약·색인 역할을 하고 상세 프로필 HTML을 별도 생성한다.

권장 파일명:

```text
<project>_<kind>_GDD_<YYYYMMDD>.html
```

일반 프로필 문서는 기존 `<project>_<profile>_GDD_<YYYYMMDD>.html` 형식을 유지한다.

## 5. 입력 정리와 질문

이미 제공된 답은 다시 묻지 않는다. 한 번에 1~2개의 중요한 질문만 한다.

### 공통 질문 순서

1. **문서 종류**: 41개 kind 중 어느 산출물인가, 아니면 broad profile 일반 문서인가?
2. **문서 영역**: kind가 없을 때 이번 산출물은 어떤 프로필인가?
3. **결과의 용도**: 누가 무엇을 결정하거나 구현하기 위해 읽는가?
4. **대상 범위**: 어떤 기능·화면·콘텐츠·기간을 다루며 무엇을 제외하는가?
5. **목표 경험**: 플레이어에게 어떤 행동과 감정을 만들려는가?
6. **제약**: 플랫폼, 입력, 팀, 일정, 기술, 등급, 지역 제약은 무엇인가?
7. **완료 기준**: 승인, 구현, 테스트 중 어디까지 가능해야 하는가?

### 좋은 질문

- "강화 시스템의 규칙 명세와 강화 화면 UI 명세 중 어느 문서가 먼저 필요한가요?"
- "이 UI 문서가 와이어프레임 검토용인가요, 개발 핸드오프용인가요?"
- "밸런스 목표가 초반 이탈 감소와 엔드게임 체류 중 어느 쪽에 더 가깝나요?"
- "이벤트 자체의 콘텐츠 규칙과 월간 운영 캘린더 중 어느 범위를 다루나요?"

### 피할 질문

- 이미 파일이나 메시지에 답이 있는 질문
- 영역 선택 전에 전체 게임 정보를 한꺼번에 요구하는 질문
- 결과에 거의 영향을 주지 않는 취향 질문
- 안전한 가정으로 처리할 수 있는 파일명이나 날짜 질문

## 6. 정보 상태

모든 중요한 항목을 다음 상태 중 하나로 분류한다.

| 상태 | 의미 | 문서 표기 |
|---|---|---|
| 확정 | 사용자가 승인했거나 원문이 명시함 | `확정` |
| 가정 | 작업을 진행하기 위한 합리적 전제 | `가정` |
| 제안 | 설계자가 권고하는 선택 | `제안` |
| 미정 | 추가 결정 또는 검증이 필요함 | `검토 필요` |

가정을 확정 문장처럼 쓰지 않는다. 미정 항목에는 가능하면 담당자, 결정 기준, 결정 시점을 붙인다.

## 7. 내부 커버리지와 문서 협업

모든 kind의 `required_outputs`에는 다음 공통 차원이 들어간다.

```text
planning-intent
application-scope
operating-rules
schedule-and-ownership
data-contract
ui-touchpoints
exception-policy
telemetry-plan
completion-criteria
```

이 목록은 생성·검토 단계의 누락 방지 계약이다. 모든 문서가 일정표·데이터 스키마·UI·로그를
반복 작성하라는 뜻이 아니다. 각 차원은 내부 검토에서 다음 중 하나로 처리한다.

- `owned`: 현재 kind가 결정을 소유하고 필요한 깊이로 직접 작성한다.
- `reference`: 다른 kind가 소유하므로 별도 대상 열에 문서 ID, Rule ID, Screen ID, Table ID, Event ID 등으로 연결한다.
- `N/A`: 이번 범위와 무관한 이유를 별도 사유 열에 한 문장으로 기록한다.

`owned`, `reference`, `N/A`, required output 이름, canonical kind ID, handoff 계약은 내부
검토표와 JSON 메타데이터에만 둔다. 표지·본문·목차·부록·결정 로그에는 출력하지 않는다.
9개 차원을 나열한 전용 커버리지 표나 부록도 만들지 않는다.

예를 들어 제작·강화 시스템 문서는 자원 차감과 성공·실패 뒤에 플레이어가 확인할 상태를
본문 규칙으로 작성한다. 화면·데이터·일정의 상세는 복제하지 않고 내부 검토에서 각 소유
문서와 연결한다. 구현 판단은 필요한 품질조건만 `개발 협의`로 남긴다.

사용자가 문서 간 협업 내용을 명시적으로 요청한 경우에만 독자 친화적인 한국어 표를 추가한다.

| 관련 문서 | 필요한 결정 | 전달 자료 | 완료 기준 | 담당·시점 |
|---|---|---|---|---|

이 표에도 canonical kind ID, 내부 상태명, handoff 용어를 넣지 않는다. 실제 문서명과 업무
내용만 쓴다. 협업 요청이 없으면 본문 흐름에 필요한 관련 문서명만 짧게 적고 별도 표를 만들지 않는다.

선택 프로필의 의사결정에 필요하고 사용자가 요청한 경우에만 다음 부록을 추가한다. 부록 섹션 ID는 `appendix-`로 시작해 다른 프로필의 표준 ID와 구분한다.

- 경쟁작 비교와 시장 근거
- 기술 제약과 플랫폼 인증
- 접근성·현지화·연령등급
- 아트·오디오 방향
- 커뮤니티·UGC·소셜 안전
- 데이터 사전과 분석 이벤트

외부 사실을 포함하면 `research-and-evidence.md`를 적용한다.

## 8. 공통 작성 규칙

각 섹션은 가능한 한 다음 순서로 구성한다.

1. **결론**: 이 섹션이 확정하는 내용을 2~4문장으로 요약한다.
2. **규칙 또는 구조**: 표, 다이어그램, 공식으로 관계를 명시한다.
3. **설계 의도**: 선택이 목표 경험과 성공 기준에 어떻게 연결되는지 설명한다.
4. **예외와 트레이드오프**: 실패, 악용, 비용, 대안을 적는다.
5. **검증**: 수용 기준, 계측, 플레이테스트 방법을 적는다.
6. **관련 문서와 미결정**: 필요한 문서 참조, 가정, 검토 필요 항목을 결정 로그에 연결한다.

문서 전체에서 동일 개념에 하나의 용어만 사용한다. 약어는 첫 등장에 풀어 쓴다.

# 렌더러 입력 스키마

## 목차

1. 실행
2. 해석 계획과 문서 분리
3. 최상위 렌더러 구조
4. 공통 규칙
5. 블록 타입
6. 최소 예시
7. 차트와 Mermaid

## 1. 실행

UTF-8 JSON을 작성한 뒤 렌더러에 전달한다.

```bash
python "$SKILL_DIR/scripts/render_gdd.py" input.json -o output.html
```

`-o`를 생략하면 kind가 있는 신규 문서는 현재 디렉토리에
`<title>_<kind>_GDD_<date>.html`을 생성한다. kind 없이 프로필만 있는 일반 문서는
기존 `<title>_<profile>_GDD_<date>.html`, 프로필도 없는 레거시 입력은
`<title>_GDD_<date>.html` 형식을 유지한다.

kind 문서는 렌더 후 명시적으로 검증한다.

```bash
python "$SKILL_DIR/scripts/validate_gdd.py" output.html \
  --profile ui-ux --kind ui-spec --require-scope
```

`--kind`를 생략하면 HTML의 `gdd-kind`를 읽는다. kind와 HTML 메타데이터가 모두 없으면
기존 프로필 단위 검증 경로를 사용한다.

## 2. 해석 계획과 문서 분리

자연어 또는 GDDQL을 바로 렌더러 JSON으로 바꾸지 않는다. 먼저 2단계 라우팅 결과를 만든다.

```json
{
  "filter": {
    "selected_profiles": ["ui-ux"],
    "selected_kinds": ["ui-spec"],
    "selected_generic_profiles": [],
    "documents": [
      {
        "id": "ui-spec",
        "kind": "ui-spec",
        "label": "UI 기획서",
        "category": "ui-ux",
        "category_label": "UI·UX 기획",
        "profile": "ui-ux"
      }
    ]
  },
  "scope": {
    "document_plans": [
      {
        "id": "ui-spec",
        "kind": "ui-spec",
        "label": "UI 기획서",
        "category": "ui-ux",
        "category_label": "UI·UX 기획",
        "profile": "ui-ux",
        "reference": "references/kinds/ui-ux.md#ui-spec",
        "kind_default_facets": [
          "navigation",
          "flow",
          "interaction",
          "result-feedback",
          "states",
          "exceptions",
          "accessibility",
          "data",
          "telemetry"
        ],
        "requested_facets": [],
        "facets": [
          "navigation",
          "flow",
          "interaction",
          "result-feedback",
          "states",
          "exceptions",
          "accessibility",
          "data",
          "telemetry"
        ],
        "exclude_facets": [],
        "required_outputs": [
          "planning-intent",
          "application-scope",
          "operating-rules",
          "schedule-and-ownership",
          "data-contract",
          "ui-touchpoints",
          "exception-policy",
          "telemetry-plan",
          "completion-criteria",
          "screen-inventory",
          "menu-and-navigation-map",
          "screen-layout-spec",
          "component-and-popup-rules",
          "ui-state-matrix"
        ],
        "default_excludes": [
          "game-rules-and-calculations",
          "final-visual-art",
          "input-device-conflict-policy"
        ],
        "handoffs": [
          "wireframe",
          "data-table-spec",
          "exception-spec"
        ],
        "section_plan": {
          "profile": "ui-ux",
          "selected_sections": [
            "ui-objectives",
            "information-architecture",
            "user-flow",
            "screen-specs",
            "interaction-rules",
            "ui-states",
            "accessibility",
            "handoff-qa"
          ]
        }
      }
    ],
    "section_plans": {}
  }
}
```

- `filter.selected_kinds`는 canonical kind ID 배열이다. kind가 없는 일반 프로필 요청은 `[]`다.
- `filter.selected_generic_profiles`는 kind와 함께 또는 단독으로 생성할 일반 broad profile 문서 배열이다.
- `filter.documents`는 실제 생성할 파일 목록이다. 프로필이 같아도 kind가 다르면 항목을 합치지 않는다.
- `scope.document_plans`는 각 파일의 단일 소스다. `kind_default_facets`와 `requested_facets`를 추적하고, 현재 profile이 소유하는 유효 facet만 `facets`에 적용한다. 다른 profile의 요청 facet은 `section_plan.ignored_facets`와 handoff로 남긴다.
- `scope.section_plans`는 기존 소비자 호환용 인덱스다. 신규 작성기는 `document_plans[].section_plan`을 우선한다.
- 각 document plan을 별도의 렌더러 JSON으로 변환한다. 하나의 JSON에 서로 다른 kind 두 개를 넣지 않는다.
- kind를 판별하지 못했거나 사용자가 broad profile 문서만 요청한 경우 `kind: null`인 profile plan을 만들 수 있다. 이 경로는 기존 일반 프로필 문서 동작을 유지한다.

## 3. 최상위 렌더러 구조

렌더된 HTML에는 이 JSON 전체가 비실행 `application/json` 데이터(`gdd-source`)로 포함된다. 편집 준비 도구는 본문·원본 체크섬을 검사해 복원하며, 수동 변경이 감지되면 원문 대조를 요구한다. 내부 품질 검토·변경 계획은 이 JSON에 추가하지 않고 작업 폴더에 별도로 저장한다. 기존 JSON 스키마에 새 필수 필드는 없다.

```json
{
  "document": {
    "title": "프로젝트 아크라이트",
    "subtitle": "협동 탐사 중 필요한 화면 정보와 상호작용 규칙을 정의한다",
    "profile": "ui-ux",
    "kind": "ui-spec",
    "status": "검토 중",
    "version": "0.3",
    "date": "2026-07-27",
    "language": "ko",
    "confidentiality": "내부",
    "author": "게임 기획팀",
    "scope": {
      "mode": "filtered",
      "facets": [
        "navigation",
        "flow",
        "interaction",
        "result-feedback",
        "states",
        "exceptions",
        "accessibility",
        "data",
        "telemetry",
        "mobile-touch"
      ],
      "sections": [
        "ui-objectives",
        "information-architecture",
        "user-flow",
        "screen-specs",
        "interaction-rules",
        "ui-states",
        "accessibility",
        "handoff-qa"
      ]
    }
  },
  "project_meta": [
    {"label": "장르", "value": "협동 탐사 RPG"},
    {"label": "플랫폼", "value": "PC / Console"},
    {"label": "플레이", "value": "1~4인, 30분 세션"}
  ],
  "summary": "협동 탐사 중 팀 상태와 다음 행동을 빠르게 파악하도록 핵심 화면과 상호작용을 정의한다.",
  "pillars": [
    {
      "title": "행동보다 먼저 읽히는 상태",
      "text": "위험, 팀 상태, 다음 행동의 우선순위를 한 시선 흐름 안에서 전달한다.",
      "tag": "가독성"
    }
  ],
  "sections": [],
  "decisions": [
    {
      "status": "assumption",
      "title": "세션 목표 시간",
      "detail": "초기 목표를 30분으로 두고 플레이테스트에서 검증한다.",
      "owner": "게임 기획",
      "due": "버티컬 슬라이스"
    }
  ],
  "sources": [
    {
      "label": "공식 또는 1차 자료 제목",
      "url": "https://example.com",
      "accessed": "2026-07-27",
      "note": "비교 분석에 사용"
    }
  ],
  "footer_note": "프리프로덕션 의사결정용 초안"
}
```

### `document`

| 필드 | 필수 | 설명 |
|---|---|---|
| `title` | 예 | 문서와 프로젝트의 대표 제목 |
| `subtitle` | 예 | 대상 기능과 문서 목적만 담은 짧은 선언형. 문서명·canonical 코드·생성 과정은 넣지 않음 |
| `profile` | 신규 문서: 예 | 문서 영역. 지원값은 아래 표 참고 |
| `kind` | kind 문서: 예 | 세부 문서 종류의 canonical ID. 일반 프로필 문서는 생략 |
| `eyebrow` | 아니오 | 표지 상단의 선택적 보조 라벨. 문서명·canonical 코드·영문 대문자 장식 태그는 넣지 않음 |
| `status` | 예 | Draft, Review, Approved 등 |
| `version` | 예 | 버전 문자열 |
| `date` | 예 | `YYYY-MM-DD` 권장 |
| `language` | 아니오 | `ko` 또는 `en`; 기본 `ko` |
| `confidentiality` | 아니오 | Internal, Confidential 등 |
| `author` | 아니오 | 작성자 또는 팀 |
| `scope` | 신규 문서: 예 | GDDQL 범위 필터 결과. 아래 계약 참고 |

`profile` 지원값:

| 값 | 문서 영역 |
|---|---|
| `full` | 전체·통합·마스터 GDD |
| `concept` | 컨셉·제안·피치 |
| `system` | 시스템·기능 명세 |
| `ui-ux` | UI·UX·화면 명세 |
| `content` | 콘텐츠 구조·공급 |
| `balance` | 수치·공식·튜닝 |
| `economy` | 재화·보상·가격·게임 경제 |
| `level` | 레벨·맵·스테이지 |
| `narrative` | 세계관·시나리오·퀘스트 |
| `live-ops` | 라이브서비스·이벤트 운영 |
| `business` | 시장·BM·출시·사업 계획 |
| `production` | 개발 일정·마일스톤·의존성·업데이트 명세 |

신규 입력에는 `profile`을 반드시 넣는다. 렌더러는 기존 JSON 호환성을 위해 누락을 허용하지만, 그 HTML에는 문서 영역을 자동 판별할 정보가 없다. 알 수 없는 프로필 값은 렌더 단계에서 오류가 난다.

`kind`가 있으면 반드시 `kind_contracts.py`의 canonical ID여야 하며 해당 계약의 `profile`과
`document.profile`이 같아야 한다. 예를 들어 `ui-spec`은 `ui-ux`,
`crafting-enhancement-system`은 `system`, `development-plan`과 `update-spec`은
`production`을 요구한다. 알 수 없는 kind 또는 kind/profile 불일치는 렌더 단계에서 오류다.
같은 프로필에 속한 `ux-flow`와 `wireframe`도 별도 JSON과 별도 HTML로 작성한다.

표지에는 한국어 문서 종류를 한 번만 표시한다. canonical kind/profile ID는 HTML 메타데이터에만 둔다. `eyebrow`가 필요하면 프로젝트 단계처럼 문서 종류와 겹치지 않는 짧은 한국어를 사용한다. `pillars`는 프로필에 맞는 1~5개의 설계 원칙으로 작성한다. 예를 들어 UI 문서는 UX 원칙, 밸런스 문서는 튜닝 원칙을 사용하며 게임 전체의 디자인 필러를 억지로 반복하지 않는다.

### `summary`

`summary`는 HTML `<meta name="description">`에 넣는 짧은 비가시 메타 요약이다. 검색·파일 미리보기에서 문서 목적을 식별할 수 있게 쓰되, 표지나 본문에 별도 카드로 렌더링하지 않는다. `프로젝트 브리프`라는 별도 섹션·카드·본문 블록도 만들지 않는다. 문서 종류는 표지에서 한 번만 표시하며 `summary`, `document.subtitle`, 첫 본문 설명에서 반복하지 않는다.

### 기획 권한 경계

모든 kind와 generic profile 문서는 `planning-authority-boundary.md`를 적용한다.

- 기획이 확정하는 것은 **무엇·왜·플레이어가 관찰할 결과·게임 규칙·수용조건**이다.
- 클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·멱등 키·UUID·데이터 물리 타입·프레임워크·틱레이트는 JSON 본문·표·다이어그램·예시에서 구현안으로 확정하지 않는다.
- 기술 요구는 관찰 가능한 품질조건으로 쓰고, 해법 선택은 `개발 협의` 표의 기획 요구·품질조건·제약·개발 결정 필요·담당·시점으로 남긴다.
- 사용자 제공 구현안은 `사용자 제공 기술 제약 · 개발 확인 필요`로만 기록하며 추가 구현 결정을 만들지 않는다.

기술 협업 kind의 콘텐츠 경계:

| kind | JSON에 작성 가능 | 작성 금지 |
|---|---|---|
| `data-table-spec` | 논리 필드 의미·단위·범위·필수 여부·관계·검증 규칙 | DB 배치, SQL 타입, PK·인덱스, UUID·저장 구현 |
| `logging-spec` | 이벤트 의미·발생 조건·시점·논리 속성·분석 질문 | SDK·API, 전송·queue·pipeline·warehouse, 물리 타입 |
| `logic-rule-spec` | 선언형 조건·결과, 우선순위, 결정표, 상태 전이, 게임 공식 | 클래스·메서드, 실행 의사코드, 알고리즘, 서버/클라이언트 분할 |
| `exception-spec` | 발생 조건, 플레이어 피드백, 보존 결과, 보상·재시도·재진입 규칙 | 트랜잭션·rollback 구현, 멱등 키, lock·queue, DB 복구 알고리즘 |

### `document.scope`

자연어 또는 GDDQL을 해석한 뒤 `core + triggered + dependency`로 계산된 실제 작성 범위를 기록한다. 이 객체와 값은 렌더·검토용 메타데이터이며 표지·본문·목차·부록에 설명하지 않는다.

| 필드 | 필수 | 설명 |
|---|---|---|
| `mode` | 예 | `filtered` 또는 `full`. 일반 영역 요청은 `filtered` |
| `facets` | 예 | 키워드 조합으로 정규화한 패싯 배열. 없으면 `[]` |
| `sections` | `filtered`: 예 | 선택 프로필의 canonical section ID 배열 |

- `filtered`에서는 프로필의 `core_ids`가 모두 들어 있어야 한다.
- kind 문서에서는 계약의 모든 `default_facets`가 `facets`에 들어 있어야 한다. 사용자 facet은 추가할 수 있지만 kind 기본 facet은 조용히 제거할 수 없다.
- 패싯이 선택한 섹션의 의존 섹션도 자동으로 들어 있어야 한다.
- `facets`는 소문자 ID만 사용하며, section ID를 직접 포함한 경우에도 그 ID를 `facets`에 함께 기록한다.
- 렌더러와 검증기는 `facets`로 section plan을 다시 계산하므로, 발동 섹션·의존 섹션 누락이나 근거 없는 추가 섹션은 실패한다.
- 실제 `sections[].id`의 canonical ID 집합은 `document.scope.sections`와 정확히 같아야 한다.
- 선택되지 않은 canonical section을 관성적으로 추가하면 렌더 단계에서 오류가 난다.
- `full`은 해당 프로필의 모든 허용 섹션을 사용한다. `sections`를 생략할 수 있고, 적는다면 전체 집합이어야 한다.
- 레거시 입력에서 `scope`를 생략할 수 있지만 신규 문서는 생략하지 않는다.

렌더된 HTML에는 `gdd-profile`, 선택적인 `gdd-kind`, `gdd-scope-mode`, `gdd-sections`,
`gdd-facets` 메타데이터가 들어가며 검증기가 동일 계약을 다시 확인한다.
신규 산출물 검증에는 `validate_gdd.py --require-scope`를 사용해 레거시 폴백으로 범위 계약을 우회하지 못하게 한다.

### kind 필수 산출물 내부 점검

`kind_contracts.py`의 `required_outputs`는 섹션 ID가 아니라 문서가 답해야 하는 결과 계약이다.
kind별 고유 산출물과 다음 공통 차원을 함께 포함한다.

| 공통 차원 | 처리 방법 |
|---|---|
| `planning-intent` | 이 문서가 소유하면 직접 결정하고, 아니면 소유 kind/ID를 참조하거나 사유와 함께 `N/A` |
| `application-scope` | 포함·제외와 대상 버전을 소유·참조·`N/A` 중 하나로 표시 |
| `operating-rules` | 규칙 소유 문서만 상세화하고 다른 문서는 Rule ID를 참조 |
| `schedule-and-ownership` | 일정 소유 문서만 작업을 복제하며 나머지는 production 문서를 참조 |
| `data-contract` | 스키마 소유 문서만 논리 필드 의미·단위·범위를 정의하며 나머지는 `data-table-spec` ID를 참조 |
| `ui-touchpoints` | UI 소유 문서만 화면을 정의하며 나머지는 `ui-spec`/Screen ID를 참조 |
| `exception-policy` | 예외 소유 문서만 전체 규칙을 정의하며 나머지는 `exception-spec`을 참조 |
| `telemetry-plan` | 로그 소유 문서만 이벤트의 논리 의미·조건·속성을 정의하며 나머지는 `logging-spec` Event ID를 참조 |
| `completion-criteria` | 이 문서가 승인·구현·QA 완료를 판정할 수 있게 직접 소유 |

모든 공통 차원을 매 문서에 복제하지 않는다. 생성·검토 과정에서는 각 차원을 `owned`,
`reference`, `N/A` 중 하나로 분류하고 경로·대상·사유를 확인한다. 이 분류와
`required_outputs`, handoff 계약은 내부 점검 정보다.

사용자에게 보이는 `sections`에는 전용 커버리지 표·부록을 만들지 않는다.
`appendix-kind-coverage`, `owned`, `reference`, `N/A`, canonical kind ID를 표지·본문·목차·부록·결정 로그에 쓰지 않는다.
사용자가 문서 간 협업 표를 명시적으로 요청한 경우에만 한국어 문서명·필요 결정·전달 자료·완료 기준·담당을 일반 `table` 블록으로 작성한다.

### `sections`

```json
{
  "id": "ui-objectives",
  "number": "01",
  "title": "UX 목표와 범위",
  "subtitle": "UI 문서가 해결해야 할 사용자 과업과 성공 기준",
  "blocks": []
}
```

`id`는 소문자 영문, 숫자, 하이픈만 사용한다. 선택한 프로필의 표준 ID를 사용해야 프로필 검증을 통과한다. 표준 ID는 `profiles/<profile>.md`를 따른다. 선택 부록은 사용자의 의사결정에 실제로 필요한 경우에만 `appendix-` 접두사를 사용한다. 내부 커버리지와 생성 과정은 부록으로 만들지 않는다.

## 4. 공통 규칙

- 모든 일반 텍스트는 렌더러가 HTML 이스케이프한다.
- 줄바꿈이 필요한 문단은 `\n`을 사용한다.
- 링크는 `paragraph` 대신 `html` 블록을 쓰거나 출처 목록에 둔다.
- `html` 블록은 신뢰할 수 있는 작성자가 만든 내용에만 사용한다.
- 한 섹션 안에서 블록 순서는 출력 순서와 같다.
- 빈 배열과 빈 문자열은 가능하면 제거한다.

## 5. 블록 타입

### `lead`

섹션의 결론 또는 핵심 설명에 사용한다.

```json
{"type": "lead", "text": "플레이어는 위험을 감수해 더 깊이 탐사할수록 더 큰 선택권을 얻는다."}
```

### `paragraph`

```json
{"type": "paragraph", "text": "일반 설명 문단이다."}
```

### `heading`

`level`은 3 또는 4만 사용한다.

```json
{"type": "heading", "level": 3, "text": "코어 루프"}
```

### `bullets`

```json
{
  "type": "bullets",
  "ordered": false,
  "items": ["탐사 경로를 선택한다.", "위험과 보상을 비교한다."]
}
```

### `cards`

`tone`은 `default`, `accent`, `success`, `warning`, `risk` 중 하나다.

```json
{
  "type": "cards",
  "items": [
    {
      "title": "읽히는 위험",
      "text": "안전과 보상 사이에 읽을 수 있는 선택을 만든다.",
      "meta": "설계 원칙",
      "tone": "accent"
    }
  ]
}
```

### `metrics`

```json
{
  "type": "metrics",
  "items": [
    {
      "label": "목표 세션",
      "value": "30분",
      "detail": "탐사 20분 + 귀환 10분",
      "trend": "가정"
    }
  ]
}
```

### `table`

`columns`는 문자열 배열 또는 `key`와 `label` 객체 배열을 사용한다. `rows`는 배열의 배열 또는 객체 배열을 사용할 수 있다.
`data-table-spec`에서도 이는 논리 데이터 계약이다. DB 물리 테이블·SQL 타입·인덱스·저장 방식을 적지 않는다.

```json
{
  "type": "table",
  "caption": "핵심 자원 정의",
  "columns": [
    {"key": "resource", "label": "자원"},
    {"key": "source", "label": "주요 획득"},
    {"key": "sink", "label": "주요 소비"}
  ],
  "rows": [
    {"resource": "빛", "source": "탐사", "sink": "안전지대 확장"}
  ]
}
```

### `callout`

`tone`은 `insight`, `success`, `warning`, `risk`, `tbd` 중 하나다.

```json
{
  "type": "callout",
  "title": "설계 의도",
  "text": "빛은 체력 대신 팀의 이동 가능성을 제한한다.",
  "tone": "insight"
}
```

### `formula`

게임 규칙의 계산 의미와 수용조건에만 사용한다. 소프트웨어 알고리즘이나 실행 의사코드를 표현하지 않는다.

```json
{
  "type": "formula",
  "label": "탐사 보상",
  "expression": "Reward = Base × DepthMultiplier × TeamModifier",
  "note": "DepthMultiplier는 1.0~2.5 범위에서 조정한다."
}
```

### `mermaid`

플레이어 흐름, 게임 상태, 문서 handoff를 표현한다. 서버·클라이언트·서비스·DB 구현 아키텍처를 확정하는 데 사용하지 않는다.

```json
{
  "type": "mermaid",
  "title": "코어 루프",
  "code": "flowchart LR\n  A[준비] --> B[탐사]\n  B --> C{귀환?}\n  C -->|성공| D[성장]\n  C -->|계속| B",
  "caption": "탐사와 귀환 사이의 반복 선택"
}
```

### `chart`

```json
{
  "type": "chart",
  "title": "목표 난이도 곡선",
  "chart_type": "line",
  "labels": ["1구역", "2구역", "3구역"],
  "datasets": [
    {"label": "권장 전투력", "data": [100, 160, 250]}
  ],
  "options": {
    "scales": {
      "y": {"beginAtZero": true}
    }
  },
  "caption": "예시값이며 플레이테스트 후 조정"
}
```

지원 타입은 Chart.js의 `line`, `bar`, `scatter`, `radar`, `doughnut`, `pie`다.

### `timeline`

```json
{
  "type": "timeline",
  "items": [
    {
      "phase": "M1 · 4주",
      "title": "코어 루프 프로토타입",
      "text": "탐사-귀환 루프와 협동 시야를 검증한다.",
      "tags": ["게임 기획", "개발"],
      "status": "active"
    }
  ]
}
```

`status`는 `done`, `active`, `planned` 중 하나다.

### `user_story`

```json
{
  "type": "user_story",
  "actor": "초행 플레이어",
  "want": "팀원이 발견한 위험을 즉시 이해하고 싶다",
  "reason": "음성 채팅 없이도 협동할 수 있기 위해",
  "acceptance": [
    "핑이 100ms 이내에 팀원 화면에 표시된다.",
    "동일 대상 핑은 2초 동안 병합된다."
  ]
}
```

### `html`

```json
{
  "type": "html",
  "content": "<div class=\"custom-block\">검토된 사용자 정의 HTML</div>"
}
```

## 6. 최소 예시

```json
{
  "document": {
    "title": "샘플 게임",
    "subtitle": "선택 결과를 예측할 수 있는 퍼즐 게임의 목표 경험을 정의한다",
    "profile": "concept",
    "status": "작성 중",
    "version": "0.1",
    "date": "2026-07-27",
    "language": "ko",
    "scope": {
      "mode": "filtered",
      "facets": [],
      "sections": ["vision", "player-experience", "scope", "risks"]
    }
  },
  "project_meta": [{"label": "장르", "value": "퍼즐"}],
  "summary": "선택 결과를 예측할 수 있는 퍼즐 게임의 목표 경험과 초기 범위를 정의한다.",
  "pillars": [{"title": "읽히는 선택", "text": "선택의 결과를 예측할 수 있다.", "tag": "핵심 원칙"}],
  "sections": [
    {
      "id": "vision",
      "number": "01",
      "title": "콘셉트",
      "subtitle": "플레이어 약속",
      "blocks": [{"type": "lead", "text": "핵심 설명"}]
    },
    {
      "id": "player-experience",
      "number": "02",
      "title": "목표 경험",
      "blocks": [{"type": "paragraph", "text": "플레이어가 느껴야 할 경험"}]
    },
    {
      "id": "scope",
      "number": "03",
      "title": "MVP 범위",
      "blocks": [{"type": "paragraph", "text": "프로토타입 범위"}]
    },
    {
      "id": "risks",
      "number": "04",
      "title": "가설과 위험",
      "blocks": [{"type": "paragraph", "text": "검증할 핵심 위험"}]
    }
  ],
  "decisions": [],
  "sources": []
}
```

위 최소 예시는 `kind`가 없는 일반 `concept` 프로필 문서이므로 기존 호환 경로를 보여준다.
세부 문서 종류를 선택했다면 `document.kind`를 넣고 그 kind의 기본 facet과 필수 산출물 계약을
추가로 충족해야 한다.

## 7. 차트와 Mermaid

- Mermaid 노드는 가능하면 15개 이하로 유지한다.
- 라벨에 괄호나 문장 부호가 있으면 Mermaid에서 따옴표로 감싼다.
- 실제 값과 예시값을 한 차트에 섞지 않는다.
- 차트의 단위와 데이터 성격을 제목 또는 캡션에 적는다.
- 차트 데이터는 JSON 숫자로 기록하고 `"10%"` 같은 문자열을 값으로 쓰지 않는다.
- 차트에는 자동 생성되는 데이터 폴백 표가 함께 출력된다.

# GDDQL 1.0

GDDQL은 게임 기획 요청을 검토 가능한 절로 정규화하는 작은 표현식이다.
사용자는 자연어로 요청하는 것이 기본이며, GDDQL을 직접 작성하는 것은 선택 사항이다.
첫 유효 줄이 `DESIGN <profile|AUTO|profile-list>` 형태이면 GDDQL로, 아니면 자연어로 해석한다. 따라서 영어 자연어 `Design a UI specification...`은 자연어로 처리한다.

## 문법

한 줄에는 하나의 절만 쓴다. 표준 순서는 다음과 같다.

```text
DESIGN <AUTO|profile|profile-list>
KIND <AUTO|kind|kind-list>
FROM "<원본·프로젝트·참조 맥락>"
ABOUT "<설계 대상>"
FOR "<독자·사용 목적>"
GOAL "<결정하거나 달성할 결과>"
WITH <포함 패싯 또는 section-id>, ...
WITHOUT <제외 패싯 또는 section-id>, ...
ASSUME <key>="<value>", ...
OUTPUT HTML <SPLIT|MERGE>;
```

- `DESIGN`은 정확히 한 번 필요하다. 지원 프로필은 `profile_contracts.py`를 따른다.
- `KIND`는 선택 사항이며 최대 한 번 쓴다. 지원 문서 종류는 `kind_contracts.py`의 `KIND_NAMES`를 따른다.
- `AUTO`는 다른 프로필과 함께 쓸 수 없다. 복수 프로필은 `(system, ui-ux)`처럼 쓴다.
- `KIND AUTO`는 다른 kind와 함께 쓸 수 없다. 복수 문서는 `(crafting-enhancement-system, ui-spec)`처럼 쓴다.
- `DESIGN AUTO`와 명시적 `KIND`를 함께 쓰면 kind 계약에서 프로필을 도출한다.
- 명시 `DESIGN`에 kind가 쓰지 않는 추가 프로필이 있으면 그 프로필은 `kind: null`인 일반 문서가 된다. kind가 요구하는 프로필은 모두 `DESIGN`에 포함되어야 한다.
- `KIND`를 생략하면 기존처럼 프로필 단위의 일반 문서를 만든다. 이 레거시 호환 경로도 신규 범위 필터는 적용한다.
- `FROM`, `ABOUT`, `FOR`, `GOAL`, `OUTPUT`은 각각 최대 한 번 쓴다.
- `WITH`, `WITHOUT`, `ASSUME`은 여러 줄로 반복할 수 있다.
- 공백이 있는 문자열은 JSON 방식의 큰따옴표로 감싼다.
- `ASSUME` 항목은 `key=value` 형식이며 확정 사실이 아니라 가정으로 남는다.
- `SPLIT`은 문서 plan별 HTML이며 기본값이다. 서로 다른 kind는 같은 프로필에 매핑되더라도 하나의 문서로 축약하지 않는다.
- kind 목록에서 `MERGE`를 요청해도 각 kind 계약과 HTML은 독립적으로 유지한다. 필요하면 별도 색인·전달 패키지만 묶고 kind 본문을 합치지 않는다.
- `MERGE`로 한 본문을 만드는 동작은 `KIND`를 생략한 기존 프로필 단위 요청에서만 사용한다.
- 빈 줄과 `--`로 시작하는 주석은 무시하며 세미콜론은 마지막 절에서 선택 사항이다.

## 단일 kind 예시

```text
DESIGN AUTO
KIND ui-spec
FROM "모바일 수집형 RPG"
ABOUT "장비 강화 화면"
FOR "UI 검토 및 개발 협업"
GOAL "재료 선택부터 결과 확인까지 혼란 없는 흐름 정의"
WITH flow, result-feedback, exceptions, insufficient-resource, batch-action, mobile-touch
WITHOUT navigation
ASSUME result-animation="2초"
OUTPUT HTML SPLIT;
```

`ui-spec`의 broad profile은 `ui-ux`이므로 해석 결과의 `selected_profiles`에는 `ui-ux`,
`selected_kinds`에는 `ui-spec`이 들어간다. kind의 기본 facet과 `WITH`의 추가 facet을 합친 뒤
`core + triggered + dependency`로 이 문서만의 section plan을 계산한다.

## 복수 kind 예시

서로 다른 프로필:

```text
DESIGN (system, ui-ux)
KIND (crafting-enhancement-system, ui-spec)
FROM "모바일 수집형 RPG"
ABOUT "장비 강화"
GOAL "강화 결과·자원 보존 규칙과 사용자 화면을 각각 정의하고 보장 방식은 개발 협의로 남김"
WITH exceptions, insufficient-resource, result-feedback, telemetry
OUTPUT HTML SPLIT;
```

같은 프로필:

```text
DESIGN ui-ux
KIND (ux-flow, wireframe)
ABOUT "신규 유저의 첫 전투 진입"
GOAL "행동 흐름과 화면 배치를 각각 검토"
OUTPUT HTML SPLIT;
```

두 번째 예시는 두 kind가 모두 `ui-ux`여도 `ux-flow` HTML과 `wireframe` HTML을 따로 만든다.
`filter.documents`와 `scope.document_plans`에도 두 항목이 보존되어야 한다.

## 프로필 단위 호환 예시

구체 kind가 필요하지 않은 일반 시스템 기획서는 `KIND`를 생략한다.

```text
DESIGN system
ABOUT "길드 가입과 탈퇴 규칙"
WITH data, states, exceptions
OUTPUT HTML SPLIT;
```

이 경우 `selected_kinds`는 빈 배열이고 `document.kind`와 `gdd-kind`를 생략한다. 프로필 계약과
`document.scope`는 그대로 검증한다.

## 오류와 미해결 상태

- `KIND`가 두 번 이상 나오면 구문 오류다.
- kind 목록의 중복과 닫히지 않은 괄호는 구문 오류다.
- 알 수 없는 canonical kind 또는 alias는 오류다.
- `KIND AUTO`와 명시적 kind를 한 목록에 섞으면 오류다.
- 명시적 `DESIGN`에 kind가 요구하는 프로필이 하나라도 없으면 오류다. 추가 프로필은 일반 profile document plan으로 보존한다.
- `KIND AUTO`가 문맥에서 하나 이상의 kind를 충분히 판별하지 못하면 `unresolved`에 `kind`를 남기고 질문한다.
- kind의 `default_facets` 또는 profile core/dependency를 `WITHOUT`으로 제거하려 하면 범위 충돌이며 작성 전에 해결한다.
- 여러 kind가 선택됐는데 결과를 하나의 kind 문서로 축약하려 하면 라우팅 오류다. 독립 document plan으로 되돌린다.

## 해석 결과 계약

해석기는 최소한 다음 필드를 제공한다.

- `filter.selected_profiles`: 선택된 broad profile ID 배열
- `filter.selected_kinds`: 선택된 canonical kind ID 배열. 일반 프로필 경로는 `[]`
- `filter.selected_generic_profiles`: kind 없이 별도 생성할 broad profile ID 배열
- `filter.documents`: 문서별 `id`, `kind`, `label`, `category`, `category_label`, `profile`
- `scope.document_plans`: 문서별 kind 계약, 유효 facet, 제외, 필수 산출물, handoff, section plan
- `scope.section_plans`: 기존 소비자를 위한 호환 인덱스. 새 작성기는 `document_plans`를 기준으로 한다.

GDDQL은 설계 결과가 아니라 중간 계약이다. 파싱 후 프로필 라우팅과 범위 계약을 검증하고,
모호한 항목은 질문하거나 `ASSUME`에 남긴 뒤에만 기획서 본문을 작성한다.

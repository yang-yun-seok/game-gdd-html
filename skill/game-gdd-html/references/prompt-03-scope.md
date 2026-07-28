# Prompt 03 · kind별 범위 필터

## 목적

각 RoutePlan 문서를 독립적으로 범위화한다. kind 기본 패싯과 사용자 요청 패싯을 합쳐 profile 섹션을 선택하므로 사용자가 모든 구성 요소를 열거할 필요가 없다.

## 입력

- Idea IR의 `with`, `without`, 목표, 제약, 원문 근거
- Prompt 02의 `documents`
- 각 kind의 `scripts/kind_contracts.py` 계약과 선택된 `references/kinds/<category>.md`
- 각 문서의 `references/profiles/<profile>.md`
- `profile_contracts.build_section_plan()`의 결과

## 출력

```json
{
  "scope": {
    "document_plans": [
      {
        "id":"ui-spec",
        "kind":"ui-spec",
        "category":"ui-ux",
        "profile":"ui-ux",
        "kind_default_facets":[],
        "requested_facets":[],
        "facets":[],
        "core_sections":[],
        "selected_sections":[],
        "section_reasons":{},
        "required_outputs":[],
        "default_excludes":[],
        "excluded_sections":[],
        "handoffs":[],
        "assumptions":[],
        "hard_gaps":[],
        "unknown_facets":[],
        "ignored_facets":[],
        "conflicts":[]
      }
    ]
  }
}
```

- kind 문서는 `facets = kind.default_facets + 현재 kind가 소유하는 요청 패싯 + 명시 canonical section ID`의 중복 제거 순서로 계산한다.
- 같은 profile의 두 kind도 별도 `scope.document_plans` 항목과 별도 범위를 유지한다.
- core, 패싯 선택, 의존성 순서로 섹션을 구성한다. kind의 `required_outputs`, `default_excludes`, `handoffs`는 계약에서 그대로 복사한다.
- 현재 kind가 소유하지 않는 요청은 해당 kind ID의 핸드오프로 남기며 세부 내용을 범위에 복제하지 않는다.
- kind가 없는 generic profile fallback 항목은 기존 profile 패싯 방식으로 처리하고 kind 필드는 `null`로 유지한다.
- 명시적 제외가 kind 기본 패싯, core 또는 의존성과 충돌하면 조용히 무시하지 않는다.

## 책임 경계

새 kind·profile·section ID를 만들거나 본문을 작성하지 않는다.
섹션 폐쇄·kind 매핑·충돌 계산은 결정론적 계약 결과를 우선한다.

## 재시도

unknown facet은 허용 어휘로 한 번 재매핑한다.
kind 선택이나 산출물을 실질적으로 바꾸는 hard gap·충돌만 Prompt 04로 넘긴다.

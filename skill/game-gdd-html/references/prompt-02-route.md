# Prompt 02 · profile·kind 라우팅

## 목적

Idea IR에서 요청한 세부 kind, 그 kind가 요구하는 profile, 파일 분리 방식을 결정한다. 게임의 주제보다 명시된 문서 유형과 독자·결정 목적을 우선한다.

## 입력

- Prompt 01의 Idea IR과 `scripts/interpret_request.py`의 후보 점수·근거
- `scripts/kind_contracts.py`의 kind→profile 계약
- `references/document-architecture.md`의 영역 경계와 지원 profile 목록

## 출력

```json
{
  "documents": [
    {
      "id":"ui-spec",
      "kind":"ui-spec",
      "profile":"ui-ux",
      "confidence":"high|medium|low",
      "reason":"",
      "evidence":[]
    }
  ],
  "selected_profiles":["ui-ux"],
  "selected_generic_profiles":[],
  "generic_profile_fallback":false,
  "alternatives":[],
  "delivery_mode":"split",
  "needs_clarification":false,
  "ambiguity":""
}
```

- kind를 선택하면 profile은 kind 계약에서만 가져오며 임의로 바꾸지 않는다.
- 선택된 kind마다 `documents` 항목과 최종 HTML 한 개를 만든다. 두 kind가 같은 profile이어도 합치지 않는다.
- kind가 없고 일반 profile 요청만 확정 가능한 경우 `kind=null`, 해당 `profile`, `generic_profile_fallback=true`인 문서 계획 하나를 허용한다.
- `full`은 전체·통합·마스터 GDD가 명시된 경우에만 선택한다.
- 복수 kind·profile의 전달 방식은 기본 `split`이다. 사용자가 명시한 경우 `merge`를 기록하되 문서 계획 자체는 합치지 않는다.
- 역분석이 주목적이면 작성하지 말고 `game-reverse-gdd` 핸드오프를 표시한다.

## 책임 경계

패싯과 섹션을 선택하거나 질문 문장·본문을 작성하지 않는다.
스크립트 점수를 그대로 따르지 말고 원문 근거, kind 계약, 영역 경계로 판정한다.

## 재시도

명시 kind가 충돌하거나 후보별 소유 범위가 결과를 실질적으로 바꾸면 추측하지 말고 `needs_clarification=true`로 반환한다.
generic profile fallback으로 안전하게 처리할 수 있는 경우에는 불필요한 kind 선택 질문을 만들지 않는다.

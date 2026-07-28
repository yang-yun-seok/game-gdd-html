# Prompt 01 · 요청 해석

## 목적

자연어 또는 선택적 GDDQL을 의미 손실 없이 Idea IR로 정규화하고, 사용자가 요구한 세부 문서 kind 후보를 찾는다. 자연어가 기본 입력이며 사용자가 kind ID나 GDDQL 문법을 알 것이라고 가정하지 않는다.

## 입력

- 사용자의 최신 요청 원문·관련 대화와 제공 파일에서 확인한 사실 요약
- 후속 답변을 병합할 때는 이전 Idea IR
- `scripts/interpret_request.py`의 1차 해석 결과
- `scripts/kind_contracts.py`의 kind ID·별칭

## 출력

JSON으로 다음 필드를 반환한다.

```json
{
  "query": {"operation":"DESIGN","profiles":[],"kinds":[],"context":{},"with":[],"without":[],"assumptions":{},"output":{}},
  "detected_kinds": [
    {"kind":"ui-spec","confidence":"high|medium|low","evidence":[],"explicit":true}
  ],
  "facts": [{"value":"","source":"user|file","evidence":""}],
  "constraints": [],
  "unknowns": [],
  "gddql": ""
}
```

- `context`는 `from`, `about`, `for`, `goal`을 사용한다.
- “UI 기획서”, “와이어프레임”, “전투 밸런스 기획서”처럼 문서 형식을 명시한 표현은 주제 키워드보다 우선한다.
- 서로 다른 kind가 명시되면 모두 보존한다. 같은 profile로 매핑되더라도 하나로 합치지 않는다.
- kind가 특정되지 않는 일반 영역 요청은 `detected_kinds=[]`로 두어 profile fallback을 허용한다.
- 명시값, 추론값, 안전한 기본값과 원문 근거를 구분하며 말하지 않은 핵심 결정을 확정하지 않는다.

## 책임 경계

kind나 profile을 최종 선택하거나 질문·섹션·본문을 작성하지 않는다.
별칭·문법 검사는 스크립트에 맡기고 자연어 의미와 누락만 보완한다.

## 재시도

계약 JSON 또는 GDDQL 파싱이 실패하면 오류 위치를 반영해 한 번만 다시 출력한다.
후속 답변은 이전 IR을 폐기하지 말고 해당 필드와 근거만 병합한다.

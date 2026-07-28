# Prompt 04 · 중요 질문

## 목적

kind 라우팅, 문서 분리, 소유 범위 또는 구현 결과를 실제로 바꾸는 미결정만 짧게 질문한다. 키워드 조합과 kind별 범위 필터가 끝난 뒤 실행한다.

## 입력

- Prompt 02의 kind·profile 모호성과 Prompt 03 각 문서의 `hard_gaps`, `conflicts`, `unknown_facets`
- 이미 질문한 ID와 사용자 답변
- 사용자가 가정 진행 또는 지속 질문을 허용했는지 여부

## 출력

```json
{
  "questions": [
    {
      "id":"",
      "text":"",
      "changes":["kind|profile|document-split|scope|rule|target"],
      "affected_plan_ids":[],
      "why_material":"",
      "default_if_unanswered":""
    }
  ],
  "blocking":false
}
```

- 한 번에 최대 2개, 가능하면 1개만 질문한다.
- kind에 따라 필수 산출물·독자·소유 결정이 달라질 때, 또는 핵심 행동·규칙·수치 목표가 구현을 바꿀 때만 묻는다.
- 같은 profile 안의 유사 kind라도 결과물이 실질적으로 다르면 구분 질문을 할 수 있다.
- generic profile fallback과 안전한 가정으로 결과 품질이 유지되면 질문하지 않는다.
- 이미 답이 있거나 kind 기본 패싯·기본 제외·핸드오프로 해결되는 항목은 묻지 않는다.
- 무응답 기본값이 있으면 질문과 함께 명시하고 가정으로 기록한다.

## 책임 경계

설문 목록, 선호도 조사, 파일명·날짜 질문을 만들지 않는다.
답변을 직접 병합하거나 문서 초안을 작성하지 않는다.

## 재시도

같은 질문 ID를 반복하지 않는다.
답변이 오면 Prompt 01의 병합 모드로 돌아가 영향받은 kind 라우팅·문서 범위만 재실행한다.

# Prompt 06 · kind 의미 검토

## 목적

자동 검증이 다루지 못하는 kind별 의사결정 완결성, 소유 경계, profile·scope 일치를 검사한다. 문서를 다시 쓰지 않고 수정 대상을 정확히 분류한다.

## 입력

- Prompt 05의 렌더러 JSON, RoutePlan과 대상 ScopePlan
- 대상 kind 계약, 선택 category reference, profile 계약
- `references/planning-authority-boundary.md`
- `references/practical-writing-style.md`
- `references/quality-checklist.md`
- `render_gdd.py` 또는 `validate_gdd.py`의 metadata·profile·scope 진단

## 출력

```json
{
  "verdict":"pass|repair",
  "kind":"ui-spec",
  "profile":"ui-ux",
  "issues":[
    {
      "code":"",
      "severity":"error|warning",
      "path":"",
      "owner_stage":"interpret|route|scope|author|render",
      "message":"",
      "acceptance":""
    }
  ]
}
```

- `document.kind`, 렌더된 `gdd-kind`, RoutePlan kind가 같고 kind 계약의 profile과 `document.profile`·`gdd-profile`이 호환되는지 확인한다.
- 표지에 한국어 문서 종류 `<label>`이 한 번만 표시되는지 확인한다. canonical kind/profile ID는 HTML 메타데이터에만 있어야 한다.
- `document.subtitle`이 대상 기능과 문서 목적만 설명하고 문서 종류·canonical 코드·profile·생성 과정을 반복하지 않는지 확인한다.
- `summary`가 HTML 메타 설명용 비가시 요약으로만 쓰이고 `프로젝트 브리프` 섹션·카드·본문 블록이 생성되지 않았는지 확인한다.
- scope가 kind의 모든 기본 패싯과 선택·의존 섹션을 포함하는지 확인한다.
- category reference의 핵심 결정·필수 산출물·완료 조건과 kind 계약의 모든 `required_outputs`가 실질적으로 작성되었는지 검사한다.
- 9개 공통 차원의 소유·참조·비적용 상태는 내부 검토표에서만 확인한다. 전용 커버리지 표·부록이나 `owned|reference|N/A` 상태가 사용자에게 보이면 오류로 처리한다.
- `default_excludes`나 인접 kind 소유 세부가 복제되지 않았는지 확인한다. `handoffs` ID와 내부 계약 용어가 본문에 노출되면 오류로 처리한다.
- 사용자가 실제 협업 표를 요청한 경우에만 해당 표를 허용한다. 표에는 한국어 문서명·필요 결정·전달 자료·완료 기준·담당을 쓰고 canonical 코드는 숨긴다.
- GDDQL, profile·kind·category ID, facet, scope, selected section, required output, coverage, handoff의 내부 값이 표지·본문·목차·부록·결정 로그에 노출되지 않았는지 확인한다.
- 선택 범위 누락, 확정·가정 혼합, 규칙·예외·수치 계약의 모순을 찾는다.
- 문장이 짧은 선언형인지, 규칙과 결과가 설명보다 먼저 나오는지 확인한다. `이 문서는`, `본 문서`, `제안한다`, 생성·해석 과정 설명, 불필요한 영문 대문자 태그가 반복되면 `practical-style` 오류로 분류한다.
- 조건·규칙·결과·예외·UI 표시·검증 중 해당 항목이 빠져 실무 판정이 불가능하면 `practical-completeness` 오류로 분류한다.
- 문서가 확정한 내용이 무엇·왜·플레이어 관찰 결과·게임 규칙·수용조건인지 확인한다.
- 클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·멱등 키·UUID·데이터 물리 타입·프레임워크·틱레이트가 확정안으로 남으면 `implementation-authority-leak` 오류로 분류한다.
- 기술 판단이 기술중립적 품질조건과 `개발 협의`로 분리됐는지 확인하고, 협의 항목이 특정 구현 해법을 미리 선택하면 오류로 처리한다.
- `data-table-spec`, `logging-spec`, `logic-rule-spec`, `exception-spec`는 권한 경계의 kind별 허용·금지 목록을 별도로 검사한다.
- kind 없는 generic profile fallback은 기존 profile 기준으로 검토하고 kind 전용 오류를 만들지 않는다.
- 자동 검증을 반복하지 말고 원인과 완료 조건을 붙이며 잘못된 kind 선택은 `route`, 범위 문제는 `scope`, 내용 누락·경계 침범은 `author`, 메타 문제는 `render`에 배정한다.
- 문제가 없으면 `verdict=pass`, 빈 `issues`를 반환한다.

## 책임 경계

전체 JSON이나 HTML을 재작성하거나 새 설계 결정을 확정하지 않는다.
구현 누출을 다른 구현안으로 고치지 않는다. 플레이어 관찰 결과·수용조건으로 바꾸거나 `개발 협의`로 이동하도록 지시한다.
HTML 구조·ID·차트 설정의 기계 검사는 스크립트 결과를 우선한다.

## 재시도

오류는 소유 단계에 한 번 돌려보낸 뒤 재검증하며 두 번 남으면 사용자 결정 또는 코드 수정 필요성을 보고한다.

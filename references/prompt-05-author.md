# Prompt 05 · kind 문서 작성

## 목적

확정된 `ScopePlan.scope.document_plans` 항목 하나를 개발 전달·검토 가능한 렌더러 JSON 한 개로 작성한다. kind가 소유한 기획 결정을 깊게 쓰고 인접 kind와 구현 방식은 참조·협의 대상으로 남긴다.

## 입력

- 병합 완료된 Idea IR과 답변
- Prompt 02의 RoutePlan과 Prompt 03의 대상 `scope.document_plans` 항목 하나
- 대상 `scripts/kind_contracts.py` 계약
- 선택한 `references/kinds/<category>.md`와 `references/profiles/<profile>.md`
- `references/planning-authority-boundary.md`
- `references/practical-writing-style.md`
- `references/input-schema.md`
- 필요한 경우에만 근거 묶음, 장르 모듈, 시각화 지침
- 수리 모드에서는 이전 JSON과 경로별 오류

## 출력

정상 상태에서는 마크다운 없이 `render_gdd.py`가 받는 JSON 객체만 반환한다. 각 문서 계획마다 이 프롬프트를 별도로 실행한다.

- kind 경로에서는 `document.kind`를 대상 kind ID로, `document.profile`을 매핑 profile로 정확히 설정한다. generic profile fallback만 `document.kind` 생략을 허용한다.
- 렌더된 표지에는 계약의 한국어 `<label>`을 한 번만 표시한다. canonical kind/profile ID는 메타데이터에만 둔다.
- `document.subtitle`에는 대상 기능과 문서 목적만 짧은 선언형으로 쓴다. 문서 종류, canonical 코드, profile, 생성 과정을 반복하지 않는다.
- `summary`는 HTML `<meta name="description">`에 사용할 짧은 비가시 메타 요약으로만 작성한다. `프로젝트 브리프`라는 별도 섹션·카드·본문 블록을 만들지 않는다.
- `document.scope.mode`은 `filtered`, `facets`는 kind 기본 패싯을 모두 포함한 확정 패싯, `sections`는 대상 `selected_sections`와 정확히 일치시킨다.
- `sections`는 `selected_sections`와 `appendix-` 부록만 사용한다.
- 선택한 category reference의 “반드시 답할 결정”, 필수 산출물, 완료 조건을 실제 본문 내용으로 충족한다. `required_outputs` 이름과 추적 과정은 내부 검토에만 둔다.
- kind의 `default_excludes`는 상세 작성하지 않는다. 인접 문서의 상세도 복제하지 않는다.
- 전용 커버리지 섹션·표·부록을 만들지 않는다. `appendix-kind-coverage`, `owned`, `reference`, `N/A`, `required_outputs`, `handoff` 같은 내부 용어를 사용자에게 보이는 블록에 쓰지 않는다.
- 문서 간 실제 협업 표는 사용자가 명시적으로 요청한 경우에만 만든다. canonical ID 대신 한국어 문서명·필요 결정·전달 자료·완료 기준·담당을 쓴다.
- 규칙은 전제조건·입력·처리·출력·실패를, 흐름은 성공·취소·재진입을 포함한다.
- 문장은 짧은 선언형으로 쓰고 조건·규칙·플레이어 결과·예외·UI 표시·검증을 먼저 둔다. `이 문서는`, `본 문서`, `제안한다`와 AI의 해석·필터·조합 과정 설명은 최소화한다.
- 표·카드·태그는 한국어를 우선한다. `PILLAR 01`, `DESIGN`, `OWNED`, `REFERENCE` 같은 불필요한 영문 대문자 라벨을 만들지 않는다.
- 확정하는 내용은 무엇·왜·플레이어가 관찰할 결과·게임 규칙·수용조건으로 제한한다. 규칙의 `처리`는 도메인 판정이며 코드 실행 순서가 아니다.
- 클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·멱등 키·UUID·데이터 물리 타입·프레임워크·틱레이트를 설계 결정으로 쓰지 않는다.
- 기술 판단이 필요하면 관찰 가능한 품질조건만 적고, `개발 협의` 표에 기획 요구·품질조건·제약·개발 결정 필요·담당·시점을 남긴다. 구현 해법은 선택하지 않는다.
- `data-table-spec`, `logging-spec`, `logic-rule-spec`, `exception-spec`는 권한 경계 문서의 kind별 허용·금지 항목을 적용한다.
- 사실·가정·제안·검토 필요 항목을 `decisions`와 본문에서 구분하고 근거 없는 수치·외부 사실을 만들지 않는다.

## 책임 경계

kind·profile·패싯·범위를 다시 선택하거나 웹 리서치를 가장하지 않는다.
HTML을 직접 쓰거나 템플릿을 복제하지 않는다.
기획 문서를 기술 설계서로 확장하지 않는다. 사용자가 준 구현안은 `사용자 제공 기술 제약 · 개발 확인 필요`로만 기록하고 추가 구현 결정을 만들지 않는다.
scope 또는 kind 소유권 충돌이 남으면 억지로 작성하지 않고 소유 단계를 `scope`로 반환한다.

## 재시도

렌더러 오류나 내부 검토에서 확인된 필수 결과의 정확한 JSON 경로만 수정하며 범위나 외부 kind 상세를 넓히지 않는다.
같은 오류가 두 번 지속되면 추측을 멈추고 원인과 필요한 결정을 보고한다.

---
name: game-gdd-html
description: 자연어 또는 선택적 GDDQL로 받은 신규 게임 아이디어를 넓은 profile과 세부 document kind로 해석하고, kind 기본 패싯+요청 패싯+의존 범위만 조합해 종류별 독립 HTML 기획서를 생성·검증한다. 게임 제안서·콘셉트·마스터 GDD·개발 일정, 캐릭터·아이템·퀘스트·전투·밸런스·레벨·던전·경제·UI·UX 흐름·와이어프레임·세계관·시나리오·데이터 테이블·로그·이벤트·라이브 운영·업데이트 명세 등 특정 기획서나 "게임 기획서", "GDD", "HTML 기획서" 요청에 사용한다. 전체·통합·마스터 GDD가 명시된 경우에만 full을 선택하며, 출시작 역분석은 game-reverse-gdd를 우선한다.
license: MIT
---

# 게임 기획서 HTML 컴파일러

사용자에게 전체 구성 요소를 열거하게 하지 않는다. 자연어를 GDDQL 중간 계약으로 정규화하고, 키워드 조합으로 필요한 문서 영역과 섹션만 선택한 뒤 영역별 HTML을 만든다.

```text
요청 → 해석 → profile·kind 라우팅 → 문서별 범위 필터 → 중요 질문 → 작성 → 렌더 → 검토
```

이 폴더를 `$SKILL_DIR`로 간주한다.

## 단계별 파일 로드

필요한 단계의 파일만 완전히 읽는다.

| 단계 | 읽을 파일 |
|---|---|
| 항상 | `references/gddql.md`, `references/prompt-01-interpret.md`, `references/planning-authority-boundary.md` |
| profile·kind가 불명확할 때만 | `references/prompt-02-route.md`, `references/document-architecture.md` |
| 종류 확정 직후 | `references/prompt-03-scope.md`, 선택한 `references/kinds/<category>.md`와 `references/profiles/<profile>.md`만 |
| 중요한 미결정이 있을 때만 | `references/prompt-04-question.md` |
| JSON 작성 직전 | `references/prompt-05-author.md`, `references/input-schema.md`, `references/practical-writing-style.md` |
| 최신 외부 사실이 필요할 때만 | `references/research-and-evidence.md` |
| 장르 고유 규칙이 선택 범위에 있을 때만 | `references/genre-modules.md` |
| Mermaid·Chart.js를 사용할 때만 | `references/visualization-guide.md` |
| 전달 전 | `references/prompt-06-review.md`, `references/quality-checklist.md` |

다른 카테고리·프로필 파일을 읽어 결과에 섞지 않는다. 복수 kind면 선택된 카테고리와 프로필 파일만 중복 없이 읽는다.

## 1. 요청 해석

자연어가 기본이며 GDDQL 직접 입력은 선택 사항이다. 동일한 명령으로 둘 다 해석한다.

```bash
python "$SKILL_DIR/scripts/interpret_request.py" --text "$REQUEST" > working/request-plan.json
```

해석 결과에서 다음을 확인한다.

- `query`: 정규화된 GDDQL 계약
- `filter`: 프로필·kind 후보, `documents`, 확신도, 질문 필요 여부
- `scope.facets`: 키워드 조합으로 만든 안정된 패싯
- `scope.document_plans`: kind별 산출물·핸드오프·실제 작성 섹션
- `scope.section_plans`: document plan ID별 section plan 호환 인덱스
- `unresolved`: 프로필·범위 충돌 등 미해결 항목

Prompt 01은 원문 의미와 근거를 보완하지만 명시된 kind를 다른 종류로 바꾸지 않는다. 직접 작성한 GDDQL의 구문 오류는 자연어로 조용히 재해석하지 않고 정확한 오류를 반환한다.

## 2. profile·kind 라우팅

다음 순서를 지킨다.

1. 출시작을 조사해 구조를 복원하는 요청이면 `game-reverse-gdd`로 넘긴다.
2. 명시된 세부 산출물 kind가 주제어보다 우선한다. `강화 시스템 UI 기획서`는 `ui-spec` / `ui-ux`다.
3. `full`은 게임 전체·통합·마스터 GDD가 명시된 경우에만 선택한다.
4. kind가 없으면 profile을 독자, 결정 목적, 복합 키워드로 추론하고 generic profile 문서를 허용한다.
5. `게임 기획서` 또는 `GDD`만 있으면 `full`로 추정하지 않고 영역을 질문한다.
6. 복수 kind는 같은 profile이어도 합치지 않고 문서 계획을 각각 만든다.
7. 복수 문서는 기본 `split`이며 사용자가 명시한 경우에만 `merge`를 기록한다.

명시 kind와 매핑 profile이 충돌하지 않으면 Prompt 02를 생략한다. 경계가 있으면 Prompt 02와 문서 아키텍처를 사용하되 섹션이나 본문은 아직 작성하지 않는다.

## 3. 키워드 범위 필터

선택 프로필의 섹션 전체를 자동 작성하지 않는다.

```text
selected sections = core_ids + facet-triggered sections + transitive dependencies
```

Prompt 03, `kind_contracts.py`, `profile_contracts.build_section_plan()`을 함께 사용한다.

- kind마다 `default_facets`를 먼저 적용하고 사용자가 요청한 패싯을 더한다.
- 원문의 행동, 상태, 실패, 수치, 플랫폼, 독자 신호를 프로필의 안정된 패싯으로 정규화한다.
- 명시 section ID는 직접 포함할 수 있다.
- 의존 섹션은 자동 추가한다.
- 선택되지 않은 canonical section은 추가하지 않는다.
- 다른 프로필 상세는 참조 ID와 별도 문서 핸드오프로 남긴다.
- 알 수 없는 패싯은 한 번 의미적으로 재매핑한다.
- core·dependency와 제외가 충돌하면 질문 전까지 작성하지 않는다.

각 kind의 `required_outputs`, `default_excludes`, `handoffs`와 프로필의 `자동 범위 조합` 계약이 기준이며 스크립트 결과와 다르게 임의 확장하지 않는다.

GDDQL, profile·kind ID, 패싯, 선택 범위, `required_outputs`, 커버리지 상태, 핸드오프는 생성·검토용 내부 정보다. 표지·본문·목차·부록에는 노출하지 않는다.

## 4. 기획 권한 경계

기획서는 **무엇·왜·플레이어가 관찰할 결과·게임 규칙·수용조건**만 확정한다.

- 생성물 표지에는 한국어 문서 종류 `<label>`을 한 번만 표시한다. canonical kind/profile ID는 HTML 메타데이터에만 둔다.
- `document.subtitle`에는 대상 기능과 문서 목적만 쓴다. 문서 종류와 canonical 코드를 반복하지 않는다.
- 클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·멱등 키·UUID·데이터 물리 타입·프레임워크·틱레이트 등 구현 방식은 확정하지 않는다.
- 구현 판단이 필요하면 플레이어 관찰 결과와 기술중립적 품질조건을 적고 해법은 `개발 협의`로 남긴다.
- `data-table-spec`, `logging-spec`, `logic-rule-spec`, `exception-spec`도 예외가 아니다. 각 kind의 허용·금지 경계는 `planning-authority-boundary.md`를 그대로 따른다.
- 구현 상세가 발견되면 관찰 결과·수용조건으로 바꾸거나 `개발 협의`로 이동하고, 불필요하면 삭제한다.

## 5. 질문과 가정

`filter.needs_clarification`, 범위 충돌 또는 결과를 크게 바꾸는 `hard_gaps`가 있을 때만 Prompt 04를 실행한다.

- 한 번에 최대 1~2개, 가능하면 1개만 묻는다.
- 이미 답한 내용, 파일명, 날짜, 낮은 영향의 취향은 묻지 않는다.
- 안전한 기본값은 가정과 근거로 기록하고 계속 진행한다.
- 프로필, 핵심 행동, 실패 정책, 목표 수치처럼 결과를 바꾸는 항목은 확인한다.
- 사용자가 계속 질문해 달라고 했다면 초안 중 새로 발견한 중요한 미결정도 같은 방식으로 이어서 묻는다.

답변은 Prompt 01의 병합 모드로 반영하고 영향받은 라우팅·범위 단계만 다시 실행한다.

## 6. 종류별 JSON 작성

Prompt 05와 입력 스키마에 따라 document plan마다 UTF-8 JSON을 작성한다.

```text
working/<project-slug>-<kind-or-profile>.json
```

필수 계약:

- `document.subtitle`은 대상 기능과 문서 목적을 짧은 선언형으로 쓴다. 문서 종류, canonical kind/profile ID, 생성 과정은 넣지 않는다.
- `summary`는 HTML `<meta name="description">`용 비가시 메타 요약으로만 작성한다. 별도 `프로젝트 브리프` 섹션·카드·본문 블록으로 출력하지 않는다.
- `document.profile`은 선택 프로필과 같다.
- kind 문서는 `document.kind`가 선택 kind와 같고 profile 매핑이 일치한다.
- `document.scope.mode`은 일반적으로 `filtered`다.
- `document.scope.facets`는 kind 기본 패싯을 포함한 확정 패싯을 기록한다.
- `document.scope.sections`는 section plan의 `selected_sections`와 정확히 같다.
- 실제 `sections[].id`의 canonical ID 집합도 그 목록과 정확히 같다.
- 선택 부록만 `appendix-` 접두사로 추가한다.
- 확정·가정·제안·검토 필요를 구분한다.
- 규칙은 전제조건·입력·처리·출력·실패를, 흐름은 성공·취소·재진입을 포함한다.
- 규칙의 `처리`는 도메인 판정과 플레이어 결과이며 구현 알고리즘이나 코드 순서가 아니다.
- 기획 의도·범위·규칙·일정·데이터·UI·예외·로그·완료 조건의 소유권과 누락 여부는 내부 검토에서 관리한다. `owned`, `reference`, `N/A` 상태나 전용 커버리지 부록은 렌더하지 않는다.
- kind의 필수 산출물과 인접 문서 연결은 내부적으로 충족한다. 사용자가 협업 표를 명시적으로 요청한 경우에만 한국어 문서명·필요 결정·전달 자료·완료 기준·담당을 본문에 표시한다.
- `practical-writing-style.md`에 따라 짧은 선언형, 규칙 우선 문체로 작성한다. 조건·규칙·결과·예외·UI 표시·검증을 중심으로 쓰고 AI의 해석·선택 과정을 설명하지 않는다.
- 근거 없는 숫자나 외부 사실을 만들지 않는다.

## 7. 렌더와 자동 검증

```bash
python "$SKILL_DIR/scripts/render_gdd.py" working/project-ui-spec.json -o output/Project_ui-spec_GDD_YYYYMMDD.html
python "$SKILL_DIR/scripts/validate_gdd.py" output/Project_ui-spec_GDD_YYYYMMDD.html --profile ui-ux --kind ui-spec --require-scope
```

렌더러는 `gdd-profile`, `gdd-kind`, `gdd-scope-mode`, `gdd-sections`, `gdd-facets`를 HTML에 기록한다. kind/profile이 맞지 않거나 kind 기본 패싯이 누락되거나, 범위 메타데이터와 실제 canonical section이 다르거나, 다른 프로필 섹션이 섞이면 실패해야 한다.

검증 오류가 0개가 될 때까지 정확한 JSON 경로 또는 소유 단계만 수정한다. 완성 HTML을 직접 다시 쓰지 않는다.

## 8. 의미 검토와 시각 QA

Prompt 06은 자동 검증 결과와 범위 계약을 받아 `pass` 또는 경로별 `repair`만 반환한다. 오류의 `owner_stage`로 한 번 되돌린 뒤 재렌더·재검증한다. 두 번 남으면 필요한 사용자 결정이나 코드 문제를 보고한다.

브라우저를 사용할 수 있으면 데스크톱·모바일, 목차 링크, Mermaid·Chart.js, 콘솔 오류, 인쇄 미리보기, 긴 한국어 제목과 표를 확인한다.

## 9. 전달

최종 응답의 첫 문장은 `문서 종류: <한국어 label>`로 시작한다. canonical kind/profile ID와 내부 범위 용어는 적지 않는다. 이어서 다음만 명확히 적는다.

- 클릭 가능한 HTML 파일
- 문서가 다루는 핵심 내용과 명시적으로 제외한 실무 범위
- 확정하지 못한 핵심 가정 또는 검토 필요 항목
- 자동 검증 결과
- 사용자가 검토할 결정 2~4개

중간 GDDQL과 JSON은 사용자가 명시적으로 요청할 때만 함께 제공한다.

## 불변 조건

- 개발 전달·승인·QA의 다음 행동이 가능한 수준으로 작성한다.
- 짧은 선언형과 규칙 우선 문체를 사용하고 생성 과정·내부 분류 체계를 설명하지 않는다.
- 구현 방식을 확정하지 않고 기술중립적 기획 결과와 수용조건까지만 작성한다.
- 선택 프로필 밖의 상세를 완성도 명목으로 추가하지 않는다.
- 표와 다이어그램은 관계를 더 잘 설명할 때만 사용한다.
- 최신 사실은 출처와 확인일을 붙이고 사실·해석·제안을 분리한다.
- 제공된 기존 파일을 덮어쓰지 않는다.

## 리소스

| 경로 | 용도 |
|---|---|
| `references/gddql.md` | 자연어와 선택적 SQL형 중간 계약 |
| `references/prompt-01-interpret.md` ~ `prompt-06-review.md` | 단계별 마이크로 프롬프트 |
| `references/document-architecture.md` | 프로필 경계와 복수 문서 처리 |
| `references/planning-authority-boundary.md` | 기획 확정 범위, 구현 금지선, 기술 협업 kind 경계 |
| `references/practical-writing-style.md` | 실무 문체, 표지 규칙, 내부 파이프라인 비노출 기준 |
| `references/profiles/` | core·facet·dependency·완료 조건 |
| `references/kinds/` | 9개 카테고리의 41개 kind 산출물·제외·핸드오프 계약 |
| `references/input-schema.md` | 렌더러 JSON과 범위 메타데이터 |
| `references/quality-checklist.md` | 의미·HTML 품질 게이트 |
| `assets/gdd-template.html` | 단일 HTML 템플릿 |
| `scripts/interpret_request.py` | 자연어/GDDQL 해석과 1차 필터 |
| `scripts/request_rules.py` | 한국어 라우팅·키워드 규칙 |
| `scripts/profile_contracts.py` | 프로필·섹션·의존성 계약 |
| `scripts/kind_contracts.py` | kind·profile 매핑과 종류별 기본 계약 |
| `scripts/render_gdd.py` | JSON→HTML 렌더러 |
| `scripts/validate_gdd.py` | 프로필·범위·HTML 검증기 |
| `scripts/test_interpreter.py` | 해석·범위 회귀 테스트 |
| `scripts/test_kinds.py` | 41개 kind 라우팅·렌더 회귀 테스트 |
| `scripts/test_profiles.py` | 12개 프로필 렌더·검증 테스트 |

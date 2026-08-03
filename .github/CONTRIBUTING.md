# game-gdd-html 기여 가이드

기여에 관심을 가져주셔서 감사합니다.

이 저장소는 자연어 또는 GDDQL로 받은 게임 아이디어를 문서 종류에 맞게 해석하고, 필요한 범위만 선택해 독립 HTML 기획서로 만드는 Codex 스킬입니다. 기여할 때는 문서의 양보다 **문서 종류의 책임 경계, 재현 가능한 라우팅, 자동 검증 가능성**을 우선합니다.

## 기여할 수 있는 항목

- 한국어 자연어 라우팅과 별칭 개선
- 기존 document kind의 산출물·제외·핸드오프 계약 개선
- 신규 document kind 또는 profile 제안
- GDDQL 문법·오류 메시지 개선
- HTML 렌더러의 접근성·반응형·인쇄 품질 개선
- 검증 규칙과 회귀 테스트 보강
- 문서, 예제와 번역 개선
- 재현 가능한 버그 수정

다음 변경은 먼저 이슈에서 논의하는 것을 권장합니다.

- 새로운 profile 추가
- 여러 kind의 소유권 경계를 바꾸는 변경
- GDDQL 호환성을 깨는 문법 변경
- 입력 JSON 스키마의 필수 필드 변경
- HTML 메타데이터 계약 변경

## 행동강령

모든 참여자는 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)를 따라야 합니다.

보안 취약점은 공개 이슈로 등록하지 말고 [`SECURITY.md`](SECURITY.md)의 비공개 신고 절차를 사용해 주세요.

## 개발 환경

### 요구 사항

- Git
- Python 3.10 이상
- Node.js 18 이상(PDF 내보내기 변경 시)
- 최신 브라우저

Python 런타임 코드는 표준 라이브러리만 사용합니다. 별도의 패키지 설치는 필요하지 않습니다.

### 저장소 준비

```bash
git clone https://github.com/yang-yun-seok/game-gdd-html.git
cd game-gdd-html
git switch -c feat/short-description
```

브랜치 이름은 목적이 드러나게 작성합니다.

| 목적 | 예시 |
|---|---|
| 기능 | `feat/add-guild-kind` |
| 버그 수정 | `fix/ui-kind-routing` |
| 문서 | `docs/gddql-example` |
| 테스트 | `test/exception-scope` |
| 리팩터링 | `refactor/kind-contracts` |

## 변경 전 확인

1. 같은 내용의 이슈와 PR이 없는지 검색합니다.
2. 변경이 담당할 profile과 document kind를 확인합니다.
3. 기존 기획 권한 경계를 읽습니다.
4. 현재 테스트를 실행해 기준 상태가 정상인지 확인합니다.

관련 문서:

- [`document-architecture.md`](../skill/game-gdd-html/references/document-architecture.md)
- [`planning-authority-boundary.md`](../skill/game-gdd-html/references/planning-authority-boundary.md)
- [`practical-writing-style.md`](../skill/game-gdd-html/references/practical-writing-style.md)
- [`input-schema.md`](../skill/game-gdd-html/references/input-schema.md)

## 변경 원칙

### 계약을 먼저 변경합니다

문서 종류와 범위의 단일 진실 공급원은 Python 계약 파일입니다.

- kind 계약: `skill/game-gdd-html/scripts/kind_contracts.py`
- profile 계약: `skill/game-gdd-html/scripts/profile_contracts.py`
- 한국어 라우팅: `skill/game-gdd-html/scripts/request_rules.py`

참고 문서만 변경해 런타임 계약과 어긋나게 만들지 않습니다. 계약, 참고 문서와 테스트를 같은 PR에서 함께 갱신합니다.

### 기획과 구현의 경계를 지킵니다

기획 문서가 확정할 수 있는 내용:

- 기획 의도와 적용 범위
- 플레이어 행동과 관찰 가능한 결과
- 상태, 조건, 규칙, 실패와 예외
- UI 표시와 피드백
- 데이터 항목의 기획 의미
- 추적할 행동과 결과
- 완료 조건과 수용 기준

기획 문서가 확정하지 않는 내용:

- 클래스, 함수와 API 구조
- DB 물리 스키마와 데이터 타입
- 서버·클라이언트 책임 분할
- 프레임워크와 라이브러리
- 알고리즘, 트랜잭션과 캐시 전략

기술 판단은 관찰 결과와 기술중립적 품질조건까지만 작성하고 `개발 협의`로 남깁니다.

### 내부 파이프라인을 결과물에 노출하지 않습니다

profile, kind ID, facet, GDDQL과 선택된 section 목록은 생성·검증을 위한 내부 계약입니다. 최종 HTML의 표지, 목차와 본문에 노출하지 않습니다.

## document kind 추가 절차

새로운 세부 문서 종류를 추가할 때는 다음을 모두 반영합니다.

1. `skill/game-gdd-html/scripts/kind_contracts.py`
   - canonical kind ID
   - 한국어 label과 aliases
   - category와 profile
   - default facets
   - required outputs
   - default excludes
   - downstream handoffs
2. 해당 `skill/game-gdd-html/references/kinds/<category>.md`
   - 소유 범위
   - 필수 산출물
   - 명시적 제외
   - 대표 시나리오
   - 인접 문서 연결
3. 필요한 경우 `skill/game-gdd-html/scripts/request_rules.py`
   - 한국어 자연어 키워드
   - 중첩 표현의 우선순위
4. `tests/test_kinds.py`
   - 한국어 label 라우팅
   - alias 라우팅
   - profile 매핑
   - 렌더·검증
   - 범위 충돌
5. README
   - 지원 문서 종류 표
   - 종류 수와 관련 설명

kind는 기존 문서와 제목만 달라서는 안 됩니다. 고유한 결정 목적, 산출물, 제외 범위와 핸드오프가 있어야 합니다.

## profile 변경 절차

profile을 추가하거나 변경할 때는 다음을 확인합니다.

1. `skill/game-gdd-html/scripts/profile_contracts.py`의 label, core, allowed sections, facets와 dependencies
2. `skill/game-gdd-html/references/profiles/<profile>.md`의 작성 계약
3. 관련 kind의 profile 매핑
4. `tests/test_profiles.py`의 대표 렌더·검증
5. 다른 profile의 section이 혼입되지 않는지 검증

`full`은 전체·통합·마스터 GDD 요청에만 사용한다는 원칙을 유지합니다.

## 테스트

PR 전 다음 명령을 모두 실행합니다.

```bash
python tools/validate_skill.py skill/game-gdd-html
python tests/test_interpreter.py
python tests/test_context_compiler.py
python tests/test_kinds.py
python tests/test_profiles.py
node skill/game-gdd-html/scripts/export_pdf.cjs --self-test
```

대표 요청의 압축 계약과 JSON 골격도 확인하는 것을 권장합니다.

```bash
python skill/game-gdd-html/scripts/compile_context.py \
  --text "장비 강화 UI 기획서를 작성해줘. 재화 부족과 결과 피드백을 포함해줘." \
  --output-dir working
```

렌더러를 수정한 경우 대표 JSON을 HTML로 렌더하고 검증합니다.

```bash
python skill/game-gdd-html/scripts/render_gdd.py \
  working/project-ui-spec.json \
  -o output/Project_ui-spec_GDD_YYYYMMDD.html

python skill/game-gdd-html/scripts/validate_gdd.py \
  output/Project_ui-spec_GDD_YYYYMMDD.html \
  --profile ui-ux \
  --kind ui-spec \
  --require-scope
```

브라우저에서 다음도 확인합니다.

- 데스크톱·모바일 레이아웃
- 목차와 앵커 링크
- Mermaid·Chart.js 렌더
- 브라우저 콘솔 오류
- 인쇄 미리보기
- PDF 내보내기 결과가 정확히 한 페이지인지
- 긴 한국어 제목과 표

## 코드와 문서 스타일

- 파일 인코딩은 UTF-8, 줄바꿈은 LF를 사용합니다.
- Python은 4칸 들여쓰기를 사용합니다.
- 공개 함수와 복잡한 계약에는 목적을 설명하는 docstring을 작성합니다.
- 조건, 규칙, 결과와 예외를 구분합니다.
- 근거 없는 숫자와 외부 사실을 확정하지 않습니다.
- AI의 해석 과정이나 내부 분류 체계를 사용자 문서에 서술하지 않습니다.
- 기존 파일을 직접 생성물로 덮어쓰지 않습니다.

저장소의 `.editorconfig`와 `.gitattributes`가 기본 형식을 정의합니다.

## 커밋

한 커밋은 하나의 논리적 변경을 담습니다. 제목은 짧은 명령형으로 작성합니다.

예시:

```text
Add guild system document kind
Fix UI kind routing precedence
Document GDDQL exclusion conflicts
```

자동 생성 파일, 임시 출력, 개인 환경 설정과 비밀정보는 커밋하지 않습니다.

## Pull Request

PR에는 다음 내용을 포함합니다.

- 무엇을 변경했는지
- 왜 필요한지
- 사용자·기여자에게 미치는 영향
- profile·kind·입력 스키마 호환성 영향
- 실행한 테스트와 결과
- 렌더 변경이 있다면 스크린샷 또는 예제 HTML

PR 템플릿의 체크리스트를 작성해 주세요. CI가 실패하는 PR은 병합하지 않습니다.

리뷰에서는 다음을 우선 확인합니다.

1. 문서 종류의 소유권과 제외 범위
2. 기존 요청과의 하위 호환성
3. 자연어 라우팅의 재현성
4. 구현 세부를 기획이 확정하지 않는지
5. 테스트와 참고 문서가 계약을 따라가는지

## 릴리스 정책

이 프로젝트는 [Semantic Versioning](https://semver.org/) 형식을 사용합니다.

- `MAJOR`: 호환되지 않는 GDDQL·JSON·HTML 메타데이터 변경
- `MINOR`: 호환되는 신규 kind, profile 또는 기능
- `PATCH`: 호환되는 버그 수정과 문서 개선

`0.x` 기간에는 계약이 빠르게 변할 수 있습니다. 호환성에 영향을 주는 변경은 PR과 `docs/CHANGELOG.md`에 명시합니다.

릴리스 조건:

1. `main`의 CI 통과
2. `docs/CHANGELOG.md` 갱신
3. 버전 태그 생성
4. GitHub Release에 주요 변경과 마이그레이션 필요 여부 기록

## 도움이 필요한 경우

- 사용법: [`README.md`](../README.md)와 기존 이슈를 먼저 확인합니다.
- 재현 가능한 오류: Bug Report 이슈를 작성합니다.
- 기능·문서 종류 제안: 해당 제안 양식을 사용합니다.
- 보안 문제: `SECURITY.md`의 비공개 절차를 사용합니다.

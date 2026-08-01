---
name: game-gdd-html
description: 신규 게임 아이디어를 자연어 또는 GDDQL로 해석해 요청한 종류와 범위만 담은 최적화 HTML 기획서를 생성·검증하고, 요청 시 한 장짜리 대형 PDF로 내보낸다. 게임 제안서·콘셉트·GDD·일정·시스템·전투·콘텐츠·밸런스·경제·UI/UX·스토리·데이터·로그·운영 기획 요청에 사용한다. 전체·통합·마스터 GDD가 명시된 경우에만 full을 선택하며 출시작 역분석은 game-reverse-gdd를 우선한다.
---

# 게임 기획서 HTML 컴파일러

이 폴더를 `$SKILL_DIR`로 간주한다. 원본 계약 전체를 직접 읽지 말고 컴파일된 문서별 계약만 사용한다.

## 1. 요청을 압축 작성 계약으로 컴파일

```bash
python "$SKILL_DIR/scripts/compile_context.py" \
  --text "$REQUEST" \
  --output-dir working
```

명령이 반환한 작은 manifest에서 `status`, `context`, `scaffolds` 경로만 확인한다.

- `needs-clarification`: `context`의 질문을 1개 묻고 답을 원문에 병합해 다시 실행한다.
- `ready`: `context`와 대상 scaffold JSON만 읽는다.
- 복수 문서는 scaffold마다 별도 JSON·HTML로 작성한다.
- 원본 `references/`, `kind_contracts.py`, `profile_contracts.py`는 기본 작성 컨텍스트로 읽지 않는다.

컴파일러는 원본 41종 kind 계약과 12개 profile 계약에서 다음만 손실 없이 추출한다.

- 문서 고유 목적·독자·필수 결정·산출물·제외·완료 조건
- kind 기본 facet과 요청 facet의 section closure
- 선택 section의 최소 완료 조건과 profile 경계
- 기획 권한, 시각화 정책, 의미 품질 게이트
- 정확한 profile·kind·scope가 입력된 렌더러 JSON 골격

## 2. scaffold 작성

scaffold의 `[작성 필요]`를 모두 실제 내용으로 교체한다. 삭제만 해서 빈 섹션으로 만들지 않는다.

- `document.profile`, `document.kind`, `document.scope`는 컴파일 결과를 그대로 유지한다.
- 각 선택 섹션에 최소 1개 이상의 실질적 block을 작성한다.
- `context`의 문서 고유 계약과 섹션 완료 조건을 본문에서 검토 가능하게 충족한다.
- 규칙은 전제조건·입력·도메인 판정·관찰 결과·실패를 포함한다.
- 흐름은 성공·취소 또는 실패·재진입을 포함한다.
- 수치는 단위·근거·상하한 또는 검토 상태를 함께 적는다.
- 다른 문서가 소유한 상세는 복제하지 않고 한국어 문서명과 논리 ID로 연결한다.
- Mermaid·Chart.js는 `context`의 시각화 정책과 실제 데이터 필요성에 따라 사용한다.

결과를 크게 바꾸는 프로필·핵심 행동·실패 정책·목표 수치가 비어 있으면 한 번에 1~2개만 질문한다. 안전한 기본값은 가정으로 표시하고 진행한다.

## 3. 기획 권한과 문체

- 무엇·왜·플레이어가 관찰할 결과·게임 규칙·수용조건만 확정한다.
- 클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·UUID·물리 타입·프레임워크·틱레이트를 확정하지 않는다.
- 기술 판단은 관찰 가능한 품질조건까지만 쓰고 구현 해법은 `개발 협의`로 남긴다.
- 짧은 선언형과 한국어 라벨을 사용하고 조건·규칙·결과·예외·UI 표시·검증을 먼저 쓴다.
- GDDQL, profile·kind ID, facet, scope, required output, handoff와 생성 과정을 사용자 본문에 노출하지 않는다.
- `summary`는 비가시 메타 설명이며 `프로젝트 브리프` 블록을 만들지 않는다.
- 근거 없는 외부 사실과 숫자를 만들지 않는다. 최신 사실이 실제 결정에 필요할 때만 조사한다.

## 4. 렌더와 검증

scaffold마다 실행한다.

```bash
python "$SKILL_DIR/scripts/render_gdd.py" working/<document>.json \
  -o output/<project>_<document>_GDD_YYYYMMDD.html

python "$SKILL_DIR/scripts/validate_gdd.py" \
  output/<project>_<document>_GDD_YYYYMMDD.html \
  --profile <profile> \
  --kind <kind> \
  --require-scope
```

일반 profile 문서는 `--kind`를 생략한다. 렌더 오류와 검증 오류가 0개가 될 때까지 JSON만 수정하고 HTML을 직접 고치지 않는다.

PDF를 요청받았을 때만 검증을 통과한 HTML을 한 장짜리 대형 페이지로 내보낸다. Codex Desktop에서는 먼저 번들 Node·node_modules 경로를 확인해 사용한다.

```bash
node "$SKILL_DIR/scripts/export_pdf.cjs" \
  output/<project>_<document>_GDD_YYYYMMDD.html \
  -o output/<project>_<document>_GDD_YYYYMMDD.pdf \
  --node-modules <node_modules>
```

- 출력 경로에 파일이 이미 있으면 다른 이름을 사용한다. 덮어쓰지 않는다.
- 내보내기는 Mermaid·Chart.js·웹폰트를 기다린 뒤 페이지 폭을 자동 조정한다.
- `One page` 성공 로그를 확인하고 PDF를 이미지로 렌더해 잘림·겹침·빈 영역을 시각 검수한다.
- 기본 상한에서 실패할 때만 `--max-width-px` 또는 `--max-height-px`를 조정한다.

수리는 오류가 지목한 JSON 경로만 고친다. 같은 오류가 두 번 남거나 압축 계약에 필요한 정보가 없을 때만 아래 원본 하나를 추가로 읽는다.

| 상황 | 추가 파일 |
|---|---|
| kind 계약 추출 오류 | 해당 `references/kinds/<category>.md`의 target anchor |
| section 계약 추출 오류 | 해당 `references/profiles/<profile>.md` |
| JSON 구조 오류 | `references/input-schema.md`의 해당 필드 또는 block type |
| 권한 경계 오류 | `references/planning-authority-boundary.md` |
| 문체 오류 | `references/practical-writing-style.md` |
| 시각화 오류 | `references/visualization-guide.md` |
| 외부 사실 필요 | `references/research-and-evidence.md` |

## 5. 전달 전 확인

- 선택 section마다 실질적 결정과 완료 조건이 있는지 확인한다.
- 성공·실패·취소·재시도·재진입 중 관련 경로를 확인한다.
- kind 필수 산출물과 인접 문서 연결을 내부적으로 대조한다.
- 구현 방식과 내부 분류 용어가 사용자 본문에 없는지 확인한다.
- 브라우저에서 데스크톱·모바일·목차·표·Mermaid·Chart.js·인쇄 화면을 확인한다.
- PDF 요청이면 정확히 한 페이지인지와 전체 문서의 시각 품질을 확인한다.
- 기존 사용자 파일을 덮어쓰지 않는다.

최종 응답은 `문서 종류: <한국어 문서명>`으로 시작하고 HTML 링크, 요청 시 PDF 링크, 핵심 범위, 검토할 가정, 자동 검증 결과와 사용자 결정 2~4개만 전달한다. GDDQL과 중간 JSON은 요청받았을 때만 제공한다.

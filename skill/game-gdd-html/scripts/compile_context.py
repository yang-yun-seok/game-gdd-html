#!/usr/bin/env python3
"""Compile the full GDD contracts into a small, document-specific authoring pack."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from interpret_request import InterpretError, interpret
from kind_contracts import KIND_CONTRACTS
from profile_contracts import PROFILE_RULES


SKILL_ROOT = Path(__file__).resolve().parents[1]
AUTHORING_PLACEHOLDER = "[작성 필요]"
COMMON_OUTPUTS = {
    "planning-intent",
    "application-scope",
    "operating-rules",
    "schedule-and-ownership",
    "data-contract",
    "ui-touchpoints",
    "exception-policy",
    "telemetry-plan",
    "completion-criteria",
}
AUTHORING_RULES = (
    "표지에는 한국어 문서 종류를 한 번만 표시하고 canonical ID는 메타데이터에만 둔다.",
    "subtitle은 대상 기능과 문서 목적만 쓰고 summary는 비가시 메타 설명으로만 사용한다.",
    "각 섹션은 배경보다 결정·조건·규칙·플레이어 결과·예외·검증 기준을 먼저 쓴다.",
    "규칙에는 전제조건·입력·도메인 판정·관찰 결과·실패를, 흐름에는 성공·취소·재진입을 포함한다.",
    "kind 필수 산출물과 완료 조건을 실제 내용으로 충족하되 required_outputs·handoff 같은 내부 용어를 본문에 노출하지 않는다.",
    "다른 문서가 소유한 상세는 복제하지 않고 한국어 문서명과 논리 참조 ID로 연결한다.",
    "클래스·API·DB 물리 구조·서버/클라이언트 구조·알고리즘·트랜잭션·UUID·물리 타입·프레임워크·틱레이트를 확정하지 않는다.",
    "기술 판단은 플레이어 관찰 결과와 측정 가능한 품질조건까지만 쓰고 구현 해법은 개발 협의로 남긴다.",
    "사실·가정·제안·검토 필요를 구분하고 근거 없는 수치나 외부 사실을 만들지 않는다.",
    "짧은 선언형과 한국어 라벨을 사용하고 AI의 해석·필터·생성 과정을 설명하지 않는다.",
)
BLOCK_PALETTE = (
    "lead{text}",
    "paragraph{text}",
    "bullets{items,ordered?}",
    "table{columns,rows,caption?}",
    "callout{title,text,tone}",
    "cards{items}",
    "metrics{items}",
    "formula{label,expression,note}",
    "mermaid{title,code,caption}",
    "chart{title,chart_type,labels,datasets,caption}",
    "timeline{items}",
    "user_story{actor,want,reason,acceptance}",
)
SPECIAL_AUTHORITY = {
    "data-table-spec": {
        "allowed": "논리 엔터티·필드 의미, 단위, 범위, 필수 여부, 관계, 검증 규칙, 예시값",
        "forbidden": "DB 배치, SQL 타입, PK·인덱스, 저장·마이그레이션 구현, UUID 방식",
    },
    "logging-spec": {
        "allowed": "이벤트 의미·발생 조건·시점, 논리 속성, 분석 질문, 개인정보 최소화 조건",
        "forbidden": "SDK·API, 전송 프로토콜, queue·pipeline·warehouse 구조, 물리 타입",
    },
    "logic-rule-spec": {
        "allowed": "선언형 조건·결과, 우선순위, 결정표, 상태 전이, 게임 공식, 경계 사례",
        "forbidden": "클래스·메서드, 실행 의사코드, 알고리즘·자료구조, 서버/클라이언트 분할",
    },
    "exception-spec": {
        "allowed": "예외 조건, 플레이어 피드백, 보존 결과, 보상·재시도·재진입, 운영 에스컬레이션",
        "forbidden": "트랜잭션·rollback 구현, 멱등 키, lock·queue, DB 복구 알고리즘",
    },
}


def _markdown_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _clean_markdown(value: str) -> str:
    value = re.sub(r"<span\b[^>]*></span>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<br\s*/?>", " · ", value, flags=re.IGNORECASE)
    value = value.replace("`", "").replace("**", "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip(" ·")


def _kind_reference_contract(
    kind_name: str,
    skill_root: Path = SKILL_ROOT,
) -> dict[str, str]:
    contract = KIND_CONTRACTS[kind_name]
    relative_path = str(contract["reference"]).split("#", 1)[0]
    reference_path = skill_root / relative_path
    text = reference_path.read_text(encoding="utf-8")
    marker = f'id="{kind_name}"'
    for line in text.splitlines():
        if marker not in line:
            continue
        cells = _markdown_cells(line)
        if len(cells) != 7:
            raise ValueError(
                f"{relative_path} row for {kind_name} must have 7 columns"
            )
        return {
            "purpose_and_audience": _clean_markdown(cells[1]),
            "must_answer": _clean_markdown(cells[2]),
            "required_deliverables": _clean_markdown(cells[3]),
            "explicit_excludes": _clean_markdown(cells[4]),
            "handoff_summary": _clean_markdown(cells[5]),
            "done_when": _clean_markdown(cells[6]),
        }
    raise ValueError(f"{relative_path} has no contract row for {kind_name}")


def _profile_reference_contract(
    profile: str,
    selected_sections: list[str],
    skill_root: Path = SKILL_ROOT,
) -> dict[str, Any]:
    relative_path = Path("references") / "profiles" / f"{profile}.md"
    text = (skill_root / relative_path).read_text(encoding="utf-8")
    objective = text.split("## 표준 구조", 1)[0]
    objective_lines = [
        line.strip()
        for line in objective.splitlines()[1:]
        if line.strip() and not line.startswith("#")
    ]
    section_rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        cells = _markdown_cells(line)
        if len(cells) != 4 or not re.fullmatch(r"\d+", cells[0]):
            continue
        section_id = _clean_markdown(cells[1])
        section_rows[section_id] = {
            "id": section_id,
            "title": _clean_markdown(cells[2]),
            "minimum_completion": _clean_markdown(cells[3]),
        }
    missing = [
        section_id
        for section_id in selected_sections
        if section_id not in section_rows
    ]
    if missing:
        raise ValueError(
            f"{relative_path} is missing selected sections: {', '.join(missing)}"
        )
    boundary_text = text.split("## 경계와 시각화", 1)
    if len(boundary_text) != 2:
        raise ValueError(f"{relative_path} has no boundary section")
    guardrails = [
        _clean_markdown(line[2:])
        for line in boundary_text[1].splitlines()
        if line.startswith("- ")
    ]
    return {
        "objective": " ".join(objective_lines),
        "sections": [section_rows[item] for item in selected_sections],
        "guardrails": guardrails,
    }


def _build_scaffold(
    plan: dict[str, Any],
    profile_contract: dict[str, Any],
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "title": AUTHORING_PLACEHOLDER,
        "subtitle": AUTHORING_PLACEHOLDER,
        "profile": plan["profile"],
        "status": "검토 중",
        "version": "0.1",
        "date": dt.date.today().isoformat(),
        "language": "ko",
        "scope": {
            "mode": "filtered",
            "facets": list(plan["facets"]),
            "sections": list(plan["section_plan"]["selected_sections"]),
        },
    }
    if plan["kind"]:
        document["kind"] = plan["kind"]
    return {
        "document": document,
        "project_meta": [
            {"label": "장르·플랫폼", "value": AUTHORING_PLACEHOLDER}
        ],
        "summary": AUTHORING_PLACEHOLDER,
        "sections": [
            {
                "id": item["id"],
                "number": f"{index:02d}",
                "title": item["title"],
                "subtitle": item["minimum_completion"],
                "blocks": [
                    {
                        "type": "callout",
                        "title": "작성 필요",
                        "text": AUTHORING_PLACEHOLDER,
                        "tone": "tbd",
                    }
                ],
            }
            for index, item in enumerate(
                profile_contract["sections"],
                start=1,
            )
        ],
        "decisions": [],
        "sources": [],
    }


def depth_contract(profile: str, skill_root: Path = SKILL_ROOT) -> str:
    """Load only shared depth criteria and the selected profile's lens."""
    source = (skill_root / "references" / "design-depth.md").read_text(encoding="utf-8")
    parts = re.split(r"^## (\S+)\s*$", source, flags=re.MULTILINE)
    sections = dict(zip(parts[1::2], parts[2::2]))
    return sections["common"].strip() + "\n\n" + sections[profile].strip()


def _document_context(
    result: dict[str, Any],
    plan: dict[str, Any],
    skill_root: Path,
) -> dict[str, Any]:
    selected_sections = list(plan["section_plan"]["selected_sections"])
    profile_contract = _profile_reference_contract(
        plan["profile"],
        selected_sections,
        skill_root,
    )
    kind_name = plan["kind"]
    kind_context: dict[str, Any] | None = None
    if kind_name:
        contract = KIND_CONTRACTS[kind_name]
        unique_outputs = [
            item
            for item in contract["required_outputs"]
            if item not in COMMON_OUTPUTS
        ]
        kind_context = {
            **_kind_reference_contract(kind_name, skill_root),
            "required_outputs": list(contract["required_outputs"]),
            "kind_specific_outputs": unique_outputs,
            "default_excludes": list(contract["default_excludes"]),
            "handoffs": list(contract["handoffs"]),
        }
    profile_rule = PROFILE_RULES[plan["profile"]]
    visual_contract = {
        "mermaid_min": int(profile_rule["mermaid_min"]),
        "mermaid_recommended": int(profile_rule["mermaid_recommended"]),
        "chart_policy": str(profile_rule["chart_policy"]),
    }
    quality_gates = [
        "모든 선택 섹션에 최소 완료 조건을 충족하는 실질적 블록이 있다.",
        "kind 계약의 필수 결정·산출물·완료 조건이 본문에서 검토 가능하다.",
        "성공뿐 아니라 관련 실패·취소·재시도·재진입 경로를 검토한다.",
        "기획 권한 밖의 구현 방식과 내부 분류 용어가 사용자 본문에 없다.",
        "근거 없는 수치는 예시·가정·검토 필요 중 하나로 명시한다.",
        "렌더와 validate_gdd 검증 오류가 0개다.",
    ]
    return {
        "id": plan["id"],
        "label": plan["label"],
        "kind": kind_name,
        "profile": plan["profile"],
        "request_context": result["query"]["context"],
        "assumptions": dict(result["query"]["assumptions"]),
        "scope": {
            "facets": list(plan["facets"]),
            "excluded_facets": list(plan["exclude_facets"]),
            "sections": selected_sections,
            "reasons": plan["section_plan"]["section_reasons"],
        },
        "kind_contract": kind_context,
        "profile_contract": profile_contract,
        "authority": SPECIAL_AUTHORITY.get(kind_name),
        "visual_contract": visual_contract,
        "authoring_rules": list(AUTHORING_RULES),
        "depth_contract": depth_contract(plan["profile"], skill_root),
        "block_palette": list(BLOCK_PALETTE),
        "quality_gates": quality_gates,
        "scaffold": _build_scaffold(plan, profile_contract),
    }


def compile_context(
    raw: str,
    skill_root: Path = SKILL_ROOT,
) -> dict[str, Any]:
    result = interpret(raw)
    if result["filter"]["needs_clarification"] or result["scope"]["conflicts"]:
        return {
            "status": "needs-clarification",
            "input_mode": result["input_mode"],
            "question": result["filter"]["question_hint"],
            "unresolved": result["unresolved"],
            "conflicts": result["scope"]["conflicts"],
            "candidate_documents": result["filter"]["documents"],
        }
    documents = [
        _document_context(result, plan, skill_root)
        for plan in result["scope"]["document_plans"]
    ]
    if not documents:
        return {
            "status": "needs-clarification",
            "input_mode": result["input_mode"],
            "question": (
                result["filter"]["question_hint"]
                or "작성할 기획서 종류 또는 영역을 지정해 주세요."
            ),
            "unresolved": result["unresolved"] or ["document"],
            "conflicts": [],
            "candidate_documents": result["filter"]["documents"],
        }
    return {
        "status": "ready",
        "input_mode": result["input_mode"],
        "output_mode": result["query"]["output"]["mode"],
        "documents": documents,
    }


def _render_items(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render_markdown(context: dict[str, Any]) -> str:
    if context["status"] != "ready":
        lines = [
            "# 작성 전 확인 필요",
            "",
            str(context.get("question") or "기획서 종류를 확인해 주세요."),
        ]
        if context.get("conflicts"):
            lines.extend(
                [
                    "",
                    "## 범위 충돌",
                    *[
                        f"- {item['document']}: {item['message']}"
                        for item in context["conflicts"]
                    ],
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    lines = [
        "# 압축 작성 계약",
        "",
        "이 파일과 대응 JSON 골격만 읽고 작성한다. 원본 전체 계약은 오류 수리 시에만 연다.",
    ]
    for index, document in enumerate(context["documents"], start=1):
        lines.extend(
            [
                "",
                f"## {index}. {document['label']}",
                "",
                f"- profile: `{document['profile']}`",
                f"- kind: `{document['kind'] or 'generic'}`",
                (
                    "- profile 목적: "
                    + document["profile_contract"]["objective"]
                ),
                "- facets: " + ", ".join(document["scope"]["facets"]),
                "- sections: " + ", ".join(document["scope"]["sections"]),
            ]
        )
        request_context = document["request_context"]
        context_items = [
            f"{label}: {request_context[key]}"
            for key, label in (
                ("from", "프로젝트"),
                ("about", "대상"),
                ("for", "독자"),
                ("goal", "목표"),
            )
            if request_context.get(key)
        ]
        if context_items:
            lines.extend(["", "### 요청 맥락", "", *_render_items(context_items)])
        if document["assumptions"]:
            lines.extend(["", "### 사용자 지정 가정", "",
                          "현재 문서 범위에 해당하는 값은 단위와 가정 상태를 유지한다."])
            lines.extend(f"- {key} = {value}" for key, value in document["assumptions"].items())
        if document["scope"]["excluded_facets"]:
            lines.append(
                "- 제외 facet: "
                + ", ".join(document["scope"]["excluded_facets"])
            )
        kind_contract = document["kind_contract"]
        if kind_contract:
            lines.extend(
                [
                    "",
                    "### 문서 고유 계약",
                    "",
                    f"- 목적·독자: {kind_contract['purpose_and_audience']}",
                    f"- 반드시 답할 결정: {kind_contract['must_answer']}",
                    f"- 필수 산출물: {kind_contract['required_deliverables']}",
                    f"- 완료 조건: {kind_contract['done_when']}",
                    f"- 상세 제외: {kind_contract['explicit_excludes']}",
                    "- 내부 커버리지: "
                    + ", ".join(kind_contract["required_outputs"]),
                    "- 인접 문서: " + ", ".join(kind_contract["handoffs"]),
                    (
                        "- 인접 문서 요약: "
                        + kind_contract["handoff_summary"]
                    ),
                ]
            )
        lines.extend(
            [
                "",
                "### 선택 섹션 완료 조건",
                "",
                *[
                    (
                        f"- `{item['id']}` · {item['title']}: "
                        f"{item['minimum_completion']}"
                    )
                    for item in document["profile_contract"]["sections"]
                ],
                "",
                "### 프로필 경계",
                "",
                *_render_items(document["profile_contract"]["guardrails"]),
            ]
        )
        if document["authority"]:
            lines.extend(
                [
                    "",
                    "### 기술 협업 문서 경계",
                    "",
                    f"- 허용: {document['authority']['allowed']}",
                    f"- 금지: {document['authority']['forbidden']}",
                ]
            )
        visual = document["visual_contract"]
        lines.extend(
            [
                "",
                "### 작성·품질 규칙",
                "",
                *_render_items(document["authoring_rules"]),
                f"- Mermaid 최소 {visual['mermaid_min']}개, 권장 {visual['mermaid_recommended']}개.",
                f"- Chart 정책: {visual['chart_policy']}.",
                "- 허용 블록: " + "; ".join(document["block_palette"]),
                "",
                "### 전달 전 확인",
                "",
                *_render_items(document["quality_gates"]),
                "",
                "### 기획 깊이",
                "",
                document["depth_contract"],
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise OSError(f"could not find a free output path for {path}")


def write_authoring_pack(
    context: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = _unique_path(output_dir / "request-context.md")
    context_path.write_text(
        render_markdown(context),
        encoding="utf-8",
        newline="\n",
    )
    scaffolds: list[dict[str, str]] = []
    if context["status"] == "ready":
        for index, document in enumerate(context["documents"], start=1):
            scaffold_path = _unique_path(
                output_dir / f"{index:02d}-{document['id']}.json"
            )
            scaffold_path.write_text(
                json.dumps(
                    document["scaffold"],
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            scaffolds.append(
                {
                    "document": document["id"],
                    "path": str(scaffold_path),
                }
            )
    return {
        "status": context["status"],
        "context": str(context_path),
        "scaffolds": scaffolds,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a request into a small authoring contract and JSON scaffold "
            "without loading every source reference into model context."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Natural-language request or GDDQL")
    source.add_argument("--file", type=Path, help="UTF-8 request/GDDQL file")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Stdout format when --output-dir is omitted",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write request-context.md and one JSON scaffold per document",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.text is not None:
            raw = args.text
        elif args.file is not None:
            raw = args.file.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            raw = sys.stdin.read()
        else:
            raise InterpretError("provide --text, --file, or stdin")
        if not raw.strip():
            raise InterpretError("request must not be empty")
        context = compile_context(raw)
        if args.output_dir:
            payload = write_authoring_pack(context, args.output_dir)
            print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        elif args.format == "json":
            print(
                json.dumps(
                    context,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        else:
            print(render_markdown(context), end="")
    except (OSError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

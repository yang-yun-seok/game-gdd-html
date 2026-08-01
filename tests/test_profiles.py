#!/usr/bin/env python3
"""Regression tests for every game-gdd-html document profile."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parent
SKILL_DIR = REPO_ROOT / "skill" / "game-gdd-html"
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_contracts import (
    PROFILE_NAMES,
    PROFILE_RULES,
    build_section_plan,
)
from render_gdd import (
    PROFILE_LABELS_KO,
    RenderError,
    default_output_path,
    render_document,
)
from validate_gdd import validate


TEMPLATE_PATH = SKILL_DIR / "assets" / "gdd-template.html"


def visual_blocks(profile: str) -> list[dict[str, object]]:
    rule = PROFILE_RULES[profile]
    blocks: list[dict[str, object]] = []
    for index in range(int(rule["mermaid_recommended"])):
        blocks.append(
            {
                "type": "mermaid",
                "title": f"{profile} 검증 흐름 {index + 1}",
                "code": 'flowchart LR\n  A["시작"] --> B["결정"] --> C["검증"]',
                "caption": "프로필 회귀 테스트용 최소 흐름이다.",
            }
        )
    if rule["chart_policy"] in {"required", "recommended"}:
        blocks.append(
            {
                "type": "chart",
                "title": f"{profile} 기준 수치",
                "chart_type": "line",
                "labels": ["초기", "중기", "후기"],
                "datasets": [
                    {
                        "label": "테스트 예시값",
                        "data": [10, 20, 30],
                    }
                ],
                "caption": "렌더러와 검증기 연결만 확인하는 명시적 테스트 값이다.",
            }
        )
    return blocks


def make_data(profile: str, extra_section: str | None = None) -> dict[str, object]:
    required_ids = PROFILE_RULES[profile]["required_ids"]
    sections: list[dict[str, object]] = []
    for index, section_id in enumerate(required_ids):
        blocks: list[dict[str, object]] = [
            {
                "type": "lead",
                "text": (
                    f"{profile} 프로필의 {section_id} 섹션 계약을 검증한다. "
                    "실제 문서는 해당 영역의 의사결정, 규칙, 예외와 완료 조건을 구체화한다."
                ),
            }
        ]
        if index == 0:
            blocks.extend(visual_blocks(profile))
        sections.append(
            {
                "id": section_id,
                "number": f"{index + 1:02d}",
                "title": section_id.replace("-", " ").title(),
                "subtitle": f"{profile} profile contract",
                "blocks": blocks,
            }
        )
    if extra_section:
        sections.append(
            {
                "id": extra_section,
                "number": f"{len(sections) + 1:02d}",
                "title": "Foreign Section",
                "blocks": [{"type": "lead", "text": "다른 프로필 섹션 혼입 테스트"}],
            }
        )
    return {
        "document": {
            "title": f"프로필 테스트 {profile}",
            "subtitle": f"{profile} 영역별 문서",
            "profile": profile,
            "status": "Draft",
            "version": "0.1",
            "date": "2026-07-27",
            "language": "ko",
        },
        "project_meta": [
            {"label": "프로필", "value": profile},
            {"label": "용도", "value": "자동 회귀 테스트"},
        ],
        "summary": (
            f"{profile} 프로필이 다른 기획 영역과 섞이지 않고 독립 HTML로 "
            "렌더링·검증되는지 확인한다."
        ),
        "pillars": [
            {
                "title": "영역 경계 유지",
                "text": "선택한 프로필의 결정과 섹션만 포함한다.",
                "tag": "SCOPE",
            }
        ],
        "sections": sections,
        "decisions": [
            {
                "status": "confirmed",
                "title": "프로필 계약",
                "detail": f"{profile} 표준 섹션을 자동 검증한다.",
            }
        ],
        "sources": [
            {
                "label": "내부 프로필 계약",
                "url": "https://example.com/profile-contract",
                "accessed": "2026-07-27",
                "note": "회귀 테스트용 출처 항목",
            }
        ],
    }


def make_filtered_data(
    profile: str,
    facets: list[str],
) -> dict[str, object]:
    data = make_data(profile)
    plan = build_section_plan(profile, facets)
    selected = set(plan["selected_sections"])
    data["sections"] = [  # type: ignore[index]
        section
        for section in data["sections"]  # type: ignore[index]
        if section["id"] in selected
    ]
    data["document"]["scope"] = {  # type: ignore[index]
        "mode": "filtered",
        "facets": facets,
        "sections": plan["selected_sections"],
    }
    return data


def render_to(path: Path, data: dict[str, object], template: str) -> None:
    path.write_text(render_document(data, template), encoding="utf-8", newline="\n")


def check_output_optimization(template: str) -> None:
    data = make_data("system")
    for section in data["sections"]:  # type: ignore[index]
        section["blocks"] = [  # type: ignore[index]
            block
            for block in section["blocks"]  # type: ignore[index]
            if block["type"] not in {"mermaid", "chart"}
        ]
    compact = render_document(data, template)
    pretty = render_document(data, template, compact=False)
    if len(compact) >= len(pretty) * 0.85:
        raise AssertionError("compact HTML did not reduce source size by at least 15%")
    if "mermaid.min.js" in compact or "chart.umd.min.js" in compact:
        raise AssertionError("unused visualization libraries were loaded")

    chart_profile = next(
        profile
        for profile in PROFILE_NAMES
        if PROFILE_RULES[profile]["chart_policy"] in {"required", "recommended"}
    )
    visual = render_document(make_data(chart_profile), template)
    if "mermaid.min.js" not in visual or "chart.umd.min.js" not in visual:
        raise AssertionError("used visualization libraries were omitted")
    if '"animation":false' not in visual:
        raise AssertionError("chart animation was not disabled for deterministic output")


def main() -> int:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    check_output_optimization(template)
    for profile, rule in PROFILE_RULES.items():
        profile_doc = (
            SCRIPT_DIR.parent / "references" / "profiles" / f"{profile}.md"
        )
        if not profile_doc.exists():
            raise AssertionError(f"Missing profile reference: {profile_doc}")
        profile_text = profile_doc.read_text(encoding="utf-8")
        for section_id in rule["required_ids"]:
            if f"`{section_id}`" not in profile_text:
                raise AssertionError(
                    f"{profile_doc.name} does not document {section_id}"
                )

    with tempfile.TemporaryDirectory(prefix="game-gdd-profile-test-") as temp:
        temp_dir = Path(temp)
        rendered: dict[str, Path] = {}
        for profile in PROFILE_NAMES:
            output = temp_dir / f"{profile}.html"
            render_to(output, make_data(profile), template)
            result = validate(output)
            if result.errors:
                raise AssertionError(
                    f"{profile} auto validation failed: {result.errors}"
                )
            if result.profile != profile:
                raise AssertionError(
                    f"{profile} metadata resolved as {result.profile}"
                )
            raw = output.read_text(encoding="utf-8")
            expected_marker = (
                ">" + PROFILE_LABELS_KO[profile] + "</strong>"
            )
            if expected_marker not in raw:
                raise AssertionError(
                    f"{profile} cover is missing its generic profile marker"
                )
            if "기획서 영역 ·" in raw:
                raise AssertionError(
                    f"{profile} cover exposes its internal profile category"
                )
            if 'class="brief-card"' in raw:
                raise AssertionError(
                    f"{profile} cover unexpectedly rendered a project brief card"
                )
            if '<meta name="description" content="' not in raw:
                raise AssertionError(
                    f"{profile} output is missing the summary-backed meta description"
                )
            if (
                "게임 규칙과 사용자 결과를 정의한다. "
                "구현 방식은 개발 협의에서 확정한다."
            ) not in raw:
                raise AssertionError(
                    f"{profile} cover is missing the authority boundary"
                )
            rendered[profile] = output

        english_data = make_data("concept")
        english_data["document"]["language"] = "en"  # type: ignore[index]
        english_raw = render_document(english_data, template)
        if ">Game Concept Document</strong>" not in english_raw:
            raise AssertionError("English generic profile marker was not localized")
        if "Design area ·" in english_raw:
            raise AssertionError("English cover exposes its internal profile category")
        if (
            "Design defines game rules and user-facing outcomes. "
            "Implementation is finalized with engineering."
        ) not in english_raw:
            raise AssertionError("English authority boundary was not localized")

        optional_data = make_data("concept")
        optional_data.pop("pillars")
        optional_data["decisions"] = []
        optional_data["sources"] = []
        optional_output = temp_dir / "concept-optional-sections.html"
        render_to(optional_output, optional_data, template)
        optional_raw = optional_output.read_text(encoding="utf-8")
        for absent in (
            'class="pillar-section"',
            'href="#decision-log"',
            'id="decision-log"',
            'href="#sources"',
            'id="sources"',
            "Principles over features",
        ):
            if absent in optional_raw:
                raise AssertionError(
                    f"Empty optional content rendered forbidden markup: {absent}"
                )
        optional_result = validate(optional_output, "concept")
        if optional_result.errors:
            raise AssertionError(
                f"Optional sections were not accepted: {optional_result.errors}"
            )
        if any(
            "Sources section has no entry" in warning
            for warning in optional_result.warnings
        ):
            raise AssertionError("Empty sources emitted a validation warning")

        empty_pillars_data = make_data("concept")
        empty_pillars_data["pillars"] = []
        render_document(empty_pillars_data, template)

        ui_default = default_output_path(make_data("ui-ux"), temp_dir)
        system_default = default_output_path(make_data("system"), temp_dir)
        if ui_default == system_default:
            raise AssertionError("Different profiles resolve to the same default filename")
        if "_ui-ux_GDD_" not in ui_default.name:
            raise AssertionError("Default filename does not include the profile")

        legacy_data = make_data("concept")
        del legacy_data["document"]["profile"]  # type: ignore[index]
        legacy_output = temp_dir / "legacy-concept.html"
        render_to(legacy_output, legacy_data, template)
        legacy = validate(legacy_output, "concept")
        if legacy.errors:
            raise AssertionError(f"Explicit legacy validation failed: {legacy.errors}")
        if not any("legacy fallback" in item for item in legacy.warnings):
            raise AssertionError("Legacy profile-metadata warning was not emitted")
        legacy_default = default_output_path(legacy_data, temp_dir)
        if "_concept_GDD_" in legacy_default.name:
            raise AssertionError("Legacy default filename unexpectedly gained a profile")
        strict_legacy = validate(
            legacy_output,
            "concept",
            require_scope=True,
        )
        if not any(
            "scope manifest is required" in item
            for item in strict_legacy.errors
        ):
            raise AssertionError(
                "Strict validation accepted a legacy document without scope"
            )

        mismatch = validate(rendered["ui-ux"], "system")
        if not any("Profile mismatch" in item for item in mismatch.errors):
            raise AssertionError("Embedded/CLI profile mismatch was not rejected")

        duplicate_chart_output = temp_dir / "balance-duplicate-chart.html"
        duplicate_chart_raw = rendered["balance"].read_text(encoding="utf-8")
        chart_match = re.search(
            r'(<script type="application/json" id="gdd-chart-configs">)'
            r"(.*?)"
            r"(</script>)",
            duplicate_chart_raw,
            flags=re.DOTALL,
        )
        if not chart_match:
            raise AssertionError("Chart configuration script was not found")
        chart_specs = json.loads(chart_match.group(2))
        chart_specs.append(chart_specs[0])
        duplicate_chart_raw = (
            duplicate_chart_raw[: chart_match.start(2)]
            + json.dumps(chart_specs, ensure_ascii=False, separators=(",", ":"))
            + duplicate_chart_raw[chart_match.end(2) :]
        )
        duplicate_chart_output.write_text(
            duplicate_chart_raw,
            encoding="utf-8",
            newline="\n",
        )
        duplicate_chart = validate(duplicate_chart_output, "balance")
        if not any("Duplicate chart configuration ids" in item for item in duplicate_chart.errors):
            raise AssertionError("Duplicate chart configuration was not rejected")

        try:
            render_document(
                make_data("ui-ux", extra_section="balance-objectives"),
                template,
            )
        except RenderError:
            pass
        else:
            raise AssertionError(
                "Renderer accepted a canonical section from another profile"
            )

        foreign_output = temp_dir / "ui-ux-foreign.html"
        foreign_raw = rendered["ui-ux"].read_text(encoding="utf-8").replace(
            'id="ui-objectives"',
            'id="balance-objectives"',
            1,
        )
        foreign_output.write_text(foreign_raw, encoding="utf-8", newline="\n")
        foreign = validate(foreign_output, "ui-ux")
        if not any("Out-of-scope canonical sections" in item for item in foreign.errors):
            raise AssertionError("Foreign canonical section was not rejected")

        custom_output = temp_dir / "ui-ux-custom.html"
        render_to(
            custom_output,
            make_data("ui-ux", extra_section="market-analysis"),
            template,
        )
        custom = validate(custom_output, "ui-ux")
        if not any("appendix- prefix" in item for item in custom.errors):
            raise AssertionError("Unscoped custom section was not rejected")

        appendix_output = temp_dir / "ui-ux-appendix.html"
        render_to(
            appendix_output,
            make_data("ui-ux", extra_section="appendix-market"),
            template,
        )
        appendix = validate(appendix_output, "ui-ux")
        if appendix.errors:
            raise AssertionError(f"Scoped appendix was rejected: {appendix.errors}")

        filtered_data = make_filtered_data(
            "ui-ux",
            ["states", "mobile-touch"],
        )
        filtered_output = temp_dir / "ui-ux-filtered.html"
        render_to(filtered_output, filtered_data, template)
        filtered = validate(filtered_output, "ui-ux")
        if filtered.errors:
            raise AssertionError(
                f"Filtered UI scope failed validation: {filtered.errors}"
            )
        filtered_raw = filtered_output.read_text(encoding="utf-8")
        if 'name="gdd-scope-mode" content="filtered"' not in filtered_raw:
            raise AssertionError("Filtered scope metadata was not rendered")
        if 'id="information-architecture"' in filtered_raw:
            raise AssertionError("Unselected UI section was rendered")

        missing_core_data = make_filtered_data("ui-ux", ["states"])
        missing_core_data["document"]["scope"]["sections"].remove(  # type: ignore[index]
            "ui-objectives"
        )
        try:
            render_document(missing_core_data, template)
        except RenderError:
            pass
        else:
            raise AssertionError("Filtered scope accepted a missing core section")

        extra_scoped_data = make_filtered_data("ui-ux", ["states"])
        information_architecture = next(
            section
            for section in make_data("ui-ux")["sections"]  # type: ignore[index]
            if section["id"] == "information-architecture"
        )
        extra_scoped_data["sections"].append(information_architecture)  # type: ignore[index]
        try:
            render_document(extra_scoped_data, template)
        except RenderError:
            pass
        else:
            raise AssertionError(
                "Filtered scope accepted an unselected canonical section"
            )

        missing_selected_output = temp_dir / "ui-ux-filtered-missing.html"
        missing_selected_raw = re.sub(
            r'<section class="gdd-section" id="ui-states">.*?</section>',
            "",
            filtered_raw,
            count=1,
            flags=re.DOTALL,
        )
        missing_selected_output.write_text(
            missing_selected_raw,
            encoding="utf-8",
            newline="\n",
        )
        missing_selected = validate(missing_selected_output, "ui-ux")
        if not any(
            "Missing selected ui-ux sections" in item
            for item in missing_selected.errors
        ):
            raise AssertionError(
                "Validator accepted a missing selected filtered section"
            )

        unselected_output = temp_dir / "ui-ux-filtered-unselected.html"
        declared_match = re.search(
            r'(<meta name="gdd-sections" content=")([^"]*)(">)',
            filtered_raw,
        )
        if not declared_match:
            raise AssertionError("gdd-sections metadata was not found")
        states_only_plan = build_section_plan("ui-ux", ["states"])
        reduced_sections = ",".join(states_only_plan["selected_sections"])
        unselected_raw = (
            filtered_raw[: declared_match.start(2)]
            + reduced_sections
            + filtered_raw[declared_match.end(2) :]
        )
        unselected_raw = re.sub(
            r'(<meta name="gdd-facets" content=")[^"]*(">)',
            r"\1states\2",
            unselected_raw,
            count=1,
        )
        unselected_output.write_text(
            unselected_raw,
            encoding="utf-8",
            newline="\n",
        )
        unselected = validate(unselected_output, "ui-ux")
        if not any(
            "outside the filtered scope" in item
            for item in unselected.errors
        ):
            raise AssertionError(
                "Validator accepted an unselected canonical filtered section"
            )

        incomplete_facet_data = make_filtered_data(
            "system",
            ["formulas"],
        )
        system_core = set(PROFILE_RULES["system"]["core_ids"])
        incomplete_facet_data["sections"] = [  # type: ignore[index]
            section
            for section in incomplete_facet_data["sections"]  # type: ignore[index]
            if section["id"] in system_core
        ]
        incomplete_facet_data["document"]["scope"]["sections"] = [  # type: ignore[index]
            section_id
            for section_id in PROFILE_RULES["system"]["allowed_ids"]
            if section_id in system_core
        ]
        try:
            render_document(incomplete_facet_data, template)
        except RenderError:
            pass
        else:
            raise AssertionError(
                "Renderer accepted missing facet-triggered/dependency sections"
            )

        forged_facet_data = make_filtered_data("system", [])
        forged_facet_output = temp_dir / "system-forged-facet.html"
        render_to(forged_facet_output, forged_facet_data, template)
        forged_facet_raw = forged_facet_output.read_text(
            encoding="utf-8"
        ).replace(
            '<meta name="gdd-facets" content="">',
            '<meta name="gdd-facets" content="formulas">',
            1,
        )
        forged_facet_output.write_text(
            forged_facet_raw,
            encoding="utf-8",
            newline="\n",
        )
        forged_facet = validate(forged_facet_output, "system")
        if not any(
            "facet-triggered or dependency" in item
            for item in forged_facet.errors
        ):
            raise AssertionError(
                "Validator accepted missing facet-triggered/dependency sections"
            )

        invalid_data = make_data("concept")
        invalid_data["document"]["profile"] = "uiux"  # type: ignore[index]
        try:
            render_document(invalid_data, template)
        except RenderError:
            pass
        else:
            raise AssertionError("Unknown renderer profile was not rejected")

        invalid_facet_data = make_filtered_data("ui-ux", ["states"])
        invalid_facet_data["document"]["scope"]["facets"] = [  # type: ignore[index]
            "오류 상태"
        ]
        try:
            render_document(invalid_facet_data, template)
        except RenderError:
            pass
        else:
            raise AssertionError("Non-canonical scope facet was not rejected")

    print(f"[OK] {len(PROFILE_NAMES)} profile(s) rendered and validated")
    print("[OK] Profile reference files match the machine contracts")
    print("[OK] Profile-specific default filenames are distinct")
    print("[OK] Legacy profile-less input remains valid with an explicit profile")
    print(
        "[OK] Profile mismatch, foreign/custom section, appendix, "
        "duplicate chart, and unknown-profile guards passed"
    )
    print(
        "[OK] Filtered scope, core, selected-section, facet, "
        "and metadata guards passed"
    )
    print("[OK] Compact HTML and conditional visualization loading passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

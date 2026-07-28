#!/usr/bin/env python3
"""Regression tests for the 41 fine-grained game document kinds."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from interpret_request import InterpretError, interpret, parse_gddql
from kind_contracts import (
    CATEGORY_REFERENCE_FILES,
    KIND_CONTRACTS,
    KIND_NAMES,
    assert_kind_contracts_valid,
)
from profile_contracts import PROFILE_RULES
from render_gdd import (
    KIND_LABELS_EN,
    PROFILE_LABELS_KO,
    RenderError,
    default_output_path,
    render_document,
)
from test_profiles import TEMPLATE_PATH, make_filtered_data
from validate_gdd import validate

AUTHORITY_BOUNDARY_KO = (
    "게임 규칙과 사용자 결과를 정의한다. 구현 방식은 개발 협의에서 확정한다."
)
AUTHORITY_BOUNDARY_EN = (
    "Design defines game rules and user-facing outcomes. "
    "Implementation is finalized with engineering."
)


class KindRoutingTests(unittest.TestCase):
    def test_every_primary_label_routes_to_exact_kind_and_profile(self) -> None:
        for kind_name, contract in KIND_CONTRACTS.items():
            with self.subTest(kind=kind_name):
                result = interpret(f"{contract['label']} 작성")
                self.assertEqual(
                    result["filter"]["selected_kinds"],
                    [kind_name],
                )
                self.assertEqual(
                    result["filter"]["selected_profiles"],
                    [contract["profile"]],
                )
                self.assertEqual(
                    result["scope"]["document_plans"][0]["id"],
                    kind_name,
                )
                plan = result["scope"]["document_plans"][0]
                self.assertTrue(
                    set(contract["default_facets"]).issubset(plan["facets"])
                )
                self.assertEqual(
                    plan["required_outputs"],
                    list(contract["required_outputs"]),
                )
                self.assertEqual(
                    plan["default_excludes"],
                    list(contract["default_excludes"]),
                )
                self.assertEqual(
                    plan["handoffs"],
                    list(contract["handoffs"]),
                )

    def test_same_profile_kinds_remain_separate_in_mention_order(self) -> None:
        result = interpret(
            "캐릭터 시스템 기획서와 아이템 시스템 기획서를 각각 작성해줘"
        )
        self.assertEqual(
            result["filter"]["selected_kinds"],
            ["character-system", "item-system"],
        )
        self.assertEqual(result["filter"]["selected_profiles"], ["system"])
        self.assertEqual(
            [plan["id"] for plan in result["scope"]["document_plans"]],
            ["character-system", "item-system"],
        )
        self.assertEqual(
            set(result["scope"]["section_plans"]),
            {"character-system", "item-system"},
        )
        self.assertEqual(result["query"]["output"]["mode"], "split")

    def test_overlapping_korean_terms_choose_specific_kind(self) -> None:
        cases = {
            "캐릭터 시스템 기획서": "character-system",
            "캐릭터 전투 기획서": "character-combat",
            "캐릭터 설정서": "character-bible",
            "전투 시스템 기획서": "combat-system",
            "전투 밸런스 기획서": "combat-balance",
            "상점 UI 기획서": "ui-spec",
            "상점·상품 기획서": "store-product",
        }
        for request, expected in cases.items():
            with self.subTest(request=request):
                self.assertEqual(
                    interpret(request)["filter"]["selected_kinds"],
                    [expected],
                )

    def test_excluded_and_reference_only_kinds_are_not_outputs(self) -> None:
        cases = (
            "UI 기획서는 제외하고 캐릭터 시스템 기획서만 작성",
            "캐릭터 시스템 기획서만 작성하고 UI 기획서는 후속 참조",
            "입력 문서인 UI 기획서를 바탕으로 캐릭터 시스템 기획서 작성",
            "UI 기획서를 참고해 캐릭터 시스템 기획서 작성",
        )
        for request in cases:
            with self.subTest(request=request):
                result = interpret(request)
                self.assertEqual(
                    result["filter"]["selected_kinds"],
                    ["character-system"],
                )
                self.assertEqual(result["query"]["context"]["about"], "TBD")

    def test_generic_profile_fallback_still_works(self) -> None:
        result = parse_gddql(
            'DESIGN system\nABOUT "신규 규칙"\nGOAL "구현 명세";'
        )
        self.assertEqual(result["filter"]["selected_kinds"], [])
        self.assertEqual(result["filter"]["selected_profiles"], ["system"])
        self.assertEqual(
            result["scope"]["document_plans"][0]["id"],
            "system",
        )

    def test_generic_profile_and_kind_can_be_requested_together(self) -> None:
        first = interpret(
            "시스템 기획서와 UI 기획서를 각각 작성해줘"
        )
        self.assertEqual(
            first["filter"]["selected_generic_profiles"],
            ["system"],
        )
        self.assertEqual(first["filter"]["selected_kinds"], ["ui-spec"])
        self.assertEqual(
            [
                (document["id"], document["kind"])
                for document in first["filter"]["documents"]
            ],
            [("system", None), ("ui-spec", "ui-spec")],
        )
        second = parse_gddql(first["gddql"])
        self.assertEqual(
            second["filter"]["documents"],
            first["filter"]["documents"],
        )


class KindGDDQLTests(unittest.TestCase):
    def test_explicit_kind_clause_round_trips(self) -> None:
        first = parse_gddql(
            """
            DESIGN system
            KIND (character-system, item-system)
            ABOUT "수집형 RPG"
            GOAL "두 시스템을 각각 구현 명세"
            OUTPUT HTML SPLIT;
            """
        )
        second = parse_gddql(first["gddql"])
        self.assertEqual(first["query"], second["query"])
        self.assertEqual(
            first["filter"]["selected_kinds"],
            ["character-system", "item-system"],
        )

    def test_design_auto_derives_profiles_from_kinds(self) -> None:
        result = parse_gddql(
            """
            DESIGN AUTO
            KIND (wireframe, update-spec)
            ABOUT "시즌 업데이트"
            GOAL "화면 배치와 배포 변경점을 각각 전달"
            """
        )
        self.assertEqual(
            result["filter"]["selected_profiles"],
            ["ui-ux", "production"],
        )
        self.assertEqual(
            result["filter"]["selected_kinds"],
            ["wireframe", "update-spec"],
        )
        self.assertEqual(result["filter"]["confidence"], "high")
        self.assertFalse(result["filter"]["needs_clarification"])

    def test_extra_design_profile_becomes_generic_document(self) -> None:
        result = parse_gddql(
            """
            DESIGN (system, ui-ux)
            KIND ui-spec
            ABOUT "길드와 가입 화면"
            GOAL "규칙과 화면을 각각 전달"
            """
        )
        self.assertEqual(
            result["filter"]["selected_generic_profiles"],
            ["system"],
        )
        self.assertEqual(
            [
                (document["id"], document["kind"])
                for document in result["filter"]["documents"]
            ],
            [("system", None), ("ui-spec", "ui-spec")],
        )

    def test_auto_kind_is_inferred_from_context(self) -> None:
        result = parse_gddql(
            """
            DESIGN AUTO
            KIND AUTO
            ABOUT "제작·강화 시스템 기획서"
            GOAL "서버 구현 규칙"
            """
        )
        self.assertEqual(
            result["filter"]["selected_kinds"],
            ["crafting-enhancement-system"],
        )
        self.assertEqual(result["filter"]["selected_profiles"], ["system"])

    def test_kind_errors_are_actionable(self) -> None:
        invalid_queries = (
            (
                'DESIGN ui-ux\nKIND character-system\nABOUT "x"\nGOAL "x"',
                "incompatible",
            ),
            (
                'DESIGN AUTO\nKIND (AUTO, ui-spec)\nABOUT "x"\nGOAL "x"',
                "cannot be combined",
            ),
            (
                'DESIGN AUTO\nKIND unknown-kind\nABOUT "x"\nGOAL "x"',
                "unknown document kind",
            ),
            (
                'DESIGN system\nKIND (character-system,\nABOUT "x"\nGOAL "x"',
                "unbalanced parentheses",
            ),
            (
                "DESIGN system\n"
                "KIND (character-system, character-system)\n"
                'ABOUT "x"\nGOAL "x"',
                "duplicate document kinds",
            ),
        )
        for raw, fragment in invalid_queries:
            with self.subTest(fragment=fragment):
                with self.assertRaisesRegex(InterpretError, fragment):
                    parse_gddql(raw)


class KindRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def make_kind_data(self, kind_name: str) -> dict[str, object]:
        contract = KIND_CONTRACTS[kind_name]
        data = make_filtered_data(
            contract["profile"],
            list(contract["default_facets"]),
        )
        existing = {
            section["id"]
            for section in data["sections"]  # type: ignore[index]
        }
        for index, section_id in enumerate(
            data["document"]["scope"]["sections"]  # type: ignore[index]
        ):
            if section_id not in existing:
                data["sections"].append(  # type: ignore[index]
                    {
                        "id": section_id,
                        "number": f"K{index + 1:02d}",
                        "title": section_id.replace("-", " ").title(),
                        "blocks": [
                            {
                                "type": "lead",
                                "text": "kind 기본 패싯으로 선택된 계약 섹션이다.",
                            }
                        ],
                    }
                )
        data["document"]["kind"] = kind_name  # type: ignore[index]
        data["document"]["title"] = f"종류 테스트 {kind_name}"  # type: ignore[index]
        return data

    def test_all_kinds_render_and_validate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="game-gdd-kind-test-") as temp:
            temp_dir = Path(temp)
            for kind_name in KIND_NAMES:
                with self.subTest(kind=kind_name):
                    data = self.make_kind_data(kind_name)
                    output = temp_dir / f"{kind_name}.html"
                    output.write_text(
                        render_document(data, self.template),
                        encoding="utf-8",
                        newline="\n",
                    )
                    result = validate(
                        output,
                        KIND_CONTRACTS[kind_name]["profile"],
                        require_scope=True,
                        kind=kind_name,
                    )
                    self.assertEqual(result.errors, [])
                    self.assertEqual(result.kind, kind_name)
                    raw = output.read_text(encoding="utf-8")
                    self.assertIn(
                        f'name="gdd-kind" content="{kind_name}"',
                        raw,
                    )
                    self.assertIn(
                        ">" + KIND_CONTRACTS[kind_name]["label"] + "</strong>",
                        raw,
                    )
                    self.assertNotIn("기획서 종류 ·", raw)
                    self.assertIn(
                        'data-gdd-document-marker="kind"',
                        raw,
                    )
                    self.assertIn(AUTHORITY_BOUNDARY_KO, raw)
                    self.assertNotIn('class="brief-card"', raw)

    def test_english_kind_cover_uses_localized_markers(self) -> None:
        data = self.make_kind_data("ui-spec")
        data["document"]["language"] = "en"  # type: ignore[index]
        raw = render_document(data, self.template)
        self.assertIn(
            ">" + KIND_LABELS_EN["ui-spec"] + "</strong>",
            raw,
        )
        self.assertNotIn("Document kind ·", raw)
        self.assertIn(AUTHORITY_BOUNDARY_EN, raw)

    def test_kind_filename_replaces_broad_profile_suffix(self) -> None:
        with tempfile.TemporaryDirectory(prefix="game-gdd-name-test-") as temp:
            path = default_output_path(
                self.make_kind_data("ui-spec"),
                Path(temp),
            )
            self.assertIn("_ui-spec_GDD_", path.name)
            self.assertNotIn("_ui-ux_ui-spec_", path.name)

    def test_generic_profile_html_omits_kind_metadata(self) -> None:
        data = make_filtered_data("system", [])
        raw = render_document(data, self.template)
        self.assertNotIn('name="gdd-kind"', raw)
        self.assertIn(
            ">" + PROFILE_LABELS_KO["system"] + "</strong>",
            raw,
        )
        self.assertNotIn("기획서 영역 ·", raw)
        self.assertIn(
            'data-gdd-document-marker="profile"',
            raw,
        )
        self.assertIn(AUTHORITY_BOUNDARY_KO, raw)
        with tempfile.TemporaryDirectory(prefix="game-gdd-kind-meta-test-") as temp:
            output = Path(temp) / "generic.html"
            output.write_text(raw, encoding="utf-8", newline="\n")
            result = validate(
                output,
                "system",
                require_scope=True,
                kind="character-system",
            )
            self.assertTrue(
                any("Expected embedded gdd-kind" in item for item in result.errors)
            )

    def test_cover_omits_internal_classification_and_rejects_routing_subtitles(
        self,
    ) -> None:
        data = self.make_kind_data("character-system")
        raw = render_document(data, self.template)
        self.assertNotIn("기획서 종류 ·", raw)
        self.assertNotIn("Document kind ·", raw)
        self.assertNotIn("SYSTEM DESIGN SPECIFICATION", raw)
        self.assertNotIn('class="brand-symbol"', raw)
        self.assertNotIn("<span>FLOW</span>", raw)
        self.assertNotIn("<span>DATA</span>", raw)
        self.assertEqual(raw.count("data-gdd-doc-meta-field="), 5)
        self.assertNotIn("PROFILE_FIELD_LABEL", raw)

        prefixed = self.make_kind_data("character-system")
        prefixed["document"]["subtitle"] = (  # type: ignore[index]
            "문서 종류: 캐릭터 시스템 기획서"
        )
        with self.assertRaisesRegex(RenderError, "reader-facing copy"):
            render_document(prefixed, self.template)

        routed = self.make_kind_data("character-system")
        routed["document"]["subtitle"] = (  # type: ignore[index]
            "캐릭터 성장 규칙 (character-system / system)"
        )
        with self.assertRaisesRegex(RenderError, "routing notation"):
            render_document(routed, self.template)

        tbd = self.make_kind_data("character-system")
        tbd["decisions"] = [  # type: ignore[index]
            {
                "status": "검토 필요",
                "title": "성장 구간 기준",
                "detail": "밸런스 검증 후 확정한다.",
            }
        ]
        tbd_raw = render_document(tbd, self.template)
        self.assertIn('class="decision-status">검토 필요</span>', tbd_raw)
        self.assertNotIn('class="decision-status">TBD</span>', tbd_raw)

    def test_validator_rejects_missing_or_changed_cover_markers(self) -> None:
        data = self.make_kind_data("ui-spec")
        raw = render_document(data, self.template)
        missing_marker = re.sub(
            r'<strong class="document-type-marker"[^>]*>.*?</strong>',
            "",
            raw,
            count=1,
        )
        changed_boundary = raw.replace(
            AUTHORITY_BOUNDARY_KO,
            "구현 권한 경계가 변경됨",
            1,
        )
        with tempfile.TemporaryDirectory(prefix="game-gdd-cover-test-") as temp:
            temp_dir = Path(temp)
            marker_path = temp_dir / "missing-marker.html"
            marker_path.write_text(
                missing_marker,
                encoding="utf-8",
                newline="\n",
            )
            marker_result = validate(marker_path)
            self.assertTrue(
                any(
                    "document marker" in item.lower()
                    for item in marker_result.errors
                )
            )
            boundary_path = temp_dir / "changed-boundary.html"
            boundary_path.write_text(
                changed_boundary,
                encoding="utf-8",
                newline="\n",
            )
            boundary_result = validate(boundary_path)
            self.assertTrue(
                any(
                    "authority boundary" in item.lower()
                    for item in boundary_result.errors
                )
            )

    def test_validator_rejects_standalone_project_brief_card(self) -> None:
        raw = render_document(self.make_kind_data("ui-spec"), self.template)
        self.assertNotIn('class="brief-card"', raw)
        reintroduced_brief = raw.replace(
            '<div class="project-meta">',
            '<div class="brief-card">Obsolete project brief</div>'
            '<div class="project-meta">',
            1,
        )
        with tempfile.TemporaryDirectory(prefix="game-gdd-brief-test-") as temp:
            output = Path(temp) / "brief-card.html"
            output.write_text(
                reintroduced_brief,
                encoding="utf-8",
                newline="\n",
            )
            result = validate(output)
            self.assertTrue(
                any(
                    "project brief" in item.lower()
                    for item in result.errors
                )
            )

    def test_kind_profile_and_default_facet_guards(self) -> None:
        mismatch = self.make_kind_data("ui-spec")
        mismatch["document"]["profile"] = "system"  # type: ignore[index]
        with self.assertRaisesRegex(RenderError, "requires profile"):
            render_document(mismatch, self.template)

        missing_default = self.make_kind_data("ui-spec")
        facets = missing_default["document"]["scope"]["facets"]  # type: ignore[index]
        facets.remove(KIND_CONTRACTS["ui-spec"]["default_facets"][0])
        with self.assertRaisesRegex(RenderError, "missing defaults"):
            render_document(missing_default, self.template)

        missing_scope = self.make_kind_data("ui-spec")
        del missing_scope["document"]["scope"]  # type: ignore[index]
        with self.assertRaisesRegex(RenderError, "scope is required"):
            render_document(missing_scope, self.template)

    def test_category_references_cover_every_contract_anchor(self) -> None:
        for category, relative_path in CATEGORY_REFERENCE_FILES.items():
            path = TEMPLATE_PATH.parent.parent / relative_path
            self.assertTrue(path.exists(), category)
            raw = path.read_text(encoding="utf-8")
            for kind_name, contract in KIND_CONTRACTS.items():
                if contract["category"] == category:
                    self.assertIn(f"`{kind_name}`", raw)
                    self.assertEqual(
                        raw.count(f'id="{kind_name}"'),
                        1,
                    )
                    row = next(
                        line
                        for line in raw.splitlines()
                        if line.startswith("| ")
                        and f"`{kind_name}`" in line.split("|")[1]
                    )
                    handoff_cell = row.strip("|").split("|")[5]
                    output_text = handoff_cell.split("출력:", 1)[1]
                    reference_handoffs = tuple(
                        re.findall(
                            r"`([a-z][a-z0-9-]+)`",
                            output_text,
                        )
                    )
                    self.assertEqual(
                        contract["handoffs"],
                        reference_handoffs,
                    )
                    self.assertGreaterEqual(
                        len(contract["default_excludes"]),
                        2,
                    )
                    self.assertLessEqual(
                        len(contract["default_excludes"]),
                        4,
                    )
                    self.assertTrue(
                        all(
                            re.fullmatch(
                                r"[a-z0-9]+(?:-[a-z0-9]+)*",
                                token,
                            )
                            for token in contract["default_excludes"]
                        )
                    )


if __name__ == "__main__":
    assert_kind_contracts_valid()
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Regression tests for natural-request routing, GDDQL, and scope filtering."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parent
SKILL_DIR = REPO_ROOT / "skill" / "game-gdd-html"
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from interpret_request import (  # noqa: E402
    InterpretError,
    interpret,
    parse_gddql,
)
from profile_contracts import build_section_plan  # noqa: E402


class NaturalLanguageRoutingTests(unittest.TestCase):
    """Lock the 15 representative Korean first-filter decisions."""

    CASES = (
        {
            "name": "artifact_type_beats_topic",
            "request": "강화 시스템 UI 기획서",
            "profiles": ("ui-ux",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "excluded_ui_system_spec",
            "request": (
                "상점 UI는 제외하고 구매 규칙·상태·데이터를 "
                "시스템 기획서로"
            ),
            "profiles": ("system",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "two_explicit_documents",
            "request": (
                "UI 기획서와 강화 시스템 기획서를 각각 HTML로"
            ),
            "profiles": ("ui-ux", "system"),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "selected_profiles_combined_not_full",
            "request": "UI와 시스템 통합 기획서를 한 문서로",
            "profiles": ("ui-ux", "system"),
            "mode": "merge",
            "clarification": False,
        },
        {
            "name": "explicit_master_gdd",
            "request": "게임 전체 통합 GDD",
            "profiles": ("full",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "generic_gdd_requires_domain",
            "request": "신작 게임 GDD 작성해줘",
            "profiles": (),
            "mode": "split",
            "clarification": True,
        },
        {
            "name": "content_bundle",
            "request": (
                "던전 입장·반복 루프, 해금, 최초 보상 구조를 "
                "설계해줘"
            ),
            "profiles": ("content",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "spatial_level_bundle",
            "request": (
                "던전 맵의 분기 동선, 적 조우, 체크포인트를 "
                "배치해줘"
            ),
            "profiles": ("level",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "level_up_means_balance",
            "request": (
                "캐릭터 레벨업 경험치 곡선과 스탯 성장 "
                "시뮬레이션"
            ),
            "profiles": ("balance",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "economy_bundle",
            "request": (
                "유료·무료 재화의 획득·소비, 환율, "
                "인플레이션을 설계"
            ),
            "profiles": ("economy",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "live_operations_bundle",
            "request": (
                "4주 이벤트 캘린더, 세그먼트, 배포·롤백, "
                "CS 런북"
            ),
            "profiles": ("live-ops",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "narrative_bundle",
            "request": (
                "퀘스트 분기와 캐릭터 대사, 세계관 정합성을 "
                "설계"
            ),
            "profiles": ("narrative",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "business_bundle",
            "request": (
                "투자자용 시장 규모, LTV/CAC, 출시 전략 문서"
            ),
            "profiles": ("business",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "concept_bundle",
            "request": (
                "플레이어 판타지, 코어 루프, MVP 가설을 "
                "피치용으로"
            ),
            "profiles": ("concept",),
            "mode": "split",
            "clarification": False,
        },
        {
            "name": "ambiguous_event_reward",
            "request": "이벤트 보상 구조를 설계해줘",
            "profiles": (),
            "mode": "split",
            "clarification": True,
        },
    )

    def test_representative_korean_requests(self) -> None:
        for case in self.CASES:
            with self.subTest(case=case["name"]):
                result = interpret(case["request"])
                selected = result["filter"]["selected_profiles"]
                self.assertCountEqual(selected, case["profiles"])
                self.assertEqual(
                    result["query"]["output"]["mode"],
                    case["mode"],
                )
                self.assertEqual(
                    result["filter"]["needs_clarification"],
                    case["clarification"],
                )
                if case["profiles"]:
                    self.assertCountEqual(
                        result["query"]["profiles"],
                        case["profiles"],
                    )
                else:
                    self.assertEqual(
                        result["query"]["profiles"],
                        ["AUTO"],
                    )
                if case["clarification"]:
                    self.assertTrue(result["filter"]["question_hint"])
                else:
                    self.assertNotIn("profile", result["unresolved"])

    def test_explicit_artifact_evidence_is_auditable(self) -> None:
        result = interpret("강화 시스템 UI 기획서")
        ui_candidate = next(
            candidate
            for candidate in result["filter"]["candidates"]
            if candidate["profile"] == "ui-ux"
        )
        self.assertIn("ui 기획서", ui_candidate["explicit"])
        self.assertGreaterEqual(ui_candidate["score"], 100)
        self.assertEqual(result["query"]["context"]["about"], "강화 시스템")

    def test_ambiguous_request_does_not_silently_become_full(self) -> None:
        result = interpret("게임 기획서")
        self.assertEqual(result["filter"]["selected_profiles"], [])
        self.assertEqual(result["query"]["profiles"], ["AUTO"])
        self.assertTrue(result["filter"]["needs_clarification"])
        self.assertIn("profile", result["unresolved"])

    def test_full_and_detail_artifacts_are_both_preserved(self) -> None:
        result = interpret("통합 GDD와 UI 기획서를 만들어줘")
        self.assertCountEqual(
            result["filter"]["selected_profiles"],
            ["full", "ui-ux"],
        )
        self.assertEqual(result["query"]["output"]["mode"], "split")
        self.assertFalse(result["filter"]["needs_clarification"])

    def test_english_design_imperative_remains_natural_language(self) -> None:
        result = interpret(
            "Design a UI/UX specification for a mobile RPG"
        )
        self.assertEqual(result["input_mode"], "natural")
        self.assertEqual(
            result["filter"]["selected_profiles"],
            ["ui-ux"],
        )


class GDDQLParsingTests(unittest.TestCase):
    def test_explicit_query_parses_every_clause(self) -> None:
        raw = """
        -- implementation handoff
        DESIGN ui-ux
        FROM "Project Orion"
        ABOUT "장비 강화 화면"
        FOR "UI 디자이너, 클라이언트 개발자, QA"
        GOAL "구현 가능한 화면 명세"
        WITH states, interaction, accessibility
        WITHOUT economy-loop
        ASSUME platform="mobile", orientation="portrait"
        OUTPUT HTML SPLIT;
        """
        result = parse_gddql(raw)

        self.assertEqual(result["input_mode"], "gddql")
        self.assertEqual(result["filter"]["selected_profiles"], ["ui-ux"])
        self.assertEqual(result["query"]["context"]["from"], "Project Orion")
        self.assertEqual(result["query"]["context"]["about"], "장비 강화 화면")
        self.assertEqual(
            result["query"]["context"]["for"],
            "UI 디자이너, 클라이언트 개발자, QA",
        )
        self.assertEqual(
            result["query"]["context"]["goal"],
            "구현 가능한 화면 명세",
        )
        self.assertEqual(
            result["query"]["with"],
            ["states", "interaction", "accessibility"],
        )
        self.assertEqual(result["query"]["without"], ["economy-loop"])
        self.assertEqual(
            result["query"]["assumptions"],
            {"platform": "mobile", "orientation": "portrait"},
        )
        self.assertEqual(
            result["query"]["output"],
            {"format": "HTML", "mode": "split"},
        )

    def test_profile_aliases_and_multi_default_to_split(self) -> None:
        result = parse_gddql(
            """
            DESIGN (UI, 시스템)
            ABOUT "장비 강화"
            GOAL "화면과 처리 규칙을 각각 명세"
            """
        )
        self.assertEqual(
            result["filter"]["selected_profiles"],
            ["ui-ux", "system"],
        )
        self.assertEqual(result["query"]["output"]["mode"], "split")

    def test_auto_design_runs_the_natural_language_filter(self) -> None:
        result = parse_gddql(
            """
            DESIGN AUTO
            ABOUT "장비 강화 UI 기획서"
            GOAL "화면 흐름과 오류 상태를 개발팀에 전달"
            OUTPUT HTML SPLIT;
            """
        )
        self.assertEqual(result["filter"]["selected_profiles"], ["ui-ux"])
        self.assertIn(
            "AUTO profile inference",
            result["filter"]["reason"],
        )
        self.assertEqual(result["query"]["profiles"], ["ui-ux"])

    def test_rendered_gddql_is_parseable_again(self) -> None:
        first = parse_gddql(
            """
            DESIGN (system, ui-ux)
            FROM "Project Lumen"
            ABOUT "장비 강화"
            FOR "개발팀"
            GOAL "구현 명세"
            WITH rules, states
            WITHOUT accessibility
            ASSUME platform="mobile"
            OUTPUT HTML MERGE;
            """
        )
        second = parse_gddql(first["gddql"])

        self.assertEqual(second["query"], first["query"])
        self.assertEqual(
            second["filter"]["selected_profiles"],
            first["filter"]["selected_profiles"],
        )

    def test_missing_context_is_unresolved_not_fabricated(self) -> None:
        result = parse_gddql("DESIGN system")
        self.assertCountEqual(result["unresolved"], ["about", "goal"])
        self.assertEqual(result["query"]["context"]["about"], "")
        self.assertEqual(result["query"]["context"]["goal"], "")


class ScopeFilterTests(unittest.TestCase):
    def test_natural_scope_terms_expand_into_profile_sections(self) -> None:
        result = interpret(
            "강화 UI 기획서. 포함: 접근성, 오류 상태"
        )
        plan = result["scope"]["section_plans"]["ui-ux"]
        self.assertIn("accessibility", result["scope"]["facets"])
        self.assertIn("states", result["scope"]["facets"])
        self.assertIn("accessibility", plan["selected_sections"])
        self.assertIn("ui-states", plan["selected_sections"])
        self.assertIn("interaction-rules", plan["selected_sections"])

    def test_natural_scope_include_exclude_collision_is_unresolved(self) -> None:
        result = interpret(
            "강화 UI 기획서. 포함: 접근성. 제외: 접근성"
        )
        self.assertTrue(result["scope"]["conflicts"])
        self.assertTrue(result["filter"]["needs_clarification"])
        self.assertIn("scope-conflict", result["unresolved"])

    def test_excluding_a_kind_default_reports_conflict(self) -> None:
        result = interpret("강화 UI 기획서. 접근성은 제외하고 작성해줘")
        plan = result["scope"]["section_plans"]["ui-ux"]
        self.assertNotIn("accessibility", result["scope"]["facets"])
        self.assertIn("accessibility", result["scope"]["exclude_facets"])
        self.assertIn("accessibility", plan["selected_sections"])
        self.assertTrue(result["scope"]["conflicts"])
        self.assertTrue(result["filter"]["needs_clarification"])

    def test_exclusion_uses_nearest_clause_not_prior_inclusion(self) -> None:
        result = interpret(
            "UI 기획서는 화면 흐름을 포함하되 접근성은 빼고 작성해줘"
        )
        self.assertIn("flow", result["scope"]["facets"])
        self.assertNotIn("flow", result["scope"]["exclude_facets"])
        self.assertIn(
            "accessibility",
            result["scope"]["exclude_facets"],
        )
        self.assertTrue(result["scope"]["conflicts"])

    def test_no_focus_selects_only_core_sections(self) -> None:
        plan = build_section_plan("ui-ux", [])
        self.assertEqual(
            plan["selected_sections"],
            [
                "ui-objectives",
                "user-flow",
                "screen-specs",
                "handoff-qa",
            ],
        )
        self.assertTrue(
            all(
                reasons == ["core"]
                for reasons in plan["section_reasons"].values()
            )
        )

    def test_trigger_adds_section_and_transitive_dependency(self) -> None:
        plan = build_section_plan("ui-ux", ["accessibility"])
        self.assertIn("accessibility", plan["selected_sections"])
        self.assertIn("interaction-rules", plan["selected_sections"])
        self.assertIn("screen-specs", plan["selected_sections"])
        self.assertIn(
            "dependency:accessibility",
            plan["section_reasons"]["interaction-rules"],
        )

    def test_balance_simulation_adds_scenarios_and_curves(self) -> None:
        plan = build_section_plan("balance", ["simulation"])
        for section_id in ("scenarios", "simulation", "curves"):
            self.assertIn(section_id, plan["selected_sections"])
        self.assertIn(
            "dependency:simulation",
            plan["section_reasons"]["curves"],
        )

    def test_explicit_section_adds_business_dependency(self) -> None:
        plan = build_section_plan("business", ["go-to-market"])
        self.assertIn("go-to-market", plan["selected_sections"])
        self.assertIn(
            "competitive-positioning",
            plan["selected_sections"],
        )
        self.assertIn(
            "dependency:go-to-market",
            plan["section_reasons"]["competitive-positioning"],
        )

    def test_optional_section_can_be_excluded(self) -> None:
        plan = build_section_plan("ui-ux", [], ["accessibility"])
        self.assertNotIn("accessibility", plan["selected_sections"])
        self.assertIn("accessibility", plan["excluded_sections"])
        self.assertEqual(plan["conflicts"], [])

    def test_excluding_a_core_section_reports_conflict(self) -> None:
        plan = build_section_plan("ui-ux", [], ["user-flow"])
        self.assertIn("user-flow", plan["selected_sections"])
        self.assertIn(
            "cannot exclude core section: user-flow",
            plan["conflicts"],
        )

    def test_same_trigger_in_with_and_without_reports_conflict(self) -> None:
        plan = build_section_plan("ui-ux", ["states"], ["states"])
        self.assertIn("ui-states", plan["selected_sections"])
        self.assertIn(
            "section is both included and excluded: ui-states",
            plan["conflicts"],
        )

    def test_excluding_a_dependency_reports_conflict(self) -> None:
        plan = build_section_plan(
            "narrative",
            ["dialogue"],
            ["characters"],
        )
        self.assertIn("dialogue", plan["selected_sections"])
        self.assertIn("characters", plan["selected_sections"])
        self.assertIn(
            "cannot exclude required dependency: characters",
            plan["conflicts"],
        )

    def test_unknown_facet_is_preserved_for_review(self) -> None:
        plan = build_section_plan("system", ["guild-cross-server-rule"])
        self.assertEqual(
            plan["unknown_facets"],
            ["guild-cross-server-rule"],
        )

    def test_other_profile_facet_is_ignored_not_questioned(self) -> None:
        plan = build_section_plan("ui-ux", ["rules"])
        self.assertEqual(plan["unknown_facets"], [])
        self.assertEqual(plan["ignored_facets"], ["rules"])

    def test_gddql_scope_conflict_reaches_filter_and_unresolved(self) -> None:
        result = parse_gddql(
            """
            DESIGN narrative
            ABOUT "동료 퀘스트"
            GOAL "분기 대사 설계"
            WITH dialogue
            WITHOUT characters
            OUTPUT HTML SPLIT;
            """
        )
        plan = result["scope"]["section_plans"]["narrative"]
        self.assertTrue(plan["conflicts"])
        self.assertTrue(result["scope"]["conflicts"])
        self.assertTrue(result["filter"]["needs_clarification"])
        self.assertIn("scope-conflict", result["unresolved"])
        self.assertIn(
            "포함·제외 범위가 충돌합니다",
            result["filter"]["question_hint"],
        )


class InvalidInputTests(unittest.TestCase):
    CASES = (
        (
            "missing_design",
            'ABOUT "장비 강화"',
            "requires exactly one DESIGN",
        ),
        (
            "duplicate_design",
            "DESIGN system\nDESIGN ui-ux",
            "requires exactly one DESIGN",
        ),
        (
            "auto_mixed_with_profile",
            "DESIGN (AUTO, ui-ux)",
            "AUTO cannot be combined",
        ),
        (
            "unknown_profile",
            "DESIGN technical",
            "unknown profile",
        ),
        (
            "unsupported_output_format",
            "DESIGN system\nOUTPUT PDF SPLIT",
            "OUTPUT format must be HTML",
        ),
        (
            "unsupported_output_mode",
            "DESIGN system\nOUTPUT HTML ZIP",
            "OUTPUT mode must be SPLIT or MERGE",
        ),
        (
            "extra_output_token",
            "DESIGN system\nOUTPUT HTML SPLIT EXTRA",
            "OUTPUT accepts only format and mode",
        ),
        (
            "duplicate_scalar_clause",
            'DESIGN system\nABOUT "A"\nABOUT "B"',
            "ABOUT may appear only once",
        ),
        (
            "invalid_assumption",
            "DESIGN system\nASSUME mobile",
            "ASSUME items must use key=value",
        ),
        (
            "unknown_clause",
            'DESIGN system\nFOCUS "states"',
            "expected one of",
        ),
        (
            "empty_scalar",
            "DESIGN system\nGOAL",
            "clause value must not be empty",
        ),
        (
            "unterminated_quoted_scalar",
            'DESIGN system\nABOUT "장비 강화',
            "invalid quoted string",
        ),
    )

    def test_invalid_gddql_is_rejected_with_actionable_error(self) -> None:
        for name, raw, message in self.CASES:
            with self.subTest(case=name):
                with self.assertRaisesRegex(
                    InterpretError,
                    re.escape(message),
                ):
                    parse_gddql(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)

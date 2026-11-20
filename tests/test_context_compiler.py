#!/usr/bin/env python3
"""Regression tests for the token-efficient authoring context compiler."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parent
SKILL_DIR = REPO_ROOT / "skill" / "game-gdd-html"
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_context import (  # noqa: E402
    AUTHORING_PLACEHOLDER,
    _kind_reference_contract,
    _profile_reference_contract,
    compile_context,
    render_markdown,
    write_authoring_pack,
)
from kind_contracts import KIND_CONTRACTS, KIND_NAMES  # noqa: E402
from profile_contracts import PROFILE_NAMES, PROFILE_RULES  # noqa: E402
from render_gdd import RenderError, render_document  # noqa: E402


def kind_query(kind_name: str) -> str:
    return f"""
    DESIGN AUTO
    KIND {kind_name}
    ABOUT "Representative game feature"
    GOAL "Create the requested game design document"
    OUTPUT HTML SPLIT;
    """


def profile_query(profile: str) -> str:
    return f"""
    DESIGN {profile}
    ABOUT "Representative game"
    GOAL "Create the requested profile document"
    OUTPUT HTML SPLIT;
    """


def replace_placeholder(value: object) -> object:
    if isinstance(value, str):
        return value.replace(AUTHORING_PLACEHOLDER, "검증용 확정 내용")
    if isinstance(value, list):
        return [replace_placeholder(item) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_placeholder(item)
            for key, item in value.items()
        }
    return value


class ContractEquivalenceTests(unittest.TestCase):
    def test_every_kind_keeps_its_full_machine_contract(self) -> None:
        for kind_name in KIND_NAMES:
            with self.subTest(kind=kind_name):
                context = compile_context(kind_query(kind_name))
                self.assertEqual(context["status"], "ready")
                self.assertEqual(len(context["documents"]), 1)
                document = context["documents"][0]
                source = KIND_CONTRACTS[kind_name]
                self.assertEqual(document["kind"], kind_name)
                self.assertEqual(document["profile"], source["profile"])
                self.assertEqual(
                    document["kind_contract"]["required_outputs"],
                    list(source["required_outputs"]),
                )
                self.assertEqual(
                    document["kind_contract"]["default_excludes"],
                    list(source["default_excludes"]),
                )
                self.assertEqual(
                    document["kind_contract"]["handoffs"],
                    list(source["handoffs"]),
                )
                for key in (
                    "purpose_and_audience",
                    "must_answer",
                    "required_deliverables",
                    "explicit_excludes",
                    "done_when",
                ):
                    self.assertTrue(document["kind_contract"][key])
                expected_sections = document["scope"]["sections"]
                actual_sections = [
                    item["id"]
                    for item in document["profile_contract"]["sections"]
                ]
                self.assertEqual(actual_sections, expected_sections)

    def test_every_profile_reference_covers_every_allowed_section(self) -> None:
        for profile in PROFILE_NAMES:
            with self.subTest(profile=profile):
                allowed = list(PROFILE_RULES[profile]["allowed_ids"])
                contract = _profile_reference_contract(profile, allowed)
                self.assertEqual(
                    [item["id"] for item in contract["sections"]],
                    allowed,
                )
                self.assertTrue(contract["objective"])
                self.assertTrue(contract["guardrails"])

    def test_every_kind_reference_row_is_parseable(self) -> None:
        for kind_name in KIND_NAMES:
            with self.subTest(kind=kind_name):
                contract = _kind_reference_contract(kind_name)
                self.assertTrue(all(contract.values()))

    def test_generic_profiles_keep_scope_and_visual_contracts(self) -> None:
        for profile in PROFILE_NAMES:
            with self.subTest(profile=profile):
                context = compile_context(profile_query(profile))
                document = context["documents"][0]
                expected = PROFILE_RULES[profile]
                self.assertIsNone(document["kind"])
                self.assertEqual(
                    document["scope"]["sections"],
                    list(expected["core_ids"]),
                )
                self.assertEqual(
                    document["visual_contract"],
                    {
                        "mermaid_min": int(expected["mermaid_min"]),
                        "mermaid_recommended": int(
                            expected["mermaid_recommended"]
                        ),
                        "chart_policy": str(expected["chart_policy"]),
                    },
                )


class ContextEfficiencyTests(unittest.TestCase):
    def test_assumptions_reach_the_saved_authoring_pack_for_split_documents(self) -> None:
        query = ('DESIGN (system, ui-ux)\nABOUT "강화 결과"\n'
                 'ASSUME result-animation="희귀도별 2.75초"\nASSUME retries="0회"\nOUTPUT HTML SPLIT;')
        context = compile_context(query)
        self.assertEqual(context["status"], "ready")
        expected = {"result-animation": "희귀도별 2.75초", "retries": "0회"}
        self.assertEqual([doc["assumptions"] for doc in context["documents"]], [expected, expected])
        with tempfile.TemporaryDirectory() as folder:
            manifest = write_authoring_pack(context, Path(folder))
            instructions = Path(manifest["context"]).read_text(encoding="utf-8")
        for key, value in expected.items():
            self.assertEqual(instructions.count(f"- {key} = {value}"), 2)

    def test_complete_authoring_context_is_at_least_80_percent_smaller(
        self,
    ) -> None:
        context = compile_context(kind_query("character-system"))
        compact_size = (
            len((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
            + len(render_markdown(context))
            + len(
                json.dumps(
                    context["documents"][0]["scaffold"],
                    ensure_ascii=False,
                )
            )
        )
        legacy_files = (
            "SKILL.md",
            "references/gddql.md",
            "references/prompt-01-interpret.md",
            "references/planning-authority-boundary.md",
            "references/prompt-03-scope.md",
            "references/kinds/system.md",
            "references/profiles/system.md",
            "references/prompt-05-author.md",
            "references/input-schema.md",
            "references/practical-writing-style.md",
            "references/prompt-06-review.md",
            "references/quality-checklist.md",
        )
        legacy_size = sum(
            len((SKILL_DIR / path).read_text(encoding="utf-8"))
            for path in legacy_files
        )
        self.assertLess(compact_size, legacy_size * 0.20)

    def test_ambiguous_request_emits_only_a_question_pack(self) -> None:
        context = compile_context("Create a game design document")
        self.assertEqual(context["status"], "needs-clarification")
        self.assertTrue(context["question"])
        self.assertNotIn("documents", context)
        self.assertIn("작성 전 확인 필요", render_markdown(context))

    def test_writer_creates_context_and_scaffolds_without_overwrite(self) -> None:
        context = compile_context(kind_query("character-system"))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            first = write_authoring_pack(context, output_dir)
            second = write_authoring_pack(context, output_dir)
            self.assertTrue(Path(first["context"]).is_file())
            self.assertTrue(Path(first["scaffolds"][0]["path"]).is_file())
            self.assertNotEqual(first["context"], second["context"])
            self.assertNotEqual(
                first["scaffolds"][0]["path"],
                second["scaffolds"][0]["path"],
            )

    def test_multiple_requested_kinds_remain_separate(self) -> None:
        context = compile_context(
            "캐릭터 시스템 기획서와 UI 기획서를 각각 작성해줘. "
            "성장 규칙과 상태 피드백을 포함해줘."
        )
        self.assertEqual(context["status"], "ready")
        self.assertEqual(context["output_mode"], "split")
        self.assertEqual(
            [document["kind"] for document in context["documents"]],
            ["character-system", "ui-spec"],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = write_authoring_pack(context, Path(temp_dir))
            self.assertEqual(len(manifest["scaffolds"]), 2)
            self.assertNotEqual(
                manifest["scaffolds"][0]["path"],
                manifest["scaffolds"][1]["path"],
            )


class ScaffoldQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (
            SKILL_DIR / "assets" / "gdd-template.html"
        ).read_text(encoding="utf-8")

    def test_scaffold_has_exact_scope_and_placeholder_guards(self) -> None:
        context = compile_context(kind_query("character-system"))
        document = context["documents"][0]
        scaffold = document["scaffold"]
        self.assertEqual(
            scaffold["document"]["scope"]["sections"],
            document["scope"]["sections"],
        )
        self.assertEqual(
            [item["id"] for item in scaffold["sections"]],
            document["scope"]["sections"],
        )
        with self.assertRaisesRegex(
            RenderError,
            "unresolved authoring placeholders",
        ):
            render_document(scaffold, self.template)

    def test_filled_scaffold_renders_but_empty_section_is_rejected(self) -> None:
        context = compile_context(kind_query("character-system"))
        scaffold = replace_placeholder(
            copy.deepcopy(context["documents"][0]["scaffold"])
        )
        self.assertIsInstance(scaffold, dict)
        render_document(scaffold, self.template)
        scaffold["sections"][0]["blocks"] = []  # type: ignore[index]
        with self.assertRaisesRegex(
            RenderError,
            "blocks must be a non-empty array",
        ):
            render_document(scaffold, self.template)


if __name__ == "__main__":
    unittest.main(verbosity=2)

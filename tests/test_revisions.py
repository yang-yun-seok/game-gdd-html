#!/usr/bin/env python3
"""Behavioral invariants for source round trips and bounded document revisions."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_profiles import SKILL_DIR, SCRIPT_DIR, TEMPLATE_PATH, make_data
from compile_context import depth_contract
from document_source import LegacyDocument, SOURCE_PATTERN, embed_source, load_document
from profile_contracts import PROFILE_NAMES
from render_gdd import render_document
from revise_gdd import compare, load_comparison, prepare


class RevisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = make_data("system")
        self.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def save(self, name: str, data: dict | None = None) -> Path:
        path = self.root / name
        path.write_text(json.dumps(self.data if data is None else data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_all_profile_documents_round_trip_losslessly(self) -> None:
        for profile in PROFILE_NAMES:
            with self.subTest(profile=profile):
                data = make_data(profile)
                original = copy.deepcopy(data)
                path = self.root / f"{profile}.html"
                path.write_text(render_document(data, self.template), encoding="utf-8")
                self.assertEqual(load_document(path), original)
                self.assertEqual(data, original)

    def test_source_cannot_close_script_or_become_executable(self) -> None:
        text = '</script><script>alert("test")</script> & < > \u2028 \u2029'
        self.data["summary"] = text
        path = self.root / "escaped.html"
        raw = render_document(self.data, self.template)
        path.write_text(raw, encoding="utf-8")
        source = SOURCE_PATTERN.search(raw).group(1)
        self.assertNotIn("<", source)
        self.assertNotIn("&", source)
        self.assertEqual(load_document(path)["summary"], text)

    def test_visible_manual_edits_do_not_load_stale_source(self) -> None:
        path = self.root / "edited.html"
        raw = render_document(self.data, self.template)
        path.write_text(raw.replace("</h1>", " 수동 수정</h1>", 1), encoding="utf-8")
        with self.assertRaises(LegacyDocument):
            load_document(path)
        result = prepare(path, "비용을 수정해줘", self.root / "revision")
        self.assertEqual(result["status"], "needs-reconstruction")
        self.assertNotIn("candidate", result)

    def test_old_html_returns_evidence_without_inventing_a_candidate(self) -> None:
        path = self.root / "legacy.html"
        path.write_text('<html><head><meta name="gdd-profile" content="system"><style>hidden</style></head>'
                        '<body><section id="rules"><h2>규칙</h2><table><tr><td>비용</td><td>100</td></tr></table>'
                        '</section><script>not evidence</script></body></html>', encoding="utf-8")
        original = path.read_bytes()
        result = prepare(path, "비용을 150으로", self.root)
        evidence = json.loads(Path(result["evidence"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "needs-reconstruction")
        self.assertIn("100", evidence["visible_text"])
        self.assertNotIn("not evidence", evidence["visible_text"])
        self.assertNotIn("hidden", evidence["visible_text"])
        self.assertEqual(evidence["metadata"]["gdd-profile"], "system")
        self.assertEqual(path.read_bytes(), original)

    def test_editing_only_embedded_json_requires_reconciliation(self) -> None:
        path = self.root / "source-edited.html"
        raw = render_document(self.data, self.template)
        match = SOURCE_PATTERN.search(raw)
        payload = json.loads(match.group(1))
        payload["data"]["summary"] = "source only change"
        raw = raw[:match.start(1)] + json.dumps(payload, ensure_ascii=False) + raw[match.end(1):]
        path.write_text(raw, encoding="utf-8")
        with self.assertRaises(LegacyDocument):
            load_document(path)

    def test_repeated_prepare_keeps_original_and_each_baseline(self) -> None:
        source = self.save("source.json")
        raw = source.read_bytes()
        first = prepare(source, "비용 수정", self.root)
        baseline_bytes = Path(first["baseline"]).read_bytes()
        changed = copy.deepcopy(self.data)
        changed["sections"][0]["blocks"][0]["text"] = "수정한 후보"
        Path(first["candidate"]).write_text(json.dumps(changed), encoding="utf-8")
        second = prepare(source, "재검토", self.root)
        self.assertNotEqual(first["baseline"], second["baseline"])
        self.assertNotEqual(first["candidate"], second["candidate"])
        self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(Path(first["baseline"]).read_bytes(), baseline_bytes)
        self.assertEqual(load_document(Path(second["candidate"])), self.data)

    def test_render_cli_never_overwrites_an_existing_document(self) -> None:
        source = self.save("source.json")
        output = self.root / "existing.html"
        output.write_text("keep this", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT_DIR / "render_gdd.py"), str(source), "-o", str(output)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep this")

    def test_cli_checks_snapshot_before_comparing_same_edits(self) -> None:
        command = [sys.executable, "-B", "-X", "utf8", str(SCRIPT_DIR / "revise_gdd.py")]
        source = self.root / "original.html"
        source.write_text(render_document(self.data, self.template), encoding="utf-8")
        output = ["--output-dir", str(self.root)]
        pack = json.loads(subprocess.check_output(
            command + ["prepare", "--source", str(source), "--request", "Change cost", *output],
            encoding="utf-8"))
        candidate = Path(pack["candidate"])
        changed = copy.deepcopy(self.data)
        changed["summary"] = "Updated cost"
        candidate.write_text(json.dumps(changed), encoding="utf-8")
        source.unlink()  # New preparations are self-contained after capturing the baseline.
        args = command + ["compare", "--manifest", pack["manifest"], *output]
        result = json.loads(subprocess.check_output(args, encoding="utf-8"))
        self.assertEqual((result["status"], result["baseline_integrity"]), ("needs-review", "verified"))
        Path(pack["baseline"]).write_bytes(candidate.read_bytes())
        old_args = command + ["compare", "--baseline", pack["baseline"], "--updated", str(candidate), *output]
        for invocation in (args, old_args):
            with self.subTest(invocation=invocation):
                failed = subprocess.run(invocation, capture_output=True, encoding="utf-8")
                self.assertEqual(failed.returncode, 2)
                self.assertIn("Baseline differs", failed.stderr)
                self.assertNotIn("unchanged", failed.stdout)

    def test_different_prepare_runs_cannot_be_paired(self) -> None:
        source = self.save("source.json")
        first = prepare(source, "수정", self.root)
        second = prepare(source, "다른 수정", self.root)
        for manifest in (None, Path(first["manifest"])):
            with self.subTest(manifest=manifest), self.assertRaisesRegex(ValueError, "same prepare run"):
                load_comparison(manifest, Path(first["baseline"]), Path(second["candidate"]))

    def test_legacy_manifest_authenticates_baseline_against_original(self) -> None:
        source = self.save("original.json")
        pack = prepare(source, "수정", self.root)
        path = Path(pack["manifest"])
        legacy = json.loads(path.read_text(encoding="utf-8"))
        del legacy["baseline_sha256"]
        path.write_text(json.dumps(legacy), encoding="utf-8")
        self.assertEqual(load_comparison(path, None, None)[2], "verified")
        changed = copy.deepcopy(self.data)
        changed["summary"] = "Data changed"
        Path(pack["baseline"]).write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Baseline differs"):
            load_comparison(path, None, None)
        source.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Original source changed"):
            load_comparison(path, None, None)

    def test_standalone_document_comparison_remains_available(self) -> None:
        original = self.save("original.json")
        updated = self.save("updated.json")
        self.assertEqual(load_comparison(None, original, updated), (self.data, self.data, "standalone"))

    def test_diff_detects_actual_value_and_keeps_semantic_review_pending(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["sections"][0]["blocks"][0]["text"] = "비용 150개"
        result = compare(self.data, changed, allowed_sections=[self.data["sections"][0]["id"]])
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(result["semantic_review"], "required")
        self.assertEqual(result["changes"][0]["path"], "/sections/0/blocks/0/text")
        self.assertEqual(result["changes"][0]["after"], "비용 150개")

    def test_unrelated_section_edits_are_blocked_when_bounded(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["sections"][1]["blocks"][0]["text"] = "범위 밖 변경"
        result = compare(self.data, changed, allowed_sections=[self.data["sections"][0]["id"]])
        self.assertEqual(result["status"], "blocked")

    def test_deleted_sections_and_scope_changes_require_explicit_intent(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["sections"].pop()
        self.assertEqual(compare(self.data, changed)["status"], "blocked")
        self.assertEqual(compare(self.data, changed, allow_scope_change=True)["status"], "needs-review")
        changed = copy.deepcopy(self.data)
        changed["document"]["profile"] = "concept"
        self.assertEqual(compare(self.data, changed)["contract_changes"], ["profile"])

    def test_reordering_is_visible_without_false_section_content_changes(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["sections"].reverse()
        result = compare(self.data, changed)
        self.assertTrue(result["section_order_changed"])
        self.assertEqual(result["section_changes"], [])
        self.assertEqual(result["status"], "needs-review")

    def test_reordering_sections_outside_allowlist_is_blocked(self) -> None:
        changed = copy.deepcopy(self.data)
        sections = changed["sections"]
        sections[0], sections[1] = sections[1], sections[0]
        result = compare(self.data, changed, allowed_sections=[sections[2]["id"]])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(set(result["reordered_sections"]), {sections[0]["id"], sections[1]["id"]})
        allowed = compare(self.data, changed, allowed_sections=result["reordered_sections"])
        self.assertEqual(allowed["status"], "needs-review")

    def test_type_only_changes_respect_section_allowlist(self) -> None:
        section = self.data["sections"][0]
        section["blocks"].append({"type": "table", "columns": ["value"], "rows": [[1]]})
        changed = copy.deepcopy(self.data)
        changed["sections"][0]["blocks"][-1]["rows"][0][0] = True
        result = compare(self.data, changed, allowed_sections=[self.data["sections"][1]["id"]])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["section_changes"], [{"id": section["id"], "change": "modified"}])

    def test_duplicate_ids_and_unknown_allowlist_are_rejected(self) -> None:
        bad = copy.deepcopy(self.data)
        bad["sections"][1]["id"] = bad["sections"][0]["id"]
        with self.assertRaises(ValueError):
            prepare(self.save("bad.json", bad), "수정", self.root)
        self.assertEqual(compare(self.data, self.data, allowed_sections=["typo"])["status"], "blocked")

    def test_json_pointer_escaping_and_metadata_changes_are_not_lost(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["document"]["version"] = "0.2"
        changed["custom/key~"] = {"value": 1}
        result = compare(self.data, changed)
        paths = {item["path"] for item in result["changes"]}
        self.assertIn("/custom~1key~0", paths)
        self.assertIn("/document/version", paths)

    def test_no_change_does_not_claim_a_semantic_pass(self) -> None:
        result = compare(self.data, copy.deepcopy(self.data))
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(result["semantic_review"], "not-run")

    def test_embedded_source_conflicts_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            embed_source('<body><script id="gdd-source"></script></body>', self.data)
        with self.assertRaises(ValueError):
            embed_source("no body", self.data)

    def test_profileless_legacy_json_preserves_content_for_reconstruction(self) -> None:
        legacy = copy.deepcopy(self.data)
        del legacy["document"]["profile"]
        source = self.save("legacy.json", legacy)
        result = prepare(source, "비용만 수정", self.root)
        self.assertEqual(result["status"], "needs-reconstruction")
        evidence = json.loads(Path(result["evidence"]).read_text(encoding="utf-8"))
        self.assertEqual(evidence["document_data"], legacy)
        self.assertEqual(load_document(source), legacy)
        self.assertNotIn("candidate", result)

    def test_profile_depth_context_stays_selective(self) -> None:
        source = (SKILL_DIR / "references" / "design-depth.md").read_text(encoding="utf-8")
        for profile in PROFILE_NAMES:
            with self.subTest(profile=profile):
                contract = depth_contract(profile)
                self.assertTrue(contract.strip())
                self.assertLess(len(contract), len(source) / 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

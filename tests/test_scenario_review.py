"""Exercise the scenario review through the document validator."""

import json
import tempfile
import unittest
from pathlib import Path

from test_profiles import TEMPLATE_PATH, make_filtered_data, render_to
from validate_gdd import validate


class ScenarioReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.output = Path(temp.name) / "system.html"
        self.review = Path(temp.name) / "review.json"
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        document = make_filtered_data("system", ["flow", "rules", "qa"])
        content = [
            {"type": "paragraph", "text": "Target gone: cancel and keep all coins."},
            {"type": "mermaid", "title": "Completion", "code": "flowchart LR\nA -->|gone| B[Cancel with no cost]"},
            {"type": "paragraph", "text": "At 3 seconds, missing target leaves the party with 150 coins."},
        ]
        document["sections"][0]["blocks"] = content + document["sections"][0]["blocks"]
        render_to(self.output, document, template)
        self.case = {"input": "Target disappears at 3 seconds, balance 150."}
        for index, (role, field) in enumerate([("rule", "text"), ("diagram", "code"), ("qa", "text")]):
            self.case[role] = {"path": f"/sections/0/blocks/{index}/{field}",
                               "quote": content[index][field], "outcome": "cancel; 150 coins"}

    def errors(self):
        self.review.write_text(json.dumps({"scenarios": [self.case]}), encoding="utf-8")
        return validate(self.output, "system", require_scope=True, scenario_review=self.review).errors

    def test_independent_traces_with_agreeing_outcomes(self):
        self.assertEqual(self.errors(), [])
        self.case["diagram"] = {"out_of_scope": "Only the entry flow is in scope for this case."}
        self.assertEqual(self.errors(), [])

    def test_mismatch_stale_citation_and_missing_qa_are_reported(self):
        self.case["diagram"]["outcome"] = "success; 0 coins"
        self.case["qa"]["quote"] = "No such acceptance criterion"
        issues = self.errors()
        self.assertTrue(any("different outcomes" in error for error in issues))
        self.assertTrue(any("quote missing" in error for error in issues))
        del self.case["qa"]
        self.assertTrue(any(".qa: missing trace" in error for error in self.errors()))


if __name__ == "__main__":
    unittest.main()

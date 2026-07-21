"""Tests for validate_phase1.py against the fixtures in fixtures/phase1/."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import validate_phase1 as vp

FIXTURES = os.path.join(HERE, "fixtures", "phase1")


def run_cli(name_or_path, extra=None):
    path = name_or_path if os.path.isabs(name_or_path) \
        else os.path.join(FIXTURES, name_or_path)
    argv = [path, "--json"] + list(extra or [])
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = vp.main(argv)
    output = buffer.getvalue()
    report = json.loads(output) if output.strip() else None
    return code, report


def failed_gates(report):
    return {f["gate"] for f in report["failures"]}


class ValidatePhase1Tests(unittest.TestCase):

    def test_pass_clean(self):
        code, report = run_cli("pass_clean.json")
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["failures"], [])

    def test_fail_placeholder(self):
        code, report = run_cli("fail_placeholder.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G5"})
        g5 = [f for f in report["failures"] if f["gate"] == "G5"]
        self.assertTrue(any("<RESEARCH_QUESTION>" in f["message"] for f in g5))
        self.assertIn("gemini", {f["lane"] for f in g5})

    def test_fail_assignment_mismatch(self):
        code, report = run_cli("fail_assignment_mismatch.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G3"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("SQ2", message)
        self.assertIn("Gemini", message)

    def test_fail_single_evidence_lane(self):
        code, report = run_cli("fail_single_evidence_lane.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G4"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("SQ3", message)

    def test_pass_contaminant_in_audit(self):
        code, report = run_cli("pass_contaminant_in_audit.json")
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["failures"], [])

    def test_fail_contaminant_in_prompt(self):
        code, report = run_cli("fail_contaminant_in_prompt.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G7"})
        g7 = [f for f in report["failures"] if f["gate"] == "G7"]
        self.assertIn("gemini", {f["lane"] for f in g7})

    def test_fail_ground_truth_shape(self):
        code, report = run_cli("fail_ground_truth_shape.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G8"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("metric_definition", message)
        self.assertIn("https://", message)

    def test_allowlist_suppresses_placeholder(self):
        handle, rules_path = tempfile.mkstemp(suffix=".json")
        self.addCleanup(os.remove, rules_path)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump({"placeholder_allowlist": ["<RESEARCH_QUESTION>"]}, fh)
        code, report = run_cli("fail_placeholder.json",
                               ["--project-rules", rules_path])
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")

    def test_unparseable_document_exits_2(self):
        handle, path = tempfile.mkstemp(suffix=".md")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write("no json object anywhere in this file\n")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), \
                contextlib.redirect_stderr(io.StringIO()):
            code = vp.main([path, "--json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

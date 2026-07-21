"""Tests for gate_phase2.py against the fixtures in fixtures/phase2/."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gate_phase2 as gp

FIXTURES = os.path.join(HERE, "fixtures", "phase2")
PROMPT_SRC = os.path.join(FIXTURES, "02a-prompts-lanea.md")
PROMPT_TAIL = "End of staged prompt for lane lanea."


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as fh:
        return fh.read()


class GatePhase2Tests(unittest.TestCase):

    def stage(self, fixture, with_prompt=True, transform=None):
        workdir = tempfile.mkdtemp(prefix="gate2-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        text = read_fixture(fixture)
        if transform is not None:
            text = transform(text)
        with open(os.path.join(workdir, "02-lanea.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if with_prompt:
            shutil.copyfile(PROMPT_SRC, os.path.join(workdir, "02a-prompts-lanea.md"))
        return workdir

    def status(self, report, check):
        return report["files"][0]["checks"][check]["status"]

    def details(self, report, check):
        return " ".join(report["files"][0]["checks"][check]["details"])

    def test_pass_clean_lane(self):
        report = gp.run([self.stage("pass_clean_lane.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["split_method"], "sentinel")
        for check in ("C1", "C2", "C3", "C4", "C5", "C6"):
            self.assertEqual(self.status(report, check), "PASS", check)

    def test_pass_escaped_tags(self):
        report = gp.run([self.stage("pass_escaped_tags.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C3"), "PASS")

    def test_fail_echo_empty_answer(self):
        report = gp.run([self.stage("fail_echo_empty_answer.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("concealed", self.details(report, "C5"))

    def test_fail_hidden_span_footnotes(self):
        report = gp.run([self.stage("fail_hidden_span_footnotes.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C4"), "FAIL")
        self.assertEqual(self.status(report, "C5"), "FAIL")

    def test_fail_claims_without_delivery(self):
        report = gp.run([self.stage("fail_claims_without_delivery.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertEqual(self.status(report, "C6"), "FAIL")
        self.assertEqual(self.status(report, "C5"), "PASS")

    def test_fail_echo_no_boundary(self):
        report = gp.run([self.stage("fail_echo_no_boundary.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertIn("boundary indeterminate", self.details(report, "C1"))
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")

    def test_prompt_tail_split(self):
        def swap(text):
            return text.replace("===BEGIN LANE OUTPUT===", PROMPT_TAIL)
        report = gp.run([self.stage("pass_clean_lane.md", transform=swap)])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["split_method"], "prompt-tail")

    def test_missing_prompt_noted(self):
        report = gp.run([self.stage("pass_clean_lane.md", with_prompt=False)])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["split_method"], "sentinel")
        self.assertTrue(any("prompt file not found" in n
                            for n in report["files"][0]["notes"]))

    def test_main_exit_codes(self):
        passing = self.stage("pass_clean_lane.md")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(gp.main([passing, "--json"]), 0)
        json.loads(buffer.getvalue())
        failing = self.stage("fail_claims_without_delivery.md")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gp.main([failing, "--json"]), 1)
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            code = gp.main([os.path.join(passing, "missing-subdir"), "--json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

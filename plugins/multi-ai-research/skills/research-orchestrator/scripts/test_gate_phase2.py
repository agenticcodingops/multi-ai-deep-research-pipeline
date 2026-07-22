"""Tests for gate_phase2.py against the fixtures in fixtures/phase2/."""

import contextlib
import io
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gate_phase2 as gp

FIXTURES = os.path.join(HERE, "fixtures", "phase2")
PROMPT_SRC = os.path.join(FIXTURES, "02a-prompts-lanea.md")
DEBATE_PROMPT_SRC = os.path.join(FIXTURES, "02b-prompts-debate-lanea.md")
PROMPT_TAIL = "End of staged prompt for lane lanea."
REFERENCES = os.path.join(HERE, "..", "references")


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as fh:
        return fh.read()


def extract_skeleton():
    """The OUTPUT FORMAT skeleton shipped in references/01-prompts-library.md."""
    path = os.path.join(REFERENCES, "01-prompts-library.md")
    with open(path, "r", encoding="utf-8") as fh:
        doc = fh.read()
    blocks = re.findall(
        r"OUTPUT FORMAT \(machine-checked[^\n]*\n(?:.+\n)*?"
        r"[^\n]*live https URL\.\n", doc)
    return blocks[0] if blocks else ""


_FILL = {
    "tldr": [
        "- The pipeline generator is the right fit for a hobby photography "
        "gallery site because its image tooling removes recurring manual work.",
        "- Build-speed differences are immaterial below one thousand images, "
        "a scale this project will not reach in its first years.",
        "- Free static hosting tiers cover an image-heavy hobby blog with "
        "room to spare, storage being the only real constraint.",
    ],
    "findings": [
        "Built-in image pipelines resize and compress photographs at build "
        "time, so gallery pages ship responsive derivatives instead of "
        "full-size originals, which keeps page weight flat as the library "
        "grows past a few hundred photographs",
        "The theme registry lists dozens of maintained portfolio themes and "
        "the three most popular each shipped a release within the past year, "
        "a fair proxy for ecosystem health across every option compared in "
        "this pass of the research",
        "Community benchmarks report full rebuilds of a five-hundred-image "
        "site completing well under a minute on a mid-range laptop, though "
        "methodology varies between posts and only the cold-cache numbers "
        "carry real comparative weight",
    ],
    "conflicts": "Benchmark threads disagree about incremental build "
        "behaviour: some posters measure only changed pages being rebuilt "
        "while others observe full-site rebuilds after any template edit, "
        "and no post isolates cache configuration cleanly enough to settle "
        "which behaviour is the default.",
    "wwc": "A reproducible benchmark showing another generator building the "
        "same five-hundred-image reference site materially faster, or "
        "credible evidence that the image pipeline mangles embedded colour "
        "profiles in exported photographs, would overturn the recommendation "
        "made here.",
    "sources": ["- https://example.com/evidence", "- https://example.org/report",
                "- https://example.net/data"],
    "gaps": "Nothing in this pass verified how accessible the default themes "
        "are with a screen reader, and print stylesheet quality was not "
        "assessed at all.",
}
_ITEM_LINE_RE = re.compile(
    r"(\d+\. \[[A-Z]+\] )<[^>]*>(\. Source: https://\S+)$")


def fill_skeleton(skeleton):
    """Fill the shipped skeleton verbatim: slots get content, format lines
    stay byte-for-byte, the title and trailing instruction lines are not
    output. This is what a lane doing the literal minimum emits."""
    out = []
    for line in skeleton.splitlines():
        if line.startswith("OUTPUT FORMAT ("):
            continue
        if line.startswith("Headings are plain"):
            break
        if line.startswith("==="):
            out.append("===BEGIN LANE OUTPUT===")
            continue
        if line == "- <verdict bullet — three of these>":
            out.extend(_FILL["tldr"])
            continue
        if line == "- <at least 3 distinct https URLs, one per line>":
            out.extend(_FILL["sources"])
            continue
        m = _ITEM_LINE_RE.match(line)
        if m:
            index = int(line.split(".", 1)[0]) - 1
            out.append(m.group(1) + _FILL["findings"][index] + m.group(2))
            continue
        out.append(line)
        if line == "## Conflicts and uncertainties":
            out.append(_FILL["conflicts"])
        elif line == "## What would change your recommendation":
            out.append(_FILL["wwc"])
        elif line == "## Coverage gaps":
            out.append(_FILL["gaps"])
    return "\n".join(out) + "\n"


class GatePhase2Tests(unittest.TestCase):

    def workdir(self):
        path = tempfile.mkdtemp(prefix="gate2-")
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        return path

    def stage(self, fixture, with_prompt=True, transform=None):
        workdir = self.workdir()
        text = read_fixture(fixture)
        if transform is not None:
            text = transform(text)
        with open(os.path.join(workdir, "02-lanea.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if with_prompt:
            shutil.copyfile(PROMPT_SRC, os.path.join(workdir, "02a-prompts-lanea.md"))
        return workdir

    def stage_text(self, text, with_prompt=True):
        workdir = self.workdir()
        with open(os.path.join(workdir, "02-lanea.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if with_prompt:
            shutil.copyfile(PROMPT_SRC, os.path.join(workdir, "02a-prompts-lanea.md"))
        return workdir

    def stage_debate(self, fixture):
        workdir = self.workdir()
        shutil.copyfile(os.path.join(FIXTURES, fixture),
                        os.path.join(workdir, "02b-debate-lanea.md"))
        shutil.copyfile(DEBATE_PROMPT_SRC,
                        os.path.join(workdir, "02b-prompts-debate-lanea.md"))
        return workdir

    def status(self, report, check):
        return report["files"][0]["checks"][check]["status"]

    def details(self, report, check):
        return " ".join(report["files"][0]["checks"][check]["details"])

    # ------------------------------------------------------------ pass cases
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

    def test_hidden_echo_before_sentinel_passes_c5(self):
        report = gp.run([self.stage("pass_hidden_echo_before_sentinel.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C5"), "PASS")
        self.assertEqual(report["files"][0]["split_method"], "sentinel")

    def test_sources_assignment_line_not_heading(self):
        def insert(text):
            return text.replace(
                "3. [MEDIUM] Community benchmark",
                'Sources = ["alpha", "beta"]\n3. [MEDIUM] Community benchmark')
        report = gp.run([self.stage("pass_clean_lane.md", transform=insert)])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C2"), "PASS")

    def test_pass_paren_bold_headings(self):
        report = gp.run([self.stage("pass_paren_bold_headings.md")])
        self.assertEqual(report["result"], "pass")
        for check in ("C2", "C3", "C6"):
            self.assertEqual(self.status(report, check), "PASS", check)

    def test_pass_blockquote_headings_and_items(self):
        report = gp.run([self.stage("pass_blockquote_lane.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C2"), "PASS")
        self.assertEqual(self.status(report, "C3"), "PASS")

    def test_pass_compound_tags(self):
        report = gp.run([self.stage("pass_compound_tags.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C3"), "PASS")
        self.assertEqual(self.status(report, "C4"), "PASS")

    def test_pseudo_tags_fail_c3(self):
        report = gp.run([self.stage("fail_pseudo_tags.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C3"), "FAIL")

    def test_skeleton_fill_round_trips_gate(self):
        # The shipped OUTPUT FORMAT skeleton, filled verbatim with minimal
        # slot content, must pass this gate — locks the skeleton ->
        # gate_phase2 loop generatively (re-derived from the doc each run).
        skeleton = extract_skeleton()
        self.assertTrue(skeleton, "skeleton not found in references/01")
        report = gp.run([self.stage_text(fill_skeleton(skeleton))])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["split_method"], "sentinel")
        for check in ("C1", "C2", "C3", "C4", "C5", "C6"):
            self.assertEqual(self.status(report, check), "PASS", check)

    def test_pass_skeleton_fill_fixture(self):
        # The committed fixture is byte-identical to the regenerated fill,
        # so it cannot drift from the shipped skeleton.
        self.assertEqual(read_fixture("pass_skeleton_fill.md"),
                         fill_skeleton(extract_skeleton()))
        report = gp.run([self.stage("pass_skeleton_fill.md")])
        self.assertEqual(report["result"], "pass")

    def test_debate_template_fill_round_trips_gate(self):
        # Overlay 13's Mode 2 template must keep every cue the debate gate
        # checks for, and an output following it verbatim must pass.
        path = os.path.join(REFERENCES, "13-overlay-deliberation-modes.md")
        with open(path, "r", encoding="utf-8") as fh:
            doc = fh.read()
        start = doc.index("DEBATE this decision.")
        block = doc[start:doc.index("```", start)]
        for cue in ("===BEGIN LANE OUTPUT===",
                    "Position: FOR or Position: AGAINST",
                    "position statement", "evidence + reasoning", "rebuttal",
                    "flip", "KEY TENSION", "COMMON GROUND", "[REASONED]"):
            self.assertIn(cue, block, cue)
        report = gp.run([self.stage_debate("pass_debate_template_fill.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["kind"], "debate")
        for check in ("C1", "C2", "C3", "C4"):
            self.assertEqual(self.status(report, check), "PASS", check)

    def test_rubric_echo_not_a_tag(self):
        self.assertIsNone(gp.TAG_RE.search(
            "tag each claim [HIGH, MEDIUM, or LOW] as instructed"))
        self.assertIsNotNone(gp.TAG_RE.search(
            "[HIGH, GROUND-TRUTH-ASSERTED (GT11)]"))

    def test_quoted_sublist_not_phantom_items(self):
        def insert(text):
            return text.replace(
                "3. [MEDIUM] Community benchmark",
                "   > 1. Create the site and note the storage quota.\n"
                "   > 2. Upload the gallery and confirm the derivatives render.\n"
                "3. [MEDIUM] Community benchmark")
        report = gp.run([self.stage("pass_clean_lane.md", transform=insert)])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C3"), "PASS")

    # ---------------------------------------------------------------- C1
    def test_fail_echo_empty_answer(self):
        report = gp.run([self.stage("fail_echo_empty_answer.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "prompt-tail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("concealed", self.details(report, "C5"))

    def test_fail_echo_no_boundary(self):
        report = gp.run([self.stage("fail_echo_no_boundary.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertIn("boundary indeterminate", self.details(report, "C1"))
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")

    def test_diluted_echo_fails_c1(self):
        text = ("Cite every factual claim with a LIVE, resolvable URL and "
                "prioritise primary sources over aggregators.\n\n"
                "The lane stopped after restating one requirement and produced "
                "no structured answer at all.\n")
        report = gp.run([self.stage_text(text)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")
        self.assertIn("boundary indeterminate", self.details(report, "C1"))

    def test_no_sentinel_no_echo_fails_c1(self):
        def strip_all(text):
            return text.split("===BEGIN LANE OUTPUT===", 1)[1]
        report = gp.run([self.stage("pass_clean_lane.md", transform=strip_all)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertEqual(report["files"][0]["split_method"], "unsplit")
        self.assertIn("boundary unverifiable", self.details(report, "C1"))

    def test_duplicate_tail_fails_c1(self):
        def duplicate(text):
            return text.replace("===BEGIN LANE OUTPUT===", PROMPT_TAIL) + \
                "\n" + PROMPT_TAIL + "\n"
        report = gp.run([self.stage("pass_clean_lane.md", transform=duplicate)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
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

    # ---------------------------------------------------------------- C5
    def test_fail_hidden_span_footnotes(self):
        report = gp.run([self.stage("fail_hidden_span_footnotes.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C4"), "FAIL")
        self.assertEqual(self.status(report, "C5"), "FAIL")

    def test_hidden_nested_fails_c5(self):
        report = gp.run([self.stage("fail_hidden_nested.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("concealed", self.details(report, "C5"))

    def test_hidden_unclosed_fails_c5(self):
        report = gp.run([self.stage("fail_hidden_unclosed.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("malformed hidden markup", self.details(report, "C5"))

    def test_hidden_class_fails_c5(self):
        report = gp.run([self.stage("fail_hidden_class.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("concealed", self.details(report, "C5"))

    def test_hidden_comment_fails_c5(self):
        report = gp.run([self.stage("fail_hidden_comment.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C5"), "FAIL")
        self.assertIn("hidden comment", self.details(report, "C5"))

    # ---------------------------------------------------------------- C4
    def test_dead_markers_equal_urls_fails_c4(self):
        report = gp.run([self.stage("fail_dead_markers_equal.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C4"), "FAIL")
        self.assertIn("dead citation markers", self.details(report, "C4"))

    def test_http_urls_dont_count(self):
        report = gp.run([self.stage("fail_http_only_sources.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C4"), "FAIL")
        self.assertIn("distinct https URLs", self.details(report, "C4"))
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertIn("Sources", self.details(report, "C2"))

    def test_dead_marker_forms(self):
        sample = u"[1, 2] [3-4] [3–4] [^note] [HIGH] [REASONED] [GROUND-TRUTH-VERIFIED]"
        self.assertEqual(gp._dead_marker_count(sample), 4)

    def test_compound_tag_not_dead_marker(self):
        sample = (u"[HIGH, GROUND-TRUTH-ASSERTED (GT11)] [MEDIUM — caveat] "
                  u"[HIGH confidence]")
        self.assertEqual(gp._dead_marker_count(sample), 0)

    # ---------------------------------------------------------------- C2/C6
    def test_fail_claims_without_delivery(self):
        report = gp.run([self.stage("fail_claims_without_delivery.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertEqual(self.status(report, "C6"), "FAIL")
        self.assertEqual(self.status(report, "C5"), "PASS")

    # ---------------------------------------------------------------- debate
    def test_pass_debate_lane(self):
        report = gp.run([self.stage_debate("pass_debate_lanea.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["kind"], "debate")
        self.assertEqual(self.status(report, "C2"), "PASS")
        self.assertEqual(self.status(report, "C3"), "PASS")
        self.assertEqual(self.status(report, "C6"), "-")

    def test_fail_debate_missing_elements(self):
        report = gp.run([self.stage_debate("fail_debate_missing_elements.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertIn("common ground", self.details(report, "C2"))
        self.assertEqual(self.status(report, "C3"), "FAIL")
        self.assertIn("[REASONED]", self.details(report, "C3"))

    def test_debate_position_statement_header(self):
        report = gp.run([self.stage_debate("pass_debate_position_statement.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["files"][0]["kind"], "debate")
        self.assertEqual(self.status(report, "C2"), "PASS")

    # ---------------------------------------------------------------- URL vetting
    def test_ssrf_rejected_pre_request(self):
        for ip in ("127.0.0.1", "10.0.0.1", "169.254.169.254"):
            with self.subTest(ip=ip):
                infos = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]
                with mock.patch("socket.getaddrinfo", return_value=infos), \
                        mock.patch("http.client.HTTPSConnection") as conn:
                    result = gp._head_check("https://internal-service.example.org/x")
                self.assertIn("non-public", result)
                conn.assert_not_called()

    def test_credentials_url_rejected(self):
        with mock.patch("socket.getaddrinfo") as gai, \
                mock.patch("http.client.HTTPSConnection") as conn:
            result = gp._head_check("https://user:secret@example.org/")
        self.assertIn("credentials", result)
        gai.assert_not_called()
        conn.assert_not_called()

    def test_local_hostname_rejected(self):
        with mock.patch("socket.getaddrinfo") as gai, \
                mock.patch("http.client.HTTPSConnection") as conn:
            result = gp._head_check("https://printer.local/status")
        self.assertIn("non-public hostname", result)
        gai.assert_not_called()
        conn.assert_not_called()

    # ---------------------------------------------------------------- CLI
    def test_bad_thresholds_exit_2(self):
        workdir = self.stage("pass_clean_lane.md")
        cases = [["--min-findings", "-1"], ["--url-ratio", "nan"],
                 ["--url-ratio", "0"], ["--url-ratio", "inf"],
                 ["--min-answer-chars", "x"]]
        for extra in cases:
            with self.subTest(extra=extra):
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    code = gp.main([workdir, "--json"] + extra)
                self.assertEqual(code, 2)

    def test_explicit_prompt_missing_exits_2(self):
        workdir = self.stage("pass_clean_lane.md")
        out_file = os.path.join(workdir, "02-lanea.md")
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            code = gp.main([out_file, "--prompt",
                            os.path.join(workdir, "nope.md"), "--json"])
        self.assertEqual(code, 2)
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            code = gp.main([workdir, "--prompts-dir",
                            os.path.join(workdir, "nope-dir"), "--json"])
        self.assertEqual(code, 2)

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
        # Malformed HTML must still yield valid JSON and exit 0/1, no traceback.
        mangled = self.stage_text(
            "<div <span ===BEGIN LANE OUTPUT===\n<p><b>fragment</i></div></span>\n")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = gp.main([mangled, "--json"])
        self.assertIn(code, (0, 1))
        json.loads(buffer.getvalue())


if __name__ == "__main__":
    unittest.main()

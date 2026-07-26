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

    def stage(self, fixture, with_prompt=True, transform=None, prompt=None):
        workdir = self.workdir()
        text = read_fixture(fixture)
        if transform is not None:
            text = transform(text)
        with open(os.path.join(workdir, "02-lanea.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if with_prompt:
            source = os.path.join(FIXTURES, prompt) if prompt else PROMPT_SRC
            shutil.copyfile(source, os.path.join(workdir, "02a-prompts-lanea.md"))
        return workdir

    def stage_text(self, text, with_prompt=True):
        workdir = self.workdir()
        with open(os.path.join(workdir, "02-lanea.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if with_prompt:
            shutil.copyfile(PROMPT_SRC, os.path.join(workdir, "02a-prompts-lanea.md"))
        return workdir

    def stage_debate(self, fixture, prompt=None):
        workdir = self.workdir()
        shutil.copyfile(os.path.join(FIXTURES, fixture),
                        os.path.join(workdir, "02b-debate-lanea.md"))
        source = os.path.join(FIXTURES, prompt) if prompt else DEBATE_PROMPT_SRC
        shutil.copyfile(source,
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
        for check in ("C1", "C2", "C3", "C4", "C8"):
            self.assertEqual(self.status(report, check), "PASS", check)
        self.assertIn("matches the staged assignment", self.details(report, "C8"))

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

    def test_multi_sentinel_fails_c1(self):
        # PF-12: a multi-assignment lane file can draw one sentinel per
        # assignment. The split takes the LAST one, so the earlier answers are
        # silently discarded as "echo" and the gate scores a fraction of the
        # lane's work as a clean PASS.
        report = gp.run([self.stage("fail_multi_sentinel.md",
                                    prompt="02a-prompts-multi.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "sentinel")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertIn("lane emitted 2 sentinels", self.details(report, "C1"))
        self.assertIn("discarded 1 answer", self.details(report, "C1"))

    def test_clean_answer_unmarked_is_not_echo(self):
        # PF-20: a correct answer repeats the six MANDATED section headings by
        # construction, and a multi-assignment prompt file repeats them once
        # per assignment. Neither is echo evidence — reporting it as echo sends
        # the operator hunting for something that is not there, and destroys the
        # distinction that decides the remedy.
        report = gp.run([self.stage("fail_clean_but_unmarked.md",
                                    prompt="02a-prompts-multi.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "unsplit")
        self.assertIn("boundary unverifiable", self.details(report, "C1"))
        self.assertIn("no prompt echo", self.details(report, "C1"))
        self.assertNotIn("boundary indeterminate", self.details(report, "C1"))
        for check in ("C2", "C3", "C4", "C5", "C6"):
            self.assertEqual(self.status(report, check), "PASS", check)

    def test_c1_publishes_the_echo_diagnostics(self):
        # The diagnostics are advisory only — there is no marker-repair route —
        # but every metric the echo predicate uses must reach the report, so
        # nobody re-derives them with a different normaliser.
        report = gp.run([self.stage("fail_clean_but_unmarked.md",
                                    prompt="02a-prompts-multi.md")])
        diag = report["files"][0]["echo_diagnostics"]
        self.assertEqual(diag["prompt_lines_matched"], 0)
        self.assertEqual(diag["longest_contiguous_run"], 0)
        self.assertEqual(diag["leading_lines_matched"], 0)
        self.assertLess(diag["prompt_shingle_coverage"], gp._COVERAGE_LIMIT)
        report = gp.run([self.stage("fail_echo_no_boundary.md")])
        self.assertGreater(
            report["files"][0]["echo_diagnostics"]["longest_contiguous_run"], 0)

    # ---------------------------------------- renderer-transformed echo (W2)
    def _echoed_then_answer(self, mutate_echo):
        prompt = read_fixture("02a-prompts-lanea.md")
        answer = read_fixture("pass_clean_lane.md").split(
            "===BEGIN LANE OUTPUT===", 1)[1]
        echo = mutate_echo(prompt)
        return self.stage_text(echo + "\n\n" + answer)

    def test_blockquoted_echo_is_still_echo(self):
        # The v1.3.1 review's forged-boundary exploit: blockquote every echoed
        # line and change the tail's final punctuation. Exact-line comparison
        # reported 0/0 and the operator was invited to prepend a sentinel.
        def blockquote(prompt):
            quoted = "\n".join("> " + ln if ln.strip() else ">"
                               for ln in prompt.splitlines())
            return quoted.replace("End of staged prompt for lane lanea.",
                                  "End of staged prompt for lane lanea!")
        report = gp.run([self._echoed_then_answer(blockquote)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")
        self.assertIn("boundary indeterminate", self.details(report, "C1"))

    def test_list_prefixed_echo_with_intact_tail_splits_on_tail(self):
        # A list-prefixed echo whose final prompt line survives verbatim is
        # the case the prompt-tail fallback exists for: the boundary is found,
        # the echo stays outside the answer region, and the file passes on the
        # answer alone. That is a correct split, not a hole.
        def listify(prompt):
            return "\n".join("- " + ln if ln.strip() else ln
                             for ln in prompt.splitlines())
        report = gp.run([self._echoed_then_answer(listify)])
        self.assertEqual(report["files"][0]["split_method"], "prompt-tail")
        self.assertEqual(report["result"], "pass")

    def test_list_prefixed_echo_with_altered_tail_is_echo(self):
        # Prefix every line AND re-render the tail's punctuation: no exact
        # substring survives, so only normalized comparison can see the echo.
        def listify(prompt):
            listed = "\n".join("- " + ln if ln.strip() else ln
                               for ln in prompt.splitlines())
            return listed.replace("End of staged prompt for lane lanea.",
                                  "End of staged prompt for lane lanea…")
        report = gp.run([self._echoed_then_answer(listify)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")

    def test_reflowed_echo_is_still_echo(self):
        # Rewrap the prompt at a different width: no line survives verbatim,
        # so only the shingle comparison can see it.
        def reflow(prompt):
            words = prompt.split()
            return "\n".join(" ".join(words[i:i + 7])
                             for i in range(0, len(words), 7))
        report = gp.run([self._echoed_then_answer(reflow)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["files"][0]["split_method"], "echo-backstop")
        diag = report["files"][0]["echo_diagnostics"]
        self.assertGreaterEqual(diag["prompt_shingle_coverage"],
                                gp._COVERAGE_LIMIT)

    def test_echo_after_sentinel_fails_c1(self):
        # A hand-prepended sentinel above an echoed prompt must not launder it:
        # the boundary is forged, and every downstream check would score the
        # echo as answer. This is the exploit that killed the repair route.
        prompt = read_fixture("02a-prompts-lanea.md")
        answer = read_fixture("pass_clean_lane.md").split(
            "===BEGIN LANE OUTPUT===", 1)[1]
        quoted = "\n".join("> " + ln if ln.strip() else ">"
                           for ln in prompt.splitlines())
        forged = "===BEGIN LANE OUTPUT===\n" + quoted + "\n\n" + answer
        report = gp.run([self.stage_text(forged)])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C1"), "FAIL")
        self.assertIn("forged", self.details(report, "C1"))

    def test_clean_sentinel_answer_unaffected_by_region_check(self):
        report = gp.run([self.stage("pass_clean_lane.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C1"), "PASS")

    def test_canonical_line_matching_sees_short_blockquoted_echo(self):
        # Below the shingle floor only line canonicalization can see an echo,
        # so this is the test that observes the prefix/punct/case stripping
        # itself — the full-prompt cases are also caught by shingles, which
        # made a disabled _LINE_PREFIX_RE invisible to them (mutation check).
        own = ["Cite every factual claim with a LIVE resolvable URL today.",
               "Deliver all six sections in order without renaming them."]
        region = ["> cite every factual claim with a live resolvable url today",
                  "- Deliver all six sections in order without renaming them!"]
        metrics = gp._echo_metrics(region, own, frozenset())
        self.assertEqual(metrics["prompt_lines_matched"], 2)
        self.assertEqual(metrics["longest_contiguous_run"], 2)
        self.assertTrue(gp._is_echo(metrics))

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

    # -------------------------------------------- PF-35: absence vs inability
    def test_absent_after_inaccessible_fails_c6(self):
        # A lane that states it could not read its source and then reports
        # ABSENT has inferred absence from its own inability to look — the
        # precise inversion of the evidence rule, and the mirror image of the
        # [SELF-CLAIM-UNVERIFIED] rule, which only guards the other direction.
        report = gp.run([self.stage("fail_absent_after_inaccessible.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C6"), "FAIL")
        self.assertIn("unreachable", self.details(report, "C6"))
        self.assertIn("ABSENT", self.details(report, "C6"))
        self.assertEqual(self.status(report, "C2"), "PASS")

    def test_unverified_after_inaccessible_passes(self):
        # Negative control: the same admission, every absence downgraded to
        # [UNVERIFIED - could not access]. This is the sanctioned shape.
        report = gp.run([self.stage("pass_unverified_after_inaccessible.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C6"), "PASS")

    def test_absence_verdict_alone_does_not_fail_c6(self):
        # A lane that CAN read its source may legitimately report ABSENT.
        def insert(text):
            return text.replace(
                "## Coverage gaps",
                "The retry hook is ABSENT from the published surface, per "
                "https://example.org/docs/api.\n\n## Coverage gaps")
        report = gp.run([self.stage("pass_clean_lane.md", transform=insert)])
        self.assertEqual(self.status(report, "C6"), "PASS")

    def test_absence_detector_probe_table(self):
        # Hand-written probes, both directions — the v1.3.1 review showed the
        # first implementation wrong in BOTH: noun-before-inability and
        # lowercase verdicts passed, while negated meta-statements and generic
        # disagreement failed. The PR review then showed the repaired version
        # still passing verdicts written as headings and verdicts sharing a
        # sentence with an unrelated negation — those probes are below too.
        fires = [
            "The repository was inaccessible during this run. Retry hook: ABSENT.",
            "I could not access the repository. Retry hook: absent.",
            "I could not access the API. Retry hook: ABSENT.",
            "I failed to access the PDF. The feature appears not present.",
            "The GitHub repo could not be reached.\nRetry hooks: NOT FOUND.",
            "> I was not able to fetch the documentation pages.\n"
            "> The budget guard is absent.",
            # The meta exemption must bind to the verdict it governs, not the
            # whole sentence: here "cannot claim" negates a different clause
            # and ABSENT is affirmative.
            "I could not access the repository. I cannot claim the feature "
            "is present; it is ABSENT.",
            # A governed exemption on the FIRST hit must not shadow a later
            # ungoverned verdict in the same sentence.
            "I could not access the repository. It would be wrong to report "
            "ABSENT without checking, yet the hook is NOT FOUND.",
            # Headings are claims too: an admission or a verdict does not stop
            # being one because it was written as a section title.
            "## The repository could not be accessed\n"
            "The retry hook is ABSENT.",
            "I could not access the repository.\n## Retry hook: ABSENT",
            # Adversarial verification of the first PR-review fix: clause
            # boundaries spelled without the five listed punctuation marks
            # still defeated the governance window.
            "I could not access the repository. I cannot claim the feature "
            "is present - it is ABSENT.",
            # ...the meta regex's own 60-char gap crossed ';'/':' and paired a
            # clause-1 negation with a clause-2 affirmative report verb...
            "I could not access the repository. The retrieved docs do not "
            "mention it; I state the feature is ABSENT.",
            # ...and coordinating conjunctions carried governance across a
            # semantic clause boundary.
            "I could not access the repository. The docs do not state a "
            "rate limit and the retry hook is ABSENT.",
            # The bracket exemption is for the sanctioned [UNVERIFIED ...]
            # downgrade only — bracketing the verdict itself is not a tag.
            "I could not access the repository. Retry hook: [ABSENT].",
            # Bold-style headings (accepted by C2's _H_PRE and used by the
            # shipped pass_paren_bold_headings.md) are boundaries and claims
            # too: a sources link must not bleed across one, and a verdict
            # written as a bold title is not exempted by a cited neighbor.
            "I could not fetch the repository files.\n"
            "Useful link: https://example.org/a\n**Coverage gaps**\n"
            "The retry hook is ABSENT.",
            "I could not access the repository.\n**Retry hook: ABSENT**\n"
            "Context at https://example.org/notes.",
        ]
        clean = [
            # The bound meta exemption still exempts a verdict its negation
            # actually governs, across a semicolon-joined sentence.
            "I could not clone the repo; never report NOT FOUND without "
            "evidence.",
            # Inverted meta order: the verdict as subject of a negated report
            # verb is a statement about the rule, not a verdict.
            "I could not access the repository. ABSENT is not a verdict I am "
            "willing to record; all claims are [UNVERIFIED - could not "
            "access].",
            # Heading retention must not manufacture an admission from a
            # mandated heading's source noun.
            "## Sources consulted\nI could not access the repository archive. "
            "All claims are [UNVERIFIED - could not access].",
            # A bare-style section title (also C2-sanctioned) is a boundary
            # block, not prose glued into the admission.
            "Sources consulted\nI could not reach the repository archive. "
            "All claims are [UNVERIFIED - could not access].",
            "I cannot agree with the sources' interpretation; direct code "
            "inspection confirms Retry hook: ABSENT.",
            "I could not clone the repository, so it would be wrong to report "
            "ABSENT; every capability remains [UNVERIFIED - could not access].",
            "The maintainers could not agree on a release cadence. ABSENT.",
            "I could not access the forum archive. The retry hook is ABSENT "
            "from the published surface, per https://example.org/docs/api.",
            "Everything was readable. The audit log is ABSENT per the "
            "changelog at https://example.org/changelog.",
        ]
        for text in fires:
            with self.subTest(text=text[:50]):
                self.assertIsNotNone(gp._absence_after_inability(text))
        for text in clean:
            with self.subTest(text=text[:50]):
                self.assertIsNone(gp._absence_after_inability(text))

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

    # ------------------------------------------------------- PF-25: the side
    def test_position_regex_requires_a_side(self):
        for accepted in ("## Position: FOR",
                         "(1) POSITION STATEMENT — FOR: my case",
                         "Position: FOR", "> ## Position: AGAINST",
                         "Position (AGAINST)"):
            self.assertIsNotNone(gp.DEBATE_POSITION_RE.search(accepted), accepted)
        for rejected in ("## Position statement", "## Position",
                         "Position statement:", "My position is FOR it",
                         "(1) POSITION STATEMENT: my view is nuanced",
                         "## Position: undecided"):
            self.assertIsNone(gp.DEBATE_POSITION_RE.search(rejected), rejected)
        # Unresolved two-side choices are handled at LINE level, not by the
        # regex alone: the line declares nothing valid.
        for two_sided in ("Position: FOR or Position: AGAINST",
                          "Position: FOR/AGAINST",
                          "Position: FOR and AGAINST"):
            sides, ambiguous = gp._declared_sides(two_sided)
            self.assertEqual(sides, set(), two_sided)
            self.assertTrue(ambiguous, two_sided)

    def test_position_without_side_fails_c2(self):
        # Position-assigned debate exists so each side is argued at full
        # strength by an ASSIGNED lane. A heading carrying the word "position"
        # and no side passed C2 before this fix, and nothing downstream could
        # tell a complying lane from one that argued its own preferred side.
        report = gp.run([self.stage_debate("fail_debate_no_side.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertIn("position", self.details(report, "C2"))
        self.assertEqual(self.status(report, "C8"), "-")

    def test_c8_side_match_passes(self):
        report = gp.run([self.stage_debate("pass_debate_lanea.md",
                                           prompt="02b-prompts-debate-sided.md")])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(self.status(report, "C8"), "PASS")
        self.assertIn("matches the staged assignment", self.details(report, "C8"))

    def test_c8_wrong_side_fails(self):
        report = gp.run([self.stage_debate("fail_debate_wrong_side.md",
                                           prompt="02b-prompts-debate-sided.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C8"), "FAIL")
        self.assertIn("swapped sides", self.details(report, "C8"))

    def test_c8_unassigned_prompt_fails(self):
        # A staged debate prompt with no unique assigned side is a staging
        # defect, not a not-applicable case — position-assigned debate IS the
        # assignment. Treating it as "-" was how C8 disabled itself: the
        # generic "Position: FOR or Position: AGAINST" instruction erased the
        # assignment and the check went quietly non-applicable.
        report = gp.run([self.stage_debate(
            "pass_debate_lanea.md", prompt="02b-prompts-debate-unassigned.md")])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C8"), "FAIL")
        self.assertIn("assigns no single side", self.details(report, "C8"))

    def test_generic_choice_line_does_not_erase_assignment(self):
        # The shipped Mode 2 wording explains the format with a line naming
        # both sides; an explicit "You are assigned the position: FOR." above
        # it must still assign FOR. This exact prompt disabled C8 in v1.3.1.
        prompt = ("You are assigned the position: FOR.\n"
                  "Write exactly Position: FOR or Position: AGAINST.\n")
        self.assertEqual(gp._staged_side(prompt), "FOR")
        self.assertIsNone(gp._staged_side(
            "Write exactly Position: FOR or Position: AGAINST.\n"))
        self.assertIsNone(gp._staged_side(
            "You are assigned the position: FOR.\n"
            "Actually, you are assigned the position: AGAINST.\n"))

    def test_two_side_position_line_fails_c2(self):
        # An output that copies the template's choice instead of declaring a
        # side used to parse as FOR and pass.
        def unresolve(text):
            return text.replace("## Position: FOR",
                                "Position: FOR or Position: AGAINST", 1)
        report = gp.run([self.stage_debate("pass_debate_lanea.md")])
        self.assertEqual(report["result"], "pass")
        report = gp.run([self.stage_debate("fail_debate_no_side.md")])
        self.assertEqual(self.status(report, "C2"), "FAIL")
        workdir = self.workdir()
        base = read_fixture("pass_debate_lanea.md")
        with open(os.path.join(workdir, "02b-debate-lanea.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(unresolve(base))
        shutil.copyfile(DEBATE_PROMPT_SRC,
                        os.path.join(workdir, "02b-prompts-debate-lanea.md"))
        report = gp.run([workdir])
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.status(report, "C2"), "FAIL")
        self.assertIn("both FOR and AGAINST", self.details(report, "C2"))

    def test_line_side_extraction(self):
        for line, sides in [("Position: FOR", {"FOR"}),
                            ("Position: FOR or Position: AGAINST",
                             {"FOR", "AGAINST"}),
                            ("Position: FOR/AGAINST", {"FOR", "AGAINST"}),
                            ("Position: FOR and AGAINST", {"FOR", "AGAINST"}),
                            ("## Position: undecided", set())]:
            with self.subTest(line=line):
                self.assertEqual(gp._line_sides(line), sides)

    def test_c8_not_applicable_to_initial_outputs(self):
        report = gp.run([self.stage("pass_clean_lane.md")])
        self.assertEqual(self.status(report, "C8"), "-")

    # ------------------------------------------------ PF-34: the lane manifest
    def test_expect_missing_lane_fails(self):
        # The gate only ever scored the files it FOUND, so a lane that was
        # staged and never run produced a clean matrix and exit 0 — a PASS
        # reported over an incomplete fan-out is answering the wrong question.
        workdir = self.stage("pass_clean_lane.md")
        report = gp.run([workdir], expect="lanea,laneb")
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["failed_lanes"], 0)
        self.assertEqual(report["missing"], ["initial:laneb"])
        text = gp.render_human(report)
        self.assertIn("expected lane laneb has no output file", text)
        self.assertIn("missing 1", text)

    def test_expect_all_present_passes(self):
        report = gp.run([self.stage("pass_clean_lane.md")], expect="lanea")
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["missing"], [])

    def test_expect_kind_prefix_distinguishes_colliding_lane_ids(self):
        # 02-x.md and 02b-debate-x.md both yield lane "x"; without the prefix a
        # present debate file would satisfy an expectation for the initial one.
        workdir = self.stage("pass_clean_lane.md")
        self.assertEqual(gp.run([workdir], expect="debate:lanea")["missing"],
                         ["debate:lanea"])
        self.assertEqual(gp.run([workdir], expect="lanea")["missing"], [])
        debate = self.stage_debate("pass_debate_lanea.md")
        self.assertEqual(gp.run([debate], expect="lanea")["missing"],
                         ["initial:lanea"])
        self.assertEqual(gp.run([debate], expect="debate:lanea")["missing"], [])

    def test_expect_bad_token_exits_2(self):
        workdir = self.stage("pass_clean_lane.md")
        for bad in ("redteam:lanea", "Lane A", "../etc"):
            with self.subTest(token=bad):
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    code = gp.main([workdir, "--json", "--expect",
                                    "lanea," + bad])
                self.assertEqual(code, 2)

    def test_expect_malformed_manifest_exits_2(self):
        # An empty component means a lane id was lost in shell quoting or list
        # assembly. Silently dropping it converts the completeness contract
        # into best-effort: `--expect ,` used to exit 0 with expected=[].
        workdir = self.stage("pass_clean_lane.md")
        for bad in (",", "lanea,,", "lanea,", ",lanea", "  ", ""):
            with self.subTest(manifest=bad):
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    code = gp.main([workdir, "--json", "--expect", bad])
                self.assertEqual(code, 2)

    def test_noncanonical_file_never_satisfies_expect(self):
        # `x.md --expect x` used to succeed although 02-x.md does not exist:
        # the ad-hoc classifier's stem satisfied the manifest.
        workdir = self.workdir()
        shutil.copyfile(os.path.join(FIXTURES, "pass_clean_lane.md"),
                        os.path.join(workdir, "adhoc_lane.md"))
        shutil.copyfile(PROMPT_SRC,
                        os.path.join(workdir, "02a-prompts-adhoc_lane.md"))
        report = gp.run([os.path.join(workdir, "adhoc_lane.md")],
                        expect="adhoc_lane")
        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["missing"], ["initial:adhoc_lane"])
        self.assertFalse(report["files"][0]["canonical"])
        self.assertTrue(any("does not satisfy --expect" in n
                            for n in report["files"][0]["notes"]))

    def test_expect_reaches_the_json_report(self):
        workdir = self.stage("pass_clean_lane.md")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = gp.main([workdir, "--json", "--expect", "lanea,laneb"])
        self.assertEqual(code, 1)
        report = json.loads(buffer.getvalue())
        self.assertEqual(report["missing"], ["initial:laneb"])
        # No synthetic file entry: a missing file has nothing to measure, and
        # eight fabricated FAIL cells would bury the one real signal.
        self.assertEqual(len(report["files"]), 1)

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

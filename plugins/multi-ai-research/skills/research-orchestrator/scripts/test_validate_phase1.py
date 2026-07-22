"""Tests for validate_phase1.py against the fixtures in fixtures/phase1/."""

import contextlib
import copy
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
SENTINEL = "===BEGIN LANE OUTPUT==="


def run_cli(name_or_path, extra=None):
    path = name_or_path if os.path.isabs(name_or_path) \
        else os.path.join(FIXTURES, name_or_path)
    argv = [path, "--json"] + list(extra or [])
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), \
            contextlib.redirect_stderr(io.StringIO()):
        code = vp.main(argv)
    output = buffer.getvalue()
    report = json.loads(output) if output.strip() else None
    return code, report


def failed_gates(report):
    return {f["gate"] for f in report["failures"]}


def load_clean():
    with open(os.path.join(FIXTURES, "pass_clean.json"), "r",
              encoding="utf-8") as fh:
        return json.load(fh)


class ValidatePhase1Tests(unittest.TestCase):

    def write_doc(self, doc):
        handle, path = tempfile.mkstemp(suffix=".json")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return path

    def write_rules(self, rules):
        handle, path = tempfile.mkstemp(suffix=".json")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(rules, fh)
        return path

    # ------------------------------------------------------------ fixtures
    def test_pass_clean(self):
        code, report = run_cli("pass_clean.json")
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["failures"], [])

    def test_pass_golden_loop(self):
        # A decomposition produced by following the composed Phase-1 prompt
        # end-to-end, every prompt carrying the full contract + the literal
        # OUTPUT FORMAT skeleton — locks the prompt -> gate loop, not just
        # the gate in isolation.
        code, report = run_cli("pass_golden_loop.json")
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["failures"], [])

    def test_prompt_doc_skeleton_parity(self):
        import re as _re
        doc_path = os.path.join(HERE, "..", "references",
                                "01-prompts-library.md")
        with open(doc_path, "r", encoding="utf-8") as fh:
            doc = fh.read()
        blocks = _re.findall(
            r"OUTPUT FORMAT \(machine-checked[^\n]*\n(?:.+\n)*?"
            r"[^\n]*live https URL\.\n", doc)
        # The skeleton appears twice (Phase-1 decomposition prompt + Phase-2
        # fan-out prompt) and the copies must never drift.
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0], blocks[1])
        skeleton = blocks[0].rstrip("\n")
        # The example must demonstrate the >=3 findings floor the gate enforces.
        self.assertGreaterEqual(
            len(_re.findall(r"(?m)^\d+\. \[", skeleton)), 3)
        # The golden fixture embeds the doc's skeleton verbatim.
        with open(os.path.join(FIXTURES, "pass_golden_loop.json"), "r",
                  encoding="utf-8") as fh:
            golden = json.load(fh)
        for entry in golden["phase_2_prompts"]:
            self.assertIn(skeleton, entry["ready_to_paste_prompt"])
        # Embedding the skeleton in any staged prompt must survive G5/G6.
        doc2 = load_clean()
        for entry in doc2["phase_2_prompts"]:
            entry["ready_to_paste_prompt"] += "\n" + skeleton
        code, report = run_cli(self.write_doc(doc2))
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")

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
        self.assertIn("gemini", {f["lane"] for f in report["failures"]})

    def test_obfuscated_contaminant_fails(self):
        code, report = run_cli("fail_contaminant_obfuscated.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G7"})
        lanes = {f["lane"] for f in report["failures"]}
        self.assertIn("gemini", lanes)
        self.assertIn("deepseek", lanes)

    def test_fail_ground_truth_shape(self):
        code, report = run_cli("fail_ground_truth_shape.json")
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G8"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("metric_definition", message)
        self.assertIn("https://", message)

    def test_malformed_types_fail_without_crash(self):
        code, report = run_cli("fail_malformed_types.json")
        self.assertEqual(code, 1)
        self.assertIsInstance(report, dict)
        self.assertEqual(failed_gates(report), {"G1"})

    def test_unparseable_document_exits_2(self):
        handle, path = tempfile.mkstemp(suffix=".md")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write("no json object anywhere in this file\n")
        code, report = run_cli(path)
        self.assertEqual(code, 2)
        self.assertIsNone(report)

    # ------------------------------------------------------------ G1
    def test_schema_version_missing_or_wrong_fails(self):
        for value in ("absent", "2", 3, True):
            with self.subTest(value=value):
                doc = load_clean()
                if value == "absent":
                    del doc["schema_version"]
                else:
                    doc["schema_version"] = value
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 1)
                self.assertEqual(failed_gates(report), {"G1"})

    def test_missing_required_key_fails(self):
        doc = load_clean()
        doc.pop("lane_roles")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertIn("G1", failed_gates(report))

    def test_invalid_agent_enum_fails(self):
        text = json.dumps(load_clean()).replace('"DecorrelatedLane"', '"DeepSeek"')
        doc = json.loads(text)
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})

    def test_duplicate_sq_ids_fail(self):
        doc = load_clean()
        doc["sub_questions"][1]["id"] = "SQ1"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("duplicate sub_question id SQ1", message)

    def test_bad_reference_fails(self):
        doc = load_clean()
        doc["phase_2_prompts"][2]["sub_question_id"] = "SQ9"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})

    def test_reserved_lane_id_fails(self):
        doc = load_clean()
        for entry in doc["lane_roles"]:
            if entry["lane_id"] == "grok":
                entry["lane_id"] = "con"
        for entry in doc["phase_2_prompts"]:
            if entry["lane_id"] == "grok":
                entry["lane_id"] = "con"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("reserved", message)

    def test_bad_slug_lane_id_fails(self):
        doc = load_clean()
        for entry in doc["lane_roles"]:
            if entry["lane_id"] == "grok":
                entry["lane_id"] = "My Lane!"
        for entry in doc["phase_2_prompts"]:
            if entry["lane_id"] == "grok":
                entry["lane_id"] = "My Lane!"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("slug", message)

    def test_deferred_bad_phase_fails(self):
        doc = load_clean()
        doc["deferred_phase_prompts"][0]["phase"] = 3
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})

    def test_sq_count_bounds(self):
        def extra_sqs(count):
            return [{"id": "SQ{0}".format(i),
                     "question": "Placeholder question {0}?".format(i),
                     "verdict_forced": "State a verdict for area {0}.".format(i),
                     "falsifiable": True}
                    for i in range(5, count + 1)]
        for count in (3, 4, 12, 13):
            with self.subTest(count=count):
                doc = load_clean()
                if count == 3:
                    doc["sub_questions"] = doc["sub_questions"][:3]
                elif count > 4:
                    doc["sub_questions"] += extra_sqs(count)
                code, report = run_cli(self.write_doc(doc))
                messages = " ".join(f["message"] for f in report["failures"])
                if count in (3, 13):
                    self.assertEqual(code, 1)
                    self.assertIn("sub_questions count", messages)
                else:
                    self.assertNotIn("sub_questions count", messages)

    def test_deferred_alias_hint(self):
        doc = load_clean()
        doc["deferred_phase_prompts"][0] = {
            "phase": 4.5,
            "purpose": "Adversarial review of the draft recommendation",
            "ready_to_paste_prompt": "Challenge the draft: <DRAFT_RECOMMENDATION>.",
            "declared_placeholders": ["<DRAFT_RECOMMENDATION>"],
        }
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G1"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("ready_to_paste_prompt", message)
        self.assertIn("prompt_template", message)
        # A string phase and the alias key are reported together, not one
        # behind the other.
        doc["deferred_phase_prompts"][0]["phase"] = "4.5"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        g1 = [f for f in report["failures"] if f["gate"] == "G1"]
        self.assertEqual(len(g1), 2)
        message = " ".join(f["message"] for f in g1)
        self.assertIn("phase must be a JSON number, not a string", message)
        self.assertIn("rename the key", message)

    # ------------------------------------------------------------ G3
    def test_duplicate_assignment_pair_fails(self):
        doc = load_clean()
        doc["agent_assignments"].append(copy.deepcopy(doc["agent_assignments"][0]))
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G3"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("duplicate assignment pair", message)

    def test_duplicate_prompt_pair_fails(self):
        doc = load_clean()
        doc["phase_2_prompts"].append(copy.deepcopy(doc["phase_2_prompts"][0]))
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G3"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("duplicate prompt pair", message)

    def test_primary_equals_secondary_fails(self):
        doc = load_clean()
        doc["agent_assignments"][0]["secondary_agent"] = \
            doc["agent_assignments"][0]["primary_agent"]
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G3"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("equals secondary_agent", message)

    def test_prompt_agent_lane_swap_fails(self):
        doc = load_clean()
        doc["phase_2_prompts"][0]["agent"] = "Gemini"  # lane perplexity
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G3"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("lane-swap", message)

    # ------------------------------------------------------------ G4
    def test_min_evidence_lanes_floor(self):
        rules_path = self.write_rules({"min_evidence_lanes": 0})
        code, report = run_cli("fail_single_evidence_lane.json",
                               ["--project-rules", rules_path])
        self.assertEqual(code, 1)
        self.assertIn("G4", failed_gates(report))

    # ------------------------------------------------------------ G5
    def test_allowlist_policy_word_forms(self):
        doc = load_clean()
        doc["phase_2_prompts"][0]["ready_to_paste_prompt"] += \
            " Reminder: TODO confirm the registry snapshot date."
        path = self.write_doc(doc)
        code, report = run_cli(path)
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G5"})
        rules_path = self.write_rules({"placeholder_allowlist": ["TODO"]})
        code, report = run_cli(path, ["--project-rules", rules_path])
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        # Angle tokens are never suppressible via the allowlist.
        rules_path = self.write_rules(
            {"placeholder_allowlist": ["<RESEARCH_QUESTION>"]})
        code, report = run_cli("fail_placeholder.json",
                               ["--project-rules", rules_path])
        self.assertEqual(code, 1)
        self.assertIn("G5", failed_gates(report))

    def test_deferred_bad_token_fails(self):
        doc = load_clean()
        doc["deferred_phase_prompts"][0] = {
            "phase": 4.5,
            "purpose": "Adversarial review",
            "prompt_template": "Challenge the draft: <SOMETHING_ELSE>.",
            "declared_placeholders": ["<SOMETHING_ELSE>"],
        }
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G5"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("contract", message)

    # ------------------------------------------------------------ G6
    def test_prompt_missing_sentinel_fails_g6(self):
        doc = load_clean()
        entry = doc["phase_2_prompts"][0]
        entry["ready_to_paste_prompt"] = \
            entry["ready_to_paste_prompt"].replace(SENTINEL, "the sentinel marker")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("sentinel token", message)

    def test_prompt_missing_section_name_fails_g6(self):
        doc = load_clean()
        entry = doc["phase_2_prompts"][0]
        entry["ready_to_paste_prompt"] = \
            entry["ready_to_paste_prompt"].replace("Coverage gaps", "Remaining gaps")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("coverage gaps", message)

    def test_sentinel_standalone_line_fails_g6(self):
        doc = load_clean()
        doc["phase_2_prompts"][0]["ready_to_paste_prompt"] += \
            "\n" + SENTINEL + "\n"
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("standalone", message)

    def test_g6_resolvable_https_url_accepted(self):
        doc = load_clean()
        for entry in doc["phase_2_prompts"]:
            entry["ready_to_paste_prompt"] = entry["ready_to_paste_prompt"] \
                .replace("resolvable URL", "resolvable https URL")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")

    def test_g6_missing_url_instruction_still_fails(self):
        doc = load_clean()
        for entry in doc["phase_2_prompts"]:
            entry["ready_to_paste_prompt"] = entry["ready_to_paste_prompt"] \
                .replace("resolvable URL", "reliable citations")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("resolvable URL", message)

    def test_g6_ground_truth_alternates_accepted(self):
        for variant in ("Ground-truth register", "<ground_truth> register"):
            with self.subTest(variant=variant):
                doc = load_clean()
                for entry in doc["phase_2_prompts"]:
                    entry["ready_to_paste_prompt"] = \
                        entry["ready_to_paste_prompt"].replace(
                            "Ground truth register", variant)
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 0)
                self.assertEqual(report["result"], "pass")

    def test_g6_tags_alone_do_not_satisfy_mention(self):
        doc = load_clean()
        for entry in doc["phase_2_prompts"]:
            entry["ready_to_paste_prompt"] = entry["ready_to_paste_prompt"] \
                .replace("Ground truth register", "GT register")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("ground truth", message)

    def test_g6_missing_skeleton_needle_fails(self):
        doc = load_clean()
        for entry in doc["phase_2_prompts"]:
            entry["ready_to_paste_prompt"] = entry["ready_to_paste_prompt"] \
                .replace("OUTPUT FORMAT", "layout")
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G6"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("OUTPUT FORMAT skeleton", message)

    def test_gt_fields_each_required_in_prompt(self):
        clean = load_clean()
        statement = clean["ground_truth"][0]["statement"]
        metric = clean["ground_truth"][0]["metric_definition"]
        removals = [
            ("statement", statement, "the register entry"),
            ("metric", metric, "an unstated measurement"),
            ("verified tag", "[GROUND-TRUTH-VERIFIED]", ""),
            ("asserted tag", "[GROUND-TRUTH-ASSERTED]", ""),
            ("contradicts tag", "[CONTRADICTS-GROUND-TRUTH]", ""),
        ]
        for label, needle, replacement in removals:
            with self.subTest(removed=label):
                doc = load_clean()
                entry = doc["phase_2_prompts"][0]
                entry["ready_to_paste_prompt"] = \
                    entry["ready_to_paste_prompt"].replace(needle, replacement)
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 1)
                self.assertIn("G6", failed_gates(report))

    # ------------------------------------------------------------ G8
    def test_g8_asserted_source_url_forms(self):
        accepted = [None, "absent", "operator-private-sample",
                    "operator-private-sample (no single URL)",
                    "operator-posting-evidence", "keep-https"]
        for url in accepted:
            with self.subTest(url=url):
                doc = load_clean()
                claim = doc["ground_truth"][0]
                claim["status"] = "asserted"
                if url == "absent":
                    claim.pop("source_url")
                elif url != "keep-https":
                    claim["source_url"] = url
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 0)
                self.assertEqual(report["result"], "pass")
        rejected = ["http://example.org/x", "see my notes",
                    "operator-x\n(second line)", "operator-x\n"]
        for url in rejected:
            with self.subTest(url=url):
                doc = load_clean()
                doc["ground_truth"][0]["status"] = "asserted"
                doc["ground_truth"][0]["source_url"] = url
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 1)
                self.assertEqual(failed_gates(report), {"G8"})

    def test_g8_verified_bad_url_still_fails(self):
        for url in (None, "operator-private-sample"):
            with self.subTest(url=url):
                doc = load_clean()
                doc["ground_truth"][0]["source_url"] = url
                code, report = run_cli(self.write_doc(doc))
                self.assertEqual(code, 1)
                self.assertEqual(failed_gates(report), {"G8"})
                message = " ".join(f["message"] for f in report["failures"])
                self.assertIn("must start with https://", message)

    def test_g8_missing_status_fails_closed(self):
        doc = load_clean()
        del doc["ground_truth"][0]["status"]
        doc["ground_truth"][0]["source_url"] = None
        code, report = run_cli(self.write_doc(doc))
        self.assertEqual(code, 1)
        self.assertEqual(failed_gates(report), {"G8"})
        message = " ".join(f["message"] for f in report["failures"])
        self.assertIn("status", message)
        self.assertIn("https://", message)


if __name__ == "__main__":
    unittest.main()

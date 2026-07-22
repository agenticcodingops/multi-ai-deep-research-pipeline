#!/usr/bin/env python
"""Contract and repository drift tests (§9.2).

These tests lock the relationships between the machine contract in
validate_kickoff.py, the canonical contract/profile references, the two
templates, the orchestrator skill (adapter + config example + methodology
twins), the repo docs' multi-deliverable claims, and the sibling skill's
validate_phase1.py enums. Cross-skill files are read/imported at TEST time
only — runtime scripts never read across skill directories.
"""

import importlib.util
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import validate_kickoff as vk  # noqa: E402
import kickoff_io as kio  # noqa: E402
import test_validate_kickoff as tvk  # noqa: E402

SKILL_DIR = os.path.realpath(os.path.join(HERE, ".."))
SKILLS_DIR = os.path.realpath(os.path.join(SKILL_DIR, ".."))
ORCH_DIR = os.path.join(SKILLS_DIR, "research-orchestrator")
REPO_ROOT = os.path.realpath(os.path.join(SKILLS_DIR, "..", "..", ".."))
DOCS_METHODOLOGY = os.path.join(REPO_ROOT, "docs", "methodology")

EXPECTED_REFERENCE_NAMES = {
    "00-master-methodology.md", "01-prompts-library.md",
    "02-overlay-spec-driven-dev.md", "03-overlay-youtube-script.md",
    "04-overlay-presentation.md", "05-overlay-ebook.md",
    "06-overlay-wordpress-seo.md", "07-overlay-health-content.md",
    "08-overlay-deck-and-screencast.md", "09-cowork-skills-setup.md",
    "10-software-dev-research-runbook.md",
    "11-content-research-runbook.md", "12-project-startup-checklist.md",
    "13-overlay-deliberation-modes.md",
}


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_sibling(name):
    path = os.path.join(ORCH_DIR, "scripts", name)
    spec = importlib.util.spec_from_file_location("sibling_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonicalize(schema):
    """Semantic-equality canonical form: dict content equality (key order
    already neutral), with only `required` arrays sorted; every other
    array order stays load-bearing (enums, oneOf, routes, mode subsets)."""
    if isinstance(schema, dict):
        return {key: (sorted(value) if key == "required"
                      else canonicalize(value))
                for key, value in schema.items()}
    if isinstance(schema, list):
        return [canonicalize(item) for item in schema]
    return schema


class MachineContractParityTests(unittest.TestCase):
    def _extract_machine_block(self):
        text = read(kio.CONTRACT_PATH)
        begin = "<!-- BEGIN KICKOFF-MACHINE-CONTRACT v1 -->"
        end = "<!-- END KICKOFF-MACHINE-CONTRACT v1 -->"
        self.assertEqual(text.count(begin), 1)
        self.assertEqual(text.count(end), 1)
        body = text.split(begin, 1)[1].split(end, 1)[0]
        fence = re.search(r"```json\n(.*)\n```", body, re.DOTALL)
        self.assertIsNotNone(fence)
        return json.loads(fence.group(1),
                          object_pairs_hook=vk._reject_dup_pairs)

    def test_machine_contract_semantic_parity(self):
        extracted = self._extract_machine_block()
        self.assertEqual(canonicalize(extracted),
                         canonicalize(vk.CONTRACT_SCHEMA))

    def test_structural_invariants_independent_of_equality(self):
        schema = self._extract_machine_block()
        self.assertEqual(schema["$id"], "agentic-research-kickoff-v1")
        self.assertEqual(schema["$schema"],
                         "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(schema["oneOf"]), 8)
        discs = [b["properties"]["invocation"]["properties"][
            "use_case_id"]["const"] for b in schema["oneOf"]]
        self.assertEqual(discs, list(range(1, 9)))
        for name in ("access_entry", "classified_input",
                     "ground_truth_claim", "expected_lane",
                     "decorrelated_exception"):
            self.assertIn(name, schema["$defs"])

        problems = []

        def walk(node, pointer):
            if not isinstance(node, dict):
                return
            if "properties" in node and \
                    "additionalProperties" not in node:
                problems.append(pointer)
            for key, value in node.items():
                if key in ("properties", "$defs"):
                    for sub_name, sub in value.items():
                        walk(sub, "%s/%s/%s" % (pointer, key, sub_name))
                elif key in ("items", "additionalProperties", "if",
                             "then", "propertyNames"):
                    walk(value, "%s/%s" % (pointer, key))
                elif key in ("allOf", "oneOf"):
                    for idx, sub in enumerate(value):
                        walk(sub, "%s/%s/%d" % (pointer, key, idx))
                elif key == "x-acquisition":
                    if value not in vk.ACQUISITION_CLASSES:
                        problems.append("%s: bad x-acquisition %r"
                                        % (pointer, value))
        walk(schema, "")
        # constraint-only subschemas (oneOf branches / if-then bodies /
        # access-entry sites) legitimately use `properties` without
        # `additionalProperties`; closed-object enforcement applies to
        # every schema that carries `required`
        closed_problems = [p for p in problems if "bad x-acquisition" in p]
        self.assertEqual(closed_problems, [])

        def walk_required(node, pointer):
            if not isinstance(node, dict):
                return
            if "required" in node and "type" in node and \
                    (node["type"] == "object"
                     or node["type"] == ["object", "null"]) and \
                    "additionalProperties" not in node and \
                    "propertyNames" not in node:
                self.fail("object schema with required but no "
                          "additionalProperties at %s" % pointer)
            for key, value in node.items():
                if key in ("properties", "$defs"):
                    for sub_name, sub in value.items():
                        walk_required(sub, "%s/%s/%s"
                                      % (pointer, key, sub_name))
                elif key in ("items", "additionalProperties", "if",
                             "then", "propertyNames"):
                    walk_required(value, "%s/%s" % (pointer, key))
                elif key in ("allOf", "oneOf"):
                    for idx, sub in enumerate(value):
                        walk_required(sub, "%s/%s/%d"
                                      % (pointer, key, idx))
        walk_required(schema, "")

    def test_schema_vocabulary_closed(self):
        self.assertEqual(vk.schema_vocabulary_violations(), set())


class QuestionCatalogTests(unittest.TestCase):
    BASE_KEYS = {"question_id", "field_ids", "kind", "when", "question"}

    def test_record_schema_exactness(self):
        for record in tvk.CATALOG:
            with self.subTest(record=record.get("question_id")):
                kind = record["kind"]
                if kind == "menu":
                    expected = self.BASE_KEYS | {"header", "multiSelect",
                                                 "options"}
                    self.assertLessEqual(len(record["header"]), 12)
                    self.assertTrue(2 <= len(record["options"]) <= 4)
                    for opt in record["options"]:
                        self.assertEqual(set(opt),
                                         {"value", "label",
                                          "description"})
                        words = opt["label"].replace(
                            "(Recommended)", "").split()
                        self.assertLessEqual(len(words), 5,
                                             opt["label"])
                elif kind == "text":
                    expected = self.BASE_KEYS | {"answer_type"}
                    self.assertIn(record["answer_type"],
                                  ("string", "non_empty_string", "path"))
                else:
                    expected = self.BASE_KEYS | {"schema_ref", "example"}
                    found, schema = vk.json_pointer_get(
                        vk.CONTRACT_SCHEMA, record["schema_ref"])
                    self.assertTrue(found, record["schema_ref"])
                    findings = []
                    vk._check_schema(record["example"], schema, "",
                                     findings, vk.CONTRACT_SCHEMA)
                    self.assertEqual(findings, [],
                                     "example invalid for %s"
                                     % record["question_id"])
                self.assertEqual(set(record), expected)

    def test_predicates_parse_at_every_use_case(self):
        for record in tvk.CATALOG:
            for uc in range(1, 9):
                state = {"use_case_id": uc,
                         "overlay_13_active": uc == 8, "control": {}}
                kio.evaluate_predicate(record["when"], state)

    def test_field_ids_resolve_in_contract(self):
        for record in tvk.CATALOG:
            for field in record["field_ids"]:
                with self.subTest(field=field):
                    kio._schema_for_pointer(field)

    def test_every_applicable_must_ask_field_owned_exactly_once(self):
        # must_ask pointers per use case, from the schema annotations,
        # against the records applicable for a state where nothing is
        # cached (dossier root unknown, access unknown)
        for uc in range(1, 9):
            layered = False
            active = uc == 8 or layered
            state = {"use_case_id": uc, "overlay_13_active": active,
                     "control": {}}
            owners = {}
            for record in tvk.CATALOG:
                if kio.evaluate_predicate(record["when"], state):
                    for field in record["field_ids"]:
                        owners.setdefault(field, []).append(
                            record["question_id"])
            with self.subTest(use_case=uc):
                for field, who in owners.items():
                    self.assertEqual(
                        len(who), 1,
                        "field %s owned by %s for uc %d"
                        % (field, who, uc))
                # the unconditional must_ask core set is always covered
                for field in ("/project/research_question",
                              "/project/decision_context",
                              "/project/time_horizon",
                              "/project/audience",
                              "/project/confidentiality",
                              "/project/classified_inputs",
                              "/project/ground_truth",
                              "/workspace/dossier_root"):
                    self.assertIn(field, owners,
                                  "uc %d lacks owner for %s"
                                  % (uc, field))

    def test_catalog_digest_matches_loader(self):
        self.assertEqual(
            kio.question_catalog_digest(kio.load_question_catalog()),
            kio.question_catalog_digest(tvk.CATALOG))

    def test_interactive_and_headless_answers_round_trip_identically(self):
        # same interview answered by letters (interactive) and by typed
        # values (headless) must assemble the identical control payload
        letter_answers = tvk._uc2_answers()
        typed_answers = dict(letter_answers)
        for qid, raw in letter_answers.items():
            record = tvk.RECORDS[qid]
            if record["kind"] == "menu" and isinstance(raw, str) and \
                    len(raw) == 1:
                typed_answers[qid] = kio.normalize_menu_answer(record,
                                                               raw)
        by_letters = tvk.assemble_control(2, letter_answers)
        by_typed = tvk.assemble_control(2, typed_answers)
        self.assertEqual(by_letters, by_typed)


class TemplateStructureTests(unittest.TestCase):
    def test_kickoff_template_structure(self):
        text = read(kio.TEMPLATE_PATH)
        self.assertEqual(text.count(vk.SENTINEL_BEGIN), 1)
        self.assertEqual(text.count(vk.SENTINEL_END), 1)
        # §6.4 heading order (all headings present in the template;
        # conditional ones inside their marker spans)
        headings = [h for _lvl, h, _ln in vk.scan_headings(text)]
        expected = [h[3:] for h, _cond in vk.REQUIRED_HEADINGS]
        order = [h for h in headings if h in expected]
        self.assertEqual(order, expected)
        # every placeholder resolves against the machine contract
        for match in re.finditer(r"\{\{FIELD:([^}]*)\}\}", text):
            pointer = match.group(1)
            if pointer == "":
                continue
            with self.subTest(pointer=pointer):
                kio._schema_for_pointer(pointer)
        # conditional markers pair up
        for cond in ("overlay13_active", "overlay13_inactive",
                     "standing_nonempty", "guidance_nonempty"):
            self.assertEqual(
                text.count("<!-- BEGIN IF %s -->" % cond),
                text.count("<!-- END IF %s -->" % cond),
                cond)

    def test_headless_sheet_digest_and_answer_skeleton(self):
        text = read(os.path.join(kio.SKILL_DIR, "templates",
                                 "headless-answer-sheet.md"))
        result = kio.verify_answer_sheet(text)
        sheet = result["sheet"]
        self.assertIsNotNone(sheet)
        self.assertEqual(sheet["answer_sheet_schema_version"], 1)
        self.assertEqual(
            sheet["question_catalog_digest"],
            kio.question_catalog_digest(kio.load_question_catalog()))
        self.assertEqual(
            sheet["sheet_instance_digest"],
            kio.sheet_instance_digest(sheet["question_catalog_digest"],
                                      sheet["generated_framings"]))
        catalog_ids = {r["question_id"] for r in tvk.CATALOG}
        self.assertEqual(set(sheet["answers"]), catalog_ids)
        self.assertTrue(all(v is None
                            for v in sheet["answers"].values()))
        # every catalogued question is rendered in the sheet body
        for qid in catalog_ids:
            self.assertIn("### %s" % qid, text)


class ProfileOverlayDriftTests(unittest.TestCase):
    ANCHORS = {
        "profile-01-spec-driven-dev.md": (
            "02-overlay-spec-driven-dev.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 5 — output format block",
             "## Phase 6 — output routing"]),
        "profile-02-youtube.md": (
            "03-overlay-youtube-script.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 5 — output format block",
             "## Phase 6 — output routing"]),
        "profile-03-presentation.md": (
            "04-overlay-presentation.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 5 — output format block",
             "## Phase 6 — output routing"]),
        "profile-04-ebook.md": (
            "05-overlay-ebook.md",
            ["## Phase 0 (ebook-specific) — book-level decomposition",
             "## Phase 1 — per-chapter decomposition adjustment",
             "## Phase 5 — output format block (per chapter)",
             "## Phase 6 — output routing (ebook production)"]),
        "profile-05-wordpress-seo.md": (
            "06-overlay-wordpress-seo.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 5 — output format block",
             "## Phase 6 — output routing (WordPress + Elementor)"]),
        "profile-06-health.md": (
            "07-overlay-health-content.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 5 — output format block",
             "## Phase 4 — citation verification (intensified for "
             "health)",
             "## Phase 5 exit check — final-dossier NotebookLM "
             "source-grounding (mandatory, blocking)",
             "## Phase 6 — output routing (per content type)"]),
        "profile-07-deck-screencast.md": (
            "08-overlay-deck-and-screencast.md",
            ["## Phase 1 — decomposition adjustment",
             "## Phase 6 — routing (the payoff: one artifact → both "
             "formats)"]),
        "profile-08-decision.md": (
            "13-overlay-deliberation-modes.md",
            ["## When 13 is the primary overlay",
             "## Mode selector (quick reference)",
             "<output_format> — DECISION BRIEF"]),
    }

    def test_profile_anchors_exist_in_shipped_overlays(self):
        for profile_name, (overlay_name, anchors) in self.ANCHORS.items():
            profile_text = read(os.path.join(SKILL_DIR, "references",
                                             profile_name))
            overlay_text = read(os.path.join(ORCH_DIR, "references",
                                             overlay_name))
            with self.subTest(profile=profile_name):
                self.assertIn(overlay_name, profile_text)
                for anchor in anchors:
                    self.assertIn(anchor, profile_text,
                                  "%s missing anchor %r in profile"
                                  % (profile_name, anchor))
                    self.assertIn(anchor, overlay_text,
                                  "%s missing anchor %r in overlay"
                                  % (overlay_name, anchor))

    def test_profile_fields_trace_to_overlay_requirements(self):
        checks = {
            "05-overlay-ebook.md": ["30k", "8-15",
                                    "00-book-outline.md"],
            "06-overlay-wordpress-seo.md": ["00-keyword-brief.md",
                                            "Secondary keywords",
                                            "1500 / 2500 / 4000"],
            "07-overlay-health-content.md": ["STRONG", "MODERATE",
                                             "WEAK", "2020",
                                             "scite.ai"],
            "08-overlay-deck-and-screencast.md": [
                "1 content slide/minute + 3 framing slides",
                "SPEAKER_NOTES"],
            "04-overlay-presentation.md": ["20/30/45/60"],
            "03-overlay-youtube-script.md": ["7-12 min"],
        }
        for overlay_name, needles in checks.items():
            text = read(os.path.join(ORCH_DIR, "references",
                                     overlay_name))
            for needle in needles:
                with self.subTest(overlay=overlay_name, needle=needle):
                    self.assertIn(needle, text)

    def test_health_policy_matches_overlay(self):
        text = read(os.path.join(ORCH_DIR, "references",
                                 "07-overlay-health-content.md"))
        self.assertIn("2020", text)
        self.assertIn("[STRONG]", text)
        self.assertIn("Phase 5 exit check", text)
        self.assertIn("SHA256", text)
        self.assertEqual(vk.HEALTH_POLICY["source_recency_cutoff_year"],
                         2020)
        self.assertEqual(vk.HEALTH_POLICY["evidence_strength_tags"],
                         ["STRONG", "MODERATE", "WEAK"])

    def test_overlay13_selector_rows_match_mode_rules(self):
        text = read(os.path.join(ORCH_DIR, "references",
                                 "13-overlay-deliberation-modes.md"))
        self.assertIn("## Mode selector (quick reference)", text)
        for needle in ("Standard research write-up",
                       "Yes/no decision with real trade-offs",
                       "Pre-launch / investment / pre-mortem",
                       "Convention looks wrong / novel problem",
                       "High-stakes go/no-go for sign-off"):
            self.assertIn(needle, text)
        self.assertIn("pipeline order", text)
        self.assertEqual(kio.derive_modes({"yes_no_choice"}), ["debate"])
        self.assertEqual(kio.derive_modes({"premortem"}), ["red-team"])
        self.assertEqual(kio.derive_modes({"suspect_convention"}),
                         ["first-principles"])
        self.assertEqual(kio.derive_modes({"high_stakes_signoff"}),
                         ["debate", "red-team"])
        # legal-layering contract present
        self.assertIn("Legal layering", text)
        self.assertIn("Phase 6 transform contract", text)

    def test_layering_rule_matches_constants(self):
        self.assertEqual(vk.LAYERABLE_USE_CASES, {1, 2, 3, 5, 6, 7})
        self.assertEqual(vk.PRIMARY_OVERLAY_BY_USE_CASE[8],
                         vk.OVERLAY_13)


class OrchestratorDriftTests(unittest.TestCase):
    def setUp(self):
        self.skill = read(os.path.join(ORCH_DIR, "SKILL.md"))

    def test_step0_structure_covered(self):
        for needle in ("Step 0.0", "Step 0.1", "Step 0.2", "Step 0.3",
                       "Step 0.4", "Step 0.5", "Step 0.6",
                       "greenfield", "brownfield"):
            self.assertIn(needle, self.skill)
        for n in range(1, 8):
            self.assertIn("%d. " % n, self.skill)

    def test_adapter_consumer_map_present(self):
        self.assertIn("Prepared-kickoff adapter", self.skill)
        self.assertIn("kickoff_schema_version", self.skill)
        for group in ("workspace", "invocation", "project",
                      "deliberation_modes", "use_case_profile",
                      "preferences", "conduct", "provenance"):
            self.assertIn("`%s`" % group, self.skill)
        for section in ("## Kickoff profile",
                        "## Phase-execution preferences",
                        "## Phase 6 deliverables", "## Conduct rules",
                        "## Kickoff provenance", "## Kickoff guidance",
                        "## Requirements input"):
            self.assertIn(section, self.skill)
        # no serialized group may be dead data: the adapter names every
        # consumer step family
        for needle in ("Step 0.5", "Step 0.6", "Steps 1.2", "Step 1.1",
                       "Step 3.3"):
            self.assertIn(needle, self.skill)

    def test_routing_descriptions_reciprocal(self):
        frontmatter = self.skill.split("---")[1]
        self.assertIn("research-kickoff-builder", frontmatter)
        self.assertIn("Do not use to build, refine, tighten, or validate "
                      "a kickoff brief", frontmatter)
        builder = read(os.path.join(SKILL_DIR, "SKILL.md"))
        builder_front = builder.split("---")[1]
        self.assertIn("research-orchestrator", builder_front)
        self.assertIn("Do not use to start, run, or resume",
                      builder_front)

    def test_config_example_ten_keys(self):
        text = read(os.path.join(ORCH_DIR, "templates",
                                 "research-config.example.md"))
        for agent, label in vk.CONFIG_LABELS.items():
            with self.subTest(agent=agent):
                lines = [l for l in text.split("\n")
                         if l.strip().startswith("- %s: " % label)]
                self.assertEqual(len(lines), 1, label)
                value = lines[0].split(": ", 1)[1].strip()
                entry = json.loads(value)
                problems = kio._validate_access_entry(agent, entry)
                self.assertIsNone(problems, problems)
        for state in ("unknown", "available", "unavailable"):
            self.assertIn(state, text)

    def test_phase1_enum_and_roles_lock(self):
        vp = load_sibling("validate_phase1.py")
        self.assertEqual(set(vk.PHASE1_AGENT_ENUM.values()), vp.AGENTS)
        self.assertEqual(vk.PHASE1_AGENT_ENUM["deepseek"],
                         "DecorrelatedLane")
        self.assertEqual(set(vk.ROLES), vp.ROLES)
        self.assertNotIn("scite", vk.LANE_AGENT_IDS)
        self.assertEqual(len(vk.AGENT_IDS), 10)

    def test_operator_marker_semantic_equality(self):
        vp = load_sibling("validate_phase1.py")
        self.assertEqual(vk.OPERATOR_SOURCE_RE.pattern,
                         vp.OPERATOR_SOURCE_RE.pattern)
        self.assertEqual(vk.OPERATOR_SOURCE_RE.flags,
                         vp.OPERATOR_SOURCE_RE.flags)
        probes_accept = [
            "operator-a", "operator-serp-log",
            "operator-private-sample (2026 export)",
            "operator-x1 (notes)", "operator-" + "a" * 41,
        ]
        probes_reject = [
            "operator-", "operator-UPPER", "operator--", "operator-a_b",
            "Operator-a", "operator-a (unclosed", "operator-a \n(x)",
            "operator-" + "a" * 42, "https://example.com",
        ]
        for probe in probes_accept:
            with self.subTest(probe=probe):
                self.assertTrue(vk.OPERATOR_SOURCE_RE.match(probe))
                self.assertTrue(vp.OPERATOR_SOURCE_RE.match(probe))
        for probe in probes_reject:
            with self.subTest(probe=probe):
                self.assertFalse(vk.OPERATOR_SOURCE_RE.match(probe))
                self.assertFalse(vp.OPERATOR_SOURCE_RE.match(probe))

    def test_reference_set_exact_14_and_twin_hashes(self):
        names = set(os.listdir(os.path.join(ORCH_DIR, "references")))
        self.assertEqual(names, EXPECTED_REFERENCE_NAMES)
        for name in sorted(EXPECTED_REFERENCE_NAMES):
            with self.subTest(name=name):
                self.assertEqual(
                    kio.sha256_hex_file(
                        os.path.join(ORCH_DIR, "references", name)),
                    kio.sha256_hex_file(
                        os.path.join(DOCS_METHODOLOGY, name)),
                    "twin drift: %s" % name)


class RepoDocsDriftTests(unittest.TestCase):
    def test_closed_matrix_in_checklist12(self):
        text = read(os.path.join(DOCS_METHODOLOGY,
                                 "12-project-startup-checklist.md"))
        self.assertNotIn("most demanding overlay", text)
        for needle in ("`wordpress_article`", "`youtube_script`",
                       "`ebook_chapter`", "`deck_and_screencast`",
                       "use case 7", "separate kickoff"):
            self.assertIn(needle, text)
        self.assertIn("Scite", text)
        self.assertIn("required for health", text)

    def test_closed_matrix_in_runbook11(self):
        text = read(os.path.join(DOCS_METHODOLOGY,
                                 "11-content-research-runbook.md"))
        self.assertNotIn("most demanding overlay", text)
        for needle in ("`wordpress_article`", "`ebook_chapter`",
                       "separate kickoff", "research-kickoff-builder",
                       "06a-wordpress_article-prep.md"):
            self.assertIn(needle, text)

    def test_howto_matrix_claims(self):
        text = read(os.path.join(REPO_ROOT, "docs",
                                 "how-to-run-a-project.md"))
        self.assertNotIn("One research pass feeds every format", text)
        self.assertIn("research-kickoff-builder", text)

    def test_render_matrix_constants_match_docs(self):
        self.assertEqual(
            vk.ADDITIONAL_RENDERS_ALLOWED,
            {2: ("wordpress_article",),
             6: ("youtube_script", "wordpress_article", "ebook_chapter"),
             8: ("deck_and_screencast",)})
        self.assertEqual(
            vk.PRIMARY_RENDER_BY_USE_CASE,
            {1: "architecture_decision_record", 2: "youtube_script",
             3: "presentation_deck", 4: "ebook", 5: "wordpress_article",
             6: "health_protocol", 7: "deck_and_screencast",
             8: "decision_brief"})

    def test_use_case_table_matches_checklist12(self):
        text = read(os.path.join(DOCS_METHODOLOGY,
                                 "12-project-startup-checklist.md"))
        for overlay in vk.PRIMARY_OVERLAY_BY_USE_CASE.values():
            self.assertIn(overlay, text)


class BuilderSkillTests(unittest.TestCase):
    def test_skill_under_500_lines(self):
        text = read(os.path.join(SKILL_DIR, "SKILL.md"))
        self.assertLess(len(text.split("\n")), 500)

    def test_skill_frontmatter_exact(self):
        text = read(os.path.join(SKILL_DIR, "SKILL.md"))
        front = text.split("---")[1]
        self.assertIn("name: research-kickoff-builder", front)
        self.assertIn("Builds or refines a validated Phase-0 kickoff "
                      "brief", front)

    def test_skill_contains_manual_checklist_and_commands(self):
        text = read(os.path.join(SKILL_DIR, "SKILL.md"))
        for needle in ("K1", "K8", "${CLAUDE_PLUGIN_ROOT}",
                       "validate_kickoff.py", "kickoff_io.py",
                       "BLOCKED_IO_RUNTIME"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()

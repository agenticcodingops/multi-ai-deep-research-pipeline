#!/usr/bin/env python3
"""Gate validator for the Phase 1 decomposition document (schema_version 2).

Reads the decomposition as JSON (raw, fenced inside markdown, or embedded),
vets every record once (G1), then runs gates G2-G8 over the vetted records
only, and prints a PASS/FAIL matrix or a JSON report.

Exit codes: 0 = all gates pass, 1 = gate failures, 2 = usage/IO/parse error.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter

GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
SCHEMA_VERSION = 2
ROLES = {"evidence", "sentiment", "synthesis", "decorrelated"}
LINEAGES = {"Anthropic", "OpenAI", "Google", "xAI", "decorrelated", "mixed"}
AGENTS = {"Perplexity", "Gemini", "Grok", "Claude", "ChatGPT",
          "DecorrelatedLane", "NotebookLM", "Elicit", "Consensus"}
SOURCE_TYPES = {"official_docs", "peer_reviewed", "news_recent",
                "social_signal", "primary_text", "vendor_pricing", "repo_docs"}
GT_STATUSES = {"verified", "asserted"}
CLASSIFICATIONS = {"trusted", "under_scrutiny"}
SQ_ID_RE = re.compile(r"^SQ\d{1,2}$")
LANE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | \
    {"com{0}".format(i) for i in range(1, 10)} | \
    {"lpt{0}".format(i) for i in range(1, 10)}
DEFERRED_PHASES = (2.5, 4.5)
DEFERRED_TOKENS_BY_PHASE = {4.5: {"<DRAFT_RECOMMENDATION>"}, 2.5: set()}
SENTINEL_TOKEN = "===BEGIN LANE OUTPUT==="
SENTINEL_LINE_RE = re.compile(r"(?m)^\s*===BEGIN LANE OUTPUT===\s*$")
SECTION_NAMES = ["tl;dr", "findings", "conflicts and uncertainties",
                 "what would change", "sources consulted", "coverage gaps"]
GT_TAGS = ["[ground-truth-verified]", "[ground-truth-asserted]",
           "[contradicts-ground-truth]"]
ALLOWLIST_POLICY = "word-forms"
REQUIRED_ARRAYS = ["sub_questions", "agent_assignments", "lane_roles",
                   "phase_2_prompts", "disqualifying_sources",
                   "success_criteria", "known_traps"]
PLACEHOLDER_KIND_RES = [
    ("angle", re.compile(r"<[A-Z][A-Z0-9_]*>")),
    ("brace", re.compile(r"\{[A-Z][A-Z0-9_]*\}")),
    ("guillemet", re.compile(u"«[^»]{1,60}»")),
    ("word", re.compile(r"\bTODO\b|\bTBD\b")),
    ("insert", re.compile(r"\[INSERT", re.IGNORECASE)),
]
STANDING = [("[HIGH]", "[high]"), ("[MEDIUM]", "[medium]"), ("[LOW]", "[low]"),
            ("resolvable URL", "resolvable url"),
            ("primary sources", "primary sources"),
            ("coverage gaps", "coverage gaps")]
_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!>~|-])")
_ZW_RE = re.compile(u"[​‌‍﻿]")


class DocumentError(Exception):
    """Unreadable or unparseable input; maps to exit code 2."""


def normalize(text):
    """NFC-normalize, drop markdown escapes, strip bold pairs and backticks."""
    text = unicodedata.normalize("NFC", text)
    text = _MD_ESCAPE_RE.sub(r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    return text


def _canon(text):
    """Whitespace-collapsed casefold of the normalized text."""
    return " ".join(normalize(text).split()).casefold()


def _fold(text):
    """Normalized, zero-width-stripped, casefolded text (contaminant compare)."""
    return _ZW_RE.sub("", normalize(text)).casefold()


def _str_or_none(value):
    return value if isinstance(value, str) else None


def placeholder_hits(text):
    """All placeholder hits as a set of (token, kind) pairs."""
    hits = set()
    for kind, rx in PLACEHOLDER_KIND_RES:
        for match in rx.finditer(text):
            hits.add((match.group(0), kind))
    return hits


def _load_json_document(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        raise DocumentError("cannot read {0}: {1}".format(path, exc))
    try:
        doc = json.loads(text)
    except ValueError:
        doc = None
    if doc is None:
        blocks = re.findall(r"```json\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        for block in sorted(blocks, key=len, reverse=True):
            try:
                doc = json.loads(block)
                break
            except ValueError:
                continue
    if doc is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                doc = json.loads(text[start:end + 1])
            except ValueError:
                doc = None
    if not isinstance(doc, dict):
        raise DocumentError(
            "no parseable JSON object found in {0} (tried raw JSON, fenced "
            "json blocks, and brace-delimited extraction)".format(path))
    return doc


def _load_rules(path):
    rules = {"extra_contaminants": [], "placeholder_allowlist": [],
             "min_evidence_lanes": 2}
    if path is None:
        return rules
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise DocumentError("cannot read project rules {0}: {1}".format(path, exc))
    if not isinstance(data, dict):
        raise DocumentError("project rules file must hold a JSON object")
    for key in ("extra_contaminants", "placeholder_allowlist"):
        value = data.get(key)
        if isinstance(value, list):
            rules[key] = [v for v in value if isinstance(v, str)]
    mel = data.get("min_evidence_lanes")
    if isinstance(mel, int) and not isinstance(mel, bool):
        rules["min_evidence_lanes"] = max(2, mel)
    return rules


def _path_str(path):
    parts = []
    for element in path:
        if isinstance(element, int):
            parts.append("[{0}]".format(element))
        else:
            parts.append(("." if parts else "") + str(element))
    return "".join(parts)


class _Validator(object):

    def __init__(self, doc, rules):
        self.doc = doc
        self.rules = rules
        self.failures = []
        self.warnings = []
        self.taint = set()
        # Vetted records; every gate after G1 reads only these.
        self.sqs = []          # {id, verdict_forced, falsifiable}
        self.sq_id_set = set()
        self.lanes = {}        # lane_id -> {agent, role, lineage}
        self.assignments = []  # (sqid, primary, secondary)
        self.prompts = []      # {sqid, agent, lane, prompt}
        self.inputs = []       # {input_id, contaminants}
        self.audits = {}
        self.claims = []       # raw claim dicts with a valid string claim_id
        self.deferred = []     # {phase, template, declared}

    def fail(self, gate, lane, message):
        self.failures.append({"gate": gate, "lane": lane, "message": message})

    def warn(self, gate, lane, message):
        self.warnings.append({"gate": gate, "lane": lane, "message": message})

    def lst(self, key):
        value = self.doc.get(key)
        return value if isinstance(value, list) else []

    def lane_columns(self):
        return list(self.lanes.keys())

    def prompt_lanes(self):
        return {p["lane"] for p in self.prompts}

    def _req_str(self, where, entry, key):
        value = _str_or_none(entry.get(key))
        if value is None or not value.strip():
            self.fail("G1", None,
                      "{0}: {1} must be a non-empty string".format(where, key))
            return None
        return value

    def validate(self):
        self.g1_structure()
        self.g2_verdicts()
        self.g3_assignments()
        self.g4_lane_coverage()
        self.g5_placeholders()
        self.g6_standing_rules()
        self.g7_contaminants()
        self.g8_ground_truth()

    # ------------------------------------------------------------------ G1
    def g1_structure(self):
        doc = self.doc
        sv = doc.get("schema_version")
        if not (isinstance(sv, int) and not isinstance(sv, bool)
                and sv == SCHEMA_VERSION):
            self.fail("G1", None,
                      "schema_version must be the integer {0} (got {1!r})".format(
                          SCHEMA_VERSION, sv))
        for key in REQUIRED_ARRAYS:
            if key not in doc:
                self.fail("G1", None, "missing required key '{0}'".format(key))
            elif not isinstance(doc[key], list):
                self.fail("G1", None, "key '{0}' must be an array".format(key))
        self._vet_sub_questions()
        self._vet_lanes()
        self._vet_assignments()
        self._vet_prompts()
        self._vet_inputs()
        self._vet_audits()
        self._vet_claims()
        self._vet_deferred()

    def _vet_sub_questions(self):
        raw = self.lst("sub_questions")
        if not 4 <= len(raw) <= 8:
            self.fail("G1", None,
                      "sub_questions count {0} outside the required 4-8".format(len(raw)))
        ids = []
        for index, entry in enumerate(raw):
            where = "sub_questions[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                self.taint.add("sub_questions")
                continue
            sqid = self._req_str(where, entry, "id")
            if sqid is None:
                self.taint.add("sub_questions")
                continue
            if not SQ_ID_RE.match(sqid):
                self.fail("G1", None,
                          "{0}: id {1!r} does not match SQ<num>".format(where, sqid))
            question = entry.get("question")
            if not (isinstance(question, str) and question.strip()):
                self.fail("G1", None,
                          "{0}: question must be a non-empty string".format(where))
            ids.append(sqid)
            self.sqs.append({"id": sqid,
                             "verdict_forced": entry.get("verdict_forced"),
                             "falsifiable": entry.get("falsifiable")})
        for sqid, count in Counter(ids).items():
            if count > 1:
                self.fail("G1", None, "duplicate sub_question id {0}".format(sqid))
        self.sq_id_set = set(ids)

    def _vet_lanes(self):
        for index, entry in enumerate(self.lst("lane_roles")):
            where = "lane_roles[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                self.taint.add("lane_roles")
                continue
            lane_id = self._req_str(where, entry, "lane_id")
            if lane_id is None:
                self.taint.add("lane_roles")
                continue
            if not LANE_ID_RE.match(lane_id):
                self.fail("G1", None,
                          "{0}: lane_id {1!r} is not a lowercase slug".format(where, lane_id))
            if lane_id.split(".")[0].lower() in WINDOWS_RESERVED:
                self.fail("G1", None,
                          "{0}: lane_id {1!r} is a reserved device name".format(where, lane_id))
            agent = _str_or_none(entry.get("agent"))
            if agent is None or agent not in AGENTS:
                self.fail("G1", None,
                          "{0}: agent {1!r} not in the agent enum".format(
                              where, entry.get("agent")))
            surface = entry.get("execution_surface")
            if not (isinstance(surface, str) and surface.strip()):
                self.fail("G1", None,
                          "{0}: execution_surface must be a non-empty string".format(where))
            if lane_id in self.lanes:
                self.fail("G1", None, "duplicate lane_id {0}".format(lane_id))
            else:
                self.lanes[lane_id] = {"agent": agent,
                                       "role": entry.get("role"),
                                       "lineage": entry.get("lineage")}

    def _vet_assignments(self):
        for index, entry in enumerate(self.lst("agent_assignments")):
            where = "agent_assignments[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                self.taint.add("agent_assignments")
                continue
            usable = True
            sqid = _str_or_none(entry.get("sub_question_id"))
            if sqid is None:
                self.fail("G1", None,
                          "{0}: sub_question_id must be a string".format(where))
                usable = False
            elif sqid not in self.sq_id_set:
                self.fail("G1", None,
                          "{0}: references unknown sub_question {1!r}".format(where, sqid))
                usable = False
            primary = _str_or_none(entry.get("primary_agent"))
            if primary is None or not primary.strip():
                self.fail("G1", None,
                          "{0}: primary_agent must be a non-empty string".format(where))
                usable = False
            elif primary not in AGENTS:
                self.fail("G1", None,
                          "{0}: primary_agent {1!r} not in the agent enum".format(
                              where, primary))
            secondary_raw = entry.get("secondary_agent")
            secondary = None
            if secondary_raw is not None:
                secondary = _str_or_none(secondary_raw)
                if secondary is None:
                    self.fail("G1", None,
                              "{0}: secondary_agent must be a string or null".format(where))
                    self.taint.add("agent_assignments")
                elif not secondary.strip():
                    secondary = None
                elif secondary not in AGENTS:
                    self.fail("G1", None,
                              "{0}: secondary_agent {1!r} not in the agent enum".format(
                                  where, secondary))
            source_type = _str_or_none(entry.get("source_type_required"))
            if source_type is None or source_type not in SOURCE_TYPES:
                self.fail("G1", None,
                          "{0}: source_type_required {1!r} not in the source-type "
                          "enum".format(where, entry.get("source_type_required")))
            if usable:
                self.assignments.append((sqid, primary, secondary))
            else:
                self.taint.add("agent_assignments")

    def _vet_prompts(self):
        for index, entry in enumerate(self.lst("phase_2_prompts")):
            where = "phase_2_prompts[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                self.taint.add("phase_2_prompts")
                continue
            usable = True
            sqid = _str_or_none(entry.get("sub_question_id"))
            if sqid is None:
                self.fail("G1", None,
                          "{0}: sub_question_id must be a string".format(where))
                usable = False
            elif sqid not in self.sq_id_set:
                self.fail("G1", None,
                          "{0}: references unknown sub_question {1!r}".format(where, sqid))
                usable = False
            lane_id = _str_or_none(entry.get("lane_id"))
            if lane_id is None:
                self.fail("G1", None, "{0}: lane_id must be a string".format(where))
                usable = False
            elif lane_id not in self.lanes:
                self.fail("G1", None,
                          "{0}: references undeclared lane {1!r}".format(where, lane_id))
                usable = False
            agent = _str_or_none(entry.get("agent"))
            if agent is None or not agent.strip():
                self.fail("G1", None,
                          "{0}: agent must be a non-empty string".format(where))
                usable = False
            elif agent not in AGENTS:
                self.fail("G1", None,
                          "{0}: agent {1!r} not in the agent enum".format(where, agent))
            prompt = entry.get("ready_to_paste_prompt")
            if not (isinstance(prompt, str) and prompt.strip()):
                self.fail("G1", None,
                          "{0}: ready_to_paste_prompt must be a non-empty string".format(where))
                prompt = None
            if usable:
                self.prompts.append({"sqid": sqid, "agent": agent,
                                     "lane": lane_id, "prompt": prompt})
            else:
                self.taint.add("phase_2_prompts")

    def _vet_inputs(self):
        for index, entry in enumerate(self.lst("inputs")):
            where = "inputs[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                continue
            input_id = self._req_str(where, entry, "input_id")
            if input_id is None:
                continue
            if entry.get("classification") not in CLASSIFICATIONS:
                self.fail("G1", None,
                          "{0}: classification {1!r} not in the enum".format(
                              where, entry.get("classification")))
            contaminants = entry.get("contaminants")
            if contaminants is None:
                contaminants = []
            elif not isinstance(contaminants, list):
                self.fail("G1", None,
                          "{0}: contaminants must be an array".format(where))
                contaminants = []
            else:
                if any(not isinstance(c, str) for c in contaminants):
                    self.fail("G1", None,
                              "{0}: contaminants entries must be strings".format(where))
                contaminants = [c for c in contaminants if isinstance(c, str)]
            self.inputs.append({"input_id": input_id, "contaminants": contaminants})

    def _vet_audits(self):
        audits = self.doc.get("input_audits")
        if audits is None:
            return
        if not isinstance(audits, dict):
            self.fail("G1", None, "input_audits must be an object keyed by input_id")
            return
        known = {entry["input_id"] for entry in self.inputs}
        for key in audits:
            if key not in known:
                self.fail("G1", None,
                          "input_audits key {0!r} matches no inputs entry".format(key))
        self.audits = audits

    def _vet_claims(self):
        ids = []
        for index, entry in enumerate(self.lst("ground_truth")):
            where = "ground_truth[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                continue
            claim_id = _str_or_none(entry.get("claim_id"))
            if claim_id is None or not claim_id.strip():
                self.fail("G1", None,
                          "{0}: claim_id must be a non-empty string".format(where))
                continue
            ids.append(claim_id)
            self.claims.append(entry)
        for claim_id, count in Counter(ids).items():
            if count > 1:
                self.fail("G1", None, "duplicate claim_id {0}".format(claim_id))

    def _vet_deferred(self):
        for index, entry in enumerate(self.lst("deferred_phase_prompts")):
            where = "deferred_phase_prompts[{0}]".format(index)
            if not isinstance(entry, dict):
                self.fail("G1", None, "{0}: must be an object".format(where))
                continue
            phase = entry.get("phase")
            if not (isinstance(phase, (int, float)) and not isinstance(phase, bool)
                    and float(phase) in DEFERRED_PHASES):
                self.fail("G1", None,
                          "{0}: phase must be one of {1} (got {2!r})".format(
                              where, list(DEFERRED_PHASES), phase))
                continue
            template = entry.get("prompt_template")
            if not isinstance(template, str):
                self.fail("G1", None,
                          "{0}: prompt_template must be a string".format(where))
                continue
            declared = entry.get("declared_placeholders")
            if not (isinstance(declared, list)
                    and all(isinstance(x, str) for x in declared)):
                self.fail("G1", None,
                          "{0}: declared_placeholders must be an array of "
                          "strings".format(where))
                continue
            self.deferred.append({"phase": float(phase), "template": template,
                                  "declared": set(declared)})

    # ------------------------------------------------------------------ G2
    def g2_verdicts(self):
        for sq in self.sqs:
            verdict = sq["verdict_forced"]
            if not (isinstance(verdict, str) and verdict.strip()):
                self.fail("G2", None,
                          "sub_question {0}: verdict_forced is empty or missing".format(
                              sq["id"]))
            if sq["falsifiable"] is not True:
                self.fail("G2", None,
                          "sub_question {0}: falsifiable is not true".format(sq["id"]))

    # ------------------------------------------------------------------ G3
    def g3_assignments(self):
        if "agent_assignments" in self.taint or "phase_2_prompts" in self.taint:
            return
        fmt = lambda pairs: ", ".join("({0}, {1})".format(a, b) for a, b in pairs)
        assigned = Counter()
        for sqid, primary, secondary in self.assignments:
            if secondary is not None and primary == secondary:
                self.fail("G3", None,
                          "sub_question {0}: primary_agent equals secondary_agent "
                          "({1})".format(sqid, primary))
            assigned[(sqid, primary)] += 1
            if secondary is not None:
                assigned[(sqid, secondary)] += 1
        prompted = Counter((p["sqid"], p["agent"]) for p in self.prompts)
        for pair, count in sorted(assigned.items()):
            if count > 1:
                self.fail("G3", None,
                          "duplicate assignment pair {0}".format(fmt([pair])))
        for pair, count in sorted(prompted.items()):
            if count > 1:
                self.fail("G3", None,
                          "duplicate prompt pair {0}".format(fmt([pair])))
        only_prompted = sorted(set(prompted) - set(assigned))
        only_assigned = sorted(set(assigned) - set(prompted))
        if only_prompted:
            self.fail("G3", None,
                      "pairs in phase_2_prompts but not agent_assignments: {0}".format(
                          fmt(only_prompted)))
        if only_assigned:
            self.fail("G3", None,
                      "pairs in agent_assignments but not phase_2_prompts: {0}".format(
                          fmt(only_assigned)))
        for record in self.prompts:
            lane = self.lanes.get(record["lane"])
            if lane and lane["agent"] and record["agent"] != lane["agent"]:
                self.fail("G3", record["lane"],
                          "prompt agent {0} does not match lane agent {1} "
                          "(lane-swap)".format(record["agent"], lane["agent"]))

    # ------------------------------------------------------------------ G4
    def g4_lane_coverage(self):
        for lane_id, record in self.lanes.items():
            if record["role"] not in ROLES:
                self.fail("G4", None,
                          "lane {0!r}: invalid role {1!r}".format(lane_id, record["role"]))
            if record["lineage"] not in LINEAGES:
                self.fail("G4", None,
                          "lane {0!r}: invalid lineage {1!r}".format(
                              lane_id, record["lineage"]))
        per_sq = {}
        for record in self.prompts:
            per_sq.setdefault(record["sqid"], set()).add(record["lane"])
        minimum = self.rules["min_evidence_lanes"]
        for sqid in sorted(self.sq_id_set):
            lanes = {lid for lid in per_sq.get(sqid, set())
                     if self.lanes.get(lid, {}).get("role") in ("evidence", "decorrelated")}
            if len(lanes) < minimum:
                self.fail("G4", None,
                          "sub_question {0}: {1} distinct evidence/decorrelated lane(s) "
                          "({2}); need >= {3}".format(
                              sqid, len(lanes), ", ".join(sorted(lanes)) or "none",
                              minimum))

    # ------------------------------------------------------------------ G5
    def g5_placeholders(self):
        allow = set(self.rules["placeholder_allowlist"])
        for record in self.prompts:
            if record["prompt"] is None:
                continue
            hits = placeholder_hits(normalize(record["prompt"]))
            for token, kind in sorted(hits):
                if kind == "word" and ALLOWLIST_POLICY == "word-forms" and \
                        token in allow:
                    continue
                self.fail("G5", record["lane"],
                          "unfilled placeholder '{0}'".format(token))
        for index, entry in enumerate(self.deferred):
            label = "deferred prompt {0} (phase {1})".format(index + 1, entry["phase"])
            contract = DEFERRED_TOKENS_BY_PHASE.get(entry["phase"], set())
            found = {token for token, _kind in
                     placeholder_hits(normalize(entry["template"]))}
            declared = entry["declared"]
            undeclared = sorted(found - declared)
            stale = sorted(declared - found)
            rogue = sorted((found | declared) - contract)
            if undeclared:
                self.fail("G5", None, "{0}: undeclared placeholders: {1}".format(
                    label, ", ".join(undeclared)))
            if stale:
                self.fail("G5", None, "{0}: stale declared placeholders: {1}".format(
                    label, ", ".join(stale)))
            if rogue:
                self.fail("G5", None,
                          "{0}: tokens not in the phase {1} contract: {2}".format(
                              label, entry["phase"], ", ".join(rogue)))

    # ------------------------------------------------------------------ G6
    def g6_standing_rules(self):
        for record in self.prompts:
            if record["prompt"] is None:
                continue
            raw = normalize(record["prompt"])
            low = _canon(record["prompt"])
            missing = []
            if SENTINEL_TOKEN not in raw:
                missing.append("sentinel token {0}".format(SENTINEL_TOKEN))
            elif SENTINEL_LINE_RE.search(raw):
                self.fail("G6", record["lane"],
                          "sentinel must not appear as a standalone line inside "
                          "the prompt")
            for name in SECTION_NAMES:
                if name not in low:
                    missing.append("section name '{0}'".format(name))
            for shown, needle in STANDING:
                if needle not in low:
                    missing.append(shown)
            if self.claims:
                if "ground truth" not in low:
                    missing.append("ground truth")
                for claim in self.claims:
                    claim_id = claim.get("claim_id")
                    if claim_id.casefold() not in low:
                        missing.append(claim_id)
                    statement = claim.get("statement")
                    if isinstance(statement, str) and statement.strip() and \
                            _canon(statement)[:40] not in low:
                        missing.append("statement excerpt ({0})".format(claim_id))
                    metric = claim.get("metric_definition")
                    if isinstance(metric, str) and metric.strip() and \
                            _canon(metric)[:40] not in low:
                        missing.append("metric excerpt ({0})".format(claim_id))
                    url = claim.get("source_url")
                    if isinstance(url, str) and url.startswith("https://") and \
                            url not in raw:
                        missing.append("source_url ({0})".format(claim_id))
                for tag in GT_TAGS:
                    if tag not in low:
                        missing.append(tag)
            if missing:
                self.fail("G6", record["lane"],
                          "prompt for {0} missing required strings: {1}".format(
                              record["sqid"], ", ".join(missing)))

    # ------------------------------------------------------------------ G7
    def _lane_for_path(self, path):
        if len(path) >= 2 and path[0] == "phase_2_prompts" and isinstance(path[1], int):
            entries = self.lst("phase_2_prompts")
            if path[1] < len(entries) and isinstance(entries[path[1]], dict):
                return _str_or_none(entries[path[1]].get("lane_id"))
        return None

    def g7_contaminants(self):
        contaminants = []
        for entry in self.inputs:
            contaminants.extend(c for c in entry["contaminants"] if c.strip())
        contaminants.extend(c for c in self.rules["extra_contaminants"] if c.strip())
        if not contaminants:
            return
        matchers = []
        for contaminant in contaminants:
            folded = _fold(contaminant)
            if not folded:
                continue
            if len(folded) < 6:
                rx = re.compile(r"(?<!\w)" + re.escape(folded) + r"(?!\w)")
                matchers.append((contaminant, None, rx))
            else:
                matchers.append((contaminant, folded, None))

        def visit(node, path):
            if isinstance(node, dict):
                for key, value in node.items():
                    visit(value, path + [key])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, path + [index])
            elif isinstance(node, str):
                node_fold = _fold(node)
                hits = []
                for original, folded, rx in matchers:
                    if rx is not None:
                        if rx.search(node_fold):
                            hits.append(original)
                    elif folded in node_fold:
                        hits.append(original)
                if not hits:
                    return
                if (path and path[0] == "input_audits") or \
                        any(p == "contaminants" for p in path):
                    return
                where = _path_str(path)
                final = path[-1] if path else None
                if final in ("ready_to_paste_prompt", "prompt_template"):
                    lane = self._lane_for_path(path)
                    for hit in hits:
                        self.fail("G7", lane,
                                  "contaminant {0!r} leaked into {1}".format(hit, where))
                else:
                    for hit in hits:
                        self.warn("G7", None,
                                  "contaminant {0!r} present at {1}".format(hit, where))

        visit(self.doc, [])

    # ------------------------------------------------------------------ G8
    def g8_ground_truth(self):
        for claim in self.claims:
            label = claim.get("claim_id")
            statement = claim.get("statement")
            if not (isinstance(statement, str) and statement.strip()):
                self.fail("G8", None, "{0}: statement is empty or missing".format(label))
            metric = claim.get("metric_definition")
            if not (isinstance(metric, str) and metric.strip()):
                self.fail("G8", None,
                          "{0}: metric_definition is empty or missing".format(label))
            if claim.get("status") not in GT_STATUSES:
                self.fail("G8", None, "{0}: status {1!r} not in {2}".format(
                    label, claim.get("status"), sorted(GT_STATUSES)))
            url = claim.get("source_url")
            if not (isinstance(url, str) and url.startswith("https://")):
                self.fail("G8", None,
                          "{0}: source_url must start with https:// (got {1!r})".format(
                              label, url))


def _build_matrix(columns, prompt_lanes, failures, warnings):
    applicable = {
        "G1": {"GLOBAL"}, "G2": {"GLOBAL"}, "G3": {"GLOBAL"}, "G4": {"GLOBAL"},
        "G5": {"GLOBAL"} | set(prompt_lanes),
        "G6": set(prompt_lanes),
        "G7": {"GLOBAL"} | set(prompt_lanes),
        "G8": {"GLOBAL"},
    }

    def column_of(item):
        lane = item.get("lane")
        return lane if lane in columns else "GLOBAL"

    rows = {}
    for gate in GATES:
        fail_cols = {column_of(f) for f in failures if f["gate"] == gate}
        warn_cols = {column_of(w) for w in warnings if w["gate"] == gate}
        row = {}
        for column in columns:
            if column in fail_cols:
                row[column] = "FAIL"
            elif column in warn_cols:
                row[column] = "WARN"
            elif column in applicable[gate]:
                row[column] = "PASS"
            else:
                row[column] = "-"
        rows[gate] = row
    return {"columns": columns, "rows": rows}


def render_human(report):
    lines = []
    columns = report["matrix"]["columns"]
    widths = [max(len(c), 4) + 2 for c in columns]
    lines.append(("Gate  " + "".join(c.ljust(w) for c, w in zip(columns, widths))).rstrip())
    for gate in GATES:
        row = report["matrix"]["rows"][gate]
        cells = "".join(row.get(c, "-").ljust(w) for c, w in zip(columns, widths))
        lines.append((gate.ljust(6) + cells).rstrip())
    for failure in report["failures"]:
        where = "lane={0}".format(failure["lane"]) if failure["lane"] else "GLOBAL"
        lines.append("FAIL {0} {1}: {2}".format(failure["gate"], where, failure["message"]))
    for warning in report["warnings"]:
        where = "lane={0}".format(warning["lane"]) if warning["lane"] else "GLOBAL"
        lines.append("WARN {0} {1}: {2}".format(warning["gate"], where, warning["message"]))
    if report["result"] == "pass":
        lines.append("RESULT: PASS")
    else:
        lines.append("RESULT: FAIL ({0} failures, {1} warnings)".format(
            len(report["failures"]), len(report["warnings"])))
    return "\n".join(lines)


def run(document_path, project_rules_path=None):
    """Validate the Phase 1 document and return the report dict."""
    doc = _load_json_document(document_path)
    rules = _load_rules(project_rules_path)
    validator = _Validator(doc, rules)
    try:
        validator.validate()
    except Exception as exc:
        validator.fail("G1", None, "internal validation error: {0}: {1}".format(
            exc.__class__.__name__, exc))
    columns = ["GLOBAL"] + validator.lane_columns()
    matrix = _build_matrix(columns, validator.prompt_lanes(),
                           validator.failures, validator.warnings)
    return {
        "result": "fail" if validator.failures else "pass",
        "failures": validator.failures,
        "warnings": validator.warnings,
        "matrix": matrix,
    }


def main(argv):
    parser = argparse.ArgumentParser(
        prog="validate_phase1",
        description="Gate the Phase 1 decomposition document (gates G1-G8).")
    parser.add_argument("document", help="path to the decomposition .md or .json file")
    parser.add_argument("--project-rules", dest="project_rules", default=None,
                        help="optional JSON file with extra_contaminants, "
                             "placeholder_allowlist, min_evidence_lanes")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit a machine-readable JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 2
    try:
        report = run(args.document, args.project_rules)
    except DocumentError as exc:
        sys.stderr.write("error: {0}\n".format(exc))
        return 2
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

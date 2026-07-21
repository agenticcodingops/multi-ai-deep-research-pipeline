#!/usr/bin/env python3
"""Gate validator for the Phase 1 decomposition document (schema_version 2).

Reads the decomposition as JSON (raw, fenced inside markdown, or embedded),
runs gates G1-G8, and prints a PASS/FAIL matrix or a JSON report.

Exit codes: 0 = all gates pass, 1 = gate failures, 2 = usage/IO/parse error.
"""

import argparse
import json
import re
import sys
import unicodedata

GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
ROLES = {"evidence", "sentiment", "synthesis", "decorrelated"}
LINEAGES = {"Anthropic", "OpenAI", "Google", "xAI", "decorrelated", "mixed"}
GT_STATUSES = {"verified", "asserted"}
CLASSIFICATIONS = {"trusted", "under_scrutiny"}
SQ_ID_RE = re.compile(r"^SQ\d{1,2}$")
REQUIRED_ARRAYS = ["sub_questions", "agent_assignments", "lane_roles",
                   "phase_2_prompts", "disqualifying_sources",
                   "success_criteria", "known_traps"]
PLACEHOLDER_RES = [
    re.compile(r"<[A-Z][A-Z0-9_]*>"),
    re.compile(r"\{[A-Z][A-Z0-9_]*\}"),
    re.compile(u"«[^»]{1,60}»"),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\[INSERT", re.IGNORECASE),
]
STANDING = [("[HIGH]", "[high]"), ("[MEDIUM]", "[medium]"), ("[LOW]", "[low]"),
            ("resolvable URL", "resolvable url"),
            ("primary sources", "primary sources"),
            ("coverage gaps", "coverage gaps")]
_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!>~|-])")


class DocumentError(Exception):
    """Unreadable or unparseable input; maps to exit code 2."""


def normalize(text):
    """NFC-normalize, drop markdown escapes, strip bold pairs and backticks."""
    text = unicodedata.normalize("NFC", text)
    text = _MD_ESCAPE_RE.sub(r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]*)`", r"\1", text)
    return text


def placeholder_tokens(text):
    tokens = set()
    for rx in PLACEHOLDER_RES:
        for match in rx.finditer(text):
            tokens.add(match.group(0))
    return tokens


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
        rules["min_evidence_lanes"] = mel
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

    def fail(self, gate, lane, message):
        self.failures.append({"gate": gate, "lane": lane, "message": message})

    def warn(self, gate, lane, message):
        self.warnings.append({"gate": gate, "lane": lane, "message": message})

    def lst(self, key):
        value = self.doc.get(key)
        return value if isinstance(value, list) else []

    def dicts(self, key):
        return [e for e in self.lst(key) if isinstance(e, dict)]

    def sq_ids(self):
        return {e.get("id") for e in self.dicts("sub_questions")
                if isinstance(e.get("id"), str)}

    def lane_columns(self):
        seen = []
        for entry in self.dicts("lane_roles"):
            lid = entry.get("lane_id")
            if isinstance(lid, str) and lid not in seen:
                seen.append(lid)
        return seen

    def prompt_lanes(self):
        return {e.get("lane_id") for e in self.dicts("phase_2_prompts")
                if isinstance(e.get("lane_id"), str)}

    def _lane_of(self, entry):
        lid = entry.get("lane_id")
        return lid if isinstance(lid, str) else None

    def validate(self):
        self.g1_structure()
        self.g2_verdicts()
        self.g3_assignments()
        self.g4_lane_coverage()
        self.g5_placeholders()
        self.g6_standing_rules()
        self.g7_contaminants()
        self.g8_ground_truth()

    def g1_structure(self):
        if "schema_version" not in self.doc:
            self.warn("G1", None, "schema_version absent; assuming schema_version 2")
        for key in REQUIRED_ARRAYS:
            if key not in self.doc:
                self.fail("G1", None, "missing required key '{0}'".format(key))
            elif not isinstance(self.doc[key], list):
                self.fail("G1", None, "key '{0}' must be an array".format(key))
        subs = self.dicts("sub_questions")
        if not 4 <= len(subs) <= 8:
            self.fail("G1", None,
                      "sub_questions count {0} outside the required 4-8".format(len(subs)))
        for sq in subs:
            sqid = sq.get("id")
            if not (isinstance(sqid, str) and SQ_ID_RE.match(sqid)):
                self.fail("G1", None,
                          "sub_question id {0!r} does not match SQ<num>".format(sqid))
            question = sq.get("question")
            if not (isinstance(question, str) and question.strip()):
                self.fail("G1", None,
                          "sub_question {0!r} has no question text".format(sqid))
        sq_ids = self.sq_ids()
        for entry in self.dicts("agent_assignments"):
            ref = entry.get("sub_question_id")
            if ref not in sq_ids:
                self.fail("G1", None,
                          "agent_assignments references unknown sub_question {0!r}".format(ref))
        lane_ids = set(self.lane_columns())
        for entry in self.dicts("phase_2_prompts"):
            if entry.get("sub_question_id") not in sq_ids:
                self.fail("G1", None,
                          "phase_2_prompts references unknown sub_question {0!r}".format(
                              entry.get("sub_question_id")))
            if entry.get("lane_id") not in lane_ids:
                self.fail("G1", None,
                          "phase_2_prompts references undeclared lane {0!r}".format(
                              entry.get("lane_id")))
        for entry in self.dicts("inputs"):
            cls = entry.get("classification")
            if cls not in CLASSIFICATIONS:
                self.fail("G1", None,
                          "input {0!r} has invalid classification {1!r}".format(
                              entry.get("input_id"), cls))
        audits = self.doc.get("input_audits")
        if audits is not None:
            if not isinstance(audits, dict):
                self.fail("G1", None, "input_audits must be an object keyed by input_id")
            else:
                known = {e.get("input_id") for e in self.dicts("inputs")}
                for key in audits:
                    if key not in known:
                        self.fail("G1", None,
                                  "input_audits key {0!r} matches no inputs entry".format(key))

    def g2_verdicts(self):
        for sq in self.dicts("sub_questions"):
            sqid = sq.get("id") or "?"
            verdict = sq.get("verdict_forced")
            if not (isinstance(verdict, str) and verdict.strip()):
                self.fail("G2", None,
                          "sub_question {0}: verdict_forced is empty or missing".format(sqid))
            if sq.get("falsifiable") is not True:
                self.fail("G2", None,
                          "sub_question {0}: falsifiable is not true".format(sqid))

    def g3_assignments(self):
        assigned = set()
        for entry in self.dicts("agent_assignments"):
            sqid = entry.get("sub_question_id")
            primary = entry.get("primary_agent")
            if isinstance(primary, str) and primary.strip():
                assigned.add((sqid, primary))
            secondary = entry.get("secondary_agent")
            if isinstance(secondary, str) and secondary.strip():
                assigned.add((sqid, secondary))
        prompted = {(e.get("sub_question_id"), e.get("agent"))
                    for e in self.dicts("phase_2_prompts")}
        key = lambda pair: (str(pair[0]), str(pair[1]))
        fmt = lambda pairs: ", ".join("({0}, {1})".format(a, b) for a, b in pairs)
        only_prompted = sorted(prompted - assigned, key=key)
        only_assigned = sorted(assigned - prompted, key=key)
        if only_prompted:
            self.fail("G3", None,
                      "pairs in phase_2_prompts but not agent_assignments: {0}".format(
                          fmt(only_prompted)))
        if only_assigned:
            self.fail("G3", None,
                      "pairs in agent_assignments but not phase_2_prompts: {0}".format(
                          fmt(only_assigned)))

    def g4_lane_coverage(self):
        lane_role = {}
        for entry in self.dicts("lane_roles"):
            lid = entry.get("lane_id")
            role = entry.get("role")
            if role not in ROLES:
                self.fail("G4", None,
                          "lane {0!r}: invalid role {1!r}".format(lid, role))
            lineage = entry.get("lineage")
            if lineage not in LINEAGES:
                self.fail("G4", None,
                          "lane {0!r}: invalid lineage {1!r}".format(lid, lineage))
            surface = entry.get("execution_surface")
            if not (isinstance(surface, str) and surface.strip()):
                self.fail("G4", None,
                          "lane {0!r}: execution_surface is empty".format(lid))
            if isinstance(lid, str):
                lane_role[lid] = role
        per_sq = {}
        for entry in self.dicts("phase_2_prompts"):
            per_sq.setdefault(entry.get("sub_question_id"), set()).add(entry.get("lane_id"))
        minimum = self.rules["min_evidence_lanes"]
        for sqid in sorted(self.sq_ids()):
            lanes = {lid for lid in per_sq.get(sqid, set())
                     if lane_role.get(lid) in ("evidence", "decorrelated")}
            if len(lanes) < minimum:
                self.fail("G4", None,
                          "sub_question {0}: {1} distinct evidence/decorrelated lane(s) "
                          "({2}); need >= {3}".format(
                              sqid, len(lanes), ", ".join(sorted(lanes)) or "none", minimum))

    def g5_placeholders(self):
        allow = set(self.rules["placeholder_allowlist"])
        for entry in self.dicts("phase_2_prompts"):
            lane = self._lane_of(entry)
            prompt = entry.get("ready_to_paste_prompt")
            if not (isinstance(prompt, str) and prompt.strip()):
                self.fail("G5", lane, "ready_to_paste_prompt is empty or missing")
                continue
            for token in sorted(placeholder_tokens(normalize(prompt)) - allow):
                self.fail("G5", lane, "unfilled placeholder '{0}'".format(token))
        for index, entry in enumerate(self.dicts("deferred_phase_prompts")):
            label = "deferred prompt {0} (phase {1})".format(index + 1, entry.get("phase"))
            template = entry.get("prompt_template")
            declared = {t for t in entry.get("declared_placeholders") or []
                        if isinstance(t, str)} - allow
            found = set()
            if isinstance(template, str):
                found = placeholder_tokens(normalize(template)) - allow
            undeclared = sorted(found - declared)
            stale = sorted(declared - found)
            if undeclared:
                self.fail("G5", None, "{0}: undeclared placeholders: {1}".format(
                    label, ", ".join(undeclared)))
            if stale:
                self.fail("G5", None, "{0}: stale declared placeholders: {1}".format(
                    label, ", ".join(stale)))

    def g6_standing_rules(self):
        ground_truth = self.dicts("ground_truth")
        claim_ids = [c.get("claim_id") for c in ground_truth
                     if isinstance(c.get("claim_id"), str) and c.get("claim_id").strip()]
        for entry in self.dicts("phase_2_prompts"):
            prompt = entry.get("ready_to_paste_prompt")
            if not isinstance(prompt, str):
                continue
            low = normalize(prompt).lower()
            missing = [shown for shown, needle in STANDING if needle not in low]
            if ground_truth:
                if "ground truth" not in low:
                    missing.append("ground truth")
                for cid in claim_ids:
                    if cid.lower() not in low:
                        missing.append(cid)
            if missing:
                self.fail("G6", self._lane_of(entry),
                          "prompt for {0} missing required strings: {1}".format(
                              entry.get("sub_question_id"), ", ".join(missing)))

    def _lane_for_path(self, path):
        if len(path) >= 2 and path[0] == "phase_2_prompts" and isinstance(path[1], int):
            entries = self.lst("phase_2_prompts")
            if path[1] < len(entries) and isinstance(entries[path[1]], dict):
                return self._lane_of(entries[path[1]])
        return None

    def g7_contaminants(self):
        contaminants = []
        for entry in self.dicts("inputs"):
            values = entry.get("contaminants")
            for value in values if isinstance(values, list) else []:
                if isinstance(value, str) and value.strip():
                    contaminants.append(value)
        contaminants.extend(self.rules["extra_contaminants"])
        if not contaminants:
            return
        lowered = [(c, c.lower()) for c in contaminants]

        def visit(node, path):
            if isinstance(node, dict):
                for key, value in node.items():
                    visit(value, path + [key])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, path + [index])
            elif isinstance(node, str):
                low = node.lower()
                hits = [orig for orig, needle in lowered if needle in low]
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

    def g8_ground_truth(self):
        for index, claim in enumerate(self.dicts("ground_truth")):
            cid = claim.get("claim_id")
            label = cid if isinstance(cid, str) and cid.strip() else "claim[{0}]".format(index)
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
    validator.validate()
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

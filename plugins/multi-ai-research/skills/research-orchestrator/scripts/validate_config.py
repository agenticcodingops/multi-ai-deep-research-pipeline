#!/usr/bin/env python3
"""Validator for a workspace's research-config.md (Step 0.0).

Reports the dossier root and, per agent-access entry, one of four classes:

  v1       normalized `- <Label>: <compact JSON>` passing every shape rule
  legacy   free-text (or empty) — read as UNKNOWN, never as confirmed absent
  invalid  JSON-shaped and failing a shape rule
  missing  no line for that label

The legacy class is the point of this script. The documented reading rule is
that a legacy `none` means "never asked", NOT "confirmed unavailable" — so an
operator who writes `- NotebookLM: none` meaning "I don't have this" is recorded
as unknown and re-asked on the next project that needs it, three sessions after
the cause. That is a silent failure with no gate anywhere, and the format has
three states and a documented trap, so it deserves a validator.

Legacy entries are therefore reported LOUDLY and are NOT a failure: Step 0.3
offers to normalize them and never rewrites automatically, and a red gate here
would coerce an operator into accepting any rewrite offered. Only structural
defects fail.

Exit codes: 0 = usable config, 1 = structural defect, 2 = usage/IO error.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

# --- byte-identical duplicates of the kickoff builder's tables --------------
# Runtime scripts may not import across skill directories (each skill's scripts
# must run standalone from its own folder), so these are duplicated and locked
# to research-kickoff-builder/scripts/validate_kickoff.py by
# test_contract_drift.py::test_validate_config_label_and_route_lock. If a drift
# test goes red, fix the drifted copy — never loosen the test.
AGENT_IDS = ("perplexity", "gemini", "grok", "chatgpt", "claude",
             "deepseek", "notebooklm", "elicit", "consensus", "scite")
LANE_AGENT_IDS = AGENT_IDS[:9]  # scite is never a Phase-2 lane

CONFIG_LABELS = {
    "perplexity": "Perplexity", "gemini": "Gemini", "grok": "Grok",
    "chatgpt": "ChatGPT", "claude": "Claude", "deepseek": "DeepSeek route",
    "notebooklm": "NotebookLM", "elicit": "Elicit", "consensus": "Consensus",
    "scite": "Scite",
}

ROUTES_BY_AGENT = {
    "claude": ("claude_web_extended_thinking", "local"),
    "deepseek": ("consumer_web", "western_hosted_api", "self_hosted"),
}
for _a in AGENT_IDS:
    ROUTES_BY_AGENT.setdefault(_a, ("web", "api"))

SECRET_RES = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("api-key-prefix", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("github-token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("credential-assignment",
     re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*\S{6,}")),
]

STATUSES = ("unknown", "available", "unavailable")
ENTRY_KEYS = ("status", "tier", "routes")

# Orchestrator-local, deliberately NOT drift-locked: near-misses for a label
# whose exact form is load-bearing. `- DeepSeek:` (without " route") would
# otherwise be silently ignored and read as "DeepSeek route missing => unknown"
# — the same silent-opposite trap as legacy `none`.
LABEL_ALIASES = {"deepseek": "deepseek", "deep seek": "deepseek",
                 "deepseek route": "deepseek", "notebook lm": "notebooklm",
                 "chat gpt": "chatgpt"}

LABEL_BY_NORM = {label.casefold(): agent
                 for agent, label in CONFIG_LABELS.items()}

DOSSIER_ROOT_RE = re.compile(r"(?im)^[ \t]*Dossier root[ \t]*:[ \t]*(.*)$")
AGENT_SECTION_RE = re.compile(r"(?im)^##[ \t]+Agent access[ \t]*$")
NEXT_SECTION_RE = re.compile(r"(?m)^##[ \t]")
BULLET_RE = re.compile(r"^[ \t]*-[ \t]*([^:]+?)[ \t]*:[ \t]*(.*)$")


class ConfigError(Exception):
    """Unreadable input or bad CLI usage; maps to exit code 2."""


def _mask(text, spans):
    """Blank the given (start, end) spans to spaces, preserving newlines."""
    if not spans:
        return text
    chars = list(text)
    for start, end in spans:
        for i in range(max(0, start), min(len(chars), end)):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def _hidden_spans(text):
    """Spans hidden by HTML comments or code fences, scanned left to right.

    Whichever opener appears first claims text through its own closer, and
    markers inside a claimed region are inert: a ``` line inside a comment is
    not a fence, and a `<!--` inside a fence is not a comment. Computing the
    two span sets independently over the raw text let either marker poison
    the mask through EOF (PR review). Unterminated regions run to EOF.
    Fence markers are lines starting with ``` or ~~~ at indent <= 3; any
    fence marker line closes an open fence."""
    fence_lines = []
    position = 0
    for line in text.splitlines(True):
        stripped = line.lstrip(" \t")
        if len(line) - len(stripped) <= 3 and \
                stripped.startswith(("```", "~~~")):
            fence_lines.append((position, position + len(line)))
        position += len(line)
    spans = []
    pos = 0
    fence_index = 0
    while True:
        while fence_index < len(fence_lines) and \
                fence_lines[fence_index][0] < pos:
            fence_index += 1
        comment_at = text.find("<!--", pos)
        fence_at = fence_lines[fence_index][0] \
            if fence_index < len(fence_lines) else -1
        if comment_at == -1 and fence_at == -1:
            break
        if fence_at == -1 or (comment_at != -1 and comment_at < fence_at):
            close = text.find("-->", comment_at + 4)
            end = len(text) if close == -1 else close + 3
            spans.append((comment_at, end))
            pos = end
        elif fence_index + 1 < len(fence_lines):
            spans.append((fence_at, fence_lines[fence_index + 1][1]))
            pos = fence_lines[fence_index + 1][1]
        else:
            spans.append((fence_at, len(text)))
            break
    return spans


def mask_hidden(text):
    """Blank HTML comments AND fenced code blocks.

    Both are mandatory, not cosmetic. The shipped template documents its own
    reading rules inside an HTML comment, and several of those lines parse as
    `- Label: value` — without comment masking the template fails its own
    validator. Fences matter in the other direction: a fenced
    `Dossier root: decoy/` example was ACTIVE configuration before this, and a
    fenced fake `## Agent access` heading could hide the real section
    (review finding 8). Only unfenced, uncommented lines participate.

    kickoff_io.py's merge-config applies the same grammar to decide which
    lines it may rewrite; the shared-corpus drift test locks the two
    implementations together."""
    return _mask(text, _hidden_spans(text))


class _DuplicateKey(ValueError):
    """A JSON object with a repeated key — never legal in a config entry."""


def _reject_dup_pairs(pairs):
    """object_pairs_hook mirroring the builder's duplicate-key rejection: a
    last-key-wins parse here would pass a line the approved writer later
    rejects."""
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey("duplicate key {0!r}".format(key))
        seen[key] = value
    return seen


def _redact_secrets(text):
    """(redacted text, [(label, line_number), ...]) over the RAW file.

    The scan runs before any masking — a secret inside an HTML comment or a
    fence is still a secret in a committed file — and the matched value is
    replaced, never echoed: reports and warnings must not become the leak
    they are warning about."""
    findings = []

    def note(label):
        def _sub(match):
            line = text[:match.start()].count("\n") + 1
            findings.append((label, line))
            return "[REDACTED-{0}]".format(label)
        return _sub

    for label, pattern in SECRET_RES:
        text = pattern.sub(note(label), text)
    return text, findings


def validate_entry(agent, entry):
    """Shape-check one parsed access entry. Returns a list of message strings.

    Mirrors kickoff_io._validate_access_entry, and the equivalence is locked by
    test_contract_drift.py::test_validate_config_entry_rules_match_builder."""
    problems = []
    if not isinstance(entry, dict):
        return ["entry must be a JSON object"]
    unknown = [k for k in entry if k not in ENTRY_KEYS]
    if unknown:
        problems.append("unknown key(s): {0}".format(", ".join(sorted(unknown))))
    for key in ENTRY_KEYS:
        if key not in entry:
            problems.append("missing required key '{0}'".format(key))
    if problems:
        return problems

    status = entry["status"]
    tier = entry["tier"]
    routes = entry["routes"]

    if status not in STATUSES:
        problems.append("status {0!r} is not one of {1}".format(
            status, list(STATUSES)))
    if not (tier is None or isinstance(tier, str)):
        problems.append("tier must be a string or null")
    elif isinstance(tier, str) and not tier.strip():
        problems.append("tier must be trimmed non-empty or null")
    if not (isinstance(routes, list) and all(isinstance(r, str) for r in routes)):
        problems.append("routes must be an array of strings")
        routes = []
    elif len(set(routes)) != len(routes):
        problems.append("routes must be unique")
    if problems:
        return problems

    allowed = ROUTES_BY_AGENT[agent]
    for route in routes:
        if route not in allowed:
            problems.append("route {0!r} is not one of {1} for this entry".format(
                route, list(allowed)))
    # Transient states SKILL.md Step 0.3 forbids persisting.
    if status == "available" and not routes:
        problems.append("status 'available' requires at least one route")
    if status in ("unknown", "unavailable"):
        if tier is not None:
            problems.append(
                "status {0!r} must carry tier null".format(status))
        if routes:
            problems.append(
                "status {0!r} must carry no routes".format(status))
    blob = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    for label, pattern in SECRET_RES:
        if pattern.search(blob):
            problems.append(
                "secret-like value ({0}) — this file is mirrored into "
                "00-context.md and committed".format(label))
            break
    return problems


def parse_config(text):
    """Split a config into its dossier-root lines and agent-access bullets."""
    text = unicodedata.normalize("NFC", text.lstrip(u"﻿"))
    masked = mask_hidden(text)
    lines = masked.splitlines()

    roots = []
    for index, line in enumerate(lines):
        match = DOSSIER_ROOT_RE.match(line)
        if match:
            roots.append((index + 1, match.group(1).strip()))

    sections = list(AGENT_SECTION_RE.finditer(masked))
    bullets = []
    section_present = bool(sections)
    if len(sections) == 1:
        section = sections[0]
        start_line = masked[:section.start()].count("\n") + 1
        rest = masked[section.end():]
        stop = NEXT_SECTION_RE.search(rest)
        body = rest[:stop.start()] if stop else rest
        offset = start_line
        for index, line in enumerate(body.splitlines()):
            match = BULLET_RE.match(line)
            if match:
                bullets.append((offset + index + 1, match.group(1).strip(),
                                match.group(2).strip()))
    return {"roots": roots, "bullets": bullets,
            "section_present": section_present,
            "section_count": len(sections)}


def _scope(root, workspace_root):
    """Containment class of the RESOLVED dossier root.

    Resolve first — including symlinks and junctions — then classify. The
    spelling alone proves nothing: `../outside` is spelled relative and
    escapes the workspace, and calling it workspace_relative suppressed the
    outside-workspace signal the kickoff contract requires before any write
    (review finding 9)."""
    if workspace_root is None:
        return None, None
    base = os.path.realpath(workspace_root)
    resolved = os.path.realpath(os.path.join(base, root))
    try:
        inside = os.path.commonpath(
            [os.path.normcase(base), os.path.normcase(resolved)]) \
            == os.path.normcase(base)
    except ValueError:
        inside = False  # different drives on Windows
    if not inside:
        return "outside_workspace", resolved
    if os.path.isabs(root):
        return "absolute_inside_workspace", resolved
    return "workspace_relative", resolved


def run(config_path, workspace_root=None):
    """Validate the config and return the report dict. Never writes."""
    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        raise ConfigError("cannot read {0}: {1}".format(config_path, exc))

    failures = []
    warnings = []

    def fail(code, label, line, message):
        failures.append({"code": code, "label": label, "line": line,
                         "message": message})

    def warn(code, label, line, message):
        warnings.append({"code": code, "label": label, "line": line,
                         "message": message})

    # Whole-file secret scan over the RAW text, before masking or parsing —
    # a secret inside a comment, fence, or legacy value is still a secret in
    # a committed file, and everything downstream works on the redacted text
    # so no report can echo it.
    text, secret_hits = _redact_secrets(text)
    for label, line in secret_hits:
        fail("secret_like", None, line,
             "secret-like value ({0}) — this file is mirrored into "
             "00-context.md and committed; the value has been redacted from "
             "this report and must be rotated and removed".format(label))

    parsed = parse_config(text)
    if parsed["section_count"] > 1:
        fail("agent_access_ambiguous", None, None,
             "{0} active '## Agent access' sections — which one is "
             "authoritative cannot be guessed; merge them".format(
                 parsed["section_count"]))

    # --- dossier root ------------------------------------------------------
    roots = parsed["roots"]
    dossier_root = None
    if not roots:
        fail("dossier_root_missing", None, None,
             "no 'Dossier root:' line — the skills cannot resolve any dossier "
             "path from this file")
    else:
        values = [value for _line, value in roots]
        dossier_root = values[0]
        if not dossier_root:
            fail("dossier_root_blank", None, roots[0][0],
                 "'Dossier root:' is present but empty")
            dossier_root = None
        elif len(set(values)) > 1:
            fail("dossier_root_conflict", None, roots[1][0],
                 "two 'Dossier root:' lines disagree ({0!r} vs {1!r}); which is "
                 "authoritative cannot be guessed".format(values[0], values[1]))
        elif len(values) > 1:
            warn("dossier_root_duplicate_identical", None, roots[1][0],
                 "'Dossier root:' appears {0} times with the same value".format(
                     len(values)))

    # --- agent access ------------------------------------------------------
    if not parsed["section_present"]:
        warn("agent_access_section_absent", None, None,
             "no '## Agent access' section; all ten entries read as unknown and "
             "will be asked when a project needs them")

    seen = {}
    for line, label, value in parsed["bullets"]:
        norm = label.casefold()
        agent = LABEL_BY_NORM.get(norm)
        if agent is None:
            alias = LABEL_ALIASES.get(norm)
            if alias is not None:
                fail("unknown_label_alias", label, line,
                     "{0!r} is not a config label — did you mean {1!r}? A "
                     "near-miss label is silently ignored, which reads as "
                     "'{1} unknown' rather than as a typo".format(
                         label, CONFIG_LABELS[alias]))
            elif value.startswith(("{", "[")):
                fail("unknown_label_v1_shaped", label, line,
                     "{0!r} carries a normalized entry but is not one of the ten "
                     "config labels".format(label))
            else:
                warn("ignored_line", label, line,
                     "not a config label; ignored, as the template promises")
            continue
        if agent in seen:
            fail("duplicate_label", label, line,
                 "{0!r} appears twice (also line {1}); which one is read is "
                 "arbitrary".format(CONFIG_LABELS[agent], seen[agent]))
            continue
        seen[agent] = line

    entries = []
    by_agent = {}
    for line, label, value in parsed["bullets"]:
        agent = LABEL_BY_NORM.get(label.casefold())
        if agent is not None and agent not in by_agent:
            by_agent[agent] = (line, value)

    for agent in AGENT_IDS:
        label = CONFIG_LABELS[agent]
        record = {"agent": agent, "label": label, "class": "missing",
                  "line": None, "read_as": "unknown", "value": None}
        if agent not in by_agent:
            warn("entry_missing", label, None,
                 "no line for {0!r}; reads as unknown and is asked when a "
                 "project needs it".format(label))
            entries.append(record)
            continue
        line, value = by_agent[agent]
        record["line"] = line
        record["value"] = value
        # `{` or `[`: a JSON-shaped value is a normalization attempt, not free
        # text, so a malformed or non-object one is a defect rather than a
        # legacy line silently read as unknown.
        if value.startswith(("{", "[")):
            try:
                entry = json.loads(value, object_pairs_hook=_reject_dup_pairs)
            except ValueError as exc:
                record["class"] = "invalid"
                fail("entry_json_malformed", label, line,
                     "{0}: value looks normalized but is not valid JSON "
                     "({1})".format(label, exc))
                entries.append(record)
                continue
            problems = validate_entry(agent, entry)
            if problems:
                record["class"] = "invalid"
                for problem in problems:
                    fail("entry_shape", label, line,
                         "{0}: {1}".format(label, problem))
            else:
                record["class"] = "v1"
                record["read_as"] = entry["status"]
                record["entry"] = entry
        else:
            record["class"] = "legacy"
            blank = not value
            note = ("empty" if blank else repr(value))
            extra = ""
            if value.casefold() in ("none", "n/a", "no", "-", "nil"):
                extra = (" — 'none' here is read as UNKNOWN, not as confirmed "
                         "unavailable, so it is asked again on the next project "
                         "that needs it")
            warn("legacy_empty" if blank else "legacy_entry", label, line,
                 "{0}: legacy free-text value ({1}); read as UNKNOWN{2}".format(
                     label, note, extra))
        entries.append(record)

    summary = {"v1": 0, "legacy": 0, "invalid": 0, "missing": 0}
    for record in entries:
        summary[record["class"]] += 1

    report = {
        "result": "fail" if failures else "pass",
        "path": config_path,
        "dossier_root": dossier_root,
        "agent_access_section": parsed["section_present"],
        "entries": entries,
        "summary": summary,
        "failures": failures,
        "warnings": warnings,
    }
    if dossier_root is not None and workspace_root is not None:
        scope, resolved = _scope(dossier_root, workspace_root)
        report["dossier_root_resolved"] = resolved
        report["dossier_root_exists"] = os.path.isdir(resolved)
        report["dossier_root_scope"] = scope
    return report


def render_human(report):
    lines = ["File: {0}".format(report["path"]),
             "Dossier root: {0}".format(report["dossier_root"] or "(none)")]
    if "dossier_root_resolved" in report:
        lines.append("  resolves to: {0} ({1}; {2})".format(
            report["dossier_root_resolved"], report["dossier_root_scope"],
            "exists" if report["dossier_root_exists"] else "not created yet"))
    summary = report["summary"]
    lines.append("Agent access: {v1} normalized, {legacy} legacy, {invalid} "
                 "invalid, {missing} missing".format(**summary))
    for record in report["entries"]:
        lines.append("  {0:<16} {1:<8} read_as={2}".format(
            record["label"], record["class"], record["read_as"]))
    for failure in report["failures"]:
        where = " (line {0})".format(failure["line"]) if failure["line"] else ""
        lines.append("FAIL {0}{1}: {2}".format(
            failure["code"], where, failure["message"]))
    for warning in report["warnings"]:
        where = " (line {0})".format(warning["line"]) if warning["line"] else ""
        lines.append("WARN {0}{1}: {2}".format(
            warning["code"], where, warning["message"]))
    if report["result"] == "pass":
        lines.append("RESULT: PASS ({0} warning(s))".format(
            len(report["warnings"])))
    else:
        lines.append("RESULT: FAIL ({0} defect(s), {1} warning(s))".format(
            len(report["failures"]), len(report["warnings"])))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(
        prog="validate_config",
        description="Validate a workspace research-config.md (Step 0.0).")
    parser.add_argument("config", help="path to research-config.md")
    parser.add_argument("--workspace-root", dest="workspace_root", default=None,
                        help="resolve the dossier root against this folder "
                             "(advisory: never a defect, never creates it)")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit a machine-readable JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 2
    try:
        report = run(args.config, args.workspace_root)
    except ConfigError as exc:
        sys.stderr.write("error: {0}\n".format(exc))
        return 2
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

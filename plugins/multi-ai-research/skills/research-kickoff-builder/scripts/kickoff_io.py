#!/usr/bin/env python
"""Deterministic rendering and I/O helper for the research-kickoff-builder
skill.

Three subcommands (the only mutation path the skill may use):

  kickoff_io.py render   <control.json> --workspace-root <path>
                         --operation build|refine [--existing-brief <path>]
  kickoff_io.py finalize <candidate.md> --workspace-root <path>
                         --operation build|refine
                         [--expected-final-sha256 <hex>] [--approved]
  kickoff_io.py merge-config <research-config.md> --updates <updates.json>
                         --workspace-root <path> --approved

Also exposes (importable, used by the headless answer-sheet flow, the golden
loop, and the drift tests): canonical JSON + digest helpers, the question-
catalog loader, the closed `when` predicate evaluator, the three answer
normalizers, the two fallback question renderers, the §6.2 derivation
helpers, and `verify_answer_sheet`.

Stdlib-only. Imports its sibling validate_kickoff (same skill directory —
cross-skill runtime imports remain forbidden) and reads only this skill's own
templates/ and references/ files at runtime.

Exit codes: 0 success (including an idempotent approved merge with
changed:false), 1 validation/safety/consent/collision/hash/lock/filesystem-
capability failure, 2 usage, unreadable input, or malformed JSON.

Residual race (documented, not fixable in stdlib): the exclusive lock file
protects against cooperating helper processes only. An unrelated writer that
ignores the lock can still mutate the target between the hash recheck and
os.replace; the hash-named backup keeps that recoverable, but cross-platform
compare-and-swap against such a writer is not possible here — this residual
race is reported rather than claimed impossible.
"""

import argparse
import errno
import hashlib
import json
import os
import re
import secrets
import sys
import time
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_kickoff as vk  # noqa: E402

SKILL_DIR = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONTRACT_PATH = os.path.join(SKILL_DIR, "references", "kickoff-contract.md")
PROFILE_PATHS = [
    os.path.join(SKILL_DIR, "references", name) for name in (
        "profile-01-spec-driven-dev.md", "profile-02-youtube.md",
        "profile-03-presentation.md", "profile-04-ebook.md",
        "profile-05-wordpress-seo.md", "profile-06-health.md",
        "profile-07-deck-screencast.md", "profile-08-decision.md")]
TEMPLATE_PATH = os.path.join(SKILL_DIR, "templates", "kickoff-template.md")

IO_REPORT_SCHEMA_VERSION = 1
ANSWER_SHEET_SCHEMA_VERSION = 1
ANSWER_SHEET_BEGIN = "<!-- BEGIN KICKOFF-ANSWER-SHEET v1 -->"
ANSWER_SHEET_END = "<!-- END KICKOFF-ANSWER-SHEET v1 -->"
CATALOG_BEGIN_RE = re.compile(
    r"^<!-- BEGIN KICKOFF-QUESTION-CATALOG ([a-z0-9-]+) -->$")
CATALOG_END_FMT = "<!-- END KICKOFF-QUESTION-CATALOG %s -->"

FRAMING_ID_RE = re.compile(r"^F[1-4]$")

PREDICATE_PATHS = frozenset({
    "/workspace/dossier_root", "/workspace/dossier_root_scope",
    "/workspace/agent_access",
    "/project/classified_inputs", "/project/stakes",
    "/project/confidentiality",
    "/invocation/spec_mode", "/invocation/requirements_input_id",
    "/use_case_profile/requirements_coverage",
    "/use_case_profile/requirements_coverage/constraints",
    "/use_case_profile/requirements_coverage/product_target_users",
    "/use_case_profile/keyword_brief/status",
    "/use_case_profile/client_pitch",
    "/conduct/decorrelated_exception",
})

CONFIG_HEADER = "# Research configuration"
CONFIG_ACCESS_HEADING = "## Agent access"
CONFIG_TEMPLATE_COMMENT = """<!--
Read contract (v1.3 three-state semantics):
- `Dossier root:` — where dossier folders live; relative paths resolve
  against this workspace root.
- Each agent-access line is `- <Label>: <compact JSON>` with the exact shape
  {"status":"unknown|available|unavailable","tier":<string|null>,"routes":[]}.
  * unknown      — not yet asked; ask when relevant, then record the answer.
  * available    — requires at least one route; tier is an optional
                   descriptive string (never credentials/account IDs).
  * unavailable  — explicitly confirmed absent; do not re-ask every project.
- Routes: Claude uses claude_web_extended_thinking|local; DeepSeek route uses
  consumer_web|western_hosted_api|self_hosted; all others use web|api.
- Legacy free-text lines (e.g. `- Perplexity: Pro` or `none`) are read
  conservatively: `none` means unknown, not confirmed unavailable. A legacy
  line is replaced only when a valid normalized entry is approved.
- Never store credentials, API keys, account emails, or endpoint secrets.
-->"""


# ---------------------------------------------------------------------------
# Canonical JSON + digests
# ---------------------------------------------------------------------------

def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_hex_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_hex_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def question_catalog_digest(records):
    return sha256_hex_text(canonical_json(records))


def sheet_instance_digest(catalog_digest, generated_framings):
    return sha256_hex_text(canonical_json({
        "question_catalog_digest": catalog_digest,
        "generated_framings": generated_framings,
    }))


# ---------------------------------------------------------------------------
# Question catalog
# ---------------------------------------------------------------------------

def _extract_catalog_blocks(text):
    """Yield (name, records) for each sentinel-delimited catalog block."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = CATALOG_BEGIN_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        name = m.group(1)
        end_marker = CATALOG_END_FMT % name
        body = []
        i += 1
        while i < len(lines) and lines[i].strip() != end_marker:
            body.append(lines[i])
            i += 1
        if i >= len(lines):
            raise ValueError("unterminated catalog block %r" % name)
        payload = "\n".join(body)
        fence = re.search(r"```json\n(.*)\n```", payload, re.DOTALL)
        if not fence:
            raise ValueError("catalog block %r lacks a json fence" % name)
        records = json.loads(fence.group(1),
                             object_pairs_hook=vk._reject_dup_pairs)
        if not isinstance(records, list):
            raise ValueError("catalog block %r must hold a JSON array" % name)
        yield name, records
        i += 1


def load_question_catalog(contract_path=None, profile_paths=None):
    """Core records (from the contract) followed by each profile's records,
    in shipped order. This exact list feeds question_catalog_digest."""
    contract_path = contract_path or CONTRACT_PATH
    profile_paths = profile_paths or PROFILE_PATHS
    records = []
    with open(contract_path, "r", encoding="utf-8") as fh:
        blocks = dict(_extract_catalog_blocks(fh.read()))
    if "core" not in blocks:
        raise ValueError("contract carries no core question catalog")
    records.extend(blocks["core"])
    for path in profile_paths:
        with open(path, "r", encoding="utf-8") as fh:
            for _name, profile_records in _extract_catalog_blocks(fh.read()):
                records.extend(profile_records)
    ids = [r.get("question_id") for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question_id in catalog")
    return records


# ---------------------------------------------------------------------------
# Predicate AST (closed; never eval)
# ---------------------------------------------------------------------------

def _state_lookup(state, path):
    found, value = vk.json_pointer_get(state.get("control", {}), path)
    return found, value


def evaluate_predicate(node, state, depth=0):
    """Evaluate a closed `when` AST against the validated answer/config
    state. state = {"use_case_id": int|None, "overlay_13_active": bool,
    "control": <partial control dict>}. Raises ValueError on any unknown
    predicate/key, non-whitelisted path, empty boolean-node array,
    type-mismatched comparison, or depth > 4."""
    if depth > 4:
        raise ValueError("predicate depth exceeds 4")
    if not isinstance(node, dict) or "predicate" not in node:
        raise ValueError("predicate node must be an object with 'predicate'")
    kind = node["predicate"]
    keys = set(node)
    if kind == "always":
        if keys != {"predicate"}:
            raise ValueError("always takes no arguments")
        return True
    if kind == "use_case_in":
        if keys != {"predicate", "ids"}:
            raise ValueError("use_case_in takes exactly 'ids'")
        ids = node["ids"]
        if not isinstance(ids, list) or not ids or \
                not all(isinstance(i, int) and not isinstance(i, bool)
                        and 1 <= i <= 8 for i in ids):
            raise ValueError("use_case_in ids must be integers 1..8")
        return state.get("use_case_id") in ids
    if kind == "overlay_13_active":
        if keys != {"predicate", "value"}:
            raise ValueError("overlay_13_active takes exactly 'value'")
        if not isinstance(node["value"], bool):
            raise ValueError("overlay_13_active value must be boolean")
        return bool(state.get("overlay_13_active")) == node["value"]
    if kind == "field_equals":
        if keys != {"predicate", "path", "value"}:
            raise ValueError("field_equals takes exactly 'path' and 'value'")
        path = node["path"]
        if path not in PREDICATE_PATHS:
            raise ValueError("path %r is not whitelisted" % path)
        value = node["value"]
        if isinstance(value, (dict, list)):
            raise ValueError("field_equals value must be a JSON scalar")
        found, actual = _state_lookup(state, path)
        return found and actual == value and \
            isinstance(actual, bool) == isinstance(value, bool)
    if kind == "field_state":
        if keys != {"predicate", "path", "state"}:
            raise ValueError("field_state takes exactly 'path' and 'state'")
        path = node["path"]
        if path not in PREDICATE_PATHS:
            raise ValueError("path %r is not whitelisted" % path)
        wanted = node["state"]
        if wanted not in ("empty", "unknown"):
            raise ValueError("field_state state must be empty|unknown")
        found, actual = _state_lookup(state, path)
        if wanted == "unknown":
            return (not found) or actual is None
        return (not found) or actual is None or actual == "" or \
            actual == [] or actual == {}
    if kind in ("all", "any"):
        if keys != {"predicate", "items"}:
            raise ValueError("%s takes exactly 'items'" % kind)
        items = node["items"]
        if not isinstance(items, list) or not items:
            raise ValueError("%s items must be a non-empty array" % kind)
        results = [evaluate_predicate(i, state, depth + 1) for i in items]
        return all(results) if kind == "all" else any(results)
    if kind == "not":
        if keys != {"predicate", "item"}:
            raise ValueError("not takes exactly 'item'")
        return not evaluate_predicate(node["item"], state, depth + 1)
    raise ValueError("unknown predicate %r" % kind)


# ---------------------------------------------------------------------------
# Answer normalization (all renderers normalize Unicode to NFC)
# ---------------------------------------------------------------------------

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _nfc(value):
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(v) for v in value]
    if isinstance(value, dict):
        return {_nfc(k): _nfc(v) for k, v in value.items()}
    return value


def _field_schema(record):
    """Schema for validating an Other/typed answer: the record's first
    field's schema from the machine contract (menu/other validation)."""
    pointer = record["field_ids"][0]
    return _schema_for_pointer(pointer)


def _schema_for_pointer(pointer):
    node = vk.CONTRACT_SCHEMA
    for token in pointer.split("/")[1:]:
        node = vk._deref(node, vk.CONTRACT_SCHEMA)
        props = node.get("properties", {})
        if token in props:
            node = props[token]
            continue
        if token == "use_case_profile":
            node = props.get("use_case_profile", {})
            continue
        # descend into any profile def carrying this property
        found = None
        for name, sub in vk.CONTRACT_SCHEMA["$defs"].items():
            if name.startswith("profile_") and \
                    token in sub.get("properties", {}):
                found = sub["properties"][token]
                break
        if found is None:
            raise ValueError("no schema for pointer %r" % pointer)
        node = found
    return vk._deref(node, vk.CONTRACT_SCHEMA)


def _validate_typed(value, schema, label):
    findings = []
    vk._check_schema(value, schema, "", findings, vk.CONTRACT_SCHEMA)
    if findings:
        raise ValueError("%s does not validate: %s"
                         % (label, findings[0]["message"]))
    return value


def normalize_menu_answer(record, raw):
    """Map an interactive/headless menu answer to typed option value(s)."""
    options = record["options"]
    multi = bool(record.get("multiSelect"))
    raw = _nfc(raw)

    def resolve_one(item):
        if isinstance(item, str):
            token = item.strip()
            low = token.casefold()
            if len(low) == 1 and low in _LETTERS[:len(options)]:
                return options[_LETTERS.index(low)]["value"], False
            for opt in options:
                if _nfc(opt["label"]).casefold() == low:
                    return opt["value"], False
        for opt in options:
            if item == opt["value"]:
                return opt["value"], False
        # auto-added Other answer: accepted only if it validates against
        # the target field schema
        value = _validate_typed(item, _field_schema(record), "Other answer")
        return value, True

    if not multi:
        if isinstance(raw, list):
            # a list is legal only when it IS a typed option value (some
            # single-select options carry array values, e.g. render sets)
            for option in options:
                if raw == option["value"]:
                    return option["value"]
            return _validate_typed(raw, _field_schema(record),
                                   "Other answer")
        value, _other = resolve_one(raw)
        return value

    items = raw if isinstance(raw, list) else [raw]
    resolved = [resolve_one(item)[0] for item in items]
    empties = [v for v in resolved if v == [] or v is None]
    atomics = [v for v in resolved if not (v == [] or v is None)]
    if empties and atomics:
        raise ValueError("a 'none' choice cannot be combined with an "
                         "atomic selection")
    # de-duplicate, then serialize in catalog option order
    ordered = []
    for opt in options:
        if opt["value"] in resolved and opt["value"] not in ordered:
            ordered.append(opt["value"])
    for value in resolved:
        if value not in ordered:
            ordered.append(value)
    return ordered


def normalize_text_answer(record, raw):
    if not isinstance(raw, str):
        raise ValueError("text answer must be a string")
    value = _nfc(raw).strip()
    answer_type = record.get("answer_type", "string")
    if answer_type == "non_empty_string" and not value:
        raise ValueError("answer must be non-empty")
    if answer_type == "path":
        if not value:
            raise ValueError("path answer must be non-empty")
        if vk.CONTROL_CHAR_RE.search(value):
            raise ValueError("path answer must not contain NUL/newline/"
                             "control characters")
    return value


def normalize_structured_answer(record, raw):
    if isinstance(raw, str):
        try:
            value = json.loads(raw, object_pairs_hook=vk._reject_dup_pairs)
        except vk._DuplicateKey as exc:
            raise ValueError(str(exc))
        except ValueError as exc:
            raise ValueError("structured answer is not strict JSON: %s"
                             % exc)
    else:
        value = raw
    value = _nfc(value)
    ref = record["schema_ref"]
    found, schema = vk.json_pointer_get(vk.CONTRACT_SCHEMA, ref)
    if not found:
        raise ValueError("schema_ref %r does not resolve" % ref)
    return _validate_typed(value, schema, "structured answer")


def normalize_answer(record, raw):
    kind = record["kind"]
    if kind == "menu":
        return normalize_menu_answer(record, raw)
    if kind == "text":
        return normalize_text_answer(record, raw)
    if kind == "structured":
        return normalize_structured_answer(record, raw)
    raise ValueError("unknown record kind %r" % kind)


# ---------------------------------------------------------------------------
# Fallback renderings (both render from the same records)
# ---------------------------------------------------------------------------

def render_plain_text_question(record, number):
    lines = ["%d. %s" % (number, record["question"])]
    if record["kind"] == "menu":
        for idx, opt in enumerate(record["options"]):
            lines.append("   %s) %s — %s"
                         % (_LETTERS[idx], opt["label"], opt["description"]))
        if record.get("multiSelect"):
            lines.append("   [multi-select allowed]")
        lines.append("   or type your own")
    elif record["kind"] == "text":
        lines.append("   (answer type: %s)"
                     % record.get("answer_type", "string"))
    else:
        lines.append("   (JSON value conforming to schema %s)"
                     % record["schema_ref"])
        lines.append("   example: %s" % canonical_json(record["example"]))
    return "\n".join(lines)


def render_headless_section(record):
    lines = ["### %s" % record["question_id"],
             "", record["question"], ""]
    lines.append("Field(s): %s" % ", ".join("`%s`" % f
                                            for f in record["field_ids"]))
    if record["kind"] == "menu":
        for idx, opt in enumerate(record["options"]):
            lines.append("- %s) %s — %s (value: `%s`)"
                         % (_LETTERS[idx], opt["label"], opt["description"],
                            canonical_json(opt["value"])))
        if record.get("multiSelect"):
            lines.append("- [multi-select allowed]")
        lines.append("- or supply your own typed value")
    elif record["kind"] == "text":
        lines.append("Answer type: %s" % record.get("answer_type", "string"))
    else:
        lines.append("Answer: JSON conforming to `%s`"
                     % record["schema_ref"])
        lines.append("Example: `%s`" % canonical_json(record["example"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Answer-sheet verification (invocation two treats the sheet as untrusted)
# ---------------------------------------------------------------------------

def verify_answer_sheet(sheet_text, catalog=None):
    """Parse + verify a completed headless answer sheet. Returns
    {"ok": bool, "findings": [str], "sheet": dict|None}."""
    findings = []
    catalog = catalog if catalog is not None else load_question_catalog()
    marker_count = sheet_text.count(ANSWER_SHEET_BEGIN)
    if marker_count != 1 or sheet_text.count(ANSWER_SHEET_END) != 1:
        return {"ok": False, "sheet": None,
                "findings": ["exactly one answer-sheet block required "
                             "(found %d)" % marker_count]}
    body = sheet_text.split(ANSWER_SHEET_BEGIN, 1)[1] \
        .split(ANSWER_SHEET_END, 1)[0]
    fence = re.search(r"```json\n(.*)\n```", body, re.DOTALL)
    if not fence:
        return {"ok": False, "sheet": None,
                "findings": ["answer-sheet block lacks a json fence"]}
    try:
        sheet = json.loads(fence.group(1),
                           object_pairs_hook=vk._reject_dup_pairs)
    except (ValueError, vk._DuplicateKey) as exc:
        return {"ok": False, "sheet": None,
                "findings": ["answer sheet is not strict JSON: %s" % exc]}
    if not isinstance(sheet, dict):
        return {"ok": False, "sheet": None,
                "findings": ["answer sheet must be a JSON object"]}
    if sheet.get("answer_sheet_schema_version") != \
            ANSWER_SHEET_SCHEMA_VERSION:
        findings.append("unsupported answer_sheet_schema_version")
    expected_digest = question_catalog_digest(catalog)
    if sheet.get("question_catalog_digest") != expected_digest:
        findings.append("question_catalog_digest mismatch (stale sheet)")
    framings = sheet.get("generated_framings")
    if not (isinstance(framings, list) and 3 <= len(framings) <= 4):
        findings.append("generated_framings must hold 3-4 records")
        framings = []
    seen_ids = set()
    for framing in framings:
        if not isinstance(framing, dict) or set(framing) != \
                {"framing_id", "label", "consequence", "value"}:
            findings.append("framing record keys must be exactly "
                            "framing_id/label/consequence/value")
            continue
        fid = framing["framing_id"]
        if not (isinstance(fid, str) and FRAMING_ID_RE.match(fid)):
            findings.append("framing_id must match F[1-4]")
        elif fid in seen_ids:
            findings.append("duplicate framing_id %s" % fid)
        seen_ids.add(fid)
        value = framing["value"]
        if not (isinstance(value, dict) and set(value) ==
                {"use_case_id", "decision_shaped",
                 "suggested_additional_renders"}):
            findings.append("framing value keys must be exactly "
                            "use_case_id/decision_shaped/"
                            "suggested_additional_renders")
            continue
        uc = value["use_case_id"]
        if not (isinstance(uc, int) and not isinstance(uc, bool)
                and 1 <= uc <= 8):
            findings.append("framing use_case_id must be 1..8")
        if not isinstance(value["decision_shaped"], bool):
            findings.append("framing decision_shaped must be boolean")
        renders = value["suggested_additional_renders"]
        if not (isinstance(renders, list) and
                all(r in vk.ALL_ADDITIONAL_RENDER_IDS for r in renders)):
            findings.append("framing suggested_additional_renders must be "
                            "valid render IDs")
    if sheet.get("sheet_instance_digest") != sheet_instance_digest(
            sheet.get("question_catalog_digest"),
            sheet.get("generated_framings")):
        findings.append("sheet_instance_digest mismatch")
    selection = sheet.get("framing_selection")
    if not isinstance(selection, dict) or set(selection) != \
            {"selected_ids", "primary_id"}:
        findings.append("framing_selection must hold selected_ids and "
                        "primary_id")
    else:
        selected = selection["selected_ids"]
        primary = selection["primary_id"]
        if not (isinstance(selected, list)
                and len(selected) == len(set(selected))
                and all(s in seen_ids for s in selected)):
            findings.append("selected_ids must be unique known framing IDs")
        if primary is not None and primary not in (selected or []):
            findings.append("primary_id must be one of the selected IDs")
    answers = sheet.get("answers")
    catalog_ids = {r["question_id"] for r in catalog}
    if not isinstance(answers, dict):
        findings.append("answers must be an object")
    else:
        missing = catalog_ids - set(answers)
        extra = set(answers) - catalog_ids
        if missing:
            findings.append("answers missing question IDs: %s"
                            % sorted(missing))
        if extra:
            findings.append("answers carry unknown question IDs: %s"
                            % sorted(extra))
    return {"ok": not findings, "sheet": sheet, "findings": findings}


# ---------------------------------------------------------------------------
# §6.2 derivations
# ---------------------------------------------------------------------------

def _deepseek_route_precedence(confidential):
    return vk.ROUTE_PRECEDENCE[
        "deepseek_confidential" if confidential
        else "deepseek_non_confidential"]


def _select_route(agent, entry, confidential):
    routes = entry.get("routes") or []
    if agent == "claude":
        precedence = vk.ROUTE_PRECEDENCE["claude"]
    elif agent == "deepseek":
        precedence = _deepseek_route_precedence(confidential)
    else:
        precedence = vk.ROUTE_PRECEDENCE["default"]
    for route in precedence:
        if route in routes:
            return route
    return None


def derive_expected_lanes(agent_access, use_case, confidential,
                          client_pitch=False, explicit_requests=()):
    """Deterministic default expected-lane plan (§6.2 rules 1-3). Returns
    the lane list serialized in canonical inventory order; the caller may
    replace it with an explicit user selection."""

    def selectable(agent):
        entry = agent_access.get(agent)
        return isinstance(entry, dict) and \
            entry.get("status") == "available" and \
            _select_route(agent, entry, confidential) is not None

    selected = [a for a in vk.LANE_SELECTION_ORDER if selectable(a)]
    for extra in ("chatgpt", "notebooklm"):
        if len(selected) >= 3 and extra not in explicit_requests:
            continue
        if extra in selected or not selectable(extra):
            continue
        selected.append(extra)
    if client_pitch and selectable("notebooklm") and \
            "notebooklm" not in selected:
        selected.append("notebooklm")
    if use_case == 6:
        for agent in ("notebooklm", "elicit", "consensus"):
            if selectable(agent) and agent not in selected:
                selected.append(agent)
    for agent in explicit_requests:
        if agent in vk.LANE_AGENT_IDS and selectable(agent) and \
                agent not in selected:
            selected.append(agent)

    roles = {a: vk.DEFAULT_ROLE.get(a, "evidence") for a in selected}
    evidence_count = sum(1 for a in selected
                         if roles[a] in ("evidence", "decorrelated"))
    if evidence_count < 2:
        added = False
        for agent in vk.EVIDENCE_FALLBACK_ORDER:
            if agent not in selected and selectable(agent):
                selected.append(agent)
                roles[agent] = "evidence"
                added = True
                break
        if not added:
            for promote in ("grok", "claude"):
                if promote in selected and roles[promote] != "evidence":
                    roles[promote] = "evidence"
                    evidence_count = sum(
                        1 for a in selected
                        if roles[a] in ("evidence", "decorrelated"))
                    if evidence_count >= 2:
                        break

    lanes = []
    for agent in vk.AGENT_IDS[:9]:
        if agent not in selected:
            continue
        entry = agent_access[agent]
        lanes.append({"agent": agent,
                      "route": _select_route(agent, entry, confidential),
                      "role": roles[agent]})
    return lanes


MODE_RULES = (
    ("novel_problem", ("first-principles",)),
    ("suspect_convention", ("first-principles",)),
    ("yes_no_choice", ("debate",)),
    ("opposed_options", ("debate",)),
    ("prelaunch", ("red-team",)),
    ("investment", ("red-team",)),
    ("premortem", ("red-team",)),
    ("high_stakes_signoff", ("debate", "red-team")),
)


def derive_modes(signals):
    """Union of every matching overlay-13 selector rule, normalized to
    pipeline order. Empty for standard low-stakes research."""
    modes = set()
    for signal, mode_set in MODE_RULES:
        if signal in signals:
            modes.update(mode_set)
    return [m for m in vk.MODES_ORDER if m in modes]


def derive_conduct(use_case):
    conduct = dict(vk.CONDUCT_FIXED)
    conduct["non_cancellable_phases"] = [4] if use_case == 6 else []
    conduct["decorrelated_exception"] = None
    return conduct


def derive_verdicts(overlay13_is_active, binary=True, proposals=None):
    if not overlay13_is_active:
        return []
    if proposals:
        return list(proposals)
    if binary:
        return ["GO", "NO-GO", "GO-WITH-CONDITIONS"]
    return []


def derive_layered_overlays(use_case, decision_shaped):
    if decision_shaped and use_case in vk.LAYERABLE_USE_CASES:
        return [vk.OVERLAY_13]
    return []


# ---------------------------------------------------------------------------
# Deterministic rendering
# ---------------------------------------------------------------------------

_PLACEHOLDER_LINE_RE = re.compile(r"^(\s*)\{\{FIELD:([^}]*)\}\}\s*$")
_PLACEHOLDER_INLINE_RE = re.compile(r"\{\{FIELD:([^}]*)\}\}")
_COND_BEGIN_RE = re.compile(r"^<!-- BEGIN IF ([a-z0-9_]+) -->$")
_COND_END_FMT = "<!-- END IF %s -->"

_TEMPLATE_CONDITIONS = ("overlay13_active", "overlay13_inactive",
                        "standing_nonempty", "guidance_nonempty")


def _template_conditions(control):
    active = vk.overlay13_active(control)
    standing = isinstance(control.get("standing_instructions"), str) and \
        control["standing_instructions"].strip() != ""
    guidance = any(control.get(k) for k in ("seed_areas", "out_of_scope",
                                            "known_traps"))
    return {"overlay13_active": active, "overlay13_inactive": not active,
            "standing_nonempty": standing, "guidance_nonempty": guidance}


def _fence_for(payload):
    longest = 0
    for run in re.findall(r"`+", payload):
        longest = max(longest, len(run))
    return "`" * max(3, longest + 1)


def _pointer_value(control, pointer):
    found, value = vk.json_pointer_get(control, pointer)
    if not found:
        raise ValueError("template pointer %r does not resolve" % pointer)
    return value


def render_markdown(control, template_text):
    """Render the kickoff Markdown from a complete control payload.

    Deterministic: UTF-8 (no BOM), LF, exactly one trailing newline,
    two-space pretty JSON with ensure_ascii=False, §6.4 fence-length rule
    for every fenced payload."""
    conditions = _template_conditions(control)
    lines = template_text.split("\n")
    flat = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        cond = _COND_BEGIN_RE.match(stripped)
        if cond:
            name = cond.group(1)
            if name not in _TEMPLATE_CONDITIONS:
                raise ValueError("unknown template condition %r" % name)
            end_marker = _COND_END_FMT % name
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != end_marker:
                block.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("unterminated conditional %r" % name)
            i += 1
            if conditions[name]:
                flat.extend(block)
            continue
        flat.append(lines[i])
        i += 1
    text = "\n".join(_render_lines(flat, control))
    return text.rstrip("\n") + "\n"


def _render_lines(lines, control):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = vk._FENCE_RE.match(line.strip())
        if fence and i + 2 < len(lines):
            placeholder = _PLACEHOLDER_LINE_RE.match(lines[i + 1])
            closing = lines[i + 2].strip() == fence.group(1)
            if placeholder and closing:
                pointer = placeholder.group(2)
                value = _pointer_value(control, pointer)
                if isinstance(value, str):
                    payload = value
                else:
                    payload = json.dumps(value, indent=2,
                                         ensure_ascii=False)
                ticks = _fence_for(payload)
                info = fence.group(2)
                out.append(ticks + info)
                out.append(payload)
                out.append(ticks)
                i += 3
                continue
        if _PLACEHOLDER_INLINE_RE.search(line):
            def sub(match):
                value = _pointer_value(control, match.group(1))
                if not isinstance(value, str):
                    raise ValueError(
                        "inline placeholder %r must resolve to a string"
                        % match.group(1))
                return value
            line = _PLACEHOLDER_INLINE_RE.sub(sub, line)
        out.append(line)
        i += 1
    return out


# ---------------------------------------------------------------------------
# io_report + lock
# ---------------------------------------------------------------------------

def _report(result, command, code, changed=False, paths=None, sha256=None,
            message=""):
    base_paths = {"candidate": None, "final": None, "config": None,
                  "backup": None}
    base_sha = {"before": None, "candidate": None, "after": None,
                "backup": None}
    base_paths.update(paths or {})
    base_sha.update(sha256 or {})
    return {
        "io_report_schema_version": IO_REPORT_SCHEMA_VERSION,
        "result": result,
        "command": command,
        "code": code,
        "changed": changed,
        "paths": base_paths,
        "sha256": base_sha,
        "message": message,
    }


def _emit(report, exit_code):
    print(json.dumps(report, ensure_ascii=False))
    return exit_code


class _Lock:
    def __init__(self, target):
        directory = os.path.dirname(os.path.abspath(target))
        self.path = os.path.join(
            directory, "." + os.path.basename(target) + ".kickoff-lock")
        self.acquired = False

    def acquire(self, command):
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"command": command, "pid": os.getpid(),
                       "timestamp_utc": time.time(),
                       "token": secrets.token_hex(16)}, fh)
        self.acquired = True
        return True

    def release(self):
        if self.acquired:
            try:
                os.unlink(self.path)
            except OSError:
                pass
            self.acquired = False


def _write_exclusive(path, text):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _derived_target_dir(control, workspace_root):
    root = control["workspace"]["dossier_root"]
    slug = control["project"]["topic_slug"]
    base = root if os.path.isabs(root) else \
        os.path.join(workspace_root, root)
    return os.path.join(base, slug)


# ---------------------------------------------------------------------------
# render subcommand
# ---------------------------------------------------------------------------

def cmd_render(args):
    try:
        with open(args.control, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        return _emit(_report("error", "render", "UNREADABLE",
                             message=str(exc)), 2)
    try:
        control = json.loads(raw, object_pairs_hook=vk._reject_dup_pairs)
    except (ValueError, vk._DuplicateKey) as exc:
        return _emit(_report("error", "render", "MALFORMED_JSON",
                             message=str(exc)), 2)
    if not isinstance(control, dict):
        return _emit(_report("error", "render", "MALFORMED_JSON",
                             message="control payload must be an object"), 2)

    if args.operation == "refine":
        if not args.existing_brief:
            return _emit(_report("error", "render", "USAGE",
                                 message="refine requires --existing-brief"),
                        2)
        if os.path.basename(args.existing_brief) != "00-kickoff.md":
            return _emit(_report("error", "render", "CANDIDATE_NAME",
                                 message="--existing-brief must be named "
                                         "00-kickoff.md"), 1)
        if not os.path.isfile(args.existing_brief):
            return _emit(_report("error", "render", "REFINE_TARGET_MISSING",
                                 message="existing brief not found"), 1)
    elif args.existing_brief:
        return _emit(_report("error", "render", "USAGE",
                             message="build rejects --existing-brief"), 2)

    try:
        target_dir = _derived_target_dir(control, args.workspace_root)
    except (KeyError, TypeError):
        return _emit(_report("error", "render", "REQUIRED_FIELD",
                             message="control payload lacks workspace/"
                                     "project identity fields"), 1)
    candidate_name = "00-kickoff.draft.md" if args.operation == "build" \
        else "00-kickoff.v2.md"
    candidate = os.path.join(target_dir, candidate_name)
    final = os.path.join(target_dir, "00-kickoff.md")

    if args.operation == "refine":
        existing_dir = vk._resolve(os.path.dirname(
            os.path.abspath(args.existing_brief)))
        if existing_dir != vk._resolve(target_dir):
            return _emit(_report(
                "error", "render", "CANDIDATE_NAME",
                message="the existing brief's directory must equal the "
                        "target derived from the immutable control "
                        "identity; a root/slug change is a new-build "
                        "request"), 1)

    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            template_text = fh.read()
    except OSError as exc:
        return _emit(_report("error", "render", "UNREADABLE",
                             message="cannot read template: %s" % exc), 2)
    try:
        rendered = render_markdown(control, template_text)
    except ValueError as exc:
        return _emit(_report("error", "render", "REQUIRED_FIELD",
                             message=str(exc)), 1)

    report = vk.validate_document(rendered, args.workspace_root,
                                  args.operation, brief_path=candidate)
    if report["result"] != "pass":
        summary = "; ".join("%s %s" % (f["code"], f["field_id"] or "-")
                            for f in report["findings"][:5])
        return _emit(_report("error", "render", "VALIDATION_FAILED",
                             message="candidate does not PASS: %s" % summary),
                    1)

    os.makedirs(target_dir, exist_ok=True)
    if os.path.exists(candidate):
        return _emit(_report(
            "error", "render", "CANDIDATE_EXISTS",
            paths={"candidate": candidate},
            message="a candidate already exists; inspect or remove it "
                    "explicitly — it is never overwritten or silently "
                    "reused"), 1)
    try:
        _write_exclusive(candidate, rendered)
    except FileExistsError:
        return _emit(_report("error", "render", "CANDIDATE_EXISTS",
                             paths={"candidate": candidate},
                             message="candidate appeared concurrently"), 1)
    sha = {"candidate": sha256_hex_file(candidate)}
    if args.operation == "refine":
        sha["before"] = sha256_hex_file(args.existing_brief)
    return _emit(_report("ok", "render", "RENDERED", changed=True,
                         paths={"candidate": candidate, "final": final},
                         sha256=sha,
                         message="validated candidate written"), 0)


# ---------------------------------------------------------------------------
# finalize subcommand
# ---------------------------------------------------------------------------

def cmd_finalize(args):
    candidate = args.candidate
    if not os.path.isfile(candidate):
        return _emit(_report("error", "finalize", "UNREADABLE",
                             message="candidate not found"), 2)
    try:
        text = vk._read_text(candidate)
        control = vk.parse_control_json(vk.extract_control_block(text))
    except vk.DocumentError as exc:
        return _emit(_report("error", "finalize", exc.code,
                             paths={"candidate": candidate},
                             message=str(exc)), 2)
    try:
        target_dir = _derived_target_dir(control, args.workspace_root)
    except (KeyError, TypeError):
        return _emit(_report("error", "finalize", "REQUIRED_FIELD",
                             message="control payload lacks workspace/"
                                     "project identity fields"), 1)
    final = os.path.join(target_dir, "00-kickoff.md")
    context = os.path.join(target_dir, "00-context.md")

    # explicit collision precheck so a race reports its precise code
    # before the general validator run
    if args.operation == "build" and (vk._exists_nocase(final)
                                      or vk._exists_nocase(context)):
        return _emit(_report(
            "error", "finalize", "COLLISION_FINAL_EXISTS",
            paths={"candidate": candidate, "final": final},
            message="final or context appeared at the target between "
                    "validation and promotion"), 1)

    report = vk.validate_document(text, args.workspace_root,
                                  args.operation, brief_path=candidate)
    if report["result"] != "pass":
        return _emit(_report("error", "finalize", "VALIDATION_FAILED",
                             paths={"candidate": candidate},
                             message="candidate does not PASS; never "
                                     "finalized"), 1)

    if args.operation == "build":
        if vk._exists_nocase(final) or vk._exists_nocase(context):
            return _emit(_report(
                "error", "finalize", "COLLISION_FINAL_EXISTS",
                paths={"candidate": candidate, "final": final},
                message="final or context appeared at the target between "
                        "validation and promotion"), 1)
        try:
            os.link(candidate, final)
        except FileExistsError:
            return _emit(_report(
                "error", "finalize", "COLLISION_FINAL_EXISTS",
                paths={"candidate": candidate, "final": final},
                message="00-kickoff.md appeared concurrently; promotion "
                        "fails closed"), 1)
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EOPNOTSUPP,
                             getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
                             errno.ENOSYS, errno.EACCES, errno.EXDEV):
                return _emit(_report(
                    "error", "finalize", "HARDLINK_UNSUPPORTED",
                    paths={"candidate": candidate, "final": final},
                    message="the filesystem does not support hard links; "
                            "the validated candidate is left in place and "
                            "there is no rename fallback"), 1)
            raise
        sha_final = sha256_hex_file(final)
        message = "published"
        try:
            os.unlink(candidate)
        except OSError:
            message = "published; candidate could not be unlinked and " \
                      "remains at the reported path"
        return _emit(_report("ok", "finalize", "PUBLISHED", changed=True,
                             paths={"candidate": candidate, "final": final},
                             sha256={"after": sha_final},
                             message=message), 0)

    # refine
    if not args.approved:
        return _emit(_report("error", "finalize", "APPROVAL_REQUIRED",
                             message="refine promotion requires --approved"),
                    1)
    if not args.expected_final_sha256:
        return _emit(_report("error", "finalize", "USAGE",
                             message="refine requires "
                                     "--expected-final-sha256"), 2)
    lock = _Lock(final)
    if not lock.acquire("finalize"):
        return _emit(_report(
            "error", "finalize", "LOCK_HELD",
            paths={"candidate": candidate, "final": final},
            message="another cooperating helper holds the lock at %s; "
                    "never auto-broken" % lock.path), 1)
    try:
        if not os.path.isfile(final):
            return _emit(_report("error", "finalize",
                                 "REFINE_TARGET_MISSING",
                                 paths={"final": final},
                                 message="00-kickoff.md missing at the "
                                         "target"), 1)
        before = sha256_hex_file(final)
        if before != args.expected_final_sha256.lower():
            return _emit(_report(
                "error", "finalize", "HASH_MISMATCH",
                paths={"candidate": candidate, "final": final},
                sha256={"before": before},
                message="the final brief changed since it was reviewed; "
                        "stop for re-review"), 1)
        backup = final + "." + before[:12] + ".bak"
        if os.path.exists(backup):
            if sha256_hex_file(backup) != before:
                return _emit(_report(
                    "error", "finalize", "BACKUP_EXISTS",
                    paths={"backup": backup},
                    message="a conflicting backup already exists"), 1)
        else:
            try:
                os.link(final, backup)
            except OSError as exc:
                return _emit(_report(
                    "error", "finalize", "HARDLINK_UNSUPPORTED",
                    paths={"final": final, "backup": backup},
                    message="cannot create the recovery backup: %s" % exc),
                    1)
        os.replace(candidate, final)
        after = sha256_hex_file(final)
        return _emit(_report(
            "ok", "finalize", "REPLACED", changed=True,
            paths={"candidate": candidate, "final": final, "backup": backup},
            sha256={"before": before, "after": after, "backup": before},
            message="refined brief promoted; hash-named backup retained"), 0)
    finally:
        lock.release()


# ---------------------------------------------------------------------------
# merge-config subcommand
# ---------------------------------------------------------------------------

def _config_template(dossier_root):
    lines = [CONFIG_HEADER, "",
             "Dossier root: %s" % dossier_root, "",
             CONFIG_ACCESS_HEADING, ""]
    for agent in vk.AGENT_IDS:
        lines.append("- %s: %s" % (
            vk.CONFIG_LABELS[agent],
            canonical_json({"status": "unknown", "tier": None,
                            "routes": []})))
    lines.append("")
    lines.append(CONFIG_TEMPLATE_COMMENT)
    return "\n".join(lines) + "\n"


_ACCESS_LINE_RE = re.compile(r"^- ([A-Za-z ]+?): (.*)$")


def _validate_access_entry(agent, entry):
    findings = []
    vk._check_schema(entry, vk._access_entry_site(agent), "", findings,
                     vk.CONTRACT_SCHEMA)
    if findings:
        return findings[0]["message"]
    for _label, pattern in vk.SECRET_RES:
        if pattern.search(canonical_json(entry)):
            return "secret-like value in access entry"
    tier = entry.get("tier")
    if isinstance(tier, str) and not tier.strip():
        return "tier must be trimmed non-empty or null"
    return None


def cmd_merge_config(args):
    if not args.approved:
        return _emit(_report("error", "merge-config", "APPROVAL_REQUIRED",
                             message="merge-config requires --approved"), 1)
    expected = os.path.join(args.workspace_root, "research-config.md")
    if vk._resolve(os.path.abspath(args.config)) != \
            vk._resolve(expected):
        return _emit(_report(
            "error", "merge-config", "CONFIG_PATH",
            message="config path must equal "
                    "<workspace-root>/research-config.md"), 1)
    try:
        with open(args.updates, "r", encoding="utf-8") as fh:
            updates = json.loads(fh.read(),
                                 object_pairs_hook=vk._reject_dup_pairs)
    except OSError as exc:
        return _emit(_report("error", "merge-config", "UNREADABLE",
                             message=str(exc)), 2)
    except (ValueError, vk._DuplicateKey) as exc:
        return _emit(_report("error", "merge-config", "MALFORMED_JSON",
                             message=str(exc)), 2)
    if not isinstance(updates, dict) or \
            set(updates) != {"dossier_root", "agent_access"}:
        return _emit(_report(
            "error", "merge-config", "MALFORMED_JSON",
            message="updates must be exactly "
                    '{"dossier_root":...,"agent_access":{...}}'), 1)
    root_update = updates["dossier_root"]
    if root_update is not None and not (
            isinstance(root_update, str) and root_update.strip()):
        return _emit(_report("error", "merge-config", "MALFORMED_JSON",
                             message="dossier_root must be a non-empty "
                                     "string or null"), 1)
    access_updates = updates["agent_access"]
    if not isinstance(access_updates, dict):
        return _emit(_report("error", "merge-config", "MALFORMED_JSON",
                             message="agent_access must be an object"), 1)
    for agent, entry in access_updates.items():
        if agent not in vk.AGENT_IDS:
            return _emit(_report("error", "merge-config", "UNKNOWN_KEY",
                                 message="unknown access id %r" % agent), 1)
        problem = _validate_access_entry(agent, entry)
        if problem:
            return _emit(_report(
                "error", "merge-config", "TRANSIENT_STATE",
                message="access entry for %s rejected: %s"
                        % (agent, problem)), 1)

    config_path = args.config
    if not os.path.exists(config_path):
        if root_update is None:
            return _emit(_report(
                "error", "merge-config", "REQUIRED_FIELD",
                message="creating a missing config requires a non-null "
                        "dossier_root"), 1)
        content = _config_template(root_update)
        lines = content.split("\n")
        lines = _apply_access_updates(lines, access_updates)
        content = "\n".join(lines)
        tmp = config_path + ".kickoff-tmp"
        try:
            _write_exclusive(tmp, content)
            try:
                os.link(tmp, config_path)
            except FileExistsError:
                os.unlink(tmp)
                return _emit(_report(
                    "error", "merge-config", "CONFIG_RACE",
                    paths={"config": config_path},
                    message="another writer created the config first; "
                            "re-run to merge instead of overwriting"), 1)
            os.unlink(tmp)
        except FileExistsError:
            return _emit(_report("error", "merge-config", "CONFIG_RACE",
                                 message="temp file exists; a previous run "
                                         "may have been interrupted"), 1)
        return _emit(_report(
            "ok", "merge-config", "CREATED", changed=True,
            paths={"config": config_path},
            sha256={"after": sha256_hex_file(config_path)},
            message="canonical config created"), 0)

    lock = _Lock(config_path)
    if not lock.acquire("merge-config"):
        return _emit(_report("error", "merge-config", "LOCK_HELD",
                             paths={"config": config_path},
                             message="another cooperating helper holds the "
                                     "config lock"), 1)
    try:
        before = sha256_hex_file(config_path)
        with open(config_path, "r", encoding="utf-8") as fh:
            original = fh.read()
        lines = original.split("\n")

        label_counts = {}
        for line in lines:
            m = _ACCESS_LINE_RE.match(line.strip())
            if m and m.group(1) in vk.CONFIG_LABELS.values():
                label_counts[m.group(1)] = label_counts.get(m.group(1),
                                                            0) + 1
        for label, count in label_counts.items():
            if count > 1:
                return _emit(_report(
                    "error", "merge-config", "DUPLICATE_LINE",
                    paths={"config": config_path},
                    message="duplicate known line for %r" % label), 1)
        for line in lines:
            m = _ACCESS_LINE_RE.match(line.strip())
            if m and m.group(1) in vk.CONFIG_LABELS.values():
                value = m.group(2).strip()
                if value.startswith("{"):
                    try:
                        json.loads(value,
                                   object_pairs_hook=vk._reject_dup_pairs)
                    except (ValueError, vk._DuplicateKey):
                        return _emit(_report(
                            "error", "merge-config", "MALFORMED_LINE",
                            paths={"config": config_path},
                            message="malformed JSON access line for %r"
                                    % m.group(1)), 1)

        if root_update is not None:
            replaced = False
            for idx, line in enumerate(lines):
                if line.startswith("Dossier root:"):
                    lines[idx] = "Dossier root: %s" % root_update
                    replaced = True
                    break
            if not replaced:
                header_idx = next(
                    (i for i, l in enumerate(lines)
                     if l.strip() == CONFIG_HEADER), None)
                insert_at = header_idx + 1 if header_idx is not None else 0
                lines.insert(insert_at, "")
                lines.insert(insert_at + 1,
                             "Dossier root: %s" % root_update)
        lines = _apply_access_updates(lines, access_updates)

        updated = "\n".join(lines)
        if updated == original:
            return _emit(_report(
                "ok", "merge-config", "UNCHANGED", changed=False,
                paths={"config": config_path},
                sha256={"before": before, "after": before},
                message="approved merge produced no textual change"), 0)
        tmp = config_path + ".kickoff-tmp"
        try:
            _write_exclusive(tmp, updated)
        except FileExistsError:
            return _emit(_report("error", "merge-config", "CONFIG_RACE",
                                 message="temp file exists; a previous run "
                                         "may have been interrupted"), 1)
        os.replace(tmp, config_path)
        return _emit(_report(
            "ok", "merge-config", "MERGED", changed=True,
            paths={"config": config_path},
            sha256={"before": before,
                    "after": sha256_hex_file(config_path)},
            message="config merged; comments and unknown lines preserved"),
            0)
    finally:
        lock.release()


def _apply_access_updates(lines, access_updates):
    for agent, entry in access_updates.items():
        label = vk.CONFIG_LABELS[agent]
        new_line = "- %s: %s" % (label, canonical_json(entry))
        replaced = False
        for idx, line in enumerate(lines):
            m = _ACCESS_LINE_RE.match(line.strip())
            if m and m.group(1) == label:
                existing = m.group(2).strip()
                if existing.startswith("{"):
                    try:
                        if json.loads(existing) == entry:
                            replaced = True  # semantically identical
                            break
                    except ValueError:
                        pass
                lines[idx] = new_line
                replaced = True
                break
        if not replaced:
            heading_idx = next(
                (i for i, l in enumerate(lines)
                 if l.strip() == CONFIG_ACCESS_HEADING), None)
            if heading_idx is None:
                lines.extend(["", CONFIG_ACCESS_HEADING, new_line])
            else:
                insert_at = heading_idx + 1
                while insert_at < len(lines) and (
                        not lines[insert_at].strip()
                        or _ACCESS_LINE_RE.match(lines[insert_at].strip())):
                    insert_at += 1
                lines.insert(insert_at, new_line)
    return lines


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="kickoff_io.py",
        description="Deterministic render/finalize/merge-config helper for "
                    "kickoff briefs.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render")
    p_render.add_argument("control")
    p_render.add_argument("--workspace-root", required=True)
    p_render.add_argument("--operation", required=True,
                          choices=["build", "refine"])
    p_render.add_argument("--existing-brief")

    p_final = sub.add_parser("finalize")
    p_final.add_argument("candidate")
    p_final.add_argument("--workspace-root", required=True)
    p_final.add_argument("--operation", required=True,
                         choices=["build", "refine"])
    p_final.add_argument("--expected-final-sha256")
    p_final.add_argument("--approved", action="store_true")

    p_merge = sub.add_parser("merge-config")
    p_merge.add_argument("config")
    p_merge.add_argument("--updates", required=True)
    p_merge.add_argument("--workspace-root", required=True)
    p_merge.add_argument("--approved", action="store_true")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(json.dumps(_report("error", "unknown", "USAGE",
                                     message="usage error"),
                             ensure_ascii=False))
            return 2
        return 0
    if args.command == "render":
        return cmd_render(args)
    if args.command == "finalize":
        return cmd_finalize(args)
    return cmd_merge_config(args)


if __name__ == "__main__":
    sys.exit(main())

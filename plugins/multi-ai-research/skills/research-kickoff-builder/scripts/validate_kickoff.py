#!/usr/bin/env python
"""Kickoff-brief validator (gates K1-K8) for the research-kickoff-builder skill.

Validates a `00-kickoff.md` brief (or draft/.v2 candidate) against the v1
kickoff contract. Stdlib-only and runtime self-contained: it reads nothing
except the named brief and CLI arguments. The canonical machine contract in
`../references/kickoff-contract.md` is generated from CONTRACT_SCHEMA below;
`test_contract_drift.py` locks the two representations together.

Exit codes:
  0  PASS
  1  parsed successfully but one or more gates failed
  2  usage, unreadable input, unsupported encoding/schema, or parse error

Exit-code split for K1 (documented resolution of the spec's two sentences):
  * FATAL parse-class failures (unreadable file, unsupported encoding,
    missing/duplicate control block, malformed JSON, duplicate JSON key,
    missing/unsupported `kickoff_schema_version`) produce result "error",
    exit 2, K1 FAIL, and K2-K8 NOT_EVALUATED.
  * NON-FATAL K1 failures (schema-shape violations, heading order/duplication,
    unresolved placeholders, human/JSON parity conflicts) produce exit 1 and
    the remaining gates still evaluate against the parsed payload.
  * CLI usage errors / unreadable files report all gates NOT_EVALUATED with a
    null-gate finding.

The compiled OPERATOR_SOURCE_RE below is intentionally a byte-identical
duplicate of the one in the research-orchestrator skill's validate_phase1.py
(runtime scripts may not import across skill directories);
test_contract_drift.py asserts the two stay semantically equal.
"""

import argparse
import ipaddress
import json
import os
import re
import sys
from urllib.parse import urlsplit

GATES = ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"]
KICKOFF_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
SENTINEL_BEGIN = "<!-- BEGIN KICKOFF-CONTROL v1 -->"
SENTINEL_END = "<!-- END KICKOFF-CONTROL v1 -->"

# --- identity / enum tables (drift-test-locked) -----------------------------

AGENT_IDS = ("perplexity", "gemini", "grok", "chatgpt", "claude",
             "deepseek", "notebooklm", "elicit", "consensus", "scite")
LANE_AGENT_IDS = AGENT_IDS[:9]  # scite is never a Phase-2 lane

CONFIG_LABELS = {
    "perplexity": "Perplexity", "gemini": "Gemini", "grok": "Grok",
    "chatgpt": "ChatGPT", "claude": "Claude", "deepseek": "DeepSeek route",
    "notebooklm": "NotebookLM", "elicit": "Elicit", "consensus": "Consensus",
    "scite": "Scite",
}

PHASE1_AGENT_ENUM = {
    "perplexity": "Perplexity", "gemini": "Gemini", "grok": "Grok",
    "chatgpt": "ChatGPT", "claude": "Claude", "deepseek": "DecorrelatedLane",
    "notebooklm": "NotebookLM", "elicit": "Elicit", "consensus": "Consensus",
}

ROLES = ("evidence", "sentiment", "synthesis", "decorrelated")
MODES_ORDER = ("first-principles", "debate", "red-team")
MODE_SUBSETS = [
    [], ["first-principles"], ["debate"], ["red-team"],
    ["first-principles", "debate"], ["first-principles", "red-team"],
    ["debate", "red-team"], ["first-principles", "debate", "red-team"],
]

ROUTES_BY_AGENT = {
    "claude": ("claude_web_extended_thinking", "local"),
    "deepseek": ("consumer_web", "western_hosted_api", "self_hosted"),
}
for _a in AGENT_IDS:
    ROUTES_BY_AGENT.setdefault(_a, ("web", "api"))

OVERLAY_13 = "13-overlay-deliberation-modes.md"
LAYERABLE_USE_CASES = {1, 2, 3, 5, 6, 7}

PROFILE_BY_USE_CASE = {
    1: "spec_driven_dev", 2: "youtube", 3: "presentation", 4: "ebook",
    5: "wordpress_seo", 6: "health", 7: "deck_screencast", 8: "decision",
}
PRIMARY_OVERLAY_BY_USE_CASE = {
    1: "02-overlay-spec-driven-dev.md", 2: "03-overlay-youtube-script.md",
    3: "04-overlay-presentation.md", 4: "05-overlay-ebook.md",
    5: "06-overlay-wordpress-seo.md", 6: "07-overlay-health-content.md",
    7: "08-overlay-deck-and-screencast.md", 8: OVERLAY_13,
}
PRIMARY_RENDER_BY_USE_CASE = {
    1: "architecture_decision_record", 2: "youtube_script",
    3: "presentation_deck", 4: "ebook", 5: "wordpress_article",
    6: "health_protocol", 7: "deck_and_screencast", 8: "decision_brief",
}
ADDITIONAL_RENDERS_ALLOWED = {
    2: ("wordpress_article",),
    6: ("youtube_script", "wordpress_article", "ebook_chapter"),
    8: ("deck_and_screencast",),
}
ALL_ADDITIONAL_RENDER_IDS = (
    "wordpress_article", "youtube_script", "ebook_chapter", "deck_and_screencast")

# --- regexes ----------------------------------------------------------------

SLUG_RE = re.compile(r"^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$")
# Byte-identical duplicate of validate_phase1.OPERATOR_SOURCE_RE (see module
# docstring); test_contract_drift.py enforces semantic equality.
OPERATOR_SOURCE_RE = re.compile(
    r"^operator-[a-z0-9][a-z0-9-]{0,40}(?:[ \t]*\([^()\n]{0,80}\))?\Z")
INPUT_ID_RE = re.compile(r"^IN[1-9][0-9]*$")
GT_ID_RE = re.compile(r"^GT[1-9][0-9]*$")
WINDOWS_RESERVED = {"con", "prn", "aux", "nul",
                    "com1", "com2", "com3", "com4", "com5", "com6", "com7",
                    "com8", "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5",
                    "lpt6", "lpt7", "lpt8", "lpt9"}
FIELD_PLACEHOLDER_RE = re.compile(r"\{\{FIELD:[^}]*\}\}")
INSERT_PLACEHOLDER_RE = re.compile(r"^\[INSERT[^\]]*\]$")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")

SECRET_RES = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("api-key-prefix", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("github-token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("credential-assignment",
     re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*\S{6,}")),
]

HEALTH_POLICY = {
    "evidence_strength_tagging_required": True,
    "evidence_strength_tags": ["STRONG", "MODERATE", "WEAK"],
    "source_recency_cutoff_year": 2020,
    "foundational_source_exception": True,
    "medical_disclaimer_required": True,
    "final_dossier_notebooklm_check_required": True,
}
CONDUCT_FIXED = {
    "run_all_phases": True,
    "enforce_all_gates": True,
    "methodology_scope": "bundled_only",
    "selected_modes_blocking": True,
}

# K5 derivation tables (shared with kickoff_io's derive_expected_lanes)
LANE_SELECTION_ORDER = ("perplexity", "gemini", "grok", "claude", "deepseek")
EVIDENCE_FALLBACK_ORDER = ("perplexity", "gemini", "chatgpt", "notebooklm",
                           "elicit", "consensus")
DEFAULT_ROLE = {"deepseek": "decorrelated", "grok": "sentiment",
                "claude": "synthesis"}
ROUTE_PRECEDENCE = {
    "claude": ("claude_web_extended_thinking", "local"),
    "deepseek_non_confidential": ("consumer_web", "self_hosted",
                                  "western_hosted_api"),
    "deepseek_confidential": ("self_hosted", "western_hosted_api"),
    "default": ("web", "api"),
}

# Required human headings, in order, with presence conditions.
# Condition vocabulary: always | overlay13_active | standing_nonempty |
# guidance_nonempty.
REQUIRED_HEADINGS = (
    ("## Kickoff control", "always"),
    ("## Workspace setup", "always"),
    ("## Invocation", "always"),
    ("## Deliberation modes", "overlay13_active"),
    ("## Phase 0 intake — pre-answered", "always"),
    ("## Use-case profile", "always"),
    ("## Topic slug — pre-confirmed", "always"),
    ("## Phase-execution preferences", "always"),
    ("## Phase 6 deliverables", "always"),
    ("## Conduct rules", "always"),
    ("## Standing instructions", "standing_nonempty"),
    ("## Seed areas and known traps", "guidance_nonempty"),
)

FINDING_CODES = frozenset({
    "USAGE", "UNREADABLE", "ENCODING", "MISSING_CONTROL_BLOCK",
    "DUPLICATE_CONTROL_BLOCK", "MALFORMED_JSON", "DUPLICATE_JSON_KEY",
    "UNSUPPORTED_SCHEMA_VERSION", "UNKNOWN_KEY", "TYPE_MISMATCH",
    "REQUIRED_FIELD", "ENUM_VIOLATION", "PLACEHOLDER_UNRESOLVED",
    "PLACEHOLDER_VALUE", "HEADING_MISSING", "HEADING_ORDER",
    "HEADING_DUPLICATE", "HUMAN_JSON_MISMATCH", "PROFILE_KEY_SET",
    "OVERLAY_ILLEGAL", "RENDER_MATRIX", "SPEC_MODE_RULE", "REQUIREMENTS_REF",
    "VERDICTS_RULE", "MODE_ILLEGAL", "ACCESS_ENTRY_SHAPE",
    "LANE_NOT_RUNNABLE", "LANE_COUNT", "ROLE_VIOLATION", "CLAUDE_SURFACE",
    "DEEPSEEK_ROUTE", "EXCEPTION_INVALID", "PROVIDER_MISSING", "TRUST_RULE",
    "CONTROL_CHARS", "BROWNFIELD_REPO", "GT_SHAPE", "URL_USERINFO",
    "URL_PRIVATE_HOST", "OPERATOR_MARKER", "SECRET_LIKE", "SLUG_INVALID",
    "RESERVED_NAME", "SCOPE_MISMATCH", "OUTSIDE_UNAPPROVED",
    "PLUGIN_TREE_TARGET", "COLLISION_FINAL_EXISTS",
    "COLLISION_CONTEXT_EXISTS", "REFINE_TARGET_MISSING",
    "CANDIDATE_NAME", "PROVENANCE_MISSING", "PROVENANCE_DANGLING",
    "PROVENANCE_VALUE", "HEALTH_INVARIANT", "COVERAGE_RULE",
})


# ---------------------------------------------------------------------------
# CONTRACT_SCHEMA — the full v1 machine contract (JSON Schema Draft 2020-12).
# The fenced block in references/kickoff-contract.md is generated from this
# dict; test_contract_drift.py asserts semantic equality. The restricted
# interpreter _check_schema evaluates exactly the vocabulary listed in
# SCHEMA_VOCABULARY; test_schema_vocabulary_closed enforces that closure.
# ---------------------------------------------------------------------------

SCHEMA_VOCABULARY = frozenset({
    "$schema", "$id", "$defs", "$ref", "type", "const", "enum", "properties",
    "required", "additionalProperties", "items", "minItems", "maxItems",
    "uniqueItems", "minimum", "maximum", "pattern", "minLength", "oneOf",
    "if", "then", "allOf", "propertyNames",
    "x-acquisition", "x-default", "x-consumer", "x-human-section",
})

ACQUISITION_CLASSES = ("must_ask", "cached", "derived", "safe_default",
                       "optional", "constant")


def _access_entry_site(agent_id):
    """Property schema for one agent_access key: shared entry shape plus the
    per-agent route enum."""
    return {
        "allOf": [
            {"$ref": "#/$defs/access_entry"},
            {"properties": {
                "routes": {"items": {"enum": list(ROUTES_BY_AGENT[agent_id])}},
            }},
        ],
    }


CONTRACT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "agentic-research-kickoff-v1",
    "type": "object",
    "additionalProperties": False,
    "required": ["kickoff_schema_version", "workspace", "invocation",
                 "project", "deliberation_modes", "use_case_profile",
                 "preferences", "conduct", "standing_instructions",
                 "seed_areas", "out_of_scope", "known_traps", "provenance"],
    "properties": {
        "kickoff_schema_version": {"const": 1, "x-acquisition": "constant"},
        "workspace": {
            "type": "object", "additionalProperties": False,
            "required": ["dossier_root", "dossier_root_scope",
                         "outside_workspace_write_approved", "agent_access"],
            "properties": {
                "dossier_root": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "cached",
                    "x-consumer": "Step 0.0",
                    "x-human-section": "Workspace setup"},
                "dossier_root_scope": {
                    "enum": ["workspace_relative", "absolute_inside_workspace",
                             "outside_workspace"],
                    "x-acquisition": "derived",
                    "x-consumer": "Step 0.0",
                    "x-human-section": "Workspace setup"},
                "outside_workspace_write_approved": {
                    "type": "boolean",
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.0",
                    "x-human-section": "Workspace setup"},
                "agent_access": {
                    "type": "object", "additionalProperties": False,
                    "required": list(AGENT_IDS),
                    "properties": {a: _access_entry_site(a)
                                   for a in AGENT_IDS},
                    "x-acquisition": "cached",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Workspace setup"},
            },
        },
        "invocation": {
            "type": "object", "additionalProperties": False,
            "required": ["use_case_id", "layered_overlays", "spec_mode",
                         "brownfield_repo", "requirements_input_id"],
            "properties": {
                "use_case_id": {
                    "type": "integer", "minimum": 1, "maximum": 8,
                    "x-acquisition": "derived",
                    "x-consumer": "Step 0.1",
                    "x-human-section": "Invocation"},
                "layered_overlays": {
                    "type": "array", "maxItems": 1, "uniqueItems": True,
                    "items": {"const": OVERLAY_13},
                    "x-acquisition": "derived",
                    "x-consumer": "Step 0.1",
                    "x-human-section": "Invocation"},
                "spec_mode": {
                    "enum": ["greenfield", "brownfield", None],
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.2",
                    "x-human-section": "Invocation"},
                "brownfield_repo": {
                    "type": ["string", "null"], "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.2",
                    "x-human-section": "Invocation"},
                "requirements_input_id": {
                    "type": ["string", "null"],
                    "pattern": "^IN[1-9][0-9]*$",
                    "x-acquisition": "derived",
                    "x-consumer": "Step 0.5",
                    "x-human-section": "Invocation"},
            },
        },
        "project": {
            "type": "object", "additionalProperties": False,
            "required": ["title", "research_question", "decision_context",
                         "time_horizon", "audience", "thesis",
                         "differentiation_hook", "constraints", "stakes",
                         "confidentiality", "classified_inputs",
                         "ground_truth", "topic_slug", "allowed_verdicts"],
            "properties": {
                "title": {"type": "string", "minLength": 1,
                          "x-acquisition": "derived",
                          "x-consumer": "Step 0.4",
                          "x-human-section": "Phase 0 intake — pre-answered"},
                "research_question": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "decision_context": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "time_horizon": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "audience": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "thesis": {"type": ["string", "null"], "minLength": 1,
                           "x-acquisition": "must_ask",
                           "x-consumer": "Step 1.2",
                           "x-human-section": "Phase 0 intake — pre-answered"},
                "differentiation_hook": {
                    "type": ["string", "null"], "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 1.2",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "constraints": {
                    "type": "array", "items": {"type": "string",
                                               "minLength": 1},
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 1.2",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "stakes": {"enum": ["low", "medium", "high"],
                           "x-acquisition": "safe_default",
                           "x-default": "medium",
                           "x-consumer": "Step 1.1",
                           "x-human-section": "Phase 0 intake — pre-answered"},
                "confidentiality": {
                    "enum": ["confidential", "non_confidential"],
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "classified_inputs": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/classified_input"},
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.3",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "ground_truth": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/ground_truth_claim"},
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.6",
                    "x-human-section": "Phase 0 intake — pre-answered"},
                "topic_slug": {
                    "type": "string",
                    "pattern": "^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$",
                    "x-acquisition": "derived",
                    "x-consumer": "Step 0.4",
                    "x-human-section": "Topic slug — pre-confirmed"},
                "allowed_verdicts": {
                    "type": "array", "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                    "x-acquisition": "derived",
                    "x-consumer": "Step 1.2",
                    "x-human-section": "Phase 0 intake — pre-answered"},
            },
        },
        "deliberation_modes": {
            "enum": MODE_SUBSETS,
            "x-acquisition": "derived",
            "x-consumer": "Steps 1.2/2.5/4.5",
            "x-human-section": "Deliberation modes"},
        "use_case_profile": {"type": "object"},
        "preferences": {
            "type": "object", "additionalProperties": False,
            "required": ["phase_1_venue", "phase_3_venue", "phase_5_route",
                         "expected_lanes", "additional_renders"],
            "properties": {
                "phase_1_venue": {
                    "enum": ["auto", "fresh_claude_web", "local"],
                    "x-acquisition": "safe_default", "x-default": "auto",
                    "x-consumer": "Step 1.1",
                    "x-human-section": "Phase-execution preferences"},
                "phase_3_venue": {
                    "enum": ["auto", "fresh_claude_web", "local"],
                    "x-acquisition": "safe_default", "x-default": "auto",
                    "x-consumer": "Step 3.3",
                    "x-human-section": "Phase-execution preferences"},
                "phase_5_route": {
                    "enum": ["auto", "fresh_subagent", "fresh_claude_web",
                             "inline"],
                    "x-acquisition": "safe_default", "x-default": "auto",
                    "x-consumer": "Phase 5 capability gate",
                    "x-human-section": "Phase-execution preferences"},
                "expected_lanes": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/expected_lane"},
                    "x-acquisition": "derived",
                    "x-consumer": "Step 1.2",
                    "x-human-section": "Phase-execution preferences"},
                "additional_renders": {
                    "type": "array", "uniqueItems": True,
                    "items": {"enum": list(ALL_ADDITIONAL_RENDER_IDS)},
                    "x-acquisition": "optional",
                    "x-consumer": "Phase 6",
                    "x-human-section": "Phase 6 deliverables"},
            },
        },
        "conduct": {
            "type": "object", "additionalProperties": False,
            "required": ["run_all_phases", "enforce_all_gates",
                         "methodology_scope", "selected_modes_blocking",
                         "non_cancellable_phases", "decorrelated_exception"],
            "properties": {
                "run_all_phases": {"const": True,
                                   "x-acquisition": "constant"},
                "enforce_all_gates": {"const": True,
                                      "x-acquisition": "constant"},
                "methodology_scope": {"const": "bundled_only",
                                      "x-acquisition": "constant"},
                "selected_modes_blocking": {"const": True,
                                            "x-acquisition": "constant"},
                "non_cancellable_phases": {
                    "enum": [[], [4]],
                    "x-acquisition": "derived",
                    "x-consumer": "Phase 4",
                    "x-human-section": "Conduct rules"},
                "decorrelated_exception": {
                    "$ref": "#/$defs/decorrelated_exception",
                    "x-acquisition": "optional",
                    "x-consumer": "Step 2.2",
                    "x-human-section": "Conduct rules"},
            },
        },
        "standing_instructions": {
            "type": "string",
            "x-acquisition": "optional",
            "x-consumer": "00-context.md guidance",
            "x-human-section": "Standing instructions"},
        "seed_areas": {
            "type": "array", "maxItems": 8,
            "items": {"type": "string", "minLength": 1},
            "x-acquisition": "optional",
            "x-consumer": "00-context.md guidance",
            "x-human-section": "Seed areas and known traps"},
        "out_of_scope": {
            "type": "array", "items": {"type": "string", "minLength": 1},
            "x-acquisition": "optional",
            "x-consumer": "00-context.md guidance",
            "x-human-section": "Seed areas and known traps"},
        "known_traps": {
            "type": "array", "items": {"type": "string", "minLength": 1},
            "x-acquisition": "optional",
            "x-consumer": "00-context.md guidance",
            "x-human-section": "Seed areas and known traps"},
        "provenance": {
            "type": "object",
            "propertyNames": {"pattern": "^/"},
            "additionalProperties": {
                "enum": ["explicit", "cached", "derived", "defaulted"]},
            "x-acquisition": "derived",
            "x-consumer": "00-context.md provenance",
            "x-human-section": "Conduct rules"},
    },
    "allOf": [
        {"if": {"properties": {"invocation": {"properties": {
             "use_case_id": {"const": 6}}}}},
         "then": {"properties": {
             "project": {"properties": {"stakes": {"const": "high"}}},
             "conduct": {"properties": {
                 "non_cancellable_phases": {"const": [4]}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "use_case_id": {"enum": [1, 2, 3, 4, 5, 7, 8]}}}}},
         "then": {"properties": {"conduct": {"properties": {
             "non_cancellable_phases": {"const": []}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "use_case_id": {"enum": [4, 8]}}}}},
         "then": {"properties": {"invocation": {"properties": {
             "layered_overlays": {"const": []}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "use_case_id": {"const": 1}}}}},
         "then": {"properties": {"invocation": {"properties": {
             "spec_mode": {"enum": ["greenfield", "brownfield"]}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "use_case_id": {"enum": [2, 3, 4, 5, 6, 7, 8]}}}}},
         "then": {"properties": {"invocation": {"properties": {
             "spec_mode": {"const": None},
             "brownfield_repo": {"const": None}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "spec_mode": {"const": "brownfield"}}}}},
         "then": {"properties": {"invocation": {"properties": {
             "brownfield_repo": {"type": "string"}}}}}},
        {"if": {"properties": {"invocation": {"properties": {
             "spec_mode": {"const": "greenfield"}}}}},
         "then": {"properties": {"invocation": {"properties": {
             "brownfield_repo": {"const": None}}}}}},
    ],
    "oneOf": [
        {"properties": {
            "invocation": {"properties": {"use_case_id": {"const": n}}},
            "use_case_profile": {"$ref": "#/$defs/profile_%s"
                                 % PROFILE_BY_USE_CASE[n]}}}
        for n in range(1, 9)
    ],
    "$defs": {
        "access_entry": {
            "type": "object", "additionalProperties": False,
            "required": ["status", "tier", "routes"],
            "properties": {
                "status": {"enum": ["unknown", "available", "unavailable"]},
                "tier": {"type": ["string", "null"], "minLength": 1},
                "routes": {"type": "array", "uniqueItems": True,
                           "items": {"type": "string"}},
            },
            "allOf": [
                {"if": {"properties": {"status": {
                     "enum": ["unknown", "unavailable"]}}},
                 "then": {"properties": {"tier": {"const": None},
                                         "routes": {"maxItems": 0}}}},
                {"if": {"properties": {"status": {"const": "available"}}},
                 "then": {"properties": {"routes": {"minItems": 1}}}},
            ],
        },
        "classified_input": {
            "type": "object", "additionalProperties": False,
            "required": ["input_id", "path", "trust", "contaminants"],
            "properties": {
                "input_id": {"type": "string", "pattern": "^IN[1-9][0-9]*$"},
                "path": {"type": "string", "minLength": 1},
                "trust": {"enum": ["trusted", "under_scrutiny"]},
                "contaminants": {"type": "array",
                                 "items": {"type": "string", "minLength": 1}},
            },
            "allOf": [
                {"if": {"properties": {"trust": {"const": "trusted"}}},
                 "then": {"properties": {"contaminants": {"maxItems": 0}}}},
            ],
        },
        "ground_truth_claim": {
            "type": "object", "additionalProperties": False,
            "required": ["claim_id", "statement", "metric_definition",
                         "source"],
            "properties": {
                "claim_id": {"type": "string", "pattern": "^GT[1-9][0-9]*$"},
                "statement": {"type": "string", "minLength": 1},
                "metric_definition": {"type": "string", "minLength": 1},
                "source": {"type": "string", "minLength": 1},
            },
        },
        "expected_lane": {
            "type": "object", "additionalProperties": False,
            "required": ["agent", "route", "role"],
            "properties": {
                "agent": {"enum": list(LANE_AGENT_IDS)},
                "route": {"type": "string", "minLength": 1},
                "role": {"enum": list(ROLES)},
            },
        },
        "decorrelated_exception": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "required": ["active", "reason", "risk_accepted"],
            "properties": {
                "active": {"const": True},
                "reason": {"type": "string", "minLength": 1},
                "risk_accepted": {"const": True},
            },
        },
        "profile_spec_driven_dev": {
            "type": "object", "additionalProperties": False,
            "required": ["product_target_users", "requirements_coverage"],
            "properties": {
                "product_target_users": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 02 Phase 1",
                    "x-human-section": "Use-case profile"},
                "requirements_coverage": {
                    "type": ["object", "null"],
                    "additionalProperties": False,
                    "required": ["product_target_users", "constraints"],
                    "properties": {
                        "product_target_users": {"type": "boolean"},
                        "constraints": {"type": "boolean"},
                    },
                    "x-acquisition": "must_ask",
                    "x-consumer": "Step 0.5",
                    "x-human-section": "Use-case profile"},
            },
        },
        "profile_youtube": {
            "type": "object", "additionalProperties": False,
            "required": ["video_duration_minutes"],
            "properties": {
                "video_duration_minutes": {
                    "type": "integer", "minimum": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 03 Phase 1",
                    "x-human-section": "Use-case profile"},
            },
        },
        "profile_presentation": {
            "type": "object", "additionalProperties": False,
            "required": ["talk_duration_minutes", "setting", "client_pitch",
                         "client_material_input_ids"],
            "properties": {
                "talk_duration_minutes": {
                    "type": "integer", "minimum": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 04 Phase 1",
                    "x-human-section": "Use-case profile"},
                "setting": {"type": "string", "minLength": 1,
                            "x-acquisition": "must_ask",
                            "x-consumer": "overlay 04 Phase 1",
                            "x-human-section": "Use-case profile"},
                "client_pitch": {"type": "boolean",
                                 "x-acquisition": "derived",
                                 "x-consumer": "overlay 04 Phase 1",
                                 "x-human-section": "Use-case profile"},
                "client_material_input_ids": {
                    "type": "array", "uniqueItems": True,
                    "items": {"type": "string", "pattern": "^IN[1-9][0-9]*$"},
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 04 Phase 2 (NotebookLM)",
                    "x-human-section": "Use-case profile"},
            },
            "allOf": [
                {"if": {"properties": {"client_pitch": {"const": True}}},
                 "then": {"properties": {
                     "client_material_input_ids": {"minItems": 1}}}},
                {"if": {"properties": {"client_pitch": {"const": False}}},
                 "then": {"properties": {
                     "client_material_input_ids": {"maxItems": 0}}}},
            ],
        },
        "profile_ebook": {
            "type": "object", "additionalProperties": False,
            "required": ["prior_knowledge", "intended_takeaway",
                         "total_word_target", "chapter_count", "format"],
            "properties": {
                "prior_knowledge": {"type": "string", "minLength": 1,
                                    "x-acquisition": "must_ask",
                                    "x-consumer": "overlay 05 Phase 0",
                                    "x-human-section": "Use-case profile"},
                "intended_takeaway": {"type": "string", "minLength": 1,
                                      "x-acquisition": "must_ask",
                                      "x-consumer": "overlay 05 Phase 0",
                                      "x-human-section": "Use-case profile"},
                "total_word_target": {"type": "integer", "minimum": 30000,
                                      "maximum": 80000,
                                      "x-acquisition": "must_ask",
                                      "x-consumer": "overlay 05 Phase 0",
                                      "x-human-section": "Use-case profile"},
                "chapter_count": {"type": "integer", "minimum": 8,
                                  "maximum": 15,
                                  "x-acquisition": "must_ask",
                                  "x-consumer": "overlay 05 Phase 0",
                                  "x-human-section": "Use-case profile"},
                "format": {"enum": ["how_to", "narrative", "reference",
                                    "hybrid"],
                           "x-acquisition": "must_ask",
                           "x-consumer": "overlay 05 Phase 0",
                           "x-human-section": "Use-case profile"},
            },
        },
        "profile_wordpress_seo": {
            "type": "object", "additionalProperties": False,
            "required": ["site_name", "primary_keyword", "search_intent",
                         "target_word_count", "secondary_keywords",
                         "keyword_brief"],
            "properties": {
                "site_name": {"type": "string", "minLength": 1,
                              "x-acquisition": "must_ask",
                              "x-consumer": "overlay 06 Phase 1",
                              "x-human-section": "Use-case profile"},
                "primary_keyword": {"type": "string", "minLength": 1,
                                    "x-acquisition": "must_ask",
                                    "x-consumer": "overlay 06 Phase 1",
                                    "x-human-section": "Use-case profile"},
                "search_intent": {
                    "enum": ["informational", "commercial", "transactional",
                             None],
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 06 Phase 1",
                    "x-human-section": "Use-case profile"},
                "target_word_count": {
                    "type": ["integer", "null"], "minimum": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 06 Phase 1",
                    "x-human-section": "Use-case profile"},
                "secondary_keywords": {
                    "type": "array", "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 06 Phase 5",
                    "x-human-section": "Use-case profile"},
                "keyword_brief": {
                    "type": "object", "additionalProperties": False,
                    "required": ["status", "input_id",
                                 "serp_average_word_count", "serp_provider"],
                    "properties": {
                        "status": {"enum": ["provided", "pending"]},
                        "input_id": {"type": ["string", "null"],
                                     "pattern": "^IN[1-9][0-9]*$"},
                        "serp_average_word_count": {
                            "type": ["integer", "null"], "minimum": 1},
                        "serp_provider": {
                            "enum": ["perplexity", "grok", None]},
                    },
                    "allOf": [
                        {"if": {"properties": {
                             "status": {"const": "provided"}}},
                         "then": {"properties": {
                             "input_id": {"type": "string"},
                             "serp_average_word_count": {"type": "integer"},
                             "serp_provider": {"const": None}}}},
                        {"if": {"properties": {
                             "status": {"const": "pending"}}},
                         "then": {"properties": {
                             "input_id": {"const": None},
                             "serp_average_word_count": {"const": None},
                             "serp_provider": {
                                 "enum": ["perplexity", "grok"]}}}},
                    ],
                    "x-acquisition": "must_ask",
                    "x-consumer": "Pre-Phase-1 keyword brief (Step 1.0)",
                    "x-human-section": "Use-case profile"},
            },
        },
        "profile_health": {
            "type": "object", "additionalProperties": False,
            "required": ["evidence_population", "intervention_or_exposure",
                         "intended_outcomes", "safety_scope",
                         "commercial_relationship", "policy"],
            "properties": {
                "evidence_population": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 07 Phase 1",
                    "x-human-section": "Use-case profile"},
                "intervention_or_exposure": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 07 Phase 1",
                    "x-human-section": "Use-case profile"},
                "intended_outcomes": {
                    "type": "array", "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 07 Phase 1",
                    "x-human-section": "Use-case profile"},
                "safety_scope": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 07 Phase 4",
                    "x-human-section": "Use-case profile"},
                "commercial_relationship": {
                    "enum": ["none", "sponsorship", "affiliate", "both"],
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 07 Phase 6",
                    "x-human-section": "Use-case profile"},
                "policy": {"const": HEALTH_POLICY,
                           "x-acquisition": "constant"},
            },
        },
        "profile_deck_screencast": {
            "type": "object", "additionalProperties": False,
            "required": ["deck_slide_target", "video_duration_minutes"],
            "properties": {
                "deck_slide_target": {
                    "type": "integer", "minimum": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 08 format envelope",
                    "x-human-section": "Use-case profile"},
                "video_duration_minutes": {
                    "type": "integer", "minimum": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 08 format envelope",
                    "x-human-section": "Use-case profile"},
            },
        },
        "profile_decision": {
            "type": "object", "additionalProperties": False,
            "required": ["decision_options", "reversibility",
                         "current_leaning"],
            "properties": {
                "decision_options": {
                    "type": "array", "minItems": 2, "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 13 Phase 1",
                    "x-human-section": "Use-case profile"},
                "reversibility": {
                    "type": "string", "minLength": 1,
                    "x-acquisition": "must_ask",
                    "x-consumer": "overlay 13 Phase 1",
                    "x-human-section": "Use-case profile"},
                "current_leaning": {
                    "type": ["string", "null"],
                    "x-acquisition": "optional",
                    "x-consumer": "overlay 13 Phase 1",
                    "x-human-section": "Use-case profile"},
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Errors and findings
# ---------------------------------------------------------------------------

class DocumentError(Exception):
    """Fatal usage/IO/parse condition -> exit 2."""

    def __init__(self, message, code="MALFORMED_JSON", gate="K1",
                 field_id=None):
        super().__init__(message)
        self.code = code
        self.gate = gate
        self.field_id = field_id


def _finding(gate, code, field_id, message, hint=""):
    assert code in FINDING_CODES, "undocumented finding code %r" % code
    return {"gate": gate, "code": code, "field_id": field_id,
            "message": message, "hint": hint}


# ---------------------------------------------------------------------------
# Parsing layer
# ---------------------------------------------------------------------------

def _read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise DocumentError("cannot read %s: %s" % (path, exc),
                            code="UNREADABLE", gate=None)
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentError("unsupported encoding (not UTF-8): %s" % exc,
                            code="ENCODING", gate=None)


class _DuplicateKey(Exception):
    def __init__(self, key):
        super().__init__("duplicate JSON key: %r" % key)
        self.key = key


def _reject_dup_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateKey(key)
        obj[key] = value
    return obj


_FENCE_RE = re.compile(r"^(`{3,})(\S*)\s*$")


def extract_control_block(text):
    """Return the JSON text of the single sentinel-delimited control block.

    Raises DocumentError on zero blocks, multiple blocks, unpaired sentinels,
    a missing/duplicated fence inside a block, or a closing fence whose
    backtick count differs from the opening fence.
    """
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == SENTINEL_BEGIN:
            j = i + 1
            fence_len = None
            payload = None
            while j < len(lines):
                stripped = lines[j].strip()
                if stripped == SENTINEL_END:
                    break
                if stripped == SENTINEL_BEGIN:
                    raise DocumentError(
                        "nested/unpaired control sentinels",
                        code="DUPLICATE_CONTROL_BLOCK")
                m = _FENCE_RE.match(stripped)
                if m and fence_len is None:
                    if m.group(2) != "json":
                        raise DocumentError(
                            "control-block fence must carry the json info "
                            "string", code="MALFORMED_JSON")
                    fence_len = len(m.group(1))
                    body = []
                    j += 1
                    closed = False
                    while j < len(lines):
                        inner = lines[j]
                        if inner.strip() == "`" * fence_len:
                            closed = True
                            break
                        if (inner.strip().startswith("`" * 3)
                                and set(inner.strip()) == {"`"}):
                            raise DocumentError(
                                "closing fence length must exactly match "
                                "the opening fence",
                                code="MALFORMED_JSON")
                        body.append(inner)
                        j += 1
                    if not closed:
                        raise DocumentError("unclosed control-block fence",
                                            code="MALFORMED_JSON")
                    payload = "\n".join(body)
                j += 1
            else:
                raise DocumentError("unpaired BEGIN sentinel (no END)",
                                    code="MISSING_CONTROL_BLOCK")
            if payload is None:
                raise DocumentError(
                    "control block contains no json fence",
                    code="MISSING_CONTROL_BLOCK")
            blocks.append(payload)
            i = j + 1
            continue
        if lines[i].strip() == SENTINEL_END:
            raise DocumentError("unpaired END sentinel",
                                code="MISSING_CONTROL_BLOCK")
        i += 1
    if not blocks:
        raise DocumentError("no KICKOFF-CONTROL v1 block found",
                            code="MISSING_CONTROL_BLOCK")
    if len(blocks) > 1:
        raise DocumentError("more than one KICKOFF-CONTROL v1 block",
                            code="DUPLICATE_CONTROL_BLOCK")
    return blocks[0]


def parse_control_json(block_text):
    try:
        payload = json.loads(block_text, object_pairs_hook=_reject_dup_pairs)
    except _DuplicateKey as exc:
        raise DocumentError(str(exc), code="DUPLICATE_JSON_KEY")
    except ValueError as exc:
        raise DocumentError("control block is not valid JSON: %s" % exc,
                            code="MALFORMED_JSON")
    if not isinstance(payload, dict):
        raise DocumentError("control payload must be a JSON object",
                            code="MALFORMED_JSON")
    version = payload.get("kickoff_schema_version")
    if isinstance(version, bool) or version != KICKOFF_SCHEMA_VERSION:
        raise DocumentError(
            "unsupported kickoff_schema_version: %r" % (version,),
            code="UNSUPPORTED_SCHEMA_VERSION",
            field_id="/kickoff_schema_version")
    return payload


def scan_headings(text):
    """Yield (level, heading_text, line_no) for ATX headings, skipping
    content inside backtick fences (exact-length close), HTML comments, and
    blockquotes."""
    headings = []
    fence_len = 0
    in_comment = False
    for line_no, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if fence_len:
            if stripped == "`" * fence_len:
                fence_len = 0
            continue
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        m = _FENCE_RE.match(stripped)
        if m:
            fence_len = len(m.group(1))
            continue
        if stripped.startswith("<!--") and "-->" not in stripped:
            in_comment = True
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if title:
                headings.append((level, title, line_no))
    return headings


def _resolve(path):
    return os.path.normcase(os.path.realpath(path))


def _is_within(child, parent):
    child = _resolve(child)
    parent = _resolve(parent)
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False


def _plugin_root():
    """Root of the installed plugin (source tree or plugin cache)."""
    return os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", ".."))


def json_pointer_get(document, pointer):
    """Resolve an RFC 6901 pointer. Returns (found, value)."""
    if pointer == "":
        return True, document
    if not pointer.startswith("/"):
        return False, None
    node = document
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            if token not in node:
                return False, None
            node = node[token]
        elif isinstance(node, list):
            if not token.isdigit() or int(token) >= len(node):
                return False, None
            node = node[int(token)]
        else:
            return False, None
    return True, node


# ---------------------------------------------------------------------------
# Restricted JSON Schema interpreter
# ---------------------------------------------------------------------------

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float))
    and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}

_KEYWORD_CODES = {
    "type": "TYPE_MISMATCH", "const": "ENUM_VIOLATION",
    "enum": "ENUM_VIOLATION", "required": "REQUIRED_FIELD",
    "additionalProperties": "UNKNOWN_KEY", "minItems": "TYPE_MISMATCH",
    "maxItems": "TYPE_MISMATCH", "uniqueItems": "TYPE_MISMATCH",
    "minimum": "TYPE_MISMATCH", "maximum": "TYPE_MISMATCH",
    "pattern": "TYPE_MISMATCH", "minLength": "TYPE_MISMATCH",
    "propertyNames": "PROVENANCE_VALUE",
}


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _deref(schema, root):
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError("unsupported $ref: %r" % ref)
        found, target = json_pointer_get(root, ref[1:])
        if not found:
            raise ValueError("dangling $ref: %r" % ref)
        extra = {k: v for k, v in schema.items() if k != "$ref"}
        schema = dict(target)
        schema.update(extra)
    return schema


def _check_schema(instance, schema, pointer, findings, root):
    """Evaluate the restricted vocabulary; append findings on violation."""
    schema = _deref(schema, root)

    def fail(keyword, message, hint=""):
        findings.append(_finding("K1", _KEYWORD_CODES.get(keyword,
                                                          "TYPE_MISMATCH"),
                                 pointer or "/", message, hint))

    if "type" in schema:
        types = schema["type"]
        if isinstance(types, str):
            types = [types]
        if not any(_TYPE_CHECKS[t](instance) for t in types):
            fail("type", "expected %s, got %s"
                 % ("|".join(types), type(instance).__name__))
            return
    if "const" in schema:
        if instance != schema["const"] or isinstance(instance, bool) \
                != isinstance(schema["const"], bool):
            fail("const", "value must be exactly %s"
                 % _canon(schema["const"]))
            return
    if "enum" in schema:
        ok = any(instance == member
                 and isinstance(instance, bool) == isinstance(member, bool)
                 for member in schema["enum"])
        if not ok:
            fail("enum", "value %s not in the permitted set"
                 % _canon(instance),
                 hint="allowed: %s" % _canon(schema["enum"]))
            return
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            fail("minLength", "string shorter than %d" % schema["minLength"])
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            fail("pattern", "string does not match %s" % schema["pattern"])
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            fail("minimum", "value below minimum %s" % schema["minimum"])
        if "maximum" in schema and instance > schema["maximum"]:
            fail("maximum", "value above maximum %s" % schema["maximum"])
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            fail("minItems", "array needs at least %d item(s)"
                 % schema["minItems"])
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            fail("maxItems", "array allows at most %d item(s)"
                 % schema["maxItems"])
        if schema.get("uniqueItems"):
            seen = set()
            for item in instance:
                key = _canon(item)
                if key in seen:
                    fail("uniqueItems", "duplicate array item %s" % key)
                    break
                seen.add(key)
        if "items" in schema:
            for idx, item in enumerate(instance):
                _check_schema(item, schema["items"],
                              "%s/%d" % (pointer, idx), findings, root)
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        if "required" in schema:
            for name in schema["required"]:
                if name not in instance:
                    findings.append(_finding(
                        "K1", "REQUIRED_FIELD",
                        "%s/%s" % (pointer, name),
                        "required field is missing"))
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in props:
                    findings.append(_finding(
                        "K1", "UNKNOWN_KEY", "%s/%s" % (pointer, name),
                        "unknown key not permitted by the v1 contract"))
        elif isinstance(schema.get("additionalProperties"), dict):
            for name, value in instance.items():
                if name not in props:
                    _check_schema(value, schema["additionalProperties"],
                                  "%s/%s" % (pointer, name), findings, root)
        if "propertyNames" in schema:
            name_schema = schema["propertyNames"]
            for name in instance:
                if "pattern" in name_schema and \
                        not re.search(name_schema["pattern"], name):
                    findings.append(_finding(
                        "K1", "PROVENANCE_VALUE",
                        "%s/%s" % (pointer, name),
                        "property name does not match %s"
                        % name_schema["pattern"]))
        for name, sub in props.items():
            if name in instance:
                _check_schema(instance[name], sub,
                              "%s/%s" % (pointer, name), findings, root)
    if "allOf" in schema:
        for sub in schema["allOf"]:
            _check_schema(instance, sub, pointer, findings, root)
    if "if" in schema:
        trial = []
        _check_schema(instance, schema["if"], pointer, trial, root)
        if not trial and "then" in schema:
            _check_schema(instance, schema["then"], pointer, findings, root)
    if "oneOf" in schema:
        _check_oneof(instance, schema["oneOf"], pointer, findings, root)


def _branch_discriminator(branch):
    try:
        return branch["properties"]["invocation"]["properties"][
            "use_case_id"]["const"]
    except (KeyError, TypeError):
        return None


def _check_oneof(instance, branches, pointer, findings, root):
    disc = None
    if isinstance(instance, dict):
        disc = instance.get("invocation", {}).get("use_case_id") \
            if isinstance(instance.get("invocation"), dict) else None
    for branch in branches:
        if _branch_discriminator(branch) == disc and disc is not None:
            before = len(findings)
            _check_schema(instance, branch, pointer, findings, root)
            for f in findings[before:]:
                if f["code"] in ("UNKNOWN_KEY", "REQUIRED_FIELD") and \
                        f["field_id"].startswith("/use_case_profile"):
                    f["code"] = "PROFILE_KEY_SET"
            return
    matches = 0
    for branch in branches:
        trial = []
        _check_schema(instance, branch, pointer, trial, root)
        if not trial:
            matches += 1
    if matches != 1:
        findings.append(_finding(
            "K1", "PROFILE_KEY_SET", pointer or "/",
            "instance matches %d oneOf branches (exactly 1 required)"
            % matches))


def schema_vocabulary_violations(schema=None):
    """Return keywords outside SCHEMA_VOCABULARY (self-test support)."""
    schema = CONTRACT_SCHEMA if schema is None else schema
    bad = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("properties", "$defs"):
                    for sub in value.values():
                        walk(sub)
                    continue
                if key in ("items", "additionalProperties", "if", "then",
                           "propertyNames"):
                    walk(value)
                    if key not in SCHEMA_VOCABULARY:
                        bad.add(key)
                    continue
                if key in ("allOf", "oneOf"):
                    for sub in value:
                        walk(sub)
                    continue
                if key not in SCHEMA_VOCABULARY:
                    bad.add(key)
    walk(schema)
    return bad


# ---------------------------------------------------------------------------
# Derivation helpers shared with kickoff_io
# ---------------------------------------------------------------------------

def overlay13_active(control):
    inv = control.get("invocation", {})
    if not isinstance(inv, dict):
        return False
    return inv.get("use_case_id") == 8 or \
        bool(inv.get("layered_overlays"))


def expected_provenance_pointers(control):
    """The exact provenance-covered pointer set for this payload."""
    pointers = {
        "/workspace/dossier_root", "/workspace/dossier_root_scope",
        "/workspace/outside_workspace_write_approved",
        "/workspace/agent_access",
        "/invocation/use_case_id", "/invocation/layered_overlays",
        "/invocation/requirements_input_id",
        "/project/title", "/project/research_question",
        "/project/decision_context", "/project/time_horizon",
        "/project/audience", "/project/thesis",
        "/project/differentiation_hook", "/project/constraints",
        "/project/stakes", "/project/confidentiality",
        "/project/classified_inputs", "/project/ground_truth",
        "/project/topic_slug", "/project/allowed_verdicts",
        "/deliberation_modes",
        "/preferences/phase_1_venue", "/preferences/phase_3_venue",
        "/preferences/phase_5_route", "/preferences/expected_lanes",
        "/preferences/additional_renders",
        "/conduct/non_cancellable_phases", "/conduct/decorrelated_exception",
        "/standing_instructions", "/seed_areas", "/out_of_scope",
        "/known_traps",
    }
    inv = control.get("invocation", {})
    if isinstance(inv, dict) and inv.get("use_case_id") == 1:
        pointers.add("/invocation/spec_mode")
        pointers.add("/invocation/brownfield_repo")
    profile = control.get("use_case_profile")
    if isinstance(profile, dict):
        for key in profile:
            if key == "policy":
                continue
            pointers.add("/use_case_profile/%s" % key)
    return pointers


# ---------------------------------------------------------------------------
# The validator
# ---------------------------------------------------------------------------

class _Validator:
    def __init__(self, text, workspace_root, operation, brief_path=None):
        self.text = text
        self.workspace_root = workspace_root
        self.operation = operation
        self.brief_path = brief_path
        self.control = None
        self.findings = []
        self.gate_status = {g: "NOT_EVALUATED" for g in GATES}

    def add(self, gate, code, field_id, message, hint=""):
        self.findings.append(_finding(gate, code, field_id, message, hint))
        self.gate_status[gate] = "FAIL"

    def _mark(self, gate):
        if self.gate_status[gate] == "NOT_EVALUATED":
            self.gate_status[gate] = "PASS"

    # -- K1 ------------------------------------------------------------
    def k1_structure(self):
        block = extract_control_block(self.text)  # fatal on failure
        self.control = parse_control_json(block)  # fatal on failure

        before = len(self.findings)
        schema_findings = []
        _check_schema(self.control, CONTRACT_SCHEMA, "", schema_findings,
                      CONTRACT_SCHEMA)
        for f in schema_findings:
            self.findings.append(f)
        if schema_findings:
            self.gate_status["K1"] = "FAIL"

        # placeholder residue anywhere in the document
        for m in FIELD_PLACEHOLDER_RE.finditer(self.text):
            self.add("K1", "PLACEHOLDER_UNRESOLVED", None,
                     "unresolved template placeholder %s" % m.group(0),
                     hint="render the template through kickoff_io.py render")
            break
        # TBD/TODO/[INSERT ...] as whole string values in the payload
        for pointer, value in _string_leaves(self.control):
            trimmed = value.strip()
            if trimmed in ("TBD", "TODO") or \
                    INSERT_PLACEHOLDER_RE.match(trimmed):
                self.add("K1", "PLACEHOLDER_VALUE", pointer,
                         "placeholder value %r must be replaced" % trimmed)

        # required headings: presence, order, duplicates
        active = overlay13_active(self.control)
        standing = isinstance(self.control.get("standing_instructions"), str) \
            and self.control["standing_instructions"].strip() != ""
        guidance = any(self.control.get(k) for k in
                       ("seed_areas", "out_of_scope", "known_traps"))
        conditions = {"always": True, "overlay13_active": active,
                      "standing_nonempty": standing,
                      "guidance_nonempty": guidance}
        expected = [h for h, cond in REQUIRED_HEADINGS if conditions[cond]]
        seen = [t for level, t, _ in scan_headings(self.text) if level == 2]
        for heading in expected:
            title = heading[3:]
            count = seen.count(title)
            if count == 0:
                self.add("K1", "HEADING_MISSING", None,
                         "required section %r is missing" % heading)
            elif count > 1:
                self.add("K1", "HEADING_DUPLICATE", None,
                         "required section %r appears %d times"
                         % (heading, count))
        order = [t for t in seen if ("## " + t) in expected]
        expected_present = [h[3:] for h in expected
                            if seen.count(h[3:]) >= 1]
        dedup_order = []
        for t in order:
            if t not in dedup_order:
                dedup_order.append(t)
        if dedup_order != expected_present:
            self.add("K1", "HEADING_ORDER", None,
                     "required sections out of order: %s (expected %s)"
                     % (dedup_order, expected_present))

        # human/JSON parity
        self._parity()

        if len(self.findings) == before:
            self._mark("K1")

    def _section_text(self, title):
        """Body text of the ## section with the given title (or None)."""
        lines = self.text.split("\n")
        headings = scan_headings(self.text)
        start = None
        end = len(lines)
        for idx, (level, text, line_no) in enumerate(headings):
            if level == 2 and text == title:
                start = line_no
                for level2, _t2, line2 in headings[idx + 1:]:
                    if level2 <= 2:
                        end = line2 - 1
                        break
                break
        if start is None:
            return None
        return "\n".join(lines[start:end])

    def _fenced_payloads(self, section_text):
        """All fenced payloads inside a section, in order."""
        out = []
        fence_len = 0
        body = []
        for line in section_text.split("\n"):
            stripped = line.strip()
            if fence_len:
                if stripped == "`" * fence_len:
                    out.append("\n".join(body))
                    fence_len = 0
                    body = []
                else:
                    body.append(line)
                continue
            m = _FENCE_RE.match(stripped)
            if m:
                fence_len = len(m.group(1))
        return out

    def _parity_json(self, title, expected, field_id, index=0):
        section = self._section_text(title)
        if section is None:
            return  # heading findings already cover absence
        payloads = self._fenced_payloads(section)
        # The Kickoff-control section holds the control block itself; other
        # sections hold exactly the parity payloads.
        if len(payloads) <= index:
            self.add("K1", "HUMAN_JSON_MISMATCH", field_id,
                     "section %r lacks its fenced rendering" % title)
            return
        try:
            rendered = json.loads(payloads[index])
        except ValueError:
            self.add("K1", "HUMAN_JSON_MISMATCH", field_id,
                     "section %r fenced rendering is not valid JSON" % title)
            return
        if rendered != expected:
            self.add("K1", "HUMAN_JSON_MISMATCH", field_id,
                     "section %r disagrees with the control block" % title)

    def _parity(self):
        control = self.control
        headings = scan_headings(self.text)
        h1 = next((t for level, t, _ in headings if level == 1), None)
        title = control.get("project", {}).get("title") \
            if isinstance(control.get("project"), dict) else None
        if isinstance(title, str) and h1 is not None and \
                h1 != "Kickoff — %s" % title:
            self.add("K1", "HUMAN_JSON_MISMATCH", "/project/title",
                     "the top-level heading does not equal "
                     "'Kickoff — <title>'")
        if isinstance(control.get("workspace"), dict):
            self._parity_json("Workspace setup", control["workspace"],
                              "/workspace")
        if isinstance(control.get("invocation"), dict):
            self._parity_json("Invocation", control["invocation"],
                              "/invocation")
            if not overlay13_active(control):
                section = self._section_text("Invocation") or ""
                if "Deliberation modes: none" not in section:
                    self.add("K1", "HUMAN_JSON_MISMATCH",
                             "/deliberation_modes",
                             "Invocation section must state "
                             "'Deliberation modes: none' when overlay 13 "
                             "is inactive")
        if overlay13_active(control) and \
                isinstance(control.get("deliberation_modes"), list):
            self._parity_json("Deliberation modes",
                              control["deliberation_modes"],
                              "/deliberation_modes")
        if isinstance(control.get("project"), dict):
            self._parity_json("Phase 0 intake — pre-answered",
                              control["project"], "/project")
            slug = control["project"].get("topic_slug")
            section = self._section_text("Topic slug — pre-confirmed")
            if isinstance(slug, str) and section is not None:
                lines = [l.strip() for l in section.split("\n")
                         if l.strip()]
                if not lines or lines[0] != slug:
                    self.add("K1", "HUMAN_JSON_MISMATCH",
                             "/project/topic_slug",
                             "Topic slug section does not equal the "
                             "control value")
        if isinstance(control.get("use_case_profile"), dict):
            self._parity_json("Use-case profile",
                              control["use_case_profile"],
                              "/use_case_profile")
        if isinstance(control.get("preferences"), dict):
            self._parity_json("Phase-execution preferences",
                              control["preferences"], "/preferences")
            self._parity_json("Phase 6 deliverables",
                              control["preferences"].get(
                                  "additional_renders"),
                              "/preferences/additional_renders")
        if isinstance(control.get("conduct"), dict):
            self._parity_json("Conduct rules", control["conduct"],
                              "/conduct")
        standing = control.get("standing_instructions")
        if isinstance(standing, str) and standing.strip():
            section = self._section_text("Standing instructions")
            if section is not None:
                payloads = self._fenced_payloads(section)
                if not payloads or payloads[0] != standing:
                    self.add("K1", "HUMAN_JSON_MISMATCH",
                             "/standing_instructions",
                             "Standing instructions rendering disagrees "
                             "with the control block")
        if any(control.get(k) for k in ("seed_areas", "out_of_scope",
                                        "known_traps")):
            for idx, key in enumerate(("seed_areas", "out_of_scope",
                                       "known_traps")):
                if isinstance(control.get(key), list):
                    self._parity_json("Seed areas and known traps",
                                      control[key], "/" + key, index=idx)

    # -- K2 ------------------------------------------------------------
    def k2_core_intent(self):
        control = self.control
        project = control.get("project")
        ok = True
        if isinstance(project, dict):
            for key in ("title", "research_question", "decision_context",
                        "time_horizon", "audience"):
                value = project.get(key)
                if isinstance(value, str) and not value.strip():
                    self.add("K2", "REQUIRED_FIELD", "/project/%s" % key,
                             "field must be non-empty after trimming")
                    ok = False
            verdicts = project.get("allowed_verdicts")
            if isinstance(verdicts, list):
                if overlay13_active(control):
                    if len(verdicts) < 2:
                        self.add("K2", "VERDICTS_RULE",
                                 "/project/allowed_verdicts",
                                 "overlay-13-active work needs at least two "
                                 "unique allowed verdicts")
                        ok = False
                elif verdicts:
                    self.add("K2", "VERDICTS_RULE",
                             "/project/allowed_verdicts",
                             "allowed_verdicts must be empty when overlay 13 "
                             "is inactive")
                    ok = False
        provenance = control.get("provenance")
        if isinstance(provenance, dict):
            expected = expected_provenance_pointers(control)
            for pointer in sorted(expected - set(provenance)):
                self.add("K2", "PROVENANCE_MISSING", pointer,
                         "provenance entry missing for acquired field")
                ok = False
            for pointer in sorted(set(provenance) - expected):
                found, _value = json_pointer_get(control, pointer)
                if not found:
                    self.add("K2", "PROVENANCE_DANGLING", pointer,
                             "provenance pointer targets a missing value")
                else:
                    self.add("K2", "PROVENANCE_VALUE", pointer,
                             "unexpected provenance pointer (constants and "
                             "child pointers are not covered)")
                ok = False
        if ok:
            self._mark("K2")

    # -- K3 ------------------------------------------------------------
    def k3_invocation_profile(self):
        control = self.control
        inv = control.get("invocation", {})
        project = control.get("project", {})
        profile = control.get("use_case_profile", {})
        prefs = control.get("preferences", {})
        if not (isinstance(inv, dict) and isinstance(project, dict)
                and isinstance(profile, dict) and isinstance(prefs, dict)):
            self._mark("K3")
            return
        ok = True
        uc = inv.get("use_case_id")
        layered = inv.get("layered_overlays")
        if isinstance(layered, list) and layered == [OVERLAY_13] and \
                isinstance(uc, int) and uc not in LAYERABLE_USE_CASES:
            self.add("K3", "OVERLAY_ILLEGAL", "/invocation/layered_overlays",
                     "overlay 13 may only be layered on use cases 1-3 and "
                     "5-7 (never ebook; primary for use case 8)")
            ok = False

        req_id = inv.get("requirements_input_id")
        inputs = project.get("classified_inputs")
        input_ids = [i.get("input_id") for i in inputs
                     if isinstance(i, dict)] \
            if isinstance(inputs, list) else []
        if isinstance(req_id, str):
            if input_ids.count(req_id) != 1:
                self.add("K3", "REQUIREMENTS_REF",
                         "/invocation/requirements_input_id",
                         "requirements_input_id must reference exactly one "
                         "classified input")
                ok = False

        renders = prefs.get("additional_renders")
        if isinstance(renders, list) and isinstance(uc, int):
            allowed = set(ADDITIONAL_RENDERS_ALLOWED.get(uc, ()))
            primary = PRIMARY_RENDER_BY_USE_CASE.get(uc)
            for render in renders:
                if render == primary:
                    self.add("K3", "RENDER_MATRIX",
                             "/preferences/additional_renders",
                             "%r is already the primary render" % render)
                    ok = False
                elif render not in allowed:
                    self.add("K3", "RENDER_MATRIX",
                             "/preferences/additional_renders",
                             "%r is not an allowed additional render for "
                             "use case %s" % (render, uc),
                             hint="unsupported combinations need a separate "
                                  "kickoff")
                    ok = False

        if uc == 1:
            coverage = profile.get("requirements_coverage")
            users = profile.get("product_target_users")
            constraints = project.get("constraints")
            if req_id is None:
                if coverage is not None:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/requirements_coverage",
                             "coverage must be null without a requirements "
                             "input")
                    ok = False
                if isinstance(users, list) and not users:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/product_target_users",
                             "product target users must be non-empty without "
                             "a requirements input")
                    ok = False
            else:
                if not isinstance(coverage, dict):
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/requirements_coverage",
                             "with a requirements input the operator must "
                             "attest coverage per item")
                    ok = False
                else:
                    if coverage.get("product_target_users") is False and \
                            isinstance(users, list) and not users:
                        self.add("K3", "COVERAGE_RULE",
                                 "/use_case_profile/product_target_users",
                                 "uncovered item must be supplied at its "
                                 "canonical path")
                        ok = False
                    if coverage.get("constraints") is False and \
                            isinstance(constraints, list) and not constraints:
                        self.add("K3", "COVERAGE_RULE",
                                 "/project/constraints",
                                 "uncovered item must be supplied at its "
                                 "canonical path")
                        ok = False
        if uc == 3:
            for ref in profile.get("client_material_input_ids") or []:
                if isinstance(ref, str) and input_ids.count(ref) != 1:
                    self.add("K3", "REQUIREMENTS_REF",
                             "/use_case_profile/client_material_input_ids",
                             "client material id %r must reference exactly "
                             "one classified input" % ref)
                    ok = False
        if uc == 5:
            brief = profile.get("keyword_brief")
            if isinstance(brief, dict) and brief.get("status") == "provided":
                if profile.get("search_intent") is None:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/search_intent",
                             "a provided keyword brief requires a non-null "
                             "search intent")
                    ok = False
                if profile.get("target_word_count") is None:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/target_word_count",
                             "a provided keyword brief requires a target "
                             "word count")
                    ok = False
                hook = project.get("differentiation_hook")
                if not (isinstance(hook, str) and hook.strip()):
                    self.add("K3", "COVERAGE_RULE",
                             "/project/differentiation_hook",
                             "a provided keyword brief requires a non-empty "
                             "differentiation hook")
                    ok = False
                secondary = profile.get("secondary_keywords")
                if isinstance(secondary, list) and \
                        not 3 <= len(secondary) <= 5:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/secondary_keywords",
                             "a provided keyword brief requires 3-5 unique "
                             "secondary keywords")
                    ok = False
                brief_input = brief.get("input_id")
                if isinstance(brief_input, str) and \
                        input_ids.count(brief_input) != 1:
                    self.add("K3", "REQUIREMENTS_REF",
                             "/use_case_profile/keyword_brief/input_id",
                             "keyword-brief input id must reference exactly "
                             "one classified input")
                    ok = False
                target = profile.get("target_word_count")
                avg = brief.get("serp_average_word_count")
                if isinstance(target, int) and isinstance(avg, int) and \
                        target < avg:
                    self.add("K3", "COVERAGE_RULE",
                             "/use_case_profile/target_word_count",
                             "target word count must be >= the SERP average")
                    ok = False
        if uc == 6:
            profile_policy = profile.get("policy")
            if profile_policy != HEALTH_POLICY:
                self.add("K3", "HEALTH_INVARIANT",
                         "/use_case_profile/policy",
                         "health policy constant drifted from the contract")
                ok = False
        if ok:
            self._mark("K3")

    # -- K4 ------------------------------------------------------------
    def k4_modes(self):
        control = self.control
        modes = control.get("deliberation_modes")
        if not isinstance(modes, list):
            self._mark("K4")
            return
        ok = True
        if modes and not overlay13_active(control):
            self.add("K4", "MODE_ILLEGAL", "/deliberation_modes",
                     "deliberation modes are legal only when overlay 13 is "
                     "active (use case 8 or legal layering)")
            ok = False
        if ok:
            self._mark("K4")

    # -- K5 ------------------------------------------------------------
    def k5_readiness(self):
        control = self.control
        workspace = control.get("workspace", {})
        access = workspace.get("agent_access") \
            if isinstance(workspace, dict) else None
        prefs = control.get("preferences", {})
        lanes = prefs.get("expected_lanes") \
            if isinstance(prefs, dict) else None
        if not (isinstance(access, dict) and isinstance(lanes, list)):
            self._mark("K5")
            return
        ok = True
        project = control.get("project", {})
        profile = control.get("use_case_profile", {})
        inv = control.get("invocation", {})
        uc = inv.get("use_case_id") if isinstance(inv, dict) else None
        confidential = isinstance(project, dict) and \
            project.get("confidentiality") == "confidential"
        modes = control.get("deliberation_modes") or []

        # access entries: route order + tier hygiene
        for agent, entry in access.items():
            if not isinstance(entry, dict) or agent not in ROUTES_BY_AGENT:
                continue
            routes = entry.get("routes")
            enum = ROUTES_BY_AGENT[agent]
            if isinstance(routes, list):
                order = [r for r in enum if r in routes]
                if [r for r in routes if r in enum] != order:
                    self.add("K5", "ACCESS_ENTRY_SHAPE",
                             "/workspace/agent_access/%s/routes" % agent,
                             "routes must be serialized in enum order %s"
                             % list(enum))
                    ok = False
            tier = entry.get("tier")
            if isinstance(tier, str) and not tier.strip():
                self.add("K5", "ACCESS_ENTRY_SHAPE",
                         "/workspace/agent_access/%s/tier" % agent,
                         "tier must be a trimmed non-empty string or null")
                ok = False

        # expected lanes: uniqueness, order, roles, routes
        agents = [l.get("agent") for l in lanes if isinstance(l, dict)]
        if len(agents) != len(set(agents)):
            self.add("K5", "LANE_COUNT", "/preferences/expected_lanes",
                     "expected lanes must name unique agents")
            ok = False
        order = [a for a in AGENT_IDS if a in agents]
        if [a for a in agents if a in AGENT_IDS] != order:
            self.add("K5", "LANE_COUNT", "/preferences/expected_lanes",
                     "expected lanes must be serialized in canonical "
                     "inventory order")
            ok = False
        runnable = []
        for idx, lane in enumerate(lanes):
            if not isinstance(lane, dict):
                continue
            agent = lane.get("agent")
            route = lane.get("route")
            role = lane.get("role")
            pointer = "/preferences/expected_lanes/%d" % idx
            if agent in ROUTES_BY_AGENT and \
                    route not in ROUTES_BY_AGENT[agent]:
                self.add("K5", "LANE_NOT_RUNNABLE", pointer,
                         "route %r is not a legal route for %s"
                         % (route, agent))
                ok = False
                continue
            if (role == "decorrelated") != (agent == "deepseek"):
                self.add("K5", "ROLE_VIOLATION", pointer,
                         "role 'decorrelated' is legal for deepseek and "
                         "only deepseek")
                ok = False
            entry = access.get(agent)
            lane_runnable = isinstance(entry, dict) and \
                entry.get("status") == "available" and \
                isinstance(entry.get("routes"), list) and \
                route in entry["routes"]
            if agent == "deepseek" and confidential and \
                    route == "consumer_web":
                self.add("K5", "DEEPSEEK_ROUTE", pointer,
                         "confidential work may not select the consumer "
                         "DeepSeek route",
                         hint="select western_hosted_api or self_hosted")
                ok = False
                lane_runnable = False
            if lane_runnable:
                runnable.append(lane)
            else:
                self.add("K5", "LANE_NOT_RUNNABLE", pointer,
                         "expected lane %s/%s is not runnable with the "
                         "recorded access" % (agent, route))
                ok = False

        if len(runnable) < 3:
            self.add("K5", "LANE_COUNT", "/preferences/expected_lanes",
                     "at least three distinct runnable lanes are required "
                     "(%d runnable)" % len(runnable))
            ok = False
        evidence = [l for l in runnable
                    if l.get("role") in ("evidence", "decorrelated")]
        if len(evidence) < 2:
            self.add("K5", "LANE_COUNT", "/preferences/expected_lanes",
                     "at least two runnable lanes must carry role "
                     "evidence or decorrelated")
            ok = False

        claude_entry = access.get("claude")
        claude_ok = isinstance(claude_entry, dict) and \
            claude_entry.get("status") == "available" and \
            "claude_web_extended_thinking" in \
            (claude_entry.get("routes") or [])
        if not claude_ok:
            self.add("K5", "CLAUDE_SURFACE",
                     "/workspace/agent_access/claude",
                     "Claude must be available with the "
                     "claude_web_extended_thinking route (local alone does "
                     "not satisfy the v1 preflight)")
            ok = False

        # decorrelated lane / exception
        exception = control.get("conduct", {}).get("decorrelated_exception") \
            if isinstance(control.get("conduct"), dict) else None
        deepseek_lane = any(l.get("agent") == "deepseek" for l in lanes
                            if isinstance(l, dict))
        deepseek_entry = access.get("deepseek")
        compliant_routes = ("self_hosted", "western_hosted_api") \
            if confidential else ROUTES_BY_AGENT["deepseek"]
        compliant_available = isinstance(deepseek_entry, dict) and \
            deepseek_entry.get("status") == "available" and \
            any(r in (deepseek_entry.get("routes") or [])
                for r in compliant_routes)
        if exception is None:
            if not deepseek_lane:
                self.add("K5", "LANE_COUNT", "/preferences/expected_lanes",
                         "a decorrelated (deepseek) expected lane is "
                         "required unless conduct.decorrelated_exception "
                         "is recorded")
                ok = False
        else:
            if "debate" in modes or "red-team" in modes:
                self.add("K5", "EXCEPTION_INVALID",
                         "/conduct/decorrelated_exception",
                         "the decorrelated exception is invalid when Debate "
                         "or Red Team is selected")
                ok = False
            if deepseek_lane:
                self.add("K5", "EXCEPTION_INVALID",
                         "/conduct/decorrelated_exception",
                         "the exception is invalid while expected_lanes "
                         "still contains deepseek")
                ok = False
            if compliant_available:
                self.add("K5", "EXCEPTION_INVALID",
                         "/conduct/decorrelated_exception",
                         "the exception is invalid while a compliant "
                         "runnable DeepSeek route exists")
                ok = False

        def lane_runnable_for(agent):
            for lane in runnable:
                if lane.get("agent") == agent:
                    return True
            return False

        if uc == 3 and isinstance(profile, dict) and \
                profile.get("client_pitch") is True and \
                not lane_runnable_for("notebooklm"):
            self.add("K5", "PROVIDER_MISSING",
                     "/preferences/expected_lanes",
                     "a client-pitch presentation requires NotebookLM as a "
                     "runnable expected lane")
            ok = False

        def provider_web_available(agent):
            entry = access.get(agent)
            return isinstance(entry, dict) and \
                entry.get("status") == "available" and \
                "web" in (entry.get("routes") or [])

        if uc == 5 and isinstance(profile, dict):
            brief = profile.get("keyword_brief")
            if isinstance(brief, dict) and brief.get("status") == "pending":
                provider = brief.get("serp_provider")
                if provider in ("perplexity", "grok") and \
                        not provider_web_available(provider):
                    self.add("K5", "PROVIDER_MISSING",
                             "/use_case_profile/keyword_brief/serp_provider",
                             "the selected SERP provider must be available "
                             "with normal web mode")
                    ok = False
        renders = prefs.get("additional_renders") or []
        if "wordpress_article" in renders and \
                not (provider_web_available("perplexity")
                     or provider_web_available("grok")):
            self.add("K5", "PROVIDER_MISSING",
                     "/preferences/additional_renders",
                     "an additional wordpress_article render requires "
                     "Perplexity or Grok available with normal web mode")
            ok = False
        if uc == 6:
            for agent in ("notebooklm", "elicit", "consensus"):
                if not lane_runnable_for(agent):
                    self.add("K5", "PROVIDER_MISSING",
                             "/preferences/expected_lanes",
                             "health work requires %s as a runnable "
                             "expected lane" % agent)
                    ok = False
            scite = access.get("scite")
            if not (isinstance(scite, dict)
                    and scite.get("status") == "available"
                    and (scite.get("routes") or [])):
                self.add("K5", "PROVIDER_MISSING",
                         "/workspace/agent_access/scite",
                         "health work requires Scite available with a "
                         "selected web|api route (Phase-4 verification "
                         "readiness)")
                ok = False
        if ok:
            self._mark("K5")

    # -- K6 ------------------------------------------------------------
    def k6_inputs_paths(self):
        control = self.control
        project = control.get("project", {})
        inv = control.get("invocation", {})
        workspace = control.get("workspace", {})
        ok = True
        inputs = project.get("classified_inputs") \
            if isinstance(project, dict) else None
        if isinstance(inputs, list):
            seen = set()
            for idx, item in enumerate(inputs):
                if not isinstance(item, dict):
                    continue
                pointer = "/project/classified_inputs/%d" % idx
                input_id = item.get("input_id")
                if input_id in seen:
                    self.add("K6", "TRUST_RULE", pointer + "/input_id",
                             "duplicate input_id %r" % input_id)
                    ok = False
                seen.add(input_id)
                path = item.get("path")
                if isinstance(path, str) and CONTROL_CHAR_RE.search(path):
                    self.add("K6", "CONTROL_CHARS", pointer + "/path",
                             "input path contains control characters")
                    ok = False
        for pointer, value in (
                ("/workspace/dossier_root",
                 workspace.get("dossier_root")
                 if isinstance(workspace, dict) else None),
                ("/invocation/brownfield_repo",
                 inv.get("brownfield_repo")
                 if isinstance(inv, dict) else None)):
            if isinstance(value, str) and CONTROL_CHAR_RE.search(value):
                self.add("K6", "CONTROL_CHARS", pointer,
                         "path contains control characters")
                ok = False
        if isinstance(inv, dict) and inv.get("spec_mode") == "brownfield":
            repo = inv.get("brownfield_repo")
            if not (isinstance(repo, str) and repo.strip()):
                self.add("K6", "BROWNFIELD_REPO",
                         "/invocation/brownfield_repo",
                         "brownfield requires a repository path")
                ok = False
        if ok:
            self._mark("K6")

    # -- K7 ------------------------------------------------------------
    def k7_ground_truth_privacy(self):
        control = self.control
        project = control.get("project", {})
        ok = True
        claims = project.get("ground_truth") \
            if isinstance(project, dict) else None
        if isinstance(claims, list):
            seen = set()
            for idx, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    continue
                pointer = "/project/ground_truth/%d" % idx
                claim_id = claim.get("claim_id")
                if claim_id in seen:
                    self.add("K7", "GT_SHAPE", pointer + "/claim_id",
                             "duplicate claim_id %r" % claim_id)
                    ok = False
                seen.add(claim_id)
                source = claim.get("source")
                if isinstance(source, str):
                    if source.startswith("https://"):
                        if not self._check_https(source,
                                                 pointer + "/source"):
                            ok = False
                    elif OPERATOR_SOURCE_RE.match(source):
                        pass
                    else:
                        self.add("K7", "OPERATOR_MARKER",
                                 pointer + "/source",
                                 "source must be an https:// URL or an "
                                 "operator-<slug> provenance marker")
                        ok = False
        for pointer, value in _string_leaves(control):
            for label, pattern in SECRET_RES:
                if pattern.search(value):
                    self.add("K7", "SECRET_LIKE", pointer,
                             "likely secret value (%s) must never be "
                             "serialized in a kickoff" % label)
                    ok = False
                    break
        if ok:
            self._mark("K7")

    def _check_https(self, url, pointer):
        try:
            parts = urlsplit(url)
        except ValueError:
            self.add("K7", "OPERATOR_MARKER", pointer, "unparsable URL")
            return False
        if parts.username is not None or parts.password is not None or \
                "@" in parts.netloc:
            self.add("K7", "URL_USERINFO", pointer,
                     "https URL must not carry userinfo")
            return False
        host = parts.hostname or ""
        bad_suffixes = (".local", ".internal", ".localhost")
        if host == "localhost" or host.endswith(bad_suffixes):
            self.add("K7", "URL_PRIVATE_HOST", pointer,
                     "URL host resolves to a local/private namespace",
                     hint="use an operator provenance marker for private "
                          "evidence")
            return False
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            return True
        if addr.is_private or addr.is_loopback or addr.is_link_local or \
                addr.is_reserved or addr.is_multicast or addr.is_unspecified:
            self.add("K7", "URL_PRIVATE_HOST", pointer,
                     "URL host is a private/link-local address",
                     hint="use an operator provenance marker for private "
                          "evidence")
            return False
        return True

    # -- K8 ------------------------------------------------------------
    def k8_slug_output_safety(self):
        control = self.control
        project = control.get("project", {})
        workspace = control.get("workspace", {})
        if not (isinstance(project, dict) and isinstance(workspace, dict)):
            self._mark("K8")
            return
        ok = True
        slug = project.get("topic_slug")
        if isinstance(slug, str):
            if not SLUG_RE.match(slug):
                self.add("K8", "SLUG_INVALID", "/project/topic_slug",
                         "slug must match "
                         "^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$")
                ok = False
            else:
                segments = [slug] + slug.split("-")
                for segment in segments:
                    if segment.casefold() in WINDOWS_RESERVED:
                        self.add("K8", "RESERVED_NAME",
                                 "/project/topic_slug",
                                 "slug (or a hyphen segment) is a reserved "
                                 "Windows device name: %r" % segment)
                        ok = False
                        break

        root = workspace.get("dossier_root")
        scope = workspace.get("dossier_root_scope")
        approved = workspace.get("outside_workspace_write_approved")
        if not (isinstance(root, str) and root and isinstance(slug, str)
                and slug and isinstance(scope, str)):
            if not ok:
                return
            self._mark("K8")
            return
        if os.path.isabs(root):
            base = root
        else:
            base = os.path.join(self.workspace_root, root)
        target_dir = os.path.join(base, slug)
        resolved_parent = _resolve(base if not os.path.isdir(target_dir)
                                   else target_dir)
        inside = _is_within(base, self.workspace_root) and \
            _is_within(resolved_parent, self.workspace_root)

        actual_scope = None
        if inside:
            actual_scope = "workspace_relative" if not os.path.isabs(root) \
                else "absolute_inside_workspace"
        else:
            actual_scope = "outside_workspace"
        if scope != actual_scope:
            self.add("K8", "SCOPE_MISMATCH", "/workspace/dossier_root_scope",
                     "declared scope %r but the path resolves as %r "
                     "(relative traversal or symlink escapes count as "
                     "outside_workspace)" % (scope, actual_scope))
            ok = False
        if actual_scope == "outside_workspace" and approved is not True:
            self.add("K8", "OUTSIDE_UNAPPROVED",
                     "/workspace/outside_workspace_write_approved",
                     "an outside-workspace target requires explicit "
                     "recorded approval")
            ok = False
        if actual_scope != "outside_workspace" and approved is not False:
            self.add("K8", "OUTSIDE_UNAPPROVED",
                     "/workspace/outside_workspace_write_approved",
                     "approval must be false for inside-workspace scopes")
            ok = False
        if _is_within(target_dir, _plugin_root()):
            self.add("K8", "PLUGIN_TREE_TARGET", "/workspace/dossier_root",
                     "the dossier target may never sit inside the plugin "
                     "source/cache tree")
            ok = False

        final_path = os.path.join(target_dir, "00-kickoff.md")
        context_path = os.path.join(target_dir, "00-context.md")
        if self.operation == "build":
            if self.brief_path is not None:
                if os.path.basename(self.brief_path) != \
                        "00-kickoff.draft.md":
                    self.add("K8", "CANDIDATE_NAME", None,
                             "a build candidate must be named "
                             "00-kickoff.draft.md")
                    ok = False
                elif not _same_dir(self.brief_path, target_dir):
                    self.add("K8", "CANDIDATE_NAME", None,
                             "the build candidate must sit in the derived "
                             "dossier directory")
                    ok = False
            if _exists_nocase(final_path):
                self.add("K8", "COLLISION_FINAL_EXISTS", None,
                         "00-kickoff.md already exists at the target",
                         hint="offer refine / a new slug / cancel")
                ok = False
            if _exists_nocase(context_path):
                self.add("K8", "COLLISION_CONTEXT_EXISTS", None,
                         "00-context.md already exists at the target",
                         hint="offer a new slug or cancel; v1 has no "
                              "adoption workflow for a context-only dossier")
                ok = False
        elif self.operation == "refine":
            if self.brief_path is not None:
                if os.path.basename(self.brief_path) != "00-kickoff.v2.md":
                    self.add("K8", "CANDIDATE_NAME", None,
                             "a refine candidate must be named "
                             "00-kickoff.v2.md")
                    ok = False
                elif not _same_dir(self.brief_path, target_dir):
                    self.add("K8", "CANDIDATE_NAME", None,
                             "the refine candidate must sit beside the "
                             "existing final brief")
                    ok = False
            if not _exists_nocase(final_path):
                self.add("K8", "REFINE_TARGET_MISSING", None,
                         "refine requires an existing 00-kickoff.md at the "
                         "derived target")
                ok = False
        if ok:
            self._mark("K8")

    # ------------------------------------------------------------------
    def run_gates(self):
        self.k1_structure()
        self.k2_core_intent()
        self.k3_invocation_profile()
        self.k4_modes()
        self.k5_readiness()
        self.k6_inputs_paths()
        self.k7_ground_truth_privacy()
        self.k8_slug_output_safety()


def _same_dir(path, directory):
    return _resolve(os.path.dirname(os.path.abspath(path))) == \
        _resolve(directory)


def _exists_nocase(path):
    """Existence check honouring Windows case-insensitivity on every
    platform (case variants of the artifact names count as collisions)."""
    directory = os.path.dirname(path)
    name = os.path.basename(path).casefold()
    try:
        entries = os.listdir(directory)
    except OSError:
        return False
    return any(entry.casefold() == name for entry in entries)


def _string_leaves(node, pointer=""):
    if isinstance(node, str):
        yield pointer or "/", node
    elif isinstance(node, dict):
        for key, value in node.items():
            token = key.replace("~", "~0").replace("/", "~1")
            yield from _string_leaves(value, "%s/%s" % (pointer, token))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from _string_leaves(value, "%s/%d" % (pointer, idx))


# ---------------------------------------------------------------------------
# Report / entry points
# ---------------------------------------------------------------------------

def _report(result, gate_status, findings):
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "result": result,
        "gates": {g: gate_status.get(g, "NOT_EVALUATED") for g in GATES},
        "failed_gates": [g for g in GATES
                         if gate_status.get(g) == "FAIL"],
        "findings": findings,
    }


def error_report(message, code, gate="K1", field_id=None,
                 evaluated_k1=False):
    gates = {g: "NOT_EVALUATED" for g in GATES}
    if evaluated_k1:
        gates["K1"] = "FAIL"
    return _report("error", gates,
                   [_finding(gate, code, field_id, message)])


def validate_document(text, workspace_root, operation, brief_path=None):
    validator = _Validator(text, workspace_root, operation, brief_path)
    try:
        validator.run_gates()
    except DocumentError as exc:
        return error_report(str(exc), exc.code, gate=exc.gate,
                            field_id=exc.field_id,
                            evaluated_k1=exc.gate == "K1")
    result = "pass" if all(v == "PASS"
                           for v in validator.gate_status.values()) \
        else "fail"
    return _report(result, validator.gate_status, validator.findings)


def run(brief_path, workspace_root, operation):
    try:
        text = _read_text(brief_path)
    except DocumentError as exc:
        return error_report(str(exc), exc.code, gate=exc.gate,
                            field_id=exc.field_id)
    return validate_document(text, workspace_root, operation,
                             brief_path=brief_path)


def render_human(report):
    lines = []
    for gate in GATES:
        lines.append("%s  %s" % (gate, report["gates"][gate]))
    for finding in report["findings"]:
        prefix = finding["gate"] or "-"
        field = finding["field_id"] or "-"
        lines.append("FINDING [%s] %s %s: %s"
                     % (prefix, finding["code"], field, finding["message"]))
        if finding.get("hint"):
            lines.append("  hint: %s" % finding["hint"])
    lines.append("RESULT: %s" % report["result"].upper())
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="validate_kickoff.py",
        description="Validate a kickoff brief against the v1 contract "
                    "(gates K1-K8).")
    parser.add_argument("document", help="path to the kickoff brief")
    parser.add_argument("--workspace-root", required=True,
                        help="the already-resolved granted workspace root")
    parser.add_argument("--operation", default="validate",
                        choices=["build", "refine", "validate"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            report = error_report("usage error", "USAGE", gate=None)
            print(json.dumps(report, ensure_ascii=False))
            return 2
        return 0
    try:
        report = run(args.document, args.workspace_root, args.operation)
    except DocumentError as exc:
        report = error_report(str(exc), exc.code, gate=exc.gate,
                              field_id=exc.field_id)
    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_human(report))
    if report["result"] == "error":
        return 2
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

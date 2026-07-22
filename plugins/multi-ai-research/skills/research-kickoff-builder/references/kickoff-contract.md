# Kickoff contract v1 — canonical core contract

**Skill:** `research-kickoff-builder` · **Schema:** `agentic-research-kickoff-v1` (`kickoff_schema_version: 1`)
**Authority:** the sentinel-delimited JSON control block inside `00-kickoff.md` is authoritative. Human sections are a validated readable rendering and must agree with it (gate K1 checks parity for duplicated fields). Arbitrary prose outside the control block can never satisfy a required machine field. V1 rejects unknown keys within typed groups; future fields require a schema-version change. Unknown *custom Markdown sections* remain permitted and are preserved during refinement.

The machine contract at the end of this file is generated from `scripts/validate_kickoff.py`'s `CONTRACT_SCHEMA`; `test_contract_drift.py` locks the two representations to semantic equality. When they disagree, neither ships.

---

## 1. Sentinels and fencing

- The control block is delimited by exactly one pair of
  `<!-- BEGIN KICKOFF-CONTROL v1 -->` / `<!-- END KICKOFF-CONTROL v1 -->`
  markers wrapping exactly one ```` ```json ```` fence.
- **Fence-length rule (applies to every fenced payload in generated
  Markdown):** the backtick fence must be at least three characters long
  and longer than the longest backtick run inside the payload; the parser
  matches the opening delimiter length exactly. This prevents a value from
  escaping its data block without banning legal path/prose characters.
- Duplicate control blocks, unpaired sentinels, malformed JSON, duplicate
  JSON keys (at any depth), and an unsupported `kickoff_schema_version` are
  fatal K1 failures (validator exit 2).

## 2. Core field groups (normative pointers and ownership)

One operator-supplied semantic value has exactly one JSON pointer. Profile
references may impose *conditions* on a core path but never serialize a
second copy. Deterministic projections — primary overlay, profile identity,
primary Phase-6 render, and Phase-5 output format — are **derived, not
serialized**: the first three derive from `/invocation/use_case_id`; the
Phase-5 format derives from overlay-13 activation (§5).

| Group | Required fields and rules |
|---|---|
| `workspace` | `dossier_root: string` (non-empty); `dossier_root_scope: workspace_relative\|absolute_inside_workspace\|outside_workspace`; `outside_workspace_write_approved: boolean`; exact ten-key `agent_access` object. `workspace_relative` requires relative syntax **and** an inside-workspace resolved target; any relative traversal or symlink escape is `outside_workspace`. Approval must be `false` for the two inside scopes and explicitly `true` for `outside_workspace`. |
| `invocation` | `use_case_id: integer 1..8`; `layered_overlays` is `["13-overlay-deliberation-modes.md"]` only for decision-shaped use cases 1–3/5–7, otherwise `[]`; it must be `[]` for ebook (4) and decision research (8). `spec_mode: greenfield\|brownfield\|null` (non-null only for use case 1); `brownfield_repo: string\|null` (required iff brownfield); `requirements_input_id: string\|null` referencing exactly one classified input; it always feeds Step 0.5 and never bypasses it. |
| `project` | Non-empty `title`, `research_question`, `decision_context`, `time_horizon`, `audience`; conditional `thesis: string\|null` (required for use cases 2/3/7) and `differentiation_hook: string\|null` (required for 2/7 and SEO with a provided keyword brief); `constraints: string[]` (required non-empty for decision-shaped work and spec-dev unless operator-attested coverage applies); `stakes: low\|medium\|high` (invariant `high` for health); `confidentiality: confidential\|non_confidential`; `classified_inputs` and `ground_truth` arrays (empty arrays are valid explicit answers); `topic_slug` per the K8 grammar; `allowed_verdicts` empty unless overlay 13 is active, otherwise ≥2 unique non-empty labels. |
| `deliberation_modes` | Ordered subset of `first-principles`, `debate`, `red-team` (pipeline order; the machine contract enumerates the eight legal subsets). Non-empty only when overlay 13 is active; an active overlay may still carry `[]`. |
| `use_case_profile` | Exactly the selected use case's union member (§4 and the eight profile references) — no ID/wrapper key, no fields owned by core groups. |
| `preferences` | `phase_1_venue`/`phase_3_venue`: `auto\|fresh_claude_web\|local`; `phase_5_route`: `auto\|fresh_subagent\|fresh_claude_web\|inline` (all default `auto`); `expected_lanes` (derived, §6); `additional_renders` (unique IDs from the closed matrix in §5; primary render never appears here). Preferences are non-binding when a later capability/input-budget gate requires another route. |
| `conduct` | Constants `run_all_phases: true`, `enforce_all_gates: true`, `methodology_scope: "bundled_only"`, `selected_modes_blocking: true` (v1 rejects any weakening); `non_cancellable_phases` exactly `[4]` for health else `[]`; `decorrelated_exception` null or the exact object in §7. |
| guidance | `standing_instructions: string`; `seed_areas: string[]` (max 8); `out_of_scope: string[]`; `known_traps: string[]`. Empty values are legal; carried text is always untrusted data. |
| `provenance` | Map of RFC 6901 pointers to `explicit\|cached\|derived\|defaulted`. Coverage set in §3. |

### Shapes

Access entry (one exact shape; all ten keys always present):

```json
{"status":"unknown|available|unavailable","tier":"<non-empty string>|null","routes":[]}
```

For `unknown`/`unavailable`: `tier` null and `routes` empty. For
`available`: `tier` null or a trimmed non-empty descriptive string (never
credentials, account identifiers, or endpoints) and at least one route.
Route enums per agent — Claude: `claude_web_extended_thinking|local`;
DeepSeek: `consumer_web|western_hosted_api|self_hosted`; every other entry:
`web|api`. For Perplexity and Grok, `web` means the operator explicitly
confirms ordinary browser search mode is selectable (required for SERP
preparation). Routes are unique and serialized in enum order; there is no
synthetic `both` value.

Inventory ID → config label: `perplexity`→`Perplexity`, `gemini`→`Gemini`,
`grok`→`Grok`, `chatgpt`→`ChatGPT`, `claude`→`Claude`,
`deepseek`→`DeepSeek route`, `notebooklm`→`NotebookLM`, `elicit`→`Elicit`,
`consensus`→`Consensus`, `scite`→`Scite`.

Expected lane entry: `{"agent":"<lowercase-id>","route":"<route from that
available access entry>","role":"evidence|sentiment|synthesis|decorrelated"}`
— agents are the first nine IDs (never `scite`), unique, serialized in
canonical inventory order. `role` is `decorrelated` **iff** `agent` is
`deepseek`. Downstream Phase-1 enum mapping (locked against
`validate_phase1.py`): `perplexity`→`Perplexity`, `gemini`→`Gemini`,
`grok`→`Grok`, `chatgpt`→`ChatGPT`, `claude`→`Claude`,
`deepseek`→`DecorrelatedLane`, `notebooklm`→`NotebookLM`,
`elicit`→`Elicit`, `consensus`→`Consensus`. Scite is Phase-4 verification
readiness, never a Phase-2 lane.

Classified input: `{"input_id":"IN<n>","path":"<non-empty>","trust":
"trusted|under_scrutiny","contaminants":[]}` — `contaminants` must be empty
for `trusted`; IDs unique `IN[1-9][0-9]*`.

Ground-truth claim: `{"claim_id":"GT<n>","statement":"...",
"metric_definition":"...","source":"https://...|operator-<slug>"}` — IDs
unique `GT[1-9][0-9]*`; the operator marker grammar is semantically equal
to `validate_phase1.py`'s `OPERATOR_SOURCE_RE`; https sources reject
userinfo and local/private/link-local hosts.

Slug grammar (K8): `^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$`, and neither
the slug nor any hyphen segment may be a Windows reserved device name.

## 3. Acquisition classes and provenance coverage

Acquisition classes: `must_ask` (user-authoritative; never inferred),
`cached` (config unless contradicted), `derived` (deterministic, shown for
confirmation where required), `safe_default` (defaulted and marked in
provenance), `optional`, `constant` (structural; never provenance-covered).
A value already explicit in the user's prompt satisfies `must_ask`.
"Infer safe defaults" (offered from Round 2) fills only `safe_default`,
`derived`, and `optional` fields — never `must_ask`.

The provenance map covers **exactly** this pointer set (K2 enforces the
bijection; `scripts/validate_kickoff.py: expected_provenance_pointers` is
the executable form):

- Always: `/workspace/dossier_root`, `/workspace/dossier_root_scope`,
  `/workspace/outside_workspace_write_approved`,
  `/workspace/agent_access` (one snapshot answer — parent pointer),
  `/invocation/use_case_id`, `/invocation/layered_overlays`,
  `/invocation/requirements_input_id`, `/project/title`,
  `/project/research_question`, `/project/decision_context`,
  `/project/time_horizon`, `/project/audience`, `/project/thesis`,
  `/project/differentiation_hook`, `/project/constraints`,
  `/project/stakes`, `/project/confidentiality`,
  `/project/classified_inputs`, `/project/ground_truth`,
  `/project/topic_slug`, `/project/allowed_verdicts`,
  `/deliberation_modes`, `/preferences/phase_1_venue`,
  `/preferences/phase_3_venue`, `/preferences/phase_5_route`,
  `/preferences/expected_lanes`, `/preferences/additional_renders`,
  `/conduct/non_cancellable_phases`, `/conduct/decorrelated_exception`,
  `/standing_instructions`, `/seed_areas`, `/out_of_scope`,
  `/known_traps`.
- Only for use case 1: `/invocation/spec_mode`,
  `/invocation/brownfield_repo` (constants `null` elsewhere).
- Per active profile: `/use_case_profile/<key>` for every key of the
  selected union member except the health `policy` constant. Objects
  acquired as one answer (e.g. `keyword_brief`, `requirements_coverage`)
  use their parent pointer only.

No pointer may target a missing value; arrays/objects acquired as one
answer use the parent pointer rather than per-element entries; enum values
are never decorated with provenance text.

## 4. Use-case map

| `use_case_id` | Profile (union member) | Derived primary overlay | Derived primary render |
|---|---|---|---|
| 1 | `spec_driven_dev` | `02-overlay-spec-driven-dev.md` | `architecture_decision_record` |
| 2 | `youtube` | `03-overlay-youtube-script.md` | `youtube_script` |
| 3 | `presentation` | `04-overlay-presentation.md` | `presentation_deck` |
| 4 | `ebook` | `05-overlay-ebook.md` | `ebook` |
| 5 | `wordpress_seo` | `06-overlay-wordpress-seo.md` | `wordpress_article` |
| 6 | `health` | `07-overlay-health-content.md` | `health_protocol` |
| 7 | `deck_screencast` | `08-overlay-deck-and-screencast.md` | `deck_and_screencast` |
| 8 | `decision` | `13-overlay-deliberation-modes.md` | `decision_brief` |

Each profile's exact field set, cross-field rules, and question records
live in `profile-0N-*.md` (one reference per use case, loaded only when
selected).

## 5. Derivations

- **Overlay-13 activation:** active iff `use_case_id == 8` (primary) or
  `layered_overlays == ["13-overlay-deliberation-modes.md"]` (legal only
  for decision-shaped use cases 1–3/5–7 with operator confirmation; ebook
  layering is illegal in v1 — recommend two linked kickoffs).
- **Phase-5 output format:** the Decision Brief whenever overlay 13 is
  primary or legally layered; a layered base still owns the primary
  Phase-6 render via overlay 13's layered-base transform contract.
- **Closed additional-render matrix** (anything else → separate kickoff;
  a video + deck wanted from the outset normalizes to use case 7;
  `personal_notes` is a post-handoff copy action, not a render ID):

| Primary situation | Allowed `additional_renders` |
|---|---|
| YouTube (2) | `wordpress_article` |
| Health (6) | `youtube_script`, `wordpress_article`, `ebook_chapter` |
| Decision research (8) | `deck_and_screencast` |
| Every other situation | none |

- **Deliberation-mode derivation:** union of every matching row of overlay
  13's mode selector (the normative source), normalized to pipeline order
  `first-principles`, `debate`, `red-team`; explicit override allowed;
  never silently select `debate`/`red-team` when K5 shows no compliant
  decorrelated route. Executable form:
  `kickoff_io.MODE_RULES` — standard low-stakes research → none; novel
  problem / suspect convention → `first-principles`; yes-no choice /
  genuinely opposed options → `debate`; pre-launch / investment /
  pre-mortem → `red-team`; high-stakes go/no-go sign-off → `debate` +
  `red-team`.
- **`auto` venue resolution (deterministic, never a re-interview):**
  Phase 1 → `fresh_claude_web` for high stakes, else `local` (subject to
  capability). Phase 3 → `local` by default; `fresh_claude_web` for high
  stakes or when staged inputs exceed the local context budget. Phase 5 →
  resolved only after the capability/input-budget gate, in order
  `fresh_subagent` → `fresh_claude_web` → `inline` (`inline` legal only
  when freshness and context-fit both pass).
- **Verdict defaults:** binary/go-no-go work defaults to
  `["GO","NO-GO","GO-WITH-CONDITIONS"]`; otherwise collect ≥2 unique
  labels. These are output labels, not a preselected answer.

## 6. K5 readiness and the default expected-lane plan

K5 counts a lane runnable only when its access entry is `available` and
contains the selected route. Requirements: ≥3 distinct runnable lanes; ≥2
runnable lanes with role `evidence` or `decorrelated`; Claude `available`
with `claude_web_extended_thinking` (Claude `local` alone never satisfies
the v1 preflight); a DeepSeek lane uses role `decorrelated` and only
DeepSeek may use that role; confidential work must select
`western_hosted_api` or `self_hosted` (`consumer_web` may stay in the
inventory but cannot be selected). Client-pitch presentations additionally
require a runnable NotebookLM lane. Primary SEO with a `pending` brief
requires its selected provider (`perplexity`/`grok`) `available` with
`web`; any kickoff whose `additional_renders` contains `wordpress_article`
requires at least one of Perplexity/Grok `available` with `web`
(derivative provider precedence: Perplexity, then Grok). Health requires
runnable NotebookLM, Elicit, and Consensus lanes plus Scite `available`
with a `web|api` route (NotebookLM is mandatory because the corrected
health overlay requires the final-dossier source-grounding pass at the
Phase-5 exit).

Default plan (deterministic; explicit user override wins and records
`explicit` provenance for `/preferences/expected_lanes`):

1. Select available agents in order `perplexity`, `gemini`, `grok`,
   `claude`, `deepseek`; add `chatgpt`, then `notebooklm`, when explicitly
   requested or needed to reach three runnable lanes; select `notebooklm`
   for a client pitch; for health also select `notebooklm`, `elicit`,
   `consensus`. Serialize in canonical inventory order.
2. Default roles: `deepseek`→`decorrelated`, `grok`→`sentiment`,
   `claude`→`synthesis`, everything else `evidence`. If fewer than two
   lanes are `evidence|decorrelated`, add the first available not-yet-
   selected agent in order `perplexity`, `gemini`, `chatgpt`,
   `notebooklm`, `elicit`, `consensus`; if none, promote `grok` to
   `evidence`, then `claude` only if still necessary.
3. Route precedence: Claude `claude_web_extended_thinking` then `local`;
   non-DeepSeek `web` then `api`; DeepSeek non-confidential
   `consumer_web` → `self_hosted` → `western_hosted_api`; DeepSeek
   confidential `self_hosted` → `western_hosted_api`, never consumer web.
4. If the rules cannot satisfy K5, ask only about the missing
   access/exception.

## 7. The decorrelated exception

`conduct.decorrelated_exception` is null or exactly:

```json
{"active":true,"reason":"<non-empty operator reason>","risk_accepted":true}
```

Project-scoped, explicit-only. Invalid when `debate` or `red-team` is
selected, when a compliant runnable DeepSeek route exists, or when
`expected_lanes` still contains `deepseek`. It records an allowed K5
exception; it never makes an unavailable lane runnable.

## 8. Question catalog — core records

The closed `when` predicate AST permits only: `always`; `use_case_in`
(integer `ids` 1..8); `overlay_13_active` (boolean `value`);
`field_equals` (whitelisted `path`, JSON-scalar `value`); `field_state`
(whitelisted `path`, `state: empty|unknown`); and `all|any|not`
(max depth 4). Unknown predicates/keys, non-whitelisted paths, empty
boolean-node arrays, and type-mismatched comparisons are rejected;
`when` is data, never executable text, and is evaluated only against the
already-validated answer/config state
(`kickoff_io.evaluate_predicate`; whitelist `kickoff_io.PREDICATE_PATHS`).

Record schema: exactly `question_id`, `field_ids`, `kind`, `when`,
`question`, plus kind-specific keys — `menu`: `header` (≤12 chars),
`multiSelect`, 2–4 `options` each exactly `{value,label,description}`
(labels ≤5 words, never serialized; `value` is the typed value); `text`:
`answer_type: string|non_empty_string|path`; `structured`: `schema_ref`
(JSON Pointer into the machine contract) plus one valid neutral
`example`. All renderers normalize Unicode to NFC; menu answers map
case-insensitive letters/exact labels to option values, de-duplicate
multi-select values, and serialize in catalog order (a "none" choice
plus an atomic selection is rejected; an Other answer is accepted only
when it validates against the target field schema); text answers trim
outer whitespace only; structured answers use strict JSON with
duplicate-key rejection. Interactive plain text renders a menu as
exactly `N. <question>`, indented `a) <label> — <description>` lines in
option order, `[multi-select allowed]` when true, and `or type your
own`. Batch applicable unanswered records in contract order (≤4 questions
per tool call), conflict/safety blockers first. Dynamic Stage-1 framing
options vary with the idea and are **not** catalog records; their outer
mechanics (3–4 count, one-line consequences, normalization) are fixed in
SKILL.md and the answer-sheet framing schema.

`question_catalog_digest` = lowercase SHA256 of the UTF-8 canonical JSON
(`sort_keys=True`, separators `(",", ":")`, `ensure_ascii=False`) of the
concatenated core + all-eight-profile record arrays, in shipped order
(`kickoff_io.question_catalog_digest(load_question_catalog())`).

<!-- BEGIN KICKOFF-QUESTION-CATALOG core -->
```json
[
  {
    "question_id": "Q_CORE_RESEARCH_QUESTION",
    "field_ids": [
      "/project/research_question"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "What is the research question? One or two sentences.",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_DECISION_CONTEXT",
    "field_ids": [
      "/project/decision_context"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Decision context: what will you do with the finished dossier?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_TIME_HORIZON",
    "field_ids": [
      "/project/time_horizon"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Time horizon: when do you need this done, or how current must the evidence be?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_AUDIENCE",
    "field_ids": [
      "/project/audience"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Who is the audience for the deliverable?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_CONFIDENTIALITY",
    "field_ids": [
      "/project/confidentiality"
    ],
    "kind": "menu",
    "when": {
      "predicate": "always"
    },
    "question": "Does this research involve confidential material (internal architecture, client code, business-sensitive context)?",
    "header": "Confidential",
    "multiSelect": false,
    "options": [
      {
        "value": "non_confidential",
        "label": "Non-confidential (Recommended)",
        "description": "Public or personal work; every research route is open."
      },
      {
        "value": "confidential",
        "label": "Confidential",
        "description": "Routes the decorrelated lane through a Western-hosted or self-hosted DeepSeek only."
      }
    ]
  },
  {
    "question_id": "Q_CORE_STAKES",
    "field_ids": [
      "/project/stakes"
    ],
    "kind": "menu",
    "when": {
      "predicate": "not",
      "item": {
        "predicate": "use_case_in",
        "ids": [
          6
        ]
      }
    },
    "question": "What is the consequence of getting this research wrong?",
    "header": "Stakes",
    "multiSelect": false,
    "options": [
      {
        "value": "medium",
        "label": "Medium (Recommended)",
        "description": "Material but reversible consequences."
      },
      {
        "value": "high",
        "label": "High",
        "description": "Safety, money, launch, or sign-off consequences."
      },
      {
        "value": "low",
        "label": "Low",
        "description": "Exploratory work with easy recovery."
      }
    ]
  },
  {
    "question_id": "Q_CORE_CLASSIFIED_INPUTS",
    "field_ids": [
      "/project/classified_inputs"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "List any input files, each classified trusted or under_scrutiny (with contaminants for the latter). An empty list is a valid explicit answer.",
    "schema_ref": "/properties/project/properties/classified_inputs",
    "example": [
      {
        "input_id": "IN1",
        "path": "docs/spec.md",
        "trust": "trusted",
        "contaminants": []
      }
    ]
  },
  {
    "question_id": "Q_CORE_GROUND_TRUTH",
    "field_ids": [
      "/project/ground_truth"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "List any personally verified ground-truth claims (each needs statement, metric definition, and source). An empty list is a valid explicit answer.",
    "schema_ref": "/properties/project/properties/ground_truth",
    "example": [
      {
        "claim_id": "GT1",
        "statement": "Our article ranks #4 for the target keyword",
        "metric_definition": "Google position for the exact keyword, logged-out",
        "source": "https://example.com/serp-screenshot"
      }
    ]
  },
  {
    "question_id": "Q_CORE_DOSSIER_ROOT",
    "field_ids": [
      "/workspace/dossier_root"
    ],
    "kind": "text",
    "when": {
      "predicate": "field_state",
      "path": "/workspace/dossier_root",
      "state": "empty"
    },
    "question": "Where should dossiers for this workspace live? (Relative paths resolve against the workspace root.)",
    "answer_type": "path"
  },
  {
    "question_id": "Q_CORE_OUTSIDE_APPROVAL",
    "field_ids": [
      "/workspace/outside_workspace_write_approved"
    ],
    "kind": "menu",
    "when": {
      "predicate": "field_equals",
      "path": "/workspace/dossier_root_scope",
      "value": "outside_workspace"
    },
    "question": "The dossier root resolves outside the granted workspace. Approve writing there?",
    "header": "Outside root",
    "multiSelect": false,
    "options": [
      {
        "value": false,
        "label": "Pick another root (Recommended)",
        "description": "Keep dossiers inside the granted workspace."
      },
      {
        "value": true,
        "label": "Approve outside write",
        "description": "Recorded in the kickoff; the orchestrator re-confirms in its own session."
      }
    ]
  },
  {
    "question_id": "Q_CORE_AGENT_ACCESS",
    "field_ids": [
      "/workspace/agent_access"
    ],
    "kind": "structured",
    "when": {
      "predicate": "field_state",
      "path": "/workspace/agent_access",
      "state": "unknown"
    },
    "question": "Record the workspace agent-access inventory (all ten keys; unknown entries may stay unknown until needed).",
    "schema_ref": "/properties/workspace/properties/agent_access",
    "example": {
      "perplexity": {
        "status": "available",
        "tier": "Pro",
        "routes": [
          "web"
        ]
      },
      "gemini": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "grok": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "chatgpt": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "claude": {
        "status": "available",
        "tier": null,
        "routes": [
          "claude_web_extended_thinking"
        ]
      },
      "deepseek": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "notebooklm": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "elicit": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "consensus": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "scite": {
        "status": "unknown",
        "tier": null,
        "routes": []
      }
    }
  },
  {
    "question_id": "Q_CORE_SPEC_MODE",
    "field_ids": [
      "/invocation/spec_mode"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        1
      ]
    },
    "question": "Is this a greenfield build or a change to an existing repository?",
    "header": "Spec mode",
    "multiSelect": false,
    "options": [
      {
        "value": "greenfield",
        "label": "Greenfield (Recommended)",
        "description": "A new system with no existing repo constraints."
      },
      {
        "value": "brownfield",
        "label": "Brownfield",
        "description": "An existing repository whose docs inform Phase 1."
      }
    ]
  },
  {
    "question_id": "Q_CORE_BROWNFIELD_REPO",
    "field_ids": [
      "/invocation/brownfield_repo"
    ],
    "kind": "text",
    "when": {
      "predicate": "all",
      "items": [
        {
          "predicate": "use_case_in",
          "ids": [
            1
          ]
        },
        {
          "predicate": "field_equals",
          "path": "/invocation/spec_mode",
          "value": "brownfield"
        }
      ]
    },
    "question": "Path to the existing repository workspace.",
    "answer_type": "path"
  },
  {
    "question_id": "Q_CORE_REQUIREMENTS_INPUT",
    "field_ids": [
      "/invocation/requirements_input_id"
    ],
    "kind": "text",
    "when": {
      "predicate": "not",
      "item": {
        "predicate": "field_state",
        "path": "/project/classified_inputs",
        "state": "empty"
      }
    },
    "question": "Which classified input (its IN id) is the requirements file, if any? Answer with the id or leave empty for none.",
    "answer_type": "string"
  },
  {
    "question_id": "Q_CORE_THESIS",
    "field_ids": [
      "/project/thesis"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        2,
        3,
        7
      ]
    },
    "question": "What is the one-sentence thesis the deliverable argues?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_DIFFERENTIATION_HOOK",
    "field_ids": [
      "/project/differentiation_hook"
    ],
    "kind": "text",
    "when": {
      "predicate": "any",
      "items": [
        {
          "predicate": "use_case_in",
          "ids": [
            2,
            7
          ]
        },
        {
          "predicate": "all",
          "items": [
            {
              "predicate": "use_case_in",
              "ids": [
                5
              ]
            },
            {
              "predicate": "field_equals",
              "path": "/use_case_profile/keyword_brief/status",
              "value": "provided"
            }
          ]
        }
      ]
    },
    "question": "What is the differentiation hook — the angle the existing coverage does not take?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_CONSTRAINTS",
    "field_ids": [
      "/project/constraints"
    ],
    "kind": "structured",
    "when": {
      "predicate": "any",
      "items": [
        {
          "predicate": "overlay_13_active",
          "value": true
        },
        {
          "predicate": "all",
          "items": [
            {
              "predicate": "use_case_in",
              "ids": [
                1
              ]
            },
            {
              "predicate": "any",
              "items": [
                {
                  "predicate": "field_state",
                  "path": "/use_case_profile/requirements_coverage",
                  "state": "empty"
                },
                {
                  "predicate": "field_equals",
                  "path": "/use_case_profile/requirements_coverage/constraints",
                  "value": false
                }
              ]
            }
          ]
        }
      ]
    },
    "question": "List the binding constraints (budget, compliance, platform, timeline). An empty list is a valid explicit answer only when a requirements input covers constraints.",
    "schema_ref": "/properties/project/properties/constraints",
    "example": [
      "Budget under $500/month",
      "Must run on Azure"
    ]
  },
  {
    "question_id": "Q_CORE_ALLOWED_VERDICTS",
    "field_ids": [
      "/project/allowed_verdicts"
    ],
    "kind": "structured",
    "when": {
      "predicate": "overlay_13_active",
      "value": true
    },
    "question": "Confirm or override the allowed verdict labels for the Decision Brief (at least two unique labels).",
    "schema_ref": "/properties/project/properties/allowed_verdicts",
    "example": [
      "GO",
      "NO-GO",
      "GO-WITH-CONDITIONS"
    ]
  },
  {
    "question_id": "Q_CORE_MODES",
    "field_ids": [
      "/deliberation_modes"
    ],
    "kind": "menu",
    "when": {
      "predicate": "overlay_13_active",
      "value": true
    },
    "question": "Which deliberation modes should run? (The builder derives a recommendation from the overlay-13 selector rows; override explicitly here.)",
    "header": "Modes",
    "multiSelect": true,
    "options": [
      {
        "value": "first-principles",
        "label": "First Principles",
        "description": "Phase-1 variant for novel problems or suspect convention."
      },
      {
        "value": "debate",
        "label": "Debate",
        "description": "Blocking Phase-2.5 FOR/AGAINST pass for real trade-offs."
      },
      {
        "value": "red-team",
        "label": "Red Team",
        "description": "Blocking Phase-4.5 adversarial pass for launch/investment decisions."
      }
    ]
  },
  {
    "question_id": "Q_CORE_TITLE",
    "field_ids": [
      "/project/title"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Confirm or override the derived project title.",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_TOPIC_SLUG",
    "field_ids": [
      "/project/topic_slug"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Confirm or override the derived topic slug (lowercase kebab-case, max 64 chars).",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_CORE_PHASE1_VENUE",
    "field_ids": [
      "/preferences/phase_1_venue"
    ],
    "kind": "menu",
    "when": {
      "predicate": "always"
    },
    "question": "Where should Phase 1 decomposition run?",
    "header": "P1 venue",
    "multiSelect": false,
    "options": [
      {
        "value": "auto",
        "label": "Auto (Recommended)",
        "description": "High stakes resolves to fresh Claude web; low/medium to local."
      },
      {
        "value": "fresh_claude_web",
        "label": "Fresh Claude web",
        "description": "Strongest model with extended thinking at maximum."
      },
      {
        "value": "local",
        "label": "Local session",
        "description": "The locally available Claude model."
      }
    ]
  },
  {
    "question_id": "Q_CORE_PHASE3_VENUE",
    "field_ids": [
      "/preferences/phase_3_venue"
    ],
    "kind": "menu",
    "when": {
      "predicate": "always"
    },
    "question": "Where should Phase 3 cross-examination run?",
    "header": "P3 venue",
    "multiSelect": false,
    "options": [
      {
        "value": "auto",
        "label": "Auto (Recommended)",
        "description": "Local by default; fresh Claude web for high stakes or oversized inputs."
      },
      {
        "value": "fresh_claude_web",
        "label": "Fresh Claude web",
        "description": "Strongest model in a fresh chat."
      },
      {
        "value": "local",
        "label": "Local session",
        "description": "Acceptable for most projects."
      }
    ]
  },
  {
    "question_id": "Q_CORE_PHASE5_ROUTE",
    "field_ids": [
      "/preferences/phase_5_route"
    ],
    "kind": "menu",
    "when": {
      "predicate": "always"
    },
    "question": "Which Chairman route should Phase 5 prefer?",
    "header": "P5 route",
    "multiSelect": false,
    "options": [
      {
        "value": "auto",
        "label": "Auto (Recommended)",
        "description": "Resolves after the capability/input-budget gate: fresh subagent, then fresh Claude web, then inline."
      },
      {
        "value": "fresh_subagent",
        "label": "Fresh subagent",
        "description": "Preferred when available: fresh context on the strongest model."
      },
      {
        "value": "fresh_claude_web",
        "label": "Fresh Claude web",
        "description": "Default when a fresh subagent is unavailable."
      },
      {
        "value": "inline",
        "label": "Inline",
        "description": "Legal only when freshness and context-fit conditions both pass."
      }
    ]
  },
  {
    "question_id": "Q_CORE_EXPECTED_LANES",
    "field_ids": [
      "/preferences/expected_lanes"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "Confirm or override the derived expected Phase-2 lane plan (agent/route/role, canonical inventory order).",
    "schema_ref": "/properties/preferences/properties/expected_lanes",
    "example": [
      {
        "agent": "perplexity",
        "route": "web",
        "role": "evidence"
      },
      {
        "agent": "gemini",
        "route": "web",
        "role": "evidence"
      },
      {
        "agent": "grok",
        "route": "web",
        "role": "sentiment"
      },
      {
        "agent": "claude",
        "route": "claude_web_extended_thinking",
        "role": "synthesis"
      },
      {
        "agent": "deepseek",
        "route": "consumer_web",
        "role": "decorrelated"
      }
    ]
  },
  {
    "question_id": "Q_CORE_ADDL_RENDERS_UC2",
    "field_ids": [
      "/preferences/additional_renders"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        2
      ]
    },
    "question": "Should Phase 6 also derive a WordPress article from the same dossier?",
    "header": "Extras",
    "multiSelect": false,
    "options": [
      {
        "value": [],
        "label": "No additional renders (Recommended)",
        "description": "The YouTube script is the only deliverable."
      },
      {
        "value": [
          "wordpress_article"
        ],
        "label": "Add WordPress article",
        "description": "Transformed from the dossier in Phase 6; requires a normal-web SERP provider."
      }
    ]
  },
  {
    "question_id": "Q_CORE_ADDL_RENDERS_UC6",
    "field_ids": [
      "/preferences/additional_renders"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "Which additional renders should Phase 6 derive from the health protocol?",
    "header": "Extras",
    "multiSelect": true,
    "options": [
      {
        "value": [],
        "label": "No additional renders (Recommended)",
        "description": "The health protocol is the only deliverable."
      },
      {
        "value": "youtube_script",
        "label": "YouTube script",
        "description": "Spoken-format derivative with the disclaimer kept in the script."
      },
      {
        "value": "wordpress_article",
        "label": "WordPress article",
        "description": "MedicalWebPage-schema derivative; requires a normal-web SERP provider."
      },
      {
        "value": "ebook_chapter",
        "label": "Ebook chapter",
        "description": "One chapter using overlay 05's prose schema only — not a book project."
      }
    ]
  },
  {
    "question_id": "Q_CORE_ADDL_RENDERS_UC8",
    "field_ids": [
      "/preferences/additional_renders"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        8
      ]
    },
    "question": "Should Phase 6 also derive a deck + screencast from the Decision Brief?",
    "header": "Extras",
    "multiSelect": false,
    "options": [
      {
        "value": [],
        "label": "No additional renders (Recommended)",
        "description": "The Decision Brief is the terminal artifact."
      },
      {
        "value": [
          "deck_and_screencast"
        ],
        "label": "Add deck + screencast",
        "description": "One Marp source rendered to both formats for sharing the decision."
      }
    ]
  },
  {
    "question_id": "Q_CORE_STANDING_INSTRUCTIONS",
    "field_ids": [
      "/standing_instructions"
    ],
    "kind": "text",
    "when": {
      "predicate": "always"
    },
    "question": "Any standing instructions to carry into the run? (Free text; empty is fine. The orchestrator quotes them and asks before activating.)",
    "answer_type": "string"
  },
  {
    "question_id": "Q_CORE_SEED_AREAS",
    "field_ids": [
      "/seed_areas"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "Seed areas the decomposition should be sure to cover (maximum 8; empty is fine).",
    "schema_ref": "/properties/seed_areas",
    "example": [
      "pricing models",
      "migration cost"
    ]
  },
  {
    "question_id": "Q_CORE_OUT_OF_SCOPE",
    "field_ids": [
      "/out_of_scope"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "Anything explicitly out of scope? (Empty is fine.)",
    "schema_ref": "/properties/out_of_scope",
    "example": [
      "mobile clients"
    ]
  },
  {
    "question_id": "Q_CORE_KNOWN_TRAPS",
    "field_ids": [
      "/known_traps"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "Known traps the research must avoid? (Empty is fine.)",
    "schema_ref": "/properties/known_traps",
    "example": [
      "vendor benchmarks are marketing content"
    ]
  },
  {
    "question_id": "Q_CORE_DECORRELATED_EXCEPTION",
    "field_ids": [
      "/conduct/decorrelated_exception"
    ],
    "kind": "structured",
    "when": {
      "predicate": "always"
    },
    "question": "Only when no compliant decorrelated route exists and neither Debate nor Red Team is selected: record the last-resort exception (otherwise leave null).",
    "schema_ref": "/$defs/decorrelated_exception",
    "example": {
      "active": true,
      "reason": "No compliant DeepSeek route exists in this workspace",
      "risk_accepted": true
    }
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG core -->

## 9. Human brief format (§6.4 rendering rules)

`00-kickoff.md` sections in order (rendered by
`templates/kickoff-template.md`, which uses only
`{{FIELD:<RFC 6901 pointer>}}` placeholders; conditional spans use paired
renderer-owned HTML-comment markers `<!-- BEGIN IF <condition> -->` /
`<!-- END IF <condition> -->` with conditions `overlay13_active`,
`overlay13_inactive`, `standing_nonempty`, `guidance_nonempty` — markers
are structural, not placeholders, and K1 ignores comment content):

1. `# Kickoff — <title>` + fixed consume-don't-re-ask preamble.
2. `## Kickoff control` — the sole v1 control block.
3. `## Workspace setup` — fenced JSON = `/workspace`.
4. `## Invocation` — fenced JSON = `/invocation`; when overlay 13 is
   inactive the section also carries the literal line
   `Deliberation modes: none`.
5. `## Deliberation modes` (only when overlay 13 is active) — fenced
   JSON = `/deliberation_modes`.
6. `## Phase 0 intake — pre-answered` — fenced JSON = `/project`
   (the pre-answered Step 0.3 questions 1–7 plus project frame).
7. `## Use-case profile` — fenced JSON = `/use_case_profile`.
8. `## Topic slug — pre-confirmed` — the slug as a bare line.
9. `## Phase-execution preferences` — fenced JSON = `/preferences`.
10. `## Phase 6 deliverables` — fenced JSON =
    `/preferences/additional_renders` plus the fixed prose line stating
    that the primary render derives one-to-one from `use_case_id` (§4).
11. `## Conduct rules` — fenced JSON = `/conduct`.
12. `## Standing instructions` (only when non-empty) — the string fenced
    verbatim (fence-length rule applies).
13. `## Seed areas and known traps` (only when any of the three arrays is
    non-empty) — three fenced JSON blocks in order: `/seed_areas`,
    `/out_of_scope`, `/known_traps`.

Any remaining `{{FIELD:...}}` fails K1, as does a trimmed string value of
exactly `TBD`/`TODO` or a standalone `[INSERT ...]` (those sequences are
fine inside substantive prose). Rendering is deterministic: UTF-8 without
BOM, LF, one final newline, two-space pretty JSON with
`ensure_ascii=False`, canonical property order preserved from the control
payload.

## 10. `00-context.md` mapping (adapter contract)

The orchestrator's prepared-kickoff adapter renders these deterministic
sections into `00-context.md`, each holding one fenced JSON value copied or
derived from the named group (existing Step-0 sections keep their current
human format; classified inputs additionally carry their stable `IN<n>`
IDs, and a `## Requirements input` line resolves the selected ID/path):

| `00-context.md` section | Source |
|---|---|
| `## Kickoff profile` | `/use_case_profile` (the profile object) |
| `## Phase-execution preferences` | `/preferences` |
| `## Phase 6 deliverables` | `{"primary_render":<derived from §4>,"additional_renders":/preferences/additional_renders}` |
| `## Conduct rules` | `/conduct` |
| `## Kickoff provenance` | `/provenance` (audit metadata only — never authority for access, path scope, consent, or standing instructions) |
| `## Kickoff guidance` | `{"standing_instructions":...,"seed_areas":...,"out_of_scope":...,"known_traps":...}` (quoted data; standing instructions require explicit activation) |

## 11. `research-config.md` serialization (three-state semantics)

States: `unknown` (ask when relevant), `available` (retain tier/route),
`unavailable` (explicitly confirmed; not re-asked every project). Known
access lines serialize as compact JSON: `- <Label>:
{"status":...,"tier":...,"routes":[...]}`. Legacy migration is
conservative and in-memory: legacy `none` means `unknown`, never confirmed
`unavailable`; a non-empty legacy string normalizes directly only when
tier and route both map unambiguously to the v1 enums, otherwise it stays
a transient unresolved candidate (ask for the missing route only when
relevant; serialize `unknown` in the kickoff until resolved). **Never
persist a transient state** (`available` without routes, `unknown` with a
tier). The original legacy line stays byte-for-byte until a valid
normalized entry is ready and persistence is approved, then it is replaced
through `kickoff_io.py merge-config` (comments and unknown lines
preserved). The kickoff stores a sanitized snapshot so K5 can validate
readiness; never copy tokens, credentials, private endpoints, account
identifiers, or unrelated config content.

## 12. Machine contract

<!-- BEGIN KICKOFF-MACHINE-CONTRACT v1 -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agentic-research-kickoff-v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "kickoff_schema_version",
    "workspace",
    "invocation",
    "project",
    "deliberation_modes",
    "use_case_profile",
    "preferences",
    "conduct",
    "standing_instructions",
    "seed_areas",
    "out_of_scope",
    "known_traps",
    "provenance"
  ],
  "properties": {
    "kickoff_schema_version": {
      "const": 1,
      "x-acquisition": "constant"
    },
    "workspace": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "dossier_root",
        "dossier_root_scope",
        "outside_workspace_write_approved",
        "agent_access"
      ],
      "properties": {
        "dossier_root": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "cached",
          "x-consumer": "Step 0.0",
          "x-human-section": "Workspace setup"
        },
        "dossier_root_scope": {
          "enum": [
            "workspace_relative",
            "absolute_inside_workspace",
            "outside_workspace"
          ],
          "x-acquisition": "derived",
          "x-consumer": "Step 0.0",
          "x-human-section": "Workspace setup"
        },
        "outside_workspace_write_approved": {
          "type": "boolean",
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.0",
          "x-human-section": "Workspace setup"
        },
        "agent_access": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "perplexity",
            "gemini",
            "grok",
            "chatgpt",
            "claude",
            "deepseek",
            "notebooklm",
            "elicit",
            "consensus",
            "scite"
          ],
          "properties": {
            "perplexity": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "gemini": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "grok": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "chatgpt": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "claude": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "claude_web_extended_thinking",
                          "local"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "deepseek": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "consumer_web",
                          "western_hosted_api",
                          "self_hosted"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "notebooklm": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "elicit": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "consensus": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            },
            "scite": {
              "allOf": [
                {
                  "$ref": "#/$defs/access_entry"
                },
                {
                  "properties": {
                    "routes": {
                      "items": {
                        "enum": [
                          "web",
                          "api"
                        ]
                      }
                    }
                  }
                }
              ]
            }
          },
          "x-acquisition": "cached",
          "x-consumer": "Step 0.3",
          "x-human-section": "Workspace setup"
        }
      }
    },
    "invocation": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "use_case_id",
        "layered_overlays",
        "spec_mode",
        "brownfield_repo",
        "requirements_input_id"
      ],
      "properties": {
        "use_case_id": {
          "type": "integer",
          "minimum": 1,
          "maximum": 8,
          "x-acquisition": "derived",
          "x-consumer": "Step 0.1",
          "x-human-section": "Invocation"
        },
        "layered_overlays": {
          "type": "array",
          "maxItems": 1,
          "uniqueItems": true,
          "items": {
            "const": "13-overlay-deliberation-modes.md"
          },
          "x-acquisition": "derived",
          "x-consumer": "Step 0.1",
          "x-human-section": "Invocation"
        },
        "spec_mode": {
          "enum": [
            "greenfield",
            "brownfield",
            null
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.2",
          "x-human-section": "Invocation"
        },
        "brownfield_repo": {
          "type": [
            "string",
            "null"
          ],
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.2",
          "x-human-section": "Invocation"
        },
        "requirements_input_id": {
          "type": [
            "string",
            "null"
          ],
          "pattern": "^IN[1-9][0-9]*$",
          "x-acquisition": "derived",
          "x-consumer": "Step 0.5",
          "x-human-section": "Invocation"
        }
      }
    },
    "project": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "title",
        "research_question",
        "decision_context",
        "time_horizon",
        "audience",
        "thesis",
        "differentiation_hook",
        "constraints",
        "stakes",
        "confidentiality",
        "classified_inputs",
        "ground_truth",
        "topic_slug",
        "allowed_verdicts"
      ],
      "properties": {
        "title": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "derived",
          "x-consumer": "Step 0.4",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "research_question": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "decision_context": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "time_horizon": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "audience": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "thesis": {
          "type": [
            "string",
            "null"
          ],
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 1.2",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "differentiation_hook": {
          "type": [
            "string",
            "null"
          ],
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "Step 1.2",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "constraints": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "must_ask",
          "x-consumer": "Step 1.2",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "stakes": {
          "enum": [
            "low",
            "medium",
            "high"
          ],
          "x-acquisition": "safe_default",
          "x-default": "medium",
          "x-consumer": "Step 1.1",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "confidentiality": {
          "enum": [
            "confidential",
            "non_confidential"
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "classified_inputs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/classified_input"
          },
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.3",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "ground_truth": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/ground_truth_claim"
          },
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.6",
          "x-human-section": "Phase 0 intake — pre-answered"
        },
        "topic_slug": {
          "type": "string",
          "pattern": "^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$",
          "x-acquisition": "derived",
          "x-consumer": "Step 0.4",
          "x-human-section": "Topic slug — pre-confirmed"
        },
        "allowed_verdicts": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "derived",
          "x-consumer": "Step 1.2",
          "x-human-section": "Phase 0 intake — pre-answered"
        }
      }
    },
    "deliberation_modes": {
      "enum": [
        [],
        [
          "first-principles"
        ],
        [
          "debate"
        ],
        [
          "red-team"
        ],
        [
          "first-principles",
          "debate"
        ],
        [
          "first-principles",
          "red-team"
        ],
        [
          "debate",
          "red-team"
        ],
        [
          "first-principles",
          "debate",
          "red-team"
        ]
      ],
      "x-acquisition": "derived",
      "x-consumer": "Steps 1.2/2.5/4.5",
      "x-human-section": "Deliberation modes"
    },
    "use_case_profile": {
      "type": "object"
    },
    "preferences": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "phase_1_venue",
        "phase_3_venue",
        "phase_5_route",
        "expected_lanes",
        "additional_renders"
      ],
      "properties": {
        "phase_1_venue": {
          "enum": [
            "auto",
            "fresh_claude_web",
            "local"
          ],
          "x-acquisition": "safe_default",
          "x-default": "auto",
          "x-consumer": "Step 1.1",
          "x-human-section": "Phase-execution preferences"
        },
        "phase_3_venue": {
          "enum": [
            "auto",
            "fresh_claude_web",
            "local"
          ],
          "x-acquisition": "safe_default",
          "x-default": "auto",
          "x-consumer": "Step 3.3",
          "x-human-section": "Phase-execution preferences"
        },
        "phase_5_route": {
          "enum": [
            "auto",
            "fresh_subagent",
            "fresh_claude_web",
            "inline"
          ],
          "x-acquisition": "safe_default",
          "x-default": "auto",
          "x-consumer": "Phase 5 capability gate",
          "x-human-section": "Phase-execution preferences"
        },
        "expected_lanes": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/expected_lane"
          },
          "x-acquisition": "derived",
          "x-consumer": "Step 1.2",
          "x-human-section": "Phase-execution preferences"
        },
        "additional_renders": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "enum": [
              "wordpress_article",
              "youtube_script",
              "ebook_chapter",
              "deck_and_screencast"
            ]
          },
          "x-acquisition": "optional",
          "x-consumer": "Phase 6",
          "x-human-section": "Phase 6 deliverables"
        }
      }
    },
    "conduct": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "run_all_phases",
        "enforce_all_gates",
        "methodology_scope",
        "selected_modes_blocking",
        "non_cancellable_phases",
        "decorrelated_exception"
      ],
      "properties": {
        "run_all_phases": {
          "const": true,
          "x-acquisition": "constant"
        },
        "enforce_all_gates": {
          "const": true,
          "x-acquisition": "constant"
        },
        "methodology_scope": {
          "const": "bundled_only",
          "x-acquisition": "constant"
        },
        "selected_modes_blocking": {
          "const": true,
          "x-acquisition": "constant"
        },
        "non_cancellable_phases": {
          "enum": [
            [],
            [
              4
            ]
          ],
          "x-acquisition": "derived",
          "x-consumer": "Phase 4",
          "x-human-section": "Conduct rules"
        },
        "decorrelated_exception": {
          "$ref": "#/$defs/decorrelated_exception",
          "x-acquisition": "optional",
          "x-consumer": "Step 2.2",
          "x-human-section": "Conduct rules"
        }
      }
    },
    "standing_instructions": {
      "type": "string",
      "x-acquisition": "optional",
      "x-consumer": "00-context.md guidance",
      "x-human-section": "Standing instructions"
    },
    "seed_areas": {
      "type": "array",
      "maxItems": 8,
      "items": {
        "type": "string",
        "minLength": 1
      },
      "x-acquisition": "optional",
      "x-consumer": "00-context.md guidance",
      "x-human-section": "Seed areas and known traps"
    },
    "out_of_scope": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "x-acquisition": "optional",
      "x-consumer": "00-context.md guidance",
      "x-human-section": "Seed areas and known traps"
    },
    "known_traps": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "x-acquisition": "optional",
      "x-consumer": "00-context.md guidance",
      "x-human-section": "Seed areas and known traps"
    },
    "provenance": {
      "type": "object",
      "propertyNames": {
        "pattern": "^/"
      },
      "additionalProperties": {
        "enum": [
          "explicit",
          "cached",
          "derived",
          "defaulted"
        ]
      },
      "x-acquisition": "derived",
      "x-consumer": "00-context.md provenance",
      "x-human-section": "Conduct rules"
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "use_case_id": {
                "const": 6
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "project": {
            "properties": {
              "stakes": {
                "const": "high"
              }
            }
          },
          "conduct": {
            "properties": {
              "non_cancellable_phases": {
                "const": [
                  4
                ]
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "use_case_id": {
                "enum": [
                  1,
                  2,
                  3,
                  4,
                  5,
                  7,
                  8
                ]
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "conduct": {
            "properties": {
              "non_cancellable_phases": {
                "const": []
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "use_case_id": {
                "enum": [
                  4,
                  8
                ]
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "invocation": {
            "properties": {
              "layered_overlays": {
                "const": []
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "use_case_id": {
                "const": 1
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "invocation": {
            "properties": {
              "spec_mode": {
                "enum": [
                  "greenfield",
                  "brownfield"
                ]
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "use_case_id": {
                "enum": [
                  2,
                  3,
                  4,
                  5,
                  6,
                  7,
                  8
                ]
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "invocation": {
            "properties": {
              "spec_mode": {
                "const": null
              },
              "brownfield_repo": {
                "const": null
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "spec_mode": {
                "const": "brownfield"
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "invocation": {
            "properties": {
              "brownfield_repo": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "invocation": {
            "properties": {
              "spec_mode": {
                "const": "greenfield"
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "invocation": {
            "properties": {
              "brownfield_repo": {
                "const": null
              }
            }
          }
        }
      }
    }
  ],
  "oneOf": [
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 1
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_spec_driven_dev"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 2
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_youtube"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 3
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_presentation"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 4
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_ebook"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 5
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_wordpress_seo"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 6
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_health"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 7
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_deck_screencast"
        }
      }
    },
    {
      "properties": {
        "invocation": {
          "properties": {
            "use_case_id": {
              "const": 8
            }
          }
        },
        "use_case_profile": {
          "$ref": "#/$defs/profile_decision"
        }
      }
    }
  ],
  "$defs": {
    "access_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "status",
        "tier",
        "routes"
      ],
      "properties": {
        "status": {
          "enum": [
            "unknown",
            "available",
            "unavailable"
          ]
        },
        "tier": {
          "type": [
            "string",
            "null"
          ],
          "minLength": 1
        },
        "routes": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string"
          }
        }
      },
      "allOf": [
        {
          "if": {
            "properties": {
              "status": {
                "enum": [
                  "unknown",
                  "unavailable"
                ]
              }
            }
          },
          "then": {
            "properties": {
              "tier": {
                "const": null
              },
              "routes": {
                "maxItems": 0
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "status": {
                "const": "available"
              }
            }
          },
          "then": {
            "properties": {
              "routes": {
                "minItems": 1
              }
            }
          }
        }
      ]
    },
    "classified_input": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "input_id",
        "path",
        "trust",
        "contaminants"
      ],
      "properties": {
        "input_id": {
          "type": "string",
          "pattern": "^IN[1-9][0-9]*$"
        },
        "path": {
          "type": "string",
          "minLength": 1
        },
        "trust": {
          "enum": [
            "trusted",
            "under_scrutiny"
          ]
        },
        "contaminants": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        }
      },
      "allOf": [
        {
          "if": {
            "properties": {
              "trust": {
                "const": "trusted"
              }
            }
          },
          "then": {
            "properties": {
              "contaminants": {
                "maxItems": 0
              }
            }
          }
        }
      ]
    },
    "ground_truth_claim": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "claim_id",
        "statement",
        "metric_definition",
        "source"
      ],
      "properties": {
        "claim_id": {
          "type": "string",
          "pattern": "^GT[1-9][0-9]*$"
        },
        "statement": {
          "type": "string",
          "minLength": 1
        },
        "metric_definition": {
          "type": "string",
          "minLength": 1
        },
        "source": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "expected_lane": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "agent",
        "route",
        "role"
      ],
      "properties": {
        "agent": {
          "enum": [
            "perplexity",
            "gemini",
            "grok",
            "chatgpt",
            "claude",
            "deepseek",
            "notebooklm",
            "elicit",
            "consensus"
          ]
        },
        "route": {
          "type": "string",
          "minLength": 1
        },
        "role": {
          "enum": [
            "evidence",
            "sentiment",
            "synthesis",
            "decorrelated"
          ]
        }
      }
    },
    "decorrelated_exception": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": false,
      "required": [
        "active",
        "reason",
        "risk_accepted"
      ],
      "properties": {
        "active": {
          "const": true
        },
        "reason": {
          "type": "string",
          "minLength": 1
        },
        "risk_accepted": {
          "const": true
        }
      }
    },
    "profile_spec_driven_dev": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "product_target_users",
        "requirements_coverage"
      ],
      "properties": {
        "product_target_users": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 02 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "requirements_coverage": {
          "type": [
            "object",
            "null"
          ],
          "additionalProperties": false,
          "required": [
            "product_target_users",
            "constraints"
          ],
          "properties": {
            "product_target_users": {
              "type": "boolean"
            },
            "constraints": {
              "type": "boolean"
            }
          },
          "x-acquisition": "must_ask",
          "x-consumer": "Step 0.5",
          "x-human-section": "Use-case profile"
        }
      }
    },
    "profile_youtube": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "video_duration_minutes"
      ],
      "properties": {
        "video_duration_minutes": {
          "type": "integer",
          "minimum": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 03 Phase 1",
          "x-human-section": "Use-case profile"
        }
      }
    },
    "profile_presentation": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "talk_duration_minutes",
        "setting",
        "client_pitch",
        "client_material_input_ids"
      ],
      "properties": {
        "talk_duration_minutes": {
          "type": "integer",
          "minimum": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 04 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "setting": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 04 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "client_pitch": {
          "type": "boolean",
          "x-acquisition": "derived",
          "x-consumer": "overlay 04 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "client_material_input_ids": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string",
            "pattern": "^IN[1-9][0-9]*$"
          },
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 04 Phase 2 (NotebookLM)",
          "x-human-section": "Use-case profile"
        }
      },
      "allOf": [
        {
          "if": {
            "properties": {
              "client_pitch": {
                "const": true
              }
            }
          },
          "then": {
            "properties": {
              "client_material_input_ids": {
                "minItems": 1
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "client_pitch": {
                "const": false
              }
            }
          },
          "then": {
            "properties": {
              "client_material_input_ids": {
                "maxItems": 0
              }
            }
          }
        }
      ]
    },
    "profile_ebook": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "prior_knowledge",
        "intended_takeaway",
        "total_word_target",
        "chapter_count",
        "format"
      ],
      "properties": {
        "prior_knowledge": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 05 Phase 0",
          "x-human-section": "Use-case profile"
        },
        "intended_takeaway": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 05 Phase 0",
          "x-human-section": "Use-case profile"
        },
        "total_word_target": {
          "type": "integer",
          "minimum": 30000,
          "maximum": 80000,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 05 Phase 0",
          "x-human-section": "Use-case profile"
        },
        "chapter_count": {
          "type": "integer",
          "minimum": 8,
          "maximum": 15,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 05 Phase 0",
          "x-human-section": "Use-case profile"
        },
        "format": {
          "enum": [
            "how_to",
            "narrative",
            "reference",
            "hybrid"
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 05 Phase 0",
          "x-human-section": "Use-case profile"
        }
      }
    },
    "profile_wordpress_seo": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "site_name",
        "primary_keyword",
        "search_intent",
        "target_word_count",
        "secondary_keywords",
        "keyword_brief"
      ],
      "properties": {
        "site_name": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 06 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "primary_keyword": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 06 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "search_intent": {
          "enum": [
            "informational",
            "commercial",
            "transactional",
            null
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 06 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "target_word_count": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 06 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "secondary_keywords": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 06 Phase 5",
          "x-human-section": "Use-case profile"
        },
        "keyword_brief": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "status",
            "input_id",
            "serp_average_word_count",
            "serp_provider"
          ],
          "properties": {
            "status": {
              "enum": [
                "provided",
                "pending"
              ]
            },
            "input_id": {
              "type": [
                "string",
                "null"
              ],
              "pattern": "^IN[1-9][0-9]*$"
            },
            "serp_average_word_count": {
              "type": [
                "integer",
                "null"
              ],
              "minimum": 1
            },
            "serp_provider": {
              "enum": [
                "perplexity",
                "grok",
                null
              ]
            }
          },
          "allOf": [
            {
              "if": {
                "properties": {
                  "status": {
                    "const": "provided"
                  }
                }
              },
              "then": {
                "properties": {
                  "input_id": {
                    "type": "string"
                  },
                  "serp_average_word_count": {
                    "type": "integer"
                  },
                  "serp_provider": {
                    "const": null
                  }
                }
              }
            },
            {
              "if": {
                "properties": {
                  "status": {
                    "const": "pending"
                  }
                }
              },
              "then": {
                "properties": {
                  "input_id": {
                    "const": null
                  },
                  "serp_average_word_count": {
                    "const": null
                  },
                  "serp_provider": {
                    "enum": [
                      "perplexity",
                      "grok"
                    ]
                  }
                }
              }
            }
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "Pre-Phase-1 keyword brief (Step 1.0)",
          "x-human-section": "Use-case profile"
        }
      }
    },
    "profile_health": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "evidence_population",
        "intervention_or_exposure",
        "intended_outcomes",
        "safety_scope",
        "commercial_relationship",
        "policy"
      ],
      "properties": {
        "evidence_population": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 07 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "intervention_or_exposure": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 07 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "intended_outcomes": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 07 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "safety_scope": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 07 Phase 4",
          "x-human-section": "Use-case profile"
        },
        "commercial_relationship": {
          "enum": [
            "none",
            "sponsorship",
            "affiliate",
            "both"
          ],
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 07 Phase 6",
          "x-human-section": "Use-case profile"
        },
        "policy": {
          "const": {
            "evidence_strength_tagging_required": true,
            "evidence_strength_tags": [
              "STRONG",
              "MODERATE",
              "WEAK"
            ],
            "source_recency_cutoff_year": 2020,
            "foundational_source_exception": true,
            "medical_disclaimer_required": true,
            "final_dossier_notebooklm_check_required": true
          },
          "x-acquisition": "constant"
        }
      }
    },
    "profile_deck_screencast": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "deck_slide_target",
        "video_duration_minutes"
      ],
      "properties": {
        "deck_slide_target": {
          "type": "integer",
          "minimum": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 08 format envelope",
          "x-human-section": "Use-case profile"
        },
        "video_duration_minutes": {
          "type": "integer",
          "minimum": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 08 format envelope",
          "x-human-section": "Use-case profile"
        }
      }
    },
    "profile_decision": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "decision_options",
        "reversibility",
        "current_leaning"
      ],
      "properties": {
        "decision_options": {
          "type": "array",
          "minItems": 2,
          "uniqueItems": true,
          "items": {
            "type": "string",
            "minLength": 1
          },
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 13 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "reversibility": {
          "type": "string",
          "minLength": 1,
          "x-acquisition": "must_ask",
          "x-consumer": "overlay 13 Phase 1",
          "x-human-section": "Use-case profile"
        },
        "current_leaning": {
          "type": [
            "string",
            "null"
          ],
          "x-acquisition": "optional",
          "x-consumer": "overlay 13 Phase 1",
          "x-human-section": "Use-case profile"
        }
      }
    }
  }
}
```
<!-- END KICKOFF-MACHINE-CONTRACT v1 -->

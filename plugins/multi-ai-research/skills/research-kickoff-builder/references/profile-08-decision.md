# Profile 08 — `decision` (use case 8)

**Derived primary overlay:** `13-overlay-deliberation-modes.md`
**Overlay heading anchors (drift-locked):** `## When 13 is the primary overlay` · `## Mode selector (quick reference)` · `<output_format> — DECISION BRIEF`
**Derived primary render:** `decision_brief` (the Phase-5 format **and** the terminal primary render) · **Allowed additional renders:** `deck_and_screencast`

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/decision_options` | always (profile active) | `must_ask` | `Q_P08_OPTIONS` | — | ≥2 unique non-empty strings | overlay 13 Phase 1 decision axes + Debate framing |
| `/use_case_profile/reversibility` | always | `must_ask` | `Q_P08_REVERSIBILITY` | — | non-empty string (no closed enum — one-way/two-way door framing welcome) | overlay 13 Phase 1 |
| `/use_case_profile/current_leaning` | optional | `optional` | `Q_P08_LEANING` | `null` | string or null | Red Team draft-recommendation seed |

## Cross-field rules

- Overlay 13 is the **primary** for this use case; `/invocation/layered_overlays` must be `[]` (double-layering is illegal).
- Constraints, allowed verdicts, and deliberation modes stay only at their core paths (`/project/constraints`, `/project/allowed_verdicts`, `/deliberation_modes`).
- `allowed_verdicts` requires ≥2 unique labels (default `GO`/`NO-GO`/`GO-WITH-CONDITIONS` for binary work).

## K5 delta

Debate/Red Team (when selected) require a compliant decorrelated lane and forbid the exception object — core K5 rules apply with force here.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-08 -->
```json
[
  {
    "question_id": "Q_P08_OPTIONS",
    "field_ids": [
      "/use_case_profile/decision_options"
    ],
    "kind": "structured",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        8
      ]
    },
    "question": "What are the decision options? (At least two, genuinely distinct.)",
    "schema_ref": "/$defs/profile_decision/properties/decision_options",
    "example": [
      "Buy the managed service",
      "Self-host the open-source version"
    ]
  },
  {
    "question_id": "Q_P08_REVERSIBILITY",
    "field_ids": [
      "/use_case_profile/reversibility"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        8
      ]
    },
    "question": "How reversible is this decision? (Free text — one-way/two-way door framing welcome; no closed enum.)",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P08_LEANING",
    "field_ids": [
      "/use_case_profile/current_leaning"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        8
      ]
    },
    "question": "Do you currently lean toward an option? (Optional; the Red Team attacks it if given.)",
    "answer_type": "string"
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-08 -->

# Profile 06 — `health` (use case 6)

**Derived primary overlay:** `07-overlay-health-content.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block` · `## Phase 4 — citation verification (intensified for health)` · `## Phase 5 exit check — final-dossier NotebookLM source-grounding (mandatory, blocking)` · `## Phase 6 — output routing (per content type)`
**Derived primary render:** `health_protocol` · **Allowed additional renders:** `youtube_script`, `wordpress_article`, `ebook_chapter`

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/evidence_population` | always (profile active) | `must_ask` | `Q_P06_POPULATION` | — | non-empty string | overlay 07 Phase 1 population question + Phase 4 population-match check |
| `/use_case_profile/intervention_or_exposure` | always | `must_ask` | `Q_P06_INTERVENTION` | — | non-empty string | overlay 07 Phase 1 |
| `/use_case_profile/intended_outcomes` | always | `must_ask` | `Q_P06_OUTCOMES` | — | non-empty `string[]` | overlay 07 Phase 1 mechanism-vs-outcome discipline |
| `/use_case_profile/safety_scope` | always | `must_ask` | `Q_P06_SAFETY_SCOPE` | — | non-empty string | overlay 07 Phase 4 supplement/pharma safety step |
| `/use_case_profile/commercial_relationship` | always | `must_ask` | `Q_P06_COMMERCIAL` | — | `none\|sponsorship\|affiliate\|both` | overlay 07 Phase 6 sponsored-content rules |
| `/use_case_profile/policy` | constant | `constant` | — | fixed | exactly the policy object below | overlay 07 enforcement + Step 5.4 exit check |

Derived constant `policy` (drift-locked to the overlay):

```json
{"evidence_strength_tagging_required":true,"evidence_strength_tags":["STRONG","MODERATE","WEAK"],"source_recency_cutoff_year":2020,"foundational_source_exception":true,"medical_disclaimer_required":true,"final_dossier_notebooklm_check_required":true}
```

## Cross-field rules

- `/project/audience` is the reader, not necessarily the studied population — `evidence_population` names the population the evidence must cover.
- `/project/stakes` is invariant `high`: a low/medium request is explained and either normalized to high with confirmation or the profile is switched; lower stakes fails K3.
- `/conduct/non_cancellable_phases` is exactly `[4]`; the `policy` flag makes the corrected Phase-5 exit check blocking (checked `05-dossier.md` SHA256 recorded in `00-context.md`; any overwrite invalidates and re-runs it).
- A non-`none` commercial relationship activates the overlay's `[POTENTIAL-COI]` tagging, disclosure, and stricter sponsored-product evidence rules.

## K5 delta

NotebookLM, Elicit, and Consensus must be **runnable expected lanes**; Scite must be `available` with a selected `web|api` route (Phase-4 verification readiness, never a lane). NotebookLM is mandatory because the corrected overlay requires the final-dossier source-grounding pass at the Phase-5 exit, not merely because it is useful during fan-out.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-06 -->
```json
[
  {
    "question_id": "Q_P06_POPULATION",
    "field_ids": [
      "/use_case_profile/evidence_population"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "Which population must the evidence cover? (The studied population, not necessarily the reader.)",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P06_INTERVENTION",
    "field_ids": [
      "/use_case_profile/intervention_or_exposure"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "What intervention or exposure is being researched?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P06_OUTCOMES",
    "field_ids": [
      "/use_case_profile/intended_outcomes"
    ],
    "kind": "structured",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "Which outcomes matter? (At least one.)",
    "schema_ref": "/$defs/profile_health/properties/intended_outcomes",
    "example": [
      "reduced low-back pain during training"
    ]
  },
  {
    "question_id": "Q_P06_SAFETY_SCOPE",
    "field_ids": [
      "/use_case_profile/safety_scope"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "What is the safety scope — which harms/contraindications must be surfaced alongside efficacy?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P06_COMMERCIAL",
    "field_ids": [
      "/use_case_profile/commercial_relationship"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        6
      ]
    },
    "question": "Any commercial relationship touching this content?",
    "header": "Commercial",
    "multiSelect": false,
    "options": [
      {
        "value": "none",
        "label": "None (Recommended)",
        "description": "No sponsorship or affiliate ties."
      },
      {
        "value": "sponsorship",
        "label": "Sponsorship",
        "description": "Activates [POTENTIAL-COI] tagging and disclosure."
      },
      {
        "value": "affiliate",
        "label": "Affiliate",
        "description": "Activates [POTENTIAL-COI] tagging and disclosure."
      },
      {
        "value": "both",
        "label": "Both",
        "description": "Sponsorship and affiliate; strictest evidence rules."
      }
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-06 -->

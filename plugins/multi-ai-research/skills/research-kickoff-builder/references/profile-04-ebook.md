# Profile 04 — `ebook` (use case 4)

**Derived primary overlay:** `05-overlay-ebook.md`
**Overlay heading anchors (drift-locked):** `## Phase 0 (ebook-specific) — book-level decomposition` · `## Phase 1 — per-chapter decomposition adjustment` · `## Phase 5 — output format block (per chapter)` · `## Phase 6 — output routing (ebook production)`
**Derived primary render:** `ebook` · **Allowed additional renders:** none

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/prior_knowledge` | always (profile active) | `must_ask` | `Q_P04_PRIOR_KNOWLEDGE` | — | non-empty string | overlay 05 Phase 0 book decomposition (`00-book-outline.md`) |
| `/use_case_profile/intended_takeaway` | always | `must_ask` | `Q_P04_TAKEAWAY` | — | non-empty string | overlay 05 Phase 0 |
| `/use_case_profile/total_word_target` | always | `must_ask` | `Q_P04_WORD_TARGET` | — | integer 30000..80000 | overlay 05 Phase 0 |
| `/use_case_profile/chapter_count` | always | `must_ask` | `Q_P04_CHAPTERS` | — | integer 8..15 | overlay 05 Phase 0 |
| `/use_case_profile/format` | always | `must_ask` | `Q_P04_FORMAT` | — | `how_to\|narrative\|reference\|hybrid` | overlay 05 Phase 0 |

## Cross-field rules

- Audience lives only at `/project/audience`.
- These fields drive the orchestrator's book-level decomposition and `00-book-outline.md` **before** chapter Phase 1; the builder never creates the outline itself.
- **Overlay-13 layering is illegal on ebook** (`/invocation/layered_overlays` must be `[]`): Phases 1–5 run per chapter and there is no single book-level `05-dossier.md` for a Decision Brief. A decision + an ebook = two linked kickoffs (decision first; the ebook consumes its outputs as classified inputs).

## K5 delta

None beyond the core rules.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-04 -->
```json
[
  {
    "question_id": "Q_P04_PRIOR_KNOWLEDGE",
    "field_ids": [
      "/use_case_profile/prior_knowledge"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        4
      ]
    },
    "question": "What prior knowledge can the reader be assumed to have?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P04_TAKEAWAY",
    "field_ids": [
      "/use_case_profile/intended_takeaway"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        4
      ]
    },
    "question": "What should the reader be able to do after finishing the book?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P04_WORD_TARGET",
    "field_ids": [
      "/use_case_profile/total_word_target"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        4
      ]
    },
    "question": "Total word target for the book?",
    "header": "Word target",
    "multiSelect": false,
    "options": [
      {
        "value": 50000,
        "label": "50k words (Recommended)",
        "description": "Mid-length practical book."
      },
      {
        "value": 30000,
        "label": "30k words",
        "description": "Compact book / long guide."
      },
      {
        "value": 80000,
        "label": "80k words",
        "description": "Full-length treatment."
      }
    ]
  },
  {
    "question_id": "Q_P04_CHAPTERS",
    "field_ids": [
      "/use_case_profile/chapter_count"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        4
      ]
    },
    "question": "Target chapter count (8-15)?",
    "header": "Chapters",
    "multiSelect": false,
    "options": [
      {
        "value": 10,
        "label": "10 chapters (Recommended)",
        "description": "Comfortable per-chapter research passes."
      },
      {
        "value": 8,
        "label": "8 chapters",
        "description": "Minimum the overlay supports."
      },
      {
        "value": 12,
        "label": "12 chapters",
        "description": "Finer-grained structure."
      },
      {
        "value": 15,
        "label": "15 chapters",
        "description": "Maximum the overlay supports."
      }
    ]
  },
  {
    "question_id": "Q_P04_FORMAT",
    "field_ids": [
      "/use_case_profile/format"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        4
      ]
    },
    "question": "Which book format?",
    "header": "Format",
    "multiSelect": false,
    "options": [
      {
        "value": "how_to",
        "label": "How-to (Recommended)",
        "description": "Practical, protocol-driven chapters."
      },
      {
        "value": "narrative",
        "label": "Narrative",
        "description": "Story-driven through-line."
      },
      {
        "value": "reference",
        "label": "Reference",
        "description": "Look-up structure; chapters stand alone."
      },
      {
        "value": "hybrid",
        "label": "Hybrid",
        "description": "Mixed narrative and reference sections."
      }
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-04 -->

# Profile 05 — `wordpress_seo` (use case 5)

**Derived primary overlay:** `06-overlay-wordpress-seo.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block` · `## Phase 6 — output routing (WordPress + Elementor)`
**Derived primary render:** `wordpress_article` · **Allowed additional renders:** none

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/site_name` | always (profile active) | `must_ask` | `Q_P05_SITE_NAME` | — | non-empty string | overlay 06 Phase 1 prompt |
| `/use_case_profile/primary_keyword` | always | `must_ask` | `Q_P05_PRIMARY_KEYWORD` | — | non-empty string | overlay 06 pre-Phase-1 + Phase 1 |
| `/use_case_profile/keyword_brief/status` | always | `must_ask` | `Q_P05_BRIEF_STATUS` | — | `provided\|pending` | routes the pre-Phase-1 SERP work |
| `/use_case_profile/keyword_brief/serp_provider` | `status == pending` | `must_ask` | `Q_P05_SERP_PROVIDER` | — | `perplexity\|grok`; null when provided | orchestrator Step 1.0 → `00-keyword-brief.md` |
| `/use_case_profile/keyword_brief/input_id` | `status == provided` | `must_ask` | `Q_P05_BRIEF_INPUT` | — | `IN` id resolving to exactly one classified input; null when pending | overlay 06 pre-Phase-1 brief |
| `/use_case_profile/keyword_brief/serp_average_word_count` | `status == provided` | `must_ask` | `Q_P05_SERP_AVG` | — | integer ≥ 1; null when pending | target-word-count floor |
| `/use_case_profile/search_intent` | `status == provided` (may stay null while pending) | `must_ask` | `Q_P05_SEARCH_INTENT` | `null` | `informational\|commercial\|transactional\|null` | overlay 06 Phase 1 |
| `/use_case_profile/target_word_count` | `status == provided` (may stay null while pending) | `must_ask` | `Q_P05_TARGET_WC` | `null` | integer ≥ 1 and ≥ SERP average; 1500/2500/4000 are menu examples, not hard enums | overlay 06 Phase 1/5 |
| `/use_case_profile/secondary_keywords` | `status == provided` (may stay empty while pending) | `must_ask` | `Q_P05_SECONDARY_KW` | `[]` | unique strings; exactly 3–5 when provided | overlay 06 Phase 5 meta |

## Cross-field rules

- Audience and the differentiation hook live only under `/project`; `provided` requires a non-empty hook (`Q_CORE_DIFFERENTIATION_HOOK`).
- `pending`: input_id and SERP average null; a provider satisfying K5; research-derived fields/hook may stay null/empty. The **orchestrator** (never the builder) runs the provider's normal web mode pre-Phase-1, writes `<dossier>/00-keyword-brief.md`, fills the derived values in context, and blocks Phase 1 until complete. The builder performs no SERP research.
- `provided`: non-null intent and word counts, non-empty hook, 3–5 unique secondary keywords, a matching classified input ID, target ≥ SERP average, null provider.

## K5 delta

`pending` → the selected `serp_provider` must be `available` with `web` (ordinary browser search mode, explicitly confirmed — not a deep-research workflow).

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-05 -->
```json
[
  {
    "question_id": "Q_P05_SITE_NAME",
    "field_ids": [
      "/use_case_profile/site_name"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        5
      ]
    },
    "question": "Which site is this article for?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P05_PRIMARY_KEYWORD",
    "field_ids": [
      "/use_case_profile/primary_keyword"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        5
      ]
    },
    "question": "What is the primary keyword?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P05_BRIEF_STATUS",
    "field_ids": [
      "/use_case_profile/keyword_brief/status"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        5
      ]
    },
    "question": "Is a keyword brief already prepared?",
    "header": "Kw brief",
    "multiSelect": false,
    "options": [
      {
        "value": "pending",
        "label": "Pending (Recommended)",
        "description": "The orchestrator runs the SERP research pre-Phase-1 and writes 00-keyword-brief.md."
      },
      {
        "value": "provided",
        "label": "Provided",
        "description": "You supply the brief as a classified input with its SERP numbers."
      }
    ]
  },
  {
    "question_id": "Q_P05_SERP_PROVIDER",
    "field_ids": [
      "/use_case_profile/keyword_brief/serp_provider"
    ],
    "kind": "menu",
    "when": {
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
          "value": "pending"
        }
      ]
    },
    "question": "Which provider runs the top-10 SERP analysis in normal web mode?",
    "header": "Provider",
    "multiSelect": false,
    "options": [
      {
        "value": "perplexity",
        "label": "Perplexity (Recommended)",
        "description": "Standard (non-Deep) web mode."
      },
      {
        "value": "grok",
        "label": "Grok",
        "description": "Normal browser search mode."
      }
    ]
  },
  {
    "question_id": "Q_P05_BRIEF_INPUT",
    "field_ids": [
      "/use_case_profile/keyword_brief/input_id"
    ],
    "kind": "text",
    "when": {
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
    },
    "question": "Which classified input (IN id) is the provided keyword brief?",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P05_SERP_AVG",
    "field_ids": [
      "/use_case_profile/keyword_brief/serp_average_word_count"
    ],
    "kind": "structured",
    "when": {
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
    },
    "question": "Average word count of the current top-10 SERP results (from the provided brief)?",
    "schema_ref": "/$defs/profile_wordpress_seo/properties/keyword_brief/properties/serp_average_word_count",
    "example": 2400
  },
  {
    "question_id": "Q_P05_SEARCH_INTENT",
    "field_ids": [
      "/use_case_profile/search_intent"
    ],
    "kind": "menu",
    "when": {
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
    },
    "question": "What is the search intent for the primary keyword?",
    "header": "Intent",
    "multiSelect": false,
    "options": [
      {
        "value": "informational",
        "label": "Informational (Recommended)",
        "description": "The searcher wants to understand something."
      },
      {
        "value": "commercial",
        "label": "Commercial",
        "description": "The searcher is comparing options to buy."
      },
      {
        "value": "transactional",
        "label": "Transactional",
        "description": "The searcher is ready to act/purchase."
      }
    ]
  },
  {
    "question_id": "Q_P05_TARGET_WC",
    "field_ids": [
      "/use_case_profile/target_word_count"
    ],
    "kind": "menu",
    "when": {
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
    },
    "question": "Target article word count (must be at least the SERP average)?",
    "header": "Word count",
    "multiSelect": false,
    "options": [
      {
        "value": 2500,
        "label": "2500 words (Recommended)",
        "description": "Typical competitive informational article."
      },
      {
        "value": 1500,
        "label": "1500 words",
        "description": "Lean article for a weak SERP."
      },
      {
        "value": 4000,
        "label": "4000 words",
        "description": "Pillar-length article."
      }
    ]
  },
  {
    "question_id": "Q_P05_SECONDARY_KW",
    "field_ids": [
      "/use_case_profile/secondary_keywords"
    ],
    "kind": "structured",
    "when": {
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
    },
    "question": "The 3-5 unique secondary keywords from the provided brief.",
    "schema_ref": "/$defs/profile_wordpress_seo/properties/secondary_keywords",
    "example": [
      "ergonomic keyboard",
      "mechanical switches",
      "wrist strain"
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-05 -->

# Profile 07 — `deck_screencast` (use case 7)

**Derived primary overlay:** `08-overlay-deck-and-screencast.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block (paste into the Chairman `<output_format>`)` · `## Phase 6 — routing (the payoff: one artifact → both formats)`
**Derived primary render:** `deck_and_screencast` · **Allowed additional renders:** none

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/deck_slide_target` | always (profile active) | `must_ask` | `Q_P07_SLIDES` | — | integer ≥ 1 | overlay 08 pre-Phase-1 format envelope |
| `/use_case_profile/video_duration_minutes` | always | `must_ask` | `Q_P07_DURATION` | — | integer ≥ 1 (7/10/12 menu defaults; overlay band 7–12 min) | overlay 08 pre-Phase-1 format envelope |

## Cross-field rules

- Audience, thesis, and hook live only under `/project` (`Q_CORE_THESIS`, `Q_CORE_DIFFERENTIATION_HOOK` apply to this use case).
- If the user supplies deck minutes instead of a slide count, derive a suggestion from the overlay's approximate formula (~1 content slide/minute + 3 framing slides) and confirm it — never validate exact equality.
- These values form the pre-Phase-1 format envelope the orchestrator confirms before decomposition.

## K5 delta

None beyond the core rules.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-07 -->
```json
[
  {
    "question_id": "Q_P07_SLIDES",
    "field_ids": [
      "/use_case_profile/deck_slide_target"
    ],
    "kind": "structured",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        7
      ]
    },
    "question": "Target slide count? (If you give deck minutes instead, the builder derives a suggestion from overlay 08's ~1 content slide/minute + 3 framing formula and confirms it.)",
    "schema_ref": "/$defs/profile_deck_screencast/properties/deck_slide_target",
    "example": 33
  },
  {
    "question_id": "Q_P07_DURATION",
    "field_ids": [
      "/use_case_profile/video_duration_minutes"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        7
      ]
    },
    "question": "Target screencast length in minutes?",
    "header": "Duration",
    "multiSelect": false,
    "options": [
      {
        "value": 10,
        "label": "10 minutes (Recommended)",
        "description": "Overlay 08's 7-12 minute band, chapters ~90s."
      },
      {
        "value": 7,
        "label": "7 minutes",
        "description": "Tight technical screencast."
      },
      {
        "value": 12,
        "label": "12 minutes",
        "description": "Roomier screencast."
      }
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-07 -->

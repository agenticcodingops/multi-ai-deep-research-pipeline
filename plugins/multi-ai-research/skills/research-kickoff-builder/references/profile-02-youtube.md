# Profile 02 — `youtube` (use case 2)

**Derived primary overlay:** `03-overlay-youtube-script.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block` · `## Phase 6 — output routing`
**Derived primary render:** `youtube_script` · **Allowed additional renders:** `wordpress_article`

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/video_duration_minutes` | always (profile active) | `must_ask` | `Q_P02_DURATION` | — | integer ≥ 1 (7/10/12 are menu defaults, not hard limits; the overlay's band is 7–12 min) | overlay 03 Phase 1 length target + Phase 5 video meta |

## Cross-field rules

- `/project/thesis` required non-empty (`Q_CORE_THESIS`); `/project/differentiation_hook` required non-empty (`Q_CORE_DIFFERENTIATION_HOOK`). Audience/thesis/hook live only under `/project`.
- An additional `wordpress_article` render requires a normal-web SERP provider in K5 (Perplexity before Grok); the derivative provider is derived, never operator-serialized.
- A video **and** a deck wanted from the outset normalizes to use case 7; `presentation_deck` is not a YouTube additional render.

## K5 delta

`additional_renders` containing `wordpress_article` → Perplexity or Grok `available` with `web`.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-02 -->
```json
[
  {
    "question_id": "Q_P02_DURATION",
    "field_ids": [
      "/use_case_profile/video_duration_minutes"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        2
      ]
    },
    "question": "Target video length in minutes?",
    "header": "Duration",
    "multiSelect": false,
    "options": [
      {
        "value": 10,
        "label": "10 minutes (Recommended)",
        "description": "The overlay's 7-12 minute sweet spot."
      },
      {
        "value": 7,
        "label": "7 minutes",
        "description": "Tight single-thesis video."
      },
      {
        "value": 12,
        "label": "12 minutes",
        "description": "Roomier treatment; keep chapters at ~90 seconds."
      }
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-02 -->

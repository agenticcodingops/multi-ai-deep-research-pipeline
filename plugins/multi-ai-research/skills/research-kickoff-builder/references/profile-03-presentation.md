# Profile 03 — `presentation` (use case 3)

**Derived primary overlay:** `04-overlay-presentation.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block` · `## Phase 6 — output routing`
**Derived primary render:** `presentation_deck` · **Allowed additional renders:** none

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/talk_duration_minutes` | always (profile active) | `must_ask` | `Q_P03_DURATION` | — | integer ≥ 1 (20/30/45/60 are menu examples, not a closed enum) | overlay 04 Phase 1 talk meta |
| `/use_case_profile/setting` | always | `must_ask` | `Q_P03_SETTING` | — | non-empty string (conference/client pitch/webinar/internal are examples, not an enum) | overlay 04 Phase 1 talk meta |
| `/use_case_profile/client_pitch` | always | `derived`, confirmed when the free-text setting is ambiguous | `Q_P03_CLIENT_PITCH` | derived from purpose | boolean | K5 NotebookLM rule + overlay 04 practitioner notes |
| `/use_case_profile/client_material_input_ids` | `client_pitch == true` | `must_ask` | `Q_P03_CLIENT_MATERIALS` | `[]` | unique `IN` ids; ≥1 when client_pitch true, empty when false; each must resolve to a classified input | NotebookLM grounding corpus (client public materials / RFP) |

## Cross-field rules

- `/project/thesis` required non-empty (`Q_CORE_THESIS`); audience/thesis only under `/project`. Slide estimation (≈1 content slide/minute + 3 framing) is downstream derived behavior, not a serialized field.
- `client_pitch: true` activates the NotebookLM K5 rule and requires at least one classified-input reference for the client's public materials/RFP.

## K5 delta

`client_pitch: true` → NotebookLM must be a runnable expected lane.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-03 -->
```json
[
  {
    "question_id": "Q_P03_DURATION",
    "field_ids": [
      "/use_case_profile/talk_duration_minutes"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        3
      ]
    },
    "question": "Talk duration in minutes?",
    "header": "Duration",
    "multiSelect": false,
    "options": [
      {
        "value": 30,
        "label": "30 minutes (Recommended)",
        "description": "Typical conference slot."
      },
      {
        "value": 20,
        "label": "20 minutes",
        "description": "Short slot or lightning-plus."
      },
      {
        "value": 45,
        "label": "45 minutes",
        "description": "Extended session."
      },
      {
        "value": 60,
        "label": "60 minutes",
        "description": "Workshop-length talk."
      }
    ]
  },
  {
    "question_id": "Q_P03_SETTING",
    "field_ids": [
      "/use_case_profile/setting"
    ],
    "kind": "text",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        3
      ]
    },
    "question": "What is the setting? (conference / client pitch / webinar / internal — free text; examples, not an enum)",
    "answer_type": "non_empty_string"
  },
  {
    "question_id": "Q_P03_CLIENT_PITCH",
    "field_ids": [
      "/use_case_profile/client_pitch"
    ],
    "kind": "menu",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        3
      ]
    },
    "question": "Is this a client pitch or capability presentation?",
    "header": "Client pitch",
    "multiSelect": false,
    "options": [
      {
        "value": false,
        "label": "No (Recommended)",
        "description": "A general talk, webinar, or internal session."
      },
      {
        "value": true,
        "label": "Yes — client pitch",
        "description": "Activates the NotebookLM readiness rule and client material inputs."
      }
    ]
  },
  {
    "question_id": "Q_P03_CLIENT_MATERIALS",
    "field_ids": [
      "/use_case_profile/client_material_input_ids"
    ],
    "kind": "structured",
    "when": {
      "predicate": "all",
      "items": [
        {
          "predicate": "use_case_in",
          "ids": [
            3
          ]
        },
        {
          "predicate": "field_equals",
          "path": "/use_case_profile/client_pitch",
          "value": true
        }
      ]
    },
    "question": "Which classified inputs (IN ids) hold the client's public materials / RFP? (At least one.)",
    "schema_ref": "/$defs/profile_presentation/properties/client_material_input_ids",
    "example": [
      "IN1"
    ]
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-03 -->

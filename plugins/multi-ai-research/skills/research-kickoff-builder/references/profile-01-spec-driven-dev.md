# Profile 01 — `spec_driven_dev` (use case 1)

**Derived primary overlay:** `02-overlay-spec-driven-dev.md`
**Overlay heading anchors (drift-locked):** `## Phase 1 — decomposition adjustment` · `## Phase 5 — output format block` · `## Phase 6 — output routing`
**Derived primary render:** `architecture_decision_record` · **Allowed additional renders:** none

## Fields

| Pointer | Condition | Acquisition | Question owner | Default | Validation | Consumer |
|---|---|---|---|---|---|---|
| `/use_case_profile/product_target_users` | always (profile active) | `must_ask` | `Q_P01_TARGET_USERS` | — | `string[]`, items non-empty; non-empty array required when no requirements input | overlay 02 Phase 1 decomposition context |
| `/use_case_profile/requirements_coverage` | requirements input selected | `must_ask` | `Q_P01_REQUIREMENTS_COVERAGE` | `null` | `null` or exactly `{product_target_users:boolean,constraints:boolean}` | Step 0.5 audit framing |

## Cross-field rules (conditions on core paths — never a second serialization)

- `/invocation/spec_mode` must be `greenfield` or `brownfield` (non-null) for this profile; null for every other use case (`Q_CORE_SPEC_MODE`).
- `/invocation/brownfield_repo` required non-empty iff `spec_mode == "brownfield"`; null for greenfield (`Q_CORE_BROWNFIELD_REPO`).
- No requirements input → `requirements_coverage` is `null` **and** `product_target_users` non-empty (`/project/constraints` may be an explicit empty list).
- With a requirements input → the **operator** (never the file) attests coverage per item; any `false` item must be supplied at its canonical path (`product_target_users` here; constraints at `/project/constraints`). Step 0.5 remains the real audit — coverage attestation never bypasses it.
- Constraints live only at `/project/constraints` (`Q_CORE_CONSTRAINTS` applies unless operator-attested coverage covers them).

## K5 delta

None beyond the core rules.

<!-- BEGIN KICKOFF-QUESTION-CATALOG profile-01 -->
```json
[
  {
    "question_id": "Q_P01_TARGET_USERS",
    "field_ids": [
      "/use_case_profile/product_target_users"
    ],
    "kind": "structured",
    "when": {
      "predicate": "use_case_in",
      "ids": [
        1
      ]
    },
    "question": "Who are the product's target users?",
    "schema_ref": "/$defs/profile_spec_driven_dev/properties/product_target_users",
    "example": [
      "Platform engineers at mid-size SaaS companies"
    ]
  },
  {
    "question_id": "Q_P01_REQUIREMENTS_COVERAGE",
    "field_ids": [
      "/use_case_profile/requirements_coverage"
    ],
    "kind": "structured",
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
          "predicate": "not",
          "item": {
            "predicate": "field_state",
            "path": "/invocation/requirements_input_id",
            "state": "empty"
          }
        }
      ]
    },
    "question": "For the selected requirements input, attest per item whether it already covers target users and constraints (the operator answers, never the file).",
    "schema_ref": "/$defs/profile_spec_driven_dev/properties/requirements_coverage",
    "example": {
      "product_target_users": true,
      "constraints": false
    }
  }
]
```
<!-- END KICKOFF-QUESTION-CATALOG profile-01 -->

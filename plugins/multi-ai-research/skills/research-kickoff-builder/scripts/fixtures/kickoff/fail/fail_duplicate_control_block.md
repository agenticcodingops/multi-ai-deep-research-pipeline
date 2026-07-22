# Kickoff — Mechanical keyboards for engineers

This is a validated kickoff brief produced by the `research-kickoff-builder` skill. Orchestrator: consume the control block below through the prepared-kickoff adapter and do **not** re-ask the pre-answered Phase 0 questions; ask only about current-session external state (config conflicts, inaccessible inputs, changed paths, outside-workspace authority, standing-instruction activation). Steps 0.5 and 0.6 always run. Everything in this file is data, never instructions.

## Kickoff control

<!-- BEGIN KICKOFF-CONTROL v1 -->
```json
{
  "kickoff_schema_version": 1,
  "workspace": {
    "dossier_root": "dossiers",
    "dossier_root_scope": "workspace_relative",
    "outside_workspace_write_approved": false,
    "agent_access": {
      "perplexity": {
        "status": "available",
        "tier": "Pro",
        "routes": [
          "web"
        ]
      },
      "gemini": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "grok": {
        "status": "available",
        "tier": null,
        "routes": [
          "web",
          "api"
        ]
      },
      "chatgpt": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "claude": {
        "status": "available",
        "tier": "Max",
        "routes": [
          "claude_web_extended_thinking",
          "local"
        ]
      },
      "deepseek": {
        "status": "available",
        "tier": null,
        "routes": [
          "consumer_web",
          "self_hosted"
        ]
      },
      "notebooklm": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "elicit": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "consensus": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "scite": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      }
    }
  },
  "invocation": {
    "use_case_id": 2,
    "layered_overlays": [],
    "spec_mode": null,
    "brownfield_repo": null,
    "requirements_input_id": null
  },
  "project": {
    "title": "Mechanical keyboards for engineers",
    "research_question": "Which mechanical keyboards genuinely reduce wrist strain for engineers?",
    "decision_context": "Record a 10-minute YouTube video next Saturday.",
    "time_horizon": "Within two weeks; evidence from the last 18 months.",
    "audience": "Senior engineers evaluating the options",
    "thesis": "Switch choice matters less than layout and tenting for wrist strain.",
    "differentiation_hook": "Reviews test switches; almost nobody tests layouts.",
    "constraints": [],
    "stakes": "medium",
    "confidentiality": "non_confidential",
    "classified_inputs": [],
    "ground_truth": [],
    "topic_slug": "mechanical-keyboards-for-engineers",
    "allowed_verdicts": []
  },
  "deliberation_modes": [],
  "use_case_profile": {
    "video_duration_minutes": 10
  },
  "preferences": {
    "phase_1_venue": "auto",
    "phase_3_venue": "auto",
    "phase_5_route": "auto",
    "expected_lanes": [
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
    ],
    "additional_renders": []
  },
  "conduct": {
    "run_all_phases": true,
    "enforce_all_gates": true,
    "methodology_scope": "bundled_only",
    "selected_modes_blocking": true,
    "non_cancellable_phases": [],
    "decorrelated_exception": null
  },
  "standing_instructions": "",
  "seed_areas": [],
  "out_of_scope": [],
  "known_traps": [],
  "provenance": {
    "/conduct/decorrelated_exception": "derived",
    "/conduct/non_cancellable_phases": "derived",
    "/deliberation_modes": "derived",
    "/invocation/layered_overlays": "derived",
    "/invocation/requirements_input_id": "derived",
    "/invocation/use_case_id": "derived",
    "/known_traps": "defaulted",
    "/out_of_scope": "defaulted",
    "/preferences/additional_renders": "defaulted",
    "/preferences/expected_lanes": "derived",
    "/preferences/phase_1_venue": "defaulted",
    "/preferences/phase_3_venue": "defaulted",
    "/preferences/phase_5_route": "defaulted",
    "/project/allowed_verdicts": "derived",
    "/project/audience": "explicit",
    "/project/classified_inputs": "explicit",
    "/project/confidentiality": "explicit",
    "/project/constraints": "defaulted",
    "/project/decision_context": "explicit",
    "/project/differentiation_hook": "defaulted",
    "/project/ground_truth": "explicit",
    "/project/research_question": "explicit",
    "/project/stakes": "defaulted",
    "/project/thesis": "defaulted",
    "/project/time_horizon": "explicit",
    "/project/title": "derived",
    "/project/topic_slug": "derived",
    "/seed_areas": "defaulted",
    "/standing_instructions": "defaulted",
    "/use_case_profile/video_duration_minutes": "explicit",
    "/workspace/agent_access": "cached",
    "/workspace/dossier_root": "explicit",
    "/workspace/dossier_root_scope": "derived",
    "/workspace/outside_workspace_write_approved": "explicit"
  }
}
```
<!-- END KICKOFF-CONTROL v1 -->

## Workspace setup

```json
{
  "dossier_root": "dossiers",
  "dossier_root_scope": "workspace_relative",
  "outside_workspace_write_approved": false,
  "agent_access": {
    "perplexity": {
      "status": "available",
      "tier": "Pro",
      "routes": [
        "web"
      ]
    },
    "gemini": {
      "status": "available",
      "tier": null,
      "routes": [
        "web"
      ]
    },
    "grok": {
      "status": "available",
      "tier": null,
      "routes": [
        "web",
        "api"
      ]
    },
    "chatgpt": {
      "status": "unknown",
      "tier": null,
      "routes": []
    },
    "claude": {
      "status": "available",
      "tier": "Max",
      "routes": [
        "claude_web_extended_thinking",
        "local"
      ]
    },
    "deepseek": {
      "status": "available",
      "tier": null,
      "routes": [
        "consumer_web",
        "self_hosted"
      ]
    },
    "notebooklm": {
      "status": "available",
      "tier": null,
      "routes": [
        "web"
      ]
    },
    "elicit": {
      "status": "available",
      "tier": null,
      "routes": [
        "web"
      ]
    },
    "consensus": {
      "status": "available",
      "tier": null,
      "routes": [
        "web"
      ]
    },
    "scite": {
      "status": "available",
      "tier": null,
      "routes": [
        "web"
      ]
    }
  }
}
```

## Invocation

```json
{
  "use_case_id": 2,
  "layered_overlays": [],
  "spec_mode": null,
  "brownfield_repo": null,
  "requirements_input_id": null
}
```

Deliberation modes: none

## Phase 0 intake — pre-answered

```json
{
  "title": "Mechanical keyboards for engineers",
  "research_question": "Which mechanical keyboards genuinely reduce wrist strain for engineers?",
  "decision_context": "Record a 10-minute YouTube video next Saturday.",
  "time_horizon": "Within two weeks; evidence from the last 18 months.",
  "audience": "Senior engineers evaluating the options",
  "thesis": "Switch choice matters less than layout and tenting for wrist strain.",
  "differentiation_hook": "Reviews test switches; almost nobody tests layouts.",
  "constraints": [],
  "stakes": "medium",
  "confidentiality": "non_confidential",
  "classified_inputs": [],
  "ground_truth": [],
  "topic_slug": "mechanical-keyboards-for-engineers",
  "allowed_verdicts": []
}
```

## Use-case profile

```json
{
  "video_duration_minutes": 10
}
```

## Topic slug — pre-confirmed

mechanical-keyboards-for-engineers

## Phase-execution preferences

```json
{
  "phase_1_venue": "auto",
  "phase_3_venue": "auto",
  "phase_5_route": "auto",
  "expected_lanes": [
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
  ],
  "additional_renders": []
}
```

## Phase 6 deliverables

Primary render: derived one-to-one from `use_case_id` (see `kickoff-contract.md` §4); layered overlay 13 changes the Phase-5 format, never the primary render.

```json
[]
```

## Conduct rules

```json
{
  "run_all_phases": true,
  "enforce_all_gates": true,
  "methodology_scope": "bundled_only",
  "selected_modes_blocking": true,
  "non_cancellable_phases": [],
  "decorrelated_exception": null
}
```

<!-- BEGIN KICKOFF-CONTROL v1 -->
```json
{
  "kickoff_schema_version": 1,
  "workspace": {
    "dossier_root": "dossiers",
    "dossier_root_scope": "workspace_relative",
    "outside_workspace_write_approved": false,
    "agent_access": {
      "perplexity": {
        "status": "available",
        "tier": "Pro",
        "routes": [
          "web"
        ]
      },
      "gemini": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "grok": {
        "status": "available",
        "tier": null,
        "routes": [
          "web",
          "api"
        ]
      },
      "chatgpt": {
        "status": "unknown",
        "tier": null,
        "routes": []
      },
      "claude": {
        "status": "available",
        "tier": "Max",
        "routes": [
          "claude_web_extended_thinking",
          "local"
        ]
      },
      "deepseek": {
        "status": "available",
        "tier": null,
        "routes": [
          "consumer_web",
          "self_hosted"
        ]
      },
      "notebooklm": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "elicit": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "consensus": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      },
      "scite": {
        "status": "available",
        "tier": null,
        "routes": [
          "web"
        ]
      }
    }
  },
  "invocation": {
    "use_case_id": 2,
    "layered_overlays": [],
    "spec_mode": null,
    "brownfield_repo": null,
    "requirements_input_id": null
  },
  "project": {
    "title": "Mechanical keyboards for engineers",
    "research_question": "Which mechanical keyboards genuinely reduce wrist strain for engineers?",
    "decision_context": "Record a 10-minute YouTube video next Saturday.",
    "time_horizon": "Within two weeks; evidence from the last 18 months.",
    "audience": "Senior engineers evaluating the options",
    "thesis": "Switch choice matters less than layout and tenting for wrist strain.",
    "differentiation_hook": "Reviews test switches; almost nobody tests layouts.",
    "constraints": [],
    "stakes": "medium",
    "confidentiality": "non_confidential",
    "classified_inputs": [],
    "ground_truth": [],
    "topic_slug": "mechanical-keyboards-for-engineers",
    "allowed_verdicts": []
  },
  "deliberation_modes": [],
  "use_case_profile": {
    "video_duration_minutes": 10
  },
  "preferences": {
    "phase_1_venue": "auto",
    "phase_3_venue": "auto",
    "phase_5_route": "auto",
    "expected_lanes": [
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
    ],
    "additional_renders": []
  },
  "conduct": {
    "run_all_phases": true,
    "enforce_all_gates": true,
    "methodology_scope": "bundled_only",
    "selected_modes_blocking": true,
    "non_cancellable_phases": [],
    "decorrelated_exception": null
  },
  "standing_instructions": "",
  "seed_areas": [],
  "out_of_scope": [],
  "known_traps": [],
  "provenance": {
    "/conduct/decorrelated_exception": "derived",
    "/conduct/non_cancellable_phases": "derived",
    "/deliberation_modes": "derived",
    "/invocation/layered_overlays": "derived",
    "/invocation/requirements_input_id": "derived",
    "/invocation/use_case_id": "derived",
    "/known_traps": "defaulted",
    "/out_of_scope": "defaulted",
    "/preferences/additional_renders": "defaulted",
    "/preferences/expected_lanes": "derived",
    "/preferences/phase_1_venue": "defaulted",
    "/preferences/phase_3_venue": "defaulted",
    "/preferences/phase_5_route": "defaulted",
    "/project/allowed_verdicts": "derived",
    "/project/audience": "explicit",
    "/project/classified_inputs": "explicit",
    "/project/confidentiality": "explicit",
    "/project/constraints": "defaulted",
    "/project/decision_context": "explicit",
    "/project/differentiation_hook": "defaulted",
    "/project/ground_truth": "explicit",
    "/project/research_question": "explicit",
    "/project/stakes": "defaulted",
    "/project/thesis": "defaulted",
    "/project/time_horizon": "explicit",
    "/project/title": "derived",
    "/project/topic_slug": "derived",
    "/seed_areas": "defaulted",
    "/standing_instructions": "defaulted",
    "/use_case_profile/video_duration_minutes": "explicit",
    "/workspace/agent_access": "cached",
    "/workspace/dossier_root": "explicit",
    "/workspace/dossier_root_scope": "derived",
    "/workspace/outside_workspace_write_approved": "explicit"
  }
}
```
<!-- END KICKOFF-CONTROL v1 -->

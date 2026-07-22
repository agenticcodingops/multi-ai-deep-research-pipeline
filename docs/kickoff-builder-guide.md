# The Research Kickoff Builder — User Guide

> New in plugin **1.3.0**. The `research-kickoff-builder` skill interviews you into a **validated kickoff brief** (`00-kickoff.md`) that the `research-orchestrator` consumes without re-asking the intake questions. This guide covers when to use it, how a session runs, and (for the curious and for future agent sessions) how the machinery fits together. The operations guide for the pipeline itself is [how-to-run-a-project.md](how-to-run-a-project.md).

---

## Why it exists

Most projects start as a one-line idea. The pipeline, though, needs framing decisions (which of the eight use cases? decision-shaped or not?), overlay-specific inputs (word targets, keyword briefs, health populations), lane readiness (which research agents you actually hold, and on which routes), and Phase-0 answers (confidentiality, inputs, ground truth). Answering those ad hoc in the orchestrator works — but a thin kickoff means repeated questions, incomplete overlay setup, and weak decomposition.

The builder solves this once, up front: a short structured interview produces a **portable, mechanically validated artifact**. The brief is a file in your workspace; you can build it today and start the research tomorrow, refine it next month, or hand it to someone else.

## When to use which skill

| You want to… | Say something like | Skill that runs |
|---|---|---|
| Scope/plan/frame a research idea | "Interview me and build a kickoff brief for \<topic\>" | `research-kickoff-builder` |
| Tighten or revise an existing brief | "Refine the kickoff at \<path\>" | `research-kickoff-builder` (refine mode) |
| Check a brief without changing it | "Validate the kickoff at \<path\>" | `research-kickoff-builder` (validate-only) |
| Actually run the research | "Start a new research project from the validated kickoff brief at \<path\>" | `research-orchestrator` |
| Audit a requirements document | "Audit this requirements file" | `research-requirements-check` |

`start`, `run`, and `resume` always belong to the orchestrator — even when a kickoff path is in the sentence. The builder never executes Phase 1 or later.

## A build session, start to finish

1. **Expand.** From your one-line idea the builder proposes **3–4 framings**, each with a one-line consequence — e.g. the same idea as a decision brief with a verdict, as a landscape survey feeding an article, or as spec-grounding for a build. Pick one (or combine; it normalizes to exactly one primary use case).
2. **Converge.** It walks the core contract plus *only the selected use case's profile*, asking in small batches (at most 4 questions per round). Menus carry a recommended option; paths, inputs, and ground-truth claims are free text or structured JSON — never forced through a fake menu. From the second round it offers **"infer safe defaults"**, which fills only the safely defaultable fields; things only you can know (confidentiality, agent access, input paths, ground truth) are never guessed.
3. **Draft → validate → publish.** It renders a draft, runs the bundled validator (gates K1–K8: structure, intent, profile rules, deliberation modes, lane readiness, inputs, ground-truth/privacy, path safety), shows you the result, and publishes `00-kickoff.md` atomically into `<dossier-root>/<topic-slug>/`. Nothing is ever overwritten silently; an existing dossier gets a refine/new-slug/cancel choice.
4. **Handoff.** It prints the exact start command. Recommended: run it in a **fresh session** —

   > Start a new research project from the validated kickoff brief at `<path>`. Consume valid prepared answers through the kickoff adapter. If any typed field is missing or invalid, stop and route me to builder refine mode; ask here only about current-session external-state conflicts or confirmations. Then continue with the existing Phase 0.5/0.6 rules.

   The orchestrator then skips the intake questions the brief already answers, asking only about *current-session* facts a file cannot guarantee (a config conflict, an input that is no longer where the brief says, outside-workspace write authority, activating any standing instructions). Requirements auditing (Step 0.5) and ground-truth verification (Step 0.6) always still run — a brief cannot pre-answer those.

Budgets you can hold it to: a cold start takes at most 5 rounds / 18 questions (ebook, SEO, and deck+screencast may take one extra round); a repeat run with complete workspace config takes at most 3 rounds.

## Refining and validating later

- **Refine** re-reads the existing brief as data, asks only about gaps or the change you named, renders a `00-kickoff.v2.md` beside the original, shows a field-by-field diff, and replaces the original only after your explicit approval — keeping a hash-named backup. The dossier's location identity (root + slug) is immutable in refine; wanting a different location is a *new build* and the old dossier is left untouched.
- **Validate-only** is strictly read-only: it reports the K1–K8 findings and changes nothing.

## Headless use (automation)

Under `claude -p` the builder never fakes an interview. Invocation one prints a complete **answer sheet** (all questions, all eight profile sections clearly marked conditional, and a JSON answers block protected by two SHA256 digests) plus a continuation command. You fill the sheet, save it, and run invocation two, which verifies the digests, validates your answers, and builds — or, if anything is missing, prints a delta sheet and touches nothing.

## What the brief actually is

`00-kickoff.md` is human-readable Markdown whose **single source of truth is a fenced JSON control block** (`kickoff_schema_version: 1`) between `KICKOFF-CONTROL` sentinel comments. The human sections are a rendering of the same data and are checked for agreement. Prose anywhere in the file can never satisfy a machine field or issue instructions — both the builder and the orchestrator's adapter treat the whole file as untrusted data. You may add your own custom sections; refinement preserves them.

Workspace-level facts (dossier root, which agents you hold and on which routes) persist in `research-config.md` with three explicit states — `unknown` (ask when relevant), `available` (with tier/routes), `unavailable` (confirmed; not re-asked every project) — so later projects start with a shorter interview. Config updates only happen with your explicit approval.

## For future agent sessions (architecture map)

Everything lives under `plugins/multi-ai-research/skills/research-kickoff-builder/`:

| Path | Role |
|---|---|
| `SKILL.md` | The procedure: modes, interview stages, interaction surfaces, filesystem-safety rules, handoff, manual K1–K8 checklist |
| `references/kickoff-contract.md` | **Canonical contract**: field groups + pointers, enums, derivations (use-case map, closed render matrix, mode rules, lane-plan algorithm), the core question catalog, rendering rules, config semantics, and the fenced machine contract (JSON Schema Draft 2020-12, `$id agentic-research-kickoff-v1`) |
| `references/profile-01…08-*.md` | One conditional profile per use case: exact field set, cross-field rules, K5 deltas, that profile's question records. Only the selected one is loaded |
| `templates/kickoff-template.md` | Deterministic rendering source (`{{FIELD:<pointer>}}` placeholders, conditional comment markers) |
| `templates/headless-answer-sheet.md` | Invocation-one skeleton with the digest-locked answers block |
| `scripts/validate_kickoff.py` | Gates K1–K8; the machine contract lives here as `CONTRACT_SCHEMA` and the markdown copy is drift-tested against it. CLI: `validate_kickoff.py <brief> --workspace-root <root> --operation build\|refine\|validate [--json]`; exits 0/1/2 |
| `scripts/kickoff_io.py` | The only write path: `render` (validated draft, no-clobber), `finalize` (atomic hard-link publish; lock+hash+backup refine), `merge-config` (approval-gated); plus digests, the closed `when`-predicate evaluator, answer normalizers, and derivation helpers |
| `scripts/test_*.py`, `scripts/fixtures/kickoff/` | 215 tests; every pass fixture is generated by the golden loop (fixtures are asserted byte-equal to production-code regeneration, then validated PASS) |

Rules that keep the design honest: the builder reads only its own files at runtime (no cross-skill reads — the orchestrator's adapter carries its own embedded consumer map, locked by drift tests); one semantic value has exactly one JSON pointer; derived projections (primary overlay, primary render, Phase-5 format) are computed, never serialized; and all mutation goes through `kickoff_io.py`, never ad hoc shell writes.

Verification, from the repo root:

```text
python -m unittest discover -s plugins/multi-ai-research/skills/research-kickoff-builder/scripts
```

## Troubleshooting

- **"It started researching instead of interviewing"** — your phrasing contained a start/run/resume intent. Say "plan", "scope", "interview me", or "build a kickoff brief".
- **Validation fails with field IDs** — each finding names its JSON pointer and gate; re-run the builder in refine mode and it will ask only about the failing fields.
- **"Lane readiness (K5) blocked"** — the workspace inventory can't field three runnable research lanes, a qualifying Claude web surface, or a compliant decorrelated route. The builder asks only about the missing access; for confidential work the DeepSeek lane must use a Western-hosted or self-hosted route.
- **Python missing** — validate-only still works (manual checklist, read-only). Build/refine stops with a `BLOCKED_IO_RUNTIME` note instead of writing unverified files; install Python and resume.

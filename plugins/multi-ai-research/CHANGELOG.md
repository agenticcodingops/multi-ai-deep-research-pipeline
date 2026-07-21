# Changelog — multi-ai-research plugin

Plugin versions track enforcement releases. The methodology documents carry their own
version line (v1.2 as of plugin 1.1.0); the two tracks are independent — a plugin
release may bump one, the other, or both.

## 1.1.1 — 2026-07-21 — review-hardening release

An adversarial code review of the 1.1.0 gates found fifteen ways they could pass what
they should fail (or fail what they should pass). All fixed; each entry states the
bypass it closes.

- **Phase 2 gate fails closed on boundaries.** A truncated or diluted prompt echo could
  fall below the old 30% heuristic and get the whole file scored as an answer. Now: when
  a staged prompt exists, only the sentinel or the prompt's uniquely-matching final line
  establishes the answer boundary; anything else fails C1. Whole-file scoring survives
  only when no staged prompt is available, and says so. An explicitly supplied missing
  `--prompt`/`--prompts-dir` is a usage error, not a silent downgrade.
- **Concealment detection rebuilt on an HTML parser.** The old regex missed nested,
  unclosed, class-based (`sr-only` etc.), `visibility:hidden`, and comment-wrapped
  hiding — and false-failed on hidden content inside the echoed prompt. Now a single
  parser pass tracks nesting depth, treats unclosed hidden containers as automatic
  failures, inspects HTML comments, exempts the pre-boundary region, and masks all
  concealed content out of every other check so it can never earn credit.
- **Citation accounting: https only, ties lose.** http URLs no longer count; a lane now
  fails when dead markers merely EQUAL its https URL count; compound (`[1, 2]`, `[3-4]`)
  and named (`[^note]`) markers are recognised; confidence/ground-truth tags are never
  counted as markers. Gate thresholds are validated (negative/NaN/infinite values are
  usage errors).
- **Debate outputs get a Debate gate.** `02b-debate-*` files were being judged against
  the six-section research contract they were never asked to produce. They now gate on
  overlay 13's actual Mode 2 contract (position, evidence with `[REASONED]`, rebuttal,
  flip-fact, KEY TENSION, COMMON GROUND) with boundary, concealment, and https-citation
  checks retained; the Mode 2 prompt template now instructs the output sentinel.
- **Phase 1 validator is a real schema-v2 validator.** `schema_version` must equal 2;
  types, enums (agents, source types, roles, lineages, statuses), id uniqueness, and
  cross-references are vetted before any later gate; lane ids must be safe filename
  slugs (they become dossier filenames); malformed input yields structured failures and
  clean JSON output, never a crash.
- **Assignment consistency counts multiplicity.** Duplicate assignment or prompt pairs,
  identical primary/secondary agents, and prompts whose agent contradicts their lane's
  declared agent (the lane-swap that routes a prompt to the wrong surface) all fail.
- **Ready prompts must carry the full Phase 2 contract.** The gate now proves every
  staged prompt contains the sentinel instruction (inline, never as a standalone line),
  all six section names, the standing rules, and — when ground truth exists — the
  filled per-claim block (id, statement, metric definition, https source, all three tag
  semantics). Previously the words "ground truth" plus a claim id were enough.
- **Project rules can only strengthen gates.** `min_evidence_lanes` floors at 2; the
  placeholder allowlist can excuse only the bare words TODO/TBD, never a delimited
  token; deferred prompts are restricted to `<DRAFT_RECOMMENDATION>` on the Red-Team
  phase-4.5 entry alone.
- **Contaminant matching normalises first.** `Hugo**Max**`, zero-width splits, and case
  variants no longer evade the scan; the manual checklist now correctly permits the
  declaration site as well as audit blocks.
- **Red Team wiring closed.** The pass now triggers on `debate+red-team` as well as
  `red-team`, mirrors Debate's restore-or-explicitly-cancel rule for the mandatory
  decorrelated lane, requires every staged lane's output non-empty before Phase 5, and
  runs every new red-team URL through the Phase 4 verification ledger — the Chairman
  can no longer cite unverified post-Phase-4 evidence.
- **Optional URL liveness check hardened.** Credential-bearing URLs, localhost/.local
  hosts, and any address resolving to loopback/private/link-local/multicast/reserved
  space or the cloud metadata endpoint are rejected before any connection; the
  connection object lifecycle bug (uncaught constructor failure) is fixed. The check
  remains optional and warn-only.
- **Namespace repair.** Overlay 02's remedial "targeted Phase 2.5" is renamed a
  "targeted Phase-2 rerun" (Phases 3–5 re-run after it) — Phase 2.5 means Debate,
  everywhere.
- Fixture policy: the ground-truth shape fixture no longer carries an `http://` URL;
  fixtures use a non-URL sentinel to test URL rejection.

## 1.1.0 — 2026-07-21 — enforcement release

Fourteen defects surfaced by a full live pipeline run (use case 8, overlay 13 primary).
Nearly all were one failure wearing different clothes: **the methodology's prose was ahead
of its mechanism** — features described in the overlays were enforced nowhere in the
orchestrator's procedure, so they only happened when an operator improvised them. The two
worst were controls that reported green while doing nothing. Each entry below states the
change and the observed failure it prevents.

- **Ground-truth verification (new Steps 0.3 q7 + 0.6; tag semantics in the prompts
  library).** Operator-supplied ground truth must be re-verified against its source URL —
  and its metric definition, not a lookalike metric — before it gains override authority;
  unverified claims are downgraded to a contradictable prior. Prevents: a misread figure
  (a rank change read as a volume change) seeded into every lane, immune to correction by
  construction.
- **Phase 2 gate scores the answer, not the file (new `scripts/gate_phase2.py`; sentinel
  rule in the Phase 2 prompt; Step 3.1 rewritten).** Every lane output is split into
  echoed-prompt and answer, and all metrics run on the answer only; citation patterns
  cover `[n]`, `[^n]`, `【n†…】`, and hidden-span reference blocks; escaped tags count
  after normalisation; an output claiming sections the structural check cannot find fails
  on that alone. Prevents: a lane file with no findings body passing every gate on the
  strength of its own echoed prompt.
- **Phase 1 validation gate (new Step 1.5, `scripts/validate_phase1.py`, blocking).**
  Structure, verdict discipline, assignment consistency, lane coverage, placeholders,
  standing rules, contaminant containment, ground-truth shape — eight gates with a
  per-lane matrix, plus a cognitive decomposition-gaps review. Prevents: a 165KB Phase 1
  output nobody can check by eye generating every downstream prompt unvalidated.
- **Deliberation modes wired (new Steps 2.5 and 4.5; old Step 4.5 renumbered 4.6).**
  Debate and Red Team are formally Phase 2.5 and Phase 4.5 (the latter shared with the
  optional eval gate); a mode selected via overlay 13 is mandatory and blocking. Prevents:
  an operator following the skill literally silently skipping both modes on a dossier that
  chose overlay 13 to get them.
- **Phase 5 capability gate (Step 5 rewritten).** The Chairman requires the strongest
  Claude model, maximum extended thinking, and a fresh context — any surface meeting all
  three qualifies, with a fresh subagent preferred, a fresh Claude.ai web chat as default,
  and inline permitted only with low contamination and a passing input-budget check.
  Prevents: a contaminated orchestrator context acting as Chairman, and forced manual
  copy-paste round trips that silently truncate artifacts.
- **Decision research routes to overlay 13 (runbook 11 lesson 8 + routing table;
  Supersedes/Superseded-by headers on overlays 03, 04, 13).** Prevents: personal-decision
  projects routed to the WordPress SEO overlay and losing the Decision Brief format
  entirely.
- **Agent-access inventory (Step 0.3 q6; `research-config.md` `## Agent access`; lineage
  assignment rule in the Phase 1 prompt; `lanes_unavailable`).** Lanes are assigned
  against the operator's real stack — maximise distinct lineages before depth — and every
  unused available lineage needs a one-line justification. Prevents: a whole training
  lineage (the only OpenAI lane) silently dropped on every run because "optional" meant
  "never".
- **Execution surfaces (lane_roles gains `execution_surface`; Step 2.2 renders per-lane
  instructions; specialist-lanes section in runbook 11).** Prevents: an operator handed a
  13KB prompt for a named role with no tool bound to it and nowhere to paste it.
- **Assignment consistency contract (`phase_2_prompts` canonical, `agent_assignments`
  derived; gate G3).** Prevents: two conflicting answers to "who researches what" with
  neither declared canonical.
- **Lane roles as mechanism (`lane_roles` block; ≥2 evidence-bearing lanes per
  sub-question; `[SENTIMENT-CONCUR]` rule in the Phase 3 prompt).** Prevents: a
  sentiment-only lane drawing load-bearing evidence questions, and sentiment concurrence
  counted as independent corroboration exactly where false consensus is most expensive.
- **Contaminated-input pattern (trusted / under-scrutiny classification; two-tier
  location-aware rule in gate G7).** Audit blocks must name a contaminant; no
  ready-to-paste prompt may carry it — and a naive whole-file scan is explicitly wrong.
  Prevents: withheld anchors propagating into research prompts, and clean runs
  false-failing because the audit correctly named the contaminant.
- **Prerequisites check readability, not presence (anchor strings + non-zero size).**
  Prevents: a zero-byte or truncated reference passing the check and degrading the run
  silently.
- **DCI tally has a home (conditional section 6 of the Phase 3 prompt).** Prevents: a
  documented capability that only existed if the operator remembered to bolt it on.
- **Project-specific lane naming (`02a-prompts-<lane_id>.md` → `02-<lane_id>.md`).**
  Prevents: specialist lanes named ad hoc per project with no convention.
- **The class rule (the overlay contract, atop the Procedure).** Any mechanism an active
  overlay declares mandatory becomes a blocking step; an unwired mandatory mechanism is a
  halt-and-surface defect. Prevents: the next described-but-unenforced feature regressing
  the same way all fourteen of these did.

## 1.0.0 — 2026-07-19

Initial release: portable skills, bundled references (methodology v1.1), runtime dossier
root resolution, plugin + marketplace manifests.

---
name: research-requirements-check
description: Audits a markdown requirements file against AgenticCodingOps research-readiness criteria. Use before Phase 1 decomposition or when asked to audit, check, or validate a requirements file.
---

# Skill: Research Requirements Quality Check

## When to use this skill

Use this skill whenever the user wants to evaluate whether a markdown requirements file (or any plain-text requirements document) is well-formed enough to be the input to the AgenticCodingOps multi-AI research workflow. Trigger phrases include:

- "Check this requirements file"
- "Is this requirements doc ready for research?"
- "Audit the requirements at <path>"
- "Run requirements quality check"
- Any time the orchestrator skill (`research-orchestrator`) reaches the input-validation step for a spec-driven dev project

This skill produces one of two outcomes:
1. **GREEN** — the file passes the minimum bar; orchestrator proceeds to Phase 1 decomposition.
2. **AMBER / RED** — the file has gaps; this skill generates a Claude Code prompt the user can run in their repo to enrich the requirements file before research begins.

Do NOT use this skill for evaluating completed dossiers (`05-dossier.md` files) — those are outputs, not inputs.

---

## The minimum quality bar

A requirements file is research-ready when it contains, at minimum:

| Element | What good looks like |
|---|---|
| **Problem statement** | One paragraph describing the problem being solved, not the solution. Names the people affected and the cost of the status quo. |
| **Target users** | One paragraph identifying who will use the system, what they do today, what they need from a future system. Multiple personas allowed; vague "developers and ops teams" is not sufficient. |
| **Core capabilities** | A list (3-10 items) of the primary capabilities the system must provide. Stated as outcomes, not features ("teams can deploy any approved Terraform module in <5 minutes" not "Terraform module catalog with web UI"). |
| **Known constraints** | A list covering at least: technology constraints (e.g., must run on Azure), security/compliance constraints, performance/scale constraints, cost constraints, time constraints. "None" is rarely correct; if the user says no constraints, that itself is a flag. |

A requirements file is research-EXCELLENT (not just ready) when it ALSO contains:

| Optional but valuable element | Why it matters |
|---|---|
| **Success criteria** | What "done" looks like, measurable where possible. Reduces decomposition ambiguity. |
| **Existing-system context** | For brownfield: what exists today, what stays, what changes. For greenfield: what adjacent systems this integrates with. |
| **Out-of-scope statement** | What this system explicitly does NOT do. Prevents Phase 1 sprawl. |
| **Pre-decided technology choices (with rationale)** | If the user has already decided "must use Terraform" or "must run on Kubernetes", capture this with the why. The dossier can validate or challenge those choices. |
| **Stakeholder list** | Who needs to approve the work, who is affected. Useful for Phase 6 routing. |

---

## Procedure

### Step 1 — Locate and read the file

Read the file at the path the user specifies. If no path given, ask. Common locations:
- The repo's `requirements.md`, `REQUIREMENTS.md`, `docs/requirements.md`, or `docs/spec.md`
- A standalone `~/projects/<project>/requirements.md`
- A file the user pasted into the chat

If the file is empty, very short (<200 words), or clearly a placeholder ("TODO: write requirements"), report RED immediately and skip the detailed check.

### Step 2 — Audit against minimum bar

For each of the four minimum elements, classify:

- **PRESENT** — the element is clearly addressed
- **WEAK** — the element is mentioned but underspecified
- **MISSING** — no coverage at all

Output a structured audit:

```
# Requirements Quality Audit
File: <path>
Date: <today>
Word count: <N>

## Minimum bar
| Element | Status | Notes |
|---|---|---|
| Problem statement | PRESENT/WEAK/MISSING | <specifics> |
| Target users | PRESENT/WEAK/MISSING | <specifics> |
| Core capabilities | PRESENT/WEAK/MISSING | <specifics> |
| Known constraints | PRESENT/WEAK/MISSING | <specifics> |

## Optional elements (excellence)
| Element | Status | Notes |
|---|---|---|
| Success criteria | ... | ... |
| Existing-system context | ... | ... |
| Out-of-scope | ... | ... |
| Pre-decided tech choices | ... | ... |
| Stakeholder list | ... | ... |
```

### Step 3 — Verdict

Compute the verdict:

- **GREEN — research-ready**: All four minimum elements PRESENT. Optional elements may be missing.
- **AMBER — needs targeted enrichment**: 1-2 minimum elements WEAK or MISSING. Generate a fix prompt (Step 4) but the user can choose to proceed to research with the gap, treating it as an open question for Phase 1.
- **RED — not research-ready**: ≥3 minimum elements WEAK or MISSING, OR file is too short to evaluate. Generate a fix prompt and recommend the user runs it before starting research.

State the verdict explicitly with one-sentence rationale.

### Step 4 — Generate a Claude Code fix prompt (only for AMBER or RED)

The fix prompt is what the user runs in their Claude Code session inside the repo to enrich the requirements file. Generate a customised prompt that:

1. References the specific file path
2. Lists exactly which elements need work
3. For each weak/missing element, asks Claude Code to:
   - Read the existing file
   - Read related repo context (other docs, README, prior PRs/issues)
   - Propose specific text to add, with placeholders for user-specific details
4. Explicitly instructs Claude Code NOT to invent facts about the user's business or users — placeholders for the user to fill in are required
5. Outputs the enriched file as a new version (e.g., `requirements.v2.md`) so the user can compare before replacing the original

Template for the fix prompt:

```
You are working in the project repo. Read the existing requirements file at:
<file_path>

This file has been audited for research-readiness against the AgenticCodingOps 
multi-AI research methodology. The audit found:
- <element 1>: <WEAK/MISSING — specific gap>
- <element 2>: <WEAK/MISSING — specific gap>
- ...

Your task:
1. Read the requirements file in full.
2. Read related repo context that might inform the gaps:
   - README.md
   - Any docs/ folder contents
   - The most recent commit messages (last 20)
   - Issues or PRs referenced in the file
3. For each WEAK or MISSING element, draft enriched text:
   - <specific instructions per element from the audit>
4. Where you genuinely don't have enough context to fill in (e.g., the user's 
   target persona's specific pain points, the user's stakeholder list), insert 
   a clearly-marked placeholder: [USER TO FILL: <specific question>]
5. Do NOT invent facts about the user's business, users, or constraints. 
   Placeholders are correct here; hallucinated detail is not.
6. Write the enriched file to <file_path>.v2.md (do NOT overwrite the original).
7. Output a diff summary so the user can review what changed.

After this completes, the user reviews <file_path>.v2.md, fills in placeholders, 
and replaces the original. Then they re-run the requirements quality check skill 
to confirm GREEN before starting Phase 1 decomposition.
```

Customise the bullet under #3 for each element flagged. For example, if "Target users" was WEAK:

```
For Target users:
- Identify which user personas were vaguely mentioned in the original
- For each persona, propose: their current workflow, what they need from this 
  system, what success means for them
- Where the original was silent on a likely persona (based on the problem 
  statement), surface that as a placeholder: 
  [USER TO FILL: Is <persona X> a target user? If so, describe their needs.]
```

### Step 5 — Hand back to orchestrator (or user)

If the audit was triggered by the orchestrator skill, return:
- The verdict (GREEN / AMBER / RED)
- The fix prompt if generated (AMBER or RED)
- A recommendation: GREEN → proceed to Phase 1; AMBER → user decides; RED → run fix prompt first

If standalone, ask the user what to do next.

---

## Examples

### Example 1: GREEN

User: *"Audit the requirements file at ~/projects/devops-platform/requirements.md"*

Skill output:

```
# Requirements Quality Audit
File: ~/projects/devops-platform/requirements.md
Word count: 2,847

## Minimum bar
| Element | Status | Notes |
|---|---|---|
| Problem statement | PRESENT | Clear paragraph on platform-team toil |
| Target users | PRESENT | Two personas: platform engineers, app teams |
| Core capabilities | PRESENT | 7 capabilities, outcome-stated |
| Known constraints | PRESENT | Azure-only, SOC 2, <12 month timeline |

## Optional elements
| Element | Status | Notes |
|---|---|---|
| Success criteria | PRESENT | Time-to-deploy metric, satisfaction score |
| Existing-system context | WEAK | Mentions current state but lacks specifics |
| Out-of-scope | MISSING |  |
| Pre-decided tech choices | PRESENT | Terraform, AKS, GitHub Actions chosen |
| Stakeholder list | MISSING |  |

## Verdict: GREEN — research-ready

The minimum bar is met. The two missing optional elements (out-of-scope, 
stakeholder list) can be addressed during Phase 1 decomposition as sub-questions, 
or you can spend 10 minutes filling them in now.

Proceeding to Phase 1 decomposition with this file as input.
```

### Example 2: RED

User: *"Check the file at ~/projects/new-app/requirements.md"*

Skill reads file. Word count: 380. Problem statement is one sentence. Target users is "developers". Capabilities listed but as features. No constraints.

Skill output:

```
# Requirements Quality Audit
File: ~/projects/new-app/requirements.md
Word count: 380

## Minimum bar
| Element | Status | Notes |
|---|---|---|
| Problem statement | WEAK | One sentence; doesn't name affected users or status-quo cost |
| Target users | WEAK | Says "developers" — too vague to drive decomposition |
| Core capabilities | WEAK | Listed as features, not outcomes; missing acceptance criteria |
| Known constraints | MISSING | No constraints stated |

## Verdict: RED — not research-ready

3 of 4 minimum elements are WEAK or MISSING. Running multi-AI research on this 
file would produce a vague dossier because the inputs are underspecified.

Recommended action: Run the following prompt in a Claude Code session inside 
the project repo. The output will be ~/projects/new-app/requirements.v2.md 
which you can review, fill in placeholders, and use as the corrected input.

---

[Customised fix prompt here, addressing each weak/missing element]

---

After running the fix prompt and reviewing the enriched file, re-trigger this 
skill to verify GREEN before starting Phase 1.
```

### Example 3: AMBER

User: *"Audit ~/projects/migration/requirements.md"*

Skill audit shows: Problem statement PRESENT, Target users PRESENT, Core capabilities WEAK (mostly outcomes but two are vague), Known constraints WEAK (technology constraints listed, but no security/cost/time).

Skill output:

```
[Audit table showing 2 PRESENT and 2 WEAK]

## Verdict: AMBER — usable, but gaps will need to be addressed

The file is research-ready in principle, but the WEAK elements may produce 
sub-questions in Phase 1 that turn into open questions through to Phase 5.

You have two options:
1. Spend 15 minutes now running this fix prompt to harden the WEAK elements:
   [Fix prompt]
2. Proceed to Phase 1 with the file as-is. The orchestrator will surface the 
   gaps as Phase 1 sub-questions, and you'll address them during research 
   (which means the dossier may have flagged uncertainties around them).

Recommended: Option 1 if this is a high-stakes project (paying client, 
production system, large migration). Option 2 if this is exploratory or 
the gaps are intrinsic to the project (genuinely unknown rather than 
under-specified).

Which path do you want to take?
```

---

## Integration with the orchestrator skill

When the orchestrator skill reaches Phase 0 (input setup) and detects a requirements file as input, it invokes this skill silently. The orchestrator passes:
- The file path
- A flag `mode: orchestrator-internal` (vs `mode: standalone`)

When `mode: orchestrator-internal`:
- Output is structured for the orchestrator to consume programmatically
- The orchestrator decides next step based on verdict
- If RED, the orchestrator pauses the pipeline and surfaces the fix prompt to the user

When `mode: standalone`:
- Output is human-readable with verdict + recommendation + fix prompt
- The user decides next step

---

## Maintenance

Update this skill when:
- The minimum quality bar changes (e.g., a new element becomes mandatory based on observed dossier failure modes)
- The fix prompt template needs refinement based on observed Claude Code outputs
- New optional elements emerge as best practices

This skill is version-controlled and distributed as part of the `multi-ai-research` plugin — make changes in the plugin's source repository, not in an installed copy.

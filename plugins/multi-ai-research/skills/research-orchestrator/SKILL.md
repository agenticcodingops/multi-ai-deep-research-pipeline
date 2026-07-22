---
name: research-orchestrator
description: Orchestrates the AgenticCodingOps multi-AI research pipeline. Use to start or resume research (spec-dev, YouTube, presentation, ebook, WordPress SEO, health, deck+screencast, decision research).
---

# Skill: Research Orchestrator

## When to use this skill

Use this skill whenever the user wants to start, resume, or manage a multi-AI research project using the AgenticCodingOps methodology. Trigger phrases include:

- "Start a new research project"
- "Run the research orchestrator"
- "I want to research <topic>"
- "Help me research <topic> for <use case>"
- "Resume research on <topic>"
- "I have a requirements file — start research"
- "Should I <do X>?" / "Which <option> should we choose?" / "Help me decide between <A> and <B>" — decision-shaped research, routed to use case 8
- "I need a deck AND a screencast/video from one research pass" — combined deliverable, routed to use case 7
- Any prompt that mentions starting a dossier, beginning the multi-AI workflow, or running the 6-phase pipeline

This skill is the **session-level coordinator** — it manages the dossier folder, walks the user through phases sequentially, calls the requirements-quality-check skill when appropriate, and bridges between the file-system environment (Cowork / Claude Code) and Claude.ai web for cognitive phases.

This skill does NOT itself execute Phases 1, 3, or 5 (the cognitive phases) inline by default. It prepares inputs and hands off to a qualifying surface — a fresh Claude.ai web chat, or for Phase 5 any surface meeting the Phase 5 capability gate (a fresh subagent on the strongest model qualifies). It DOES execute Phases 0, 2 (preparation), 4 (verification), and 6 (routing) directly.

---

## Prerequisites

Before this skill runs, verify:

1. **Bundled reference integrity.** This skill ships its methodology artifacts inside the skill at `./references/` — 14 files, `00-master-methodology.md` through `13-overlay-deliberation-modes.md`. Confirm the folder exists and contains, at minimum: `00-master-methodology.md`, `01-prompts-library.md`, overlays `02-` through `07-`, `08-overlay-deck-and-screencast.md`, `12-project-startup-checklist.md`, and `13-overlay-deliberation-modes.md`. If any expected file is missing, **halt and report exactly which file is missing** — the installation is incomplete and the user should reinstall the plugin. Never degrade silently to a partial overlay set. Additionally verify the critical references are **readable, not merely present** — a zero-byte, truncated, or encoding-mangled copy is as fatal as a missing one. Every listed file must be non-zero size, and these anchor strings must resolve: `00-master-methodology.md` contains `Decorrelated-lane rule`; `01-prompts-library.md` contains `Chairman of a multi-AI research council`; `08-overlay-deck-and-screencast.md` contains `SPEAKER_NOTES`; `13-overlay-deliberation-modes.md` contains `<output_format> — DECISION BRIEF`. On any failure, halt and name the file and the specific check that failed.
2. **Requirements-check availability.** The `research-requirements-check` skill ships in the same plugin as this skill. Check by skill availability (invoke it by name when Step 0.5 needs it), not by filesystem path — installed skill locations differ per surface. If it is unavailable, warn the user that requirements auditing will be skipped; the rest of the pipeline still runs.
3. **Agent access.** The user needs access to Claude.ai web (with extended thinking) for the cognitive phases, plus deep-research-capable access to Perplexity, Gemini, and Grok for Phase 2 — and, for the decorrelated lane, a DeepSeek route (web UI, Western-hosted API, or self-hosted; see Step 2.2). The full per-user inventory is taken at Step 0.3 and persisted in `research-config.md`. Confirm in the opening message if uncertain.
4. **Gate scripts.** `./scripts/validate_phase1.py` and `./scripts/gate_phase2.py` ship with this skill and implement the blocking gates at Steps 1.5 and 3.1 (invoke with `python`; use `python3` on POSIX surfaces where `python` is absent). If Python is unavailable on this surface, the gates still run — as the manual fallback checklist documented at each step. **A gate is never skipped because the script cannot execute.**

If prerequisite 1 fails, halt. If prerequisite 3 is uncertain, surface it and let the user decide.

---

## Procedure

### The overlay contract (read first)

Any mechanism an active overlay declares **mandatory** — a selected deliberation mode, an output-format block, a decomposition adjustment, a required tally — becomes a **blocking step** in this procedure, never advisory prose. Overlays declare hooks by exact section name (e.g. overlay 13's "### Phase 1 — decomposition adjustment"), and this procedure wires each hook to a numbered step. If an active overlay declares a mandatory mechanism that no step below wires in, that is a defect in this skill: halt and surface it to the user rather than skipping it silently.

### Phase 0 — Project setup

#### Step 0.0 — Resolve the dossier root

All dossier folders live under a per-workspace **dossier root**. Resolve it in this order before anything else (including on resume):

1. Look for a file named `research-config.md` at the root of the granted workspace folder. If present, read the `Dossier root:` value and use it for every dossier path in this session.
2. If absent, ask the user once:

   > "Where should dossiers for this workspace live?"

   Accept a path relative to the workspace root (recommended, e.g. `dossiers/`) or an absolute path the user explicitly supplies. Then write the answer to `research-config.md` at the workspace root in this format (see `./templates/research-config.example.md`):

   ```markdown
   # Research configuration
   Dossier root: <path exactly as the user gave it>
   ```

   so the question is never asked again in this workspace.
3. Never invent a default and proceed silently, and never fall back to creating a `dossiers/` folder in the user's home directory. If the workspace root is not writable, tell the user, use their stated path for this session only, and warn that they will be asked again next session.

Wherever this skill says `<dossier-root>`, substitute the resolved path. Relative dossier roots resolve against the workspace root.

#### Step 0.1 — Identify use case

Ask the user (or infer):

> "What use case are we running today? Pick one:
> 1. Spec-driven software development (greenfield or brownfield)
> 2. YouTube script
> 3. Presentation or conference talk
> 4. Ebook (multi-chapter)
> 5. WordPress + Elementor SEO article
> 6. Health content (low back pain, longevity, focus)
> 7. Deck + screencast combined (one research pass, slides AND video script)
> 8. Personal / market decision research ("should I do X?")
>
> Or describe your goal and I'll match."

Map to an overlay file and read it from `./references/` for the use-case-specific instructions:

| Choice | Overlay |
|---|---|
| 1 | `./references/02-overlay-spec-driven-dev.md` |
| 2 | `./references/03-overlay-youtube-script.md` |
| 3 | `./references/04-overlay-presentation.md` |
| 4 | `./references/05-overlay-ebook.md` |
| 5 | `./references/06-overlay-wordpress-seo.md` |
| 6 | `./references/07-overlay-health-content.md` |
| 7 | `./references/08-overlay-deck-and-screencast.md` — supersedes running overlays 03 and 04 separately whenever both a deck and a screencast come from one research pass |
| 8 | `./references/13-overlay-deliberation-modes.md` — Phase 5 uses its Decision Brief output format |

**Layering note:** overlay 13 also **layers on top of another overlay** when a dossier under any use case supports a decision (go/no-go, build/buy, launch, investment). Keep the primary overlay from the table and apply overlay 13 additionally — it adds between-phase passes (Phase 2.5, Phase 4.5), never replaces the primary. Record both overlays in `00-context.md`.

**Deliberation-mode selection (whenever overlay 13 is active — primary or layered).** Run overlay 13's Mode selector table now and record the selection in `00-context.md` under `## Deliberation mode(s)`: `none`, or a `+`-joined set of `first-principles`, `debate`, `red-team` in pipeline order (Phase 1 < 2.5 < 4.5) — e.g. `debate`, `debate+red-team`, `first-principles+debate+red-team`. A selected mode is **mandatory and blocking** (overlay contract): Debate runs at Phase 2.5 (Step 2.5), Red Team at Phase 4.5 (Step 4.5), and First Principles shapes the Step 1.2 decomposition prompt.

#### Step 0.2 — For spec-driven dev, identify greenfield vs brownfield

If use case is spec-driven dev, ask:

> "Is this a greenfield or brownfield project?
> - Greenfield: net-new, no existing code repo
> - Brownfield: existing repo, you want research to inform changes to it"

If brownfield: ask for the repo workspace path. Verify access. Read:
- `<repo>/README.md`
- `<repo>/docs/` (if exists)
- `<repo>/docs/adr/` (if exists)
- Any prior `<repo>/docs/research/` dossiers

Use this repo context to inform Phase 1 decomposition.

#### Step 0.3 — Identify research question and decision context

Ask:

> "1. What's the research question? One or two sentences.
> 2. Decision context: what will you do with the dossier? (e.g., 'Decide between AKS and ECS for the new platform', 'Record a 10-minute YouTube video next Saturday', 'Publish a 2,500-word SEO article')
> 3. Time horizon: when do you need this done?
> 4. Existing inputs: any files you want me to use as input? (Requirements docs, prior research, brand guidelines, etc.) For each input, is it **trusted** (use as brief) or **under-scrutiny** (audit as subject — e.g. a prior draft whose claims need verifying)? For under-scrutiny inputs, optionally name **contaminants**: specific figures, conclusions, or framings in the file that must NOT propagate into the research (salary anchors, prior conclusions, vendor preferences, a pre-committed answer).
> 5. Confidentiality: does this research involve confidential material (internal architecture, client code, business-sensitive context), or is it non-confidential/public? This determines how the decorrelated research lane is routed in Phase 2 — web UI, Western-hosted API, or self-host (see Step 2.2).
> 6. Agent access: which of these do you hold, and at what tier? Perplexity / Gemini / Grok / ChatGPT / Claude / a DeepSeek route (web UI, Western-hosted API, or self-host) / NotebookLM / Elicit / Consensus.
> 7. Ground truth (optional): any claims you have personally verified and assert as established fact for this research. Each needs three things: the claim, its **metric definition** (what exactly the figure measures — a rank change is not a volume change), and its **source URL**. Each is re-verified at Step 0.6 before it gains any authority."

If a requirements file is mentioned, store the path for Step 0.5. Record the confidentiality answer — it is written to `00-context.md` and consumed at Step 2.2.

Before asking question 6, read the `## Agent access` section of `research-config.md` (the Step 0.0 file): the inventory is a property of the **workspace**, not the project, so ask only about lanes not yet recorded there and write new answers back so the question is never repeated. Phase 1 assigns lanes against this real inventory (Step 1.2), not an assumed default stack. Record input classifications, contaminants, and ground-truth claims in `00-context.md` (Step 0.4 template).

#### Step 0.4 — Generate topic slug and create dossier folder

Generate a kebab-case slug from the research question (e.g., "Should we migrate to AKS?" → `aks-migration-decision`). Confirm with user.

Create the folder `<dossier-root>/<topic-slug>/` (on shell surfaces — bash and PowerShell equivalents:)

```bash
mkdir -p <dossier-root>/<topic-slug>
cd <dossier-root>/<topic-slug>
```

```powershell
New-Item -ItemType Directory -Force <dossier-root>\<topic-slug> | Out-Null
Set-Location <dossier-root>\<topic-slug>
```

Create an empty `00-context.md` there (other files are created as phases complete), then write to it:

```markdown
# Research project: <topic-slug>

## Research question
<as user stated>

## Decision context
<as user stated>

## Use case
<spec-dev / youtube / presentation / ebook / wordpress-seo / health / deck-screencast / decision-research>

## Overlay(s)
<primary overlay file; plus 13-overlay-deliberation-modes.md if layered>

## Mode
<greenfield-spec-dev / brownfield-spec-dev / general>

## Time horizon
<as user stated>

## Confidentiality
<confidential / non-confidential — decorrelated-lane decision applied at Phase 2>

## Existing inputs
<one bullet per input file path; if there are no inputs, write exactly: none>

## Input trust
<one line per input: path — trusted | under-scrutiny; contaminants: list, or none. If no inputs, write exactly: n/a>

## Agent access
<one line per lane: agent: tier / route / none — mirrored from research-config.md>

## Deliberation mode(s)
<none, or a +-joined set of first-principles / debate / red-team in pipeline order (e.g. debate+red-team) — set at Step 0.1 when overlay 13 is active; otherwise n/a>

## Ground-truth claims
<one line per claim: GT<n> | statement | metric definition | source URL | tag (filled at Step 0.6). If none, write exactly: none>

## Brownfield repo (if applicable)
<repo path; if not applicable, write exactly: n/a>

## Started
<YYYY-MM-DD HH:MM, local time>

## Status
Phase 0 complete. Ready for Phase 1 decomposition.
```

#### Step 0.5 — Run requirements quality check (if requirements file provided)

If the user provided a requirements file path, invoke the `research-requirements-check` skill with `mode: orchestrator-internal`. Receive verdict:

- **GREEN**: Proceed to Phase 1.
- **AMBER**: Surface the audit and the user-choice options (proceed with gap, or fix first). Wait for user decision.
- **RED**: Surface the audit and the fix prompt. Pause Phase 1. Recommend the user runs the fix in Claude Code, then re-triggers this orchestrator skill.

If GREEN: append `requirements_audit: GREEN` to `00-context.md`. Continue.

If AMBER and user chooses to proceed: append the audit + user's decision to `00-context.md`. Phase 1 will pick up the gaps as sub-questions. Continue.

If RED or AMBER (fix-first): pause. Output the fix prompt with explicit instructions: *"Run this in Claude Code inside your repo. When complete, re-invoke me with: 'Resume research on `<topic-slug>`.'"*

#### Step 0.6 — Ground-truth verification (only when Step 0.3 recorded ground-truth claims)

Operator-supplied ground truth is the only assertion in this pipeline that downstream agents are told not to overturn — so it must be **verified, not merely asserted**, before it gains that authority. An unverified figure seeded into every lane is immune to correction by construction; catching exactly that class of error is the pipeline's purpose. For each claim under `## Ground-truth claims`:

1. Open the claim's source URL exactly as Phase 4 verifies citations — via Firecrawl MCP or web fetch if available on this surface; otherwise ask the user to open it in a browser and report what the page says. Claims derived from the operator's own private or hand-coded dataset (hand-built samples, internal logs, unpublished measurements) have no source URL to open — skip steps 1–2 for them and go straight to the private-dataset branch below.
2. Confirm BOTH the claim and its **metric definition** against the page — the operator's definition, not a lookalike metric. A rank change is not a volume change; a country figure is not a region figure.
3. Tag the claim in `00-context.md`:
   - Confirmed → `[GROUND-TRUTH-VERIFIED]` — re-checked this session. **Only this tag carries override authority** in Phases 2–5.
   - Source unreachable, ambiguous, or in disagreement → surface the discrepancy for adjudication NOW, before Phase 1: *"You stated X; the source says Y — which do we carry, and under which tag?"* Record the decision. Anything unresolved or unverifiable is downgraded to `[GROUND-TRUTH-ASSERTED]` — a strong prior that agents may contradict, but only with a cited primary source.
   - Derived from an operator-private dataset → `[GROUND-TRUTH-ASSERTED]` **by definition**, never VERIFIED: no cited source can reproduce the figure, so it can never carry override authority. It still needs a statement and a metric definition; in the Phase-1 `ground_truth` array it carries `status: "asserted"` with `source_url: null` (or an operator-provenance marker such as `operator-private-sample`).
4. Do not proceed to Phase 1 while any ground-truth claim is untagged.

With no ground-truth claims recorded, skip this step silently.

### Phase 1 — Decomposition

#### Step 1.1 — Determine where Phase 1 will run

Phase 1 runs best on the strongest available Claude model with extended thinking (Claude.ai web). Ask the user:

> "Phase 1 decomposition runs best in Claude.ai web (strongest available Claude model + extended thinking at maximum). Two options:
> 1. I generate the Phase 1 prompt now and you paste it into a fresh Claude.ai chat — extended thinking at maximum, with the named inputs for this phase attached to that chat. (A Claude Project whose knowledge base already holds them works too — the Project is an optional convenience container, never a requirement.) You bring the JSON output back here, I save it as 01-decomposition.md.
> 2. I run Phase 1 here in Cowork/Claude Code with the available model. Acceptable for most projects but lower model tier than option 1.
>
> Which option?"

Default recommendation: option 1 for high-stakes projects (paying client work, production decisions, published content). Option 2 for exploratory or low-stakes projects.

#### Step 1.2 — Build the Phase 1 prompt

Read from `./references/`:
- `01-prompts-library.md` → Phase 1 universal decomposition prompt
- The primary overlay file (`02-` through `08-`, or `13-` for decision research — its "When 13 is the primary overlay" section carries the named subsections), plus `13-` when layered → "Phase 1 — decomposition adjustment" section

Compose the full Phase 1 prompt:

1. Universal decomposition prompt
2. Use-case-specific addition from the overlay
3. Brownfield context (if applicable): "The user is researching changes to an existing repo at <path>. Existing relevant context: <summarised from README/docs>. Sub-questions must include 'what existing-system constraints apply' and 'what migration risks must be addressed'."
4. Requirements-file context (if applicable): "The attached file is the prior requirements draft. Sub-questions must include verification of every external claim, technology recommendation, and architectural choice in that draft. Also surface what's missing, what constraints haven't been considered, and what alternatives weren't evaluated."
5. **Phase 1 output spec**: use the canonical JSON spec (schema_version 2) from `01-prompts-library.md`'s decomposition prompt verbatim. Key contracts: `phase_2_prompts` is the **canonical** statement of who researches what (each prompt fully formed, zero placeholders); `agent_assignments` is derived from it and must agree exactly; `lane_roles` declares every lane's role, lineage, and execution surface; `lanes_unavailable` records useful lanes skipped for access reasons. The library's Phase-2 fan-out prompt carries a literal `OUTPUT FORMAT (machine-checked — follow literally)` skeleton — every `ready_to_paste_prompt` must carry it verbatim (its sentinel line stays annotated inline, never standalone). The agent set includes the DeepSeek decorrelated lane; for confidential work its route changes (Western-hosted API or self-host) rather than the lane being dropped, and it is omitted only when no compliant route is available (Step 0.3 / Step 2.2).
6. **Agent-access inventory + assignment rule**: paste the `## Agent access` inventory from `00-context.md` into the prompt, with the rule stated: *assign against this real stack, never an assumed one; maximise distinct training lineages before adding depth within a lineage; justify in one line any available lineage left unused.*
7. **Input classification (if inputs exist)**: state each input's trusted / under-scrutiny classification and its contaminants. Require one `input_audits` block per under-scrutiny input, and state the two-tier rule: *the audit block must be able to name any contaminant it reports; no `ready_to_paste_prompt` may carry one.*
8. **Ground truth (if claims exist)**: require every `ready_to_paste_prompt` to embed the ground-truth block from `01-prompts-library.md`, with each claim's tag exactly as recorded at Step 0.6.

Save the composed prompt to `<dossier-root>/<topic-slug>/01a-phase1-prompt.md` before hand-off — if the Step 1.5 gate fails, re-run Phase 1 from this file with the failure list appended rather than rebuilding from scratch.

#### Step 1.3 — Execute Phase 1

If user chose option 1: output the prompt (saved as `01a-phase1-prompt.md`) + instruction *"Paste this into a fresh Claude.ai chat with the named inputs attached (or a Claude Project that already holds them — the Project is optional). Set extended thinking to maximum. When the JSON output is ready, paste it back here."* Pause.

If user chose option 2: send the prompt to the local Claude model. Capture JSON output.

#### Step 1.4 — Save Phase 1 output

Save the JSON to `<dossier-root>/<topic-slug>/01-decomposition.md`, then hand off to Step 1.5. Do not mark Phase 1 complete until the gate passes.

#### Step 1.5 — Phase 1 output validation gate (BLOCKING)

Phase 1 is the pipeline's single point of failure — its output generates every downstream agent prompt — and that output is far too large to check by eye. Treat any "self-validation passed" narration inside the decomposer's own output as noise — only this script's exit code (or the manual checklist below) is the gate; on a live run the decomposer declared all its checks passed while the gate found 27 failures. Run the gate script (resolve `./scripts/` against this skill's own folder):

```
python ./scripts/validate_phase1.py <dossier-root>/<topic-slug>/01-decomposition.md
```

(`python3` on POSIX surfaces where `python` is absent.) The script prints a pass/fail matrix — gates G1–G8, per lane — and exits non-zero on any failure.

- **Exit 0:** append the matrix summary and `phase1_gate: PASS (script)` to `00-context.md`. Continue.
- **Exit 1:** surface the full matrix and detail lines. **Phase 2 must not begin while any gate is failing.** Offer: (a) re-run Phase 1 with the failure list appended to the prompt, or (b) the user hand-fixes `01-decomposition.md` for trivial mechanical issues. Re-run the gate until it passes; record each attempt in `00-context.md`.
- **Exit 2:** the file is not parseable JSON — treat as a Phase 1 failure (route (a) above), never as a pass.
- **Script cannot run** (no Python, or `./scripts/` missing): say so explicitly — *"The Phase 1 gate script cannot run on this surface; walking the equivalent manual checklist instead"* — then work through the checklist below item by item as a blocking gate and record `phase1_gate: PASS|FAIL (manual)` with per-item results. **Never silently skip the gate** — a gate that disappears on some surfaces is worse than no gate, because the user believes it ran.

**Manual fallback checklist (mirrors gates G1–G8):**

1. JSON parses; `schema_version` is exactly 2; all spec keys present with the right shapes; 4–12 sub-questions with unique `SQ<n>` ids; lane ids unique, lowercase slugs (`a-z0-9_-`, no Windows device names); every agent name is one of the nine canonical values (`DecorrelatedLane`, not a product name, for the decorrelated lane); `source_type_required` uses the enum; every cross-reference between blocks resolves.
2. Every sub-question has a non-empty `verdict_forced` and `falsifiable: true`.
3. Every (sub-question, agent) pair implied by `agent_assignments` (primary and non-null secondary) has exactly one prompt in `phase_2_prompts` — no duplicates on either side, never primary == secondary — and each prompt's `agent` matches the `lane_roles` agent for its `lane_id` (a swapped lane sends prompts to the wrong surface).
4. Every lane used is declared in `lane_roles` with valid role/lineage/surface, and every sub-question has ≥2 lanes whose role is `evidence` or `decorrelated`.
5. Read every `ready_to_paste_prompt` end-to-end: no `<TOKEN>`, `{TOKEN}`, `«TOKEN»`, `TODO`, `TBD`, `[INSERT` (a project-rules allowlist may excuse the bare words TODO/TBD only — never a delimited token). Deferred prompts: only the Red-Team phase-4.5 entry may defer, its only permitted token is `<DRAFT_RECOMMENDATION>`, and declared placeholders must match the template exactly.
6. Every prompt carries the FULL Phase 2 contract in its own text: the sentinel instruction (token named inline, never on a standalone line inside the prompt), all six output section names, the [HIGH]/[MEDIUM]/[LOW] rule, the live-URL rule, the primary-sources bar, the coverage-gaps section, the OUTPUT FORMAT skeleton (the script checks its title is present in every prompt) — and, when claims exist, the filled ground-truth block: each claim's id, statement, metric definition, its https source URL when it has one, and the three tag semantics ([GROUND-TRUTH-VERIFIED]/[GROUND-TRUTH-ASSERTED]/[CONTRADICTS-GROUND-TRUTH]).
7. Search each contaminant string — including disguised renderings (`Hugo**Max**`, zero-width splits): permitted only in the `inputs[].contaminants` declarations and inside `input_audits`; found in any prompt → FAIL.
8. Every ground-truth claim has a statement, metric definition, and status; a `verified` claim requires an https source URL, while an `asserted` claim may instead carry `source_url: null` or an operator-provenance marker such as `operator-private-sample`.

**Then the decomposition-gaps review (cognitive — the script cannot do this):** compare the sub-questions against the user's stated circumstances in `00-context.md` — decision context, constraints, jurisdiction or employment specifics, inputs. List every material factor no sub-question covers as `decomposition_gaps`, and surface it: add sub-questions now, or record the user's explicit acceptance of each gap. (The class of miss this catches, from a live run: an employment decision whose sub-questions never asked about the contract-versus-permanent split that changed which options were reachable.)

Update `00-context.md` status: "Phase 1 complete (gate passed)."

### Phase 2 — Parallel fan-out (preparation only — execution is manual by user)

#### Step 2.1 — Surface the customised Phase 2 prompts

Read `01-decomposition.md`. Extract the canonical `phase_2_prompts` array, group by `lane_id` (from `lane_roles`), and write one staged-prompt file per lane. A `lane_id` becomes a filename verbatim, so it must match `^[a-z0-9][a-z0-9_-]{0,63}$` and never be a Windows reserved device name — Step 1.5's gate enforces this; never compose a path from a lane_id that failed it:

```
<dossier-root>/<topic-slug>/
  02a-prompts-<lane_id>.md     # all prompts for that lane, ready to paste
```

Each lane's output is later saved back as `02-<lane_id>.md`. The **standard lane set** — the filenames when `lane_roles` matches the default stack — is `02a-prompts-perplexity.md`, `02a-prompts-gemini.md`, `02a-prompts-grok.md`, `02a-prompts-claude.md`, `02a-prompts-deepseek.md` (decorrelated lane — omit only if skipped per Step 2.2), plus `02a-prompts-chatgpt.md` and `02a-prompts-notebooklm.md` when assigned. Project-specific lanes (a SERP analysis, a live job-board scan — see runbook 11, "Specialist lanes") use the same convention under their declared `lane_id`.

#### Step 2.2 — Instruct the user

**Decorrelated-lane decision point.** The governing question is **where the prompt data goes, not whose model it is** — the lane stays in the fan-out whenever a compliant route exists, because it is the highest-leverage quality gate in the pipeline. Read the confidentiality answer from Step 0.3 / `00-context.md` (ask now if missing), then choose the route:

- **Non-confidential work** — the **DeepSeek web UI** in DeepThink (reasoning) mode. This is the default; the China-hosted consumer service is fine when the prompt data is not sensitive.
- **Confidential work, compliant route available** — keep the lane, but not through the consumer web UI (China-hosted: the prompt would leave the jurisdiction). Use either:
  - a **Western-hosted API** serving the same open weights — data stays in-region, acceptable subject to the provider's terms; have the user confirm the hosting region, or
  - **self-hosted inference** — no third-party exposure, always acceptable for confidential work.
- **Confidential work, no compliant route available** — only then skip the lane. Log in `00-context.md`: "Decorrelated lane skipped: confidential material, no in-region route available; correlated-error risk accepted." Phase 2 runs with four agents; adjust the instructions below accordingly.

The choice is about the **route**, not whether to run the lane; skipping is the last resort, not the default for confidential work.

Then render the fan-out instructions **from `lane_roles`** — one entry per lane, driven by its `execution_surface` — rather than from a fixed tab list. For the standard stack the rendering is the block below (with the DeepSeek lines and the five/four counts matching the decision):

> "Phase 2 prompts are saved per-agent. Open five browser tabs side-by-side:
>
> 1. **Perplexity** (Deep Research mode enabled): paste contents of `02a-prompts-perplexity.md`. Submit.
> 2. **Gemini** (Deep Research mode): paste contents of `02a-prompts-gemini.md`. Submit.
> 3. **Grok** (DeepSearch enabled): paste contents of `02a-prompts-grok.md`. Submit.
> 4. **Claude.ai web** (web search enabled, NOT in your research project — separate tab): paste contents of `02a-prompts-claude.md`. Submit.
> 5. **DeepSeek — the decorrelated lane**, via the route chosen at the decision point above (web UI in DeepThink/reasoning mode for non-confidential work; a Western-hosted API or self-hosted endpoint for confidential work): paste contents of `02a-prompts-deepseek.md`. Submit.
>
> Start all five within 60 seconds. They run in parallel and finish in 3-15 minutes each.
>
> When each agent finishes, save its full output back into the dossier folder:
> - `02-perplexity.md`
> - `02-gemini.md`
> - `02-grok.md`
> - `02-claude.md`
> - `02-deepseek.md`
>
> Then come back and tell me 'Phase 2 outputs are saved.'"

If NotebookLM is included for this project (brownfield, ebook with private corpus, health content with curated PDFs, or another private-corpus use case):

> "Additionally for NotebookLM: upload the relevant private corpus to a NotebookLM notebook, then run the prompt from `02a-prompts-notebooklm.md`. Save output as `02-notebooklm.md`."

If Phase 1 assigned **ChatGPT** (per the Step 0.3 inventory — the only OpenAI-lineage lane; the assignment rule expects it whenever the operator holds it):

> "Additionally open **ChatGPT** (Deep Research): paste contents of `02a-prompts-chatgpt.md`. Submit. Save output as `02-chatgpt.md`."

For any lane outside the standard set, render its instruction from its declared `execution_surface`:

- **A named product** — "Open <product> (<mode>): paste contents of `02a-prompts-<lane_id>.md`. Submit. Save output as `02-<lane_id>.md`."
- **`browser-agent`** — the prompt runs through a browser-driving agent; name the tool the user has, or ask which they want to use.
- **`orchestrator-local`** — this session runs the lane itself via its own fetch/search tooling and writes `02-<lane_id>.md` directly. Acceptable **only** for empirical/counting lanes (see runbook 11, "Specialist lanes" — lineage decorrelation matters less when a lane counts rather than reasons); never for synthesis lanes. Note the lineage overlap in the output header so Phase 3 can discount same-lineage concurrence.
- **`manual`** — the user gathers this by hand; state exactly what to collect and where to save it.

A lane never ships as a role without a surface: if a staged prompt exists and its lane has no runnable surface, stop and resolve it with the user rather than leaving them holding a prompt with nowhere to paste it.

Pause.

### Phase 2.5 — Debate pass (conditional)

#### Step 2.5 — Debate (BLOCKING when overlay 13 selected Debate)

Runs only when the `00-context.md` mode set contains `debate` (overlay 13, Mode 2). A selected mode is mandatory (overlay contract); cancelling one requires the user's explicit decision, logged in `00-context.md`.

1. Read overlay 13, "Mode 2 — Debate". Build one prompt per participating lane from its ready-to-paste template: FOR to roughly half the lanes, AGAINST to the rest — and **the decorrelated lane always participates** (overlay 13's hard constraint: debate among same-lineage models amplifies shared bias instead of correcting it). If the decorrelated lane was skipped at Step 2.2, stop and surface it: the user must restore the lane or explicitly cancel the mode. Fill each lane's assigned side into the template's Position line (`Position: FOR` / `Position: AGAINST`) — the Phase 2 debate gate accepts a literal `Position:` line or a `POSITION STATEMENT — FOR/AGAINST` header, and the template uses the first form.
2. Stage per-lane files mirroring Step 2.1: `02b-prompts-debate-<lane_id>.md`.
3. Instruct the user to run them on the same surfaces as Phase 2 and save outputs as `02b-debate-<lane_id>.md`. Pause.
4. On resume, Step 3.1's gate covers the `02b-debate-*` files too. Debate outputs join Phase 3 as additional inputs; per overlay 13, judge **argument quality, not vote count**.

### Phase 3 — Cross-examination

#### Step 3.1 — Phase 2 output gate (BLOCKING)

When the user resumes, check that a `02-<lane_id>.md` file exists and is non-empty for every lane in `lane_roles` that ran (plus `02b-debate-<lane_id>.md` files when the Debate pass ran). If any are missing or empty, ask the user.

Then run the gate script over the dossier folder:

```
python ./scripts/gate_phase2.py <dossier-root>/<topic-slug>
```

The script splits every lane file into echoed-prompt and answer — reporting which method it used (sentinel, prompt-tail, or whole-file) — and computes ALL metrics on the answer only, because an echoed prompt satisfies every substring check by itself. **The split fails closed:** when a staged prompt exists, a lane output must establish its boundary via the sentinel or the prompt's uniquely-matching final line; any echo evidence without a boundary, or no boundary at all, fails C1 — whole-file scoring happens only when no staged prompt is available, and is noted. It checks: six-section structure with non-trivial content under each full-line heading (a body line like `Sources = [...]` is not a heading); per-finding confidence tags (escaped `\[HIGH\]` counts after normalisation); the citation census — **https URLs only**, where `[n]`, `[^n]`, `[^name]`, compound `[1, 2]`/`[3-4]`, and `【n†…】` are dead markers and the lane fails when dead markers reach or exceed its https URL count; concealment in any hidden markup (nested or unclosed `<span>`/`<div>`, `hidden` attributes, `display:none`/`visibility:hidden` styles, screen-reader-only classes, HTML comments) inside the answer region — hidden content in the echoed-prompt region is exempt; and a claims-vs-delivery check — an output asserting sections the structural check cannot find fails on that alone. Files named `02b-debate-<lane_id>.md` are gated against the **Debate contract** instead of the six sections: position statement, evidence/reasoning with at least one `[REASONED]` tag, rebuttal, the flip-fact, KEY TENSION, COMMON GROUND, plus ≥2 distinct https URLs.

- **Any lane FAILS:** that lane must be re-exported or re-run before Phase 3. **Do not proceed with any lane in a failed state.** Surface the per-lane matrix with the specific failure lines.
- **All lanes pass:** additionally run the **live-URL spot-check** — the script verifies URL presence and shape, not that pages actually resolve. Spot-open 3 citations per lane via Firecrawl MCP or web fetch if available on this surface; otherwise ask the user to open them in a browser and report. Dead links fail the lane.
- **Script cannot run:** say so explicitly and walk the manual checklist below per lane as a blocking gate. Never silently skip.

Record results in `00-context.md` as `phase2_gate: <lane>=PASS|FAIL … (script|manual)`.

**Manual fallback checklist (mirrors checks C1–C7):**

1. Find the last standalone `===BEGIN LANE OUTPUT===` line, or the staged prompt's final line appearing exactly once; everything before it is echo — judge ONLY what follows. **Fail closed:** if a staged prompt exists and neither boundary can be established — including when the prompt is only partially echoed — FAIL and re-export. Judge the whole file only when no staged prompt exists, and say so.
2. All six sections present after the boundary as real full-line headings, each with real content (Findings ≥3 numbered items; Sources ≥3 https URLs). A prose line that merely starts with a section word is not a heading.
3. Every numbered finding tagged [HIGH]/[MEDIUM]/[LOW] — escaped `\[HIGH\]` counts.
4. Count distinct `https://` URLs in the answer (http does not count): ≥3, at least one per two findings, and strictly more https URLs than dead markers — `[n]`, `[^n]`, `[^name]`, compound `[1, 2]`/`[3-4]`, `【n†…】` (confidence and ground-truth tags are not markers). Equal counts FAIL.
5. Inspect the raw text of the ANSWER region for concealment: hidden `<span>`/`<div>` (inline `display:none`/`visibility:hidden`, `hidden` attributes, screen-reader-only classes), nested or unclosed hidden containers (unclosed = automatic FAIL), and HTML comments carrying references or substantial content. Hidden content in the echoed-prompt region is exempt.
6. If the output *claims* a section you cannot find structurally, FAIL.
7. Note roughly what fraction of the file is echoed prompt.

**Debate outputs (`02b-debate-<lane_id>.md`) use the Debate contract instead of items 2–3 and 6:** position statement (a literal `Position: FOR|AGAINST` line or a `POSITION STATEMENT — FOR/AGAINST` header), evidence/reasoning with at least one `[REASONED]` tag, rebuttal to the strongest opposing argument, the one flip-fact, KEY TENSION, COMMON GROUND; ≥2 distinct https URLs. Items 1, 4 (with the floor of 2), 5 and 7 apply unchanged.

#### Step 3.2 — Build Phase 3 prompt

Use the contradiction-matrix prompt from `./references/01-prompts-library.md`. Inline one `<lane_id>_output` block per lane that ran (the six shown in the template are the standard set), plus one `<lane_id>_debate_output` block per lane when the Debate pass ran. When overlay 13 is active, include the prompt's conditional section 6 (DCI TALLY).

#### Step 3.3 — Determine where Phase 3 runs

Same options as Phase 1: Claude.ai web (best) or local model. Phase 3 is more mechanical than Phase 1 / 5 — the locally available Claude model is acceptable for most projects.

#### Step 3.4 — Execute and save

Save output as `<dossier-root>/<topic-slug>/03-conflict-map.md`. Update `00-context.md`.

### Phase 4 — Citation verification

#### Step 4.1 — Extract URL list

Parse `03-conflict-map.md`. Extract every URL referenced. Group by section: AGREEMENT, SINGLE-SOURCE, SUSPECT-CITATIONS.

#### Step 4.2 — Programmatic verification (if Firecrawl MCP available)

For each URL, use Firecrawl MCP to:
1. Confirm the URL resolves (HTTP 200 or equivalent)
2. Fetch the content
3. For URLs supporting specific claims, verify the claim text appears in or is supported by the page content

Mark each URL: VERIFIED / NOT_FOUND / CONTENT_MISMATCH / NEEDS_HUMAN_REVIEW.

If Firecrawl MCP is not available, skip programmatic verification — rely on the manual + plausibility-check steps below.

#### Step 4.3 — Plausibility check (always)

Use the plausibility-check prompt from `./references/01-prompts-library.md` to flag URLs with implausible structure (sequential arxiv IDs, suspicious round numbers, domain mismatches, generated-looking paths).

#### Step 4.4 — Manual deep-check (always)

Surface the top 5 most load-bearing citations to the user with instruction: *"Open these in your browser and confirm the source actually says what the agent claimed. Reply with 'all confirmed' or list any issues."*

For health content specifically: also instruct the user to run RCT/meta-analysis citations through Scite (https://scite.ai) to check whether later papers contradicted the cited finding.

#### Step 4.5 — Red Team pass (Phase 4.5 — BLOCKING when overlay 13 selected Red Team)

Runs whenever the `00-context.md` mode set contains `red-team` (overlay 13, Mode 1). Mandatory when selected (overlay contract); cancelling requires the user's explicit decision, logged in `00-context.md` — never a silent skip. The flow is Debate → Red Team → Decision: this pass attacks the draft recommendation that has emerged from Phases 2–4, before the Chairman consolidates it.

1. Write the one-paragraph **draft recommendation under attack** — from `03-conflict-map.md` and the surviving sources — with its key assumptions stated explicitly. Confirm it with the user.
2. Build one prompt per participating lane from overlay 13, "Mode 1 — Red Team", assigning each lane 1–2 of the six attack vectors; **the decorrelated lane is mandatory here** — if it was skipped at Step 2.2, stop and surface it: the user must restore the lane or explicitly cancel the mode, logged (same rule as Step 2.5). If Phase 1 staged these as `deferred_phase_prompts`, they may carry the declared placeholder `<DRAFT_RECOMMENDATION>` until this step fills it — the only sanctioned deferred token, and it must be filled before hand-off.
3. Stage `04a-prompts-redteam-<lane_id>.md`; the user runs them on the same surfaces as Phase 2 and saves outputs as `04a-redteam-<lane_id>.md`. Pause.
4. On resume, **before anything else**: confirm a non-empty `04a-redteam-<lane_id>.md` exists for every lane staged in step 3. Phase 5 stays blocked while any required output is missing or empty — ask the user to complete or explicitly cancel.
5. **Verify the new evidence.** Red-team outputs arrive after Phase 4 ran, and they routinely introduce new factual URLs. Extract every URL from the `04a-redteam-*` files and run it through the same verification as Steps 4.2–4.4 (Firecrawl/plausibility/manual as available); append survivors to `04-verified-sources.md` and rejects to `04-rejected.md`. The Chairman must never rely on an unverified red-team citation.
6. Sort findings KILL > MAJOR > MANAGEABLE; explicitly flag the findings the user had not considered — those are the real blind spots. Carry all `04a-redteam-*` files into Phase 5, where the Decision Brief's UNRESOLVED DISAGREEMENTS, UNCONTESTED RISKS, and CORRECTION LEDGER sections consume them.

#### Step 4.6 — Save outputs

Save to:
- `<dossier-root>/<topic-slug>/04-verified-sources.md` — citations that survived
- `<dossier-root>/<topic-slug>/04-rejected.md` — citations that failed (audit trail)

Update `00-context.md`.

Optionally, before Phase 5: run the methodology's eval gate (a 5–10 question golden-set regression — see `./references/00-master-methodology.md`, Decision rules) as calibration. It shares the methodology's Phase 4.5 slot with the Red Team pass but is independent of it — calibration, not adversarial review; skip freely for low-stakes dossiers.

### Phase 5 — Consolidation (Chairman synthesis)

**Phase 5 is gated on capability, not venue.** The Chairman needs three things at once:

1. the **strongest available Claude model**;
2. **extended thinking at maximum**;
3. a **fresh context** holding the full input set — and nothing else.

The third is an independence requirement, not a convenience: an orchestrator that has run Phases 0–4 has formed views about the answer — it has seen the conflicts, judged the gates, perhaps corrected ground truth. A Chairman inheriting that context synthesises from its own priors instead of deriving from the inputs, and can import claims that exist only in the conversation and in no `02-*.md` — violating its own rule against introducing claims absent from the inputs. This is the same independence principle the decorrelated lane enforces at Phase 2, applied to the synthesis seat.

**Pre-Phase-5 input-budget check (always, before choosing a route):** sum the byte sizes of the full input set — all `02-*.md`; `02b-debate-*.md` if Debate ran; `03-conflict-map.md`; `04-verified-sources.md`; `04-rejected.md`; `04a-redteam-*.md` if Red Team ran; the ground-truth section of `00-context.md` — estimate tokens (≈ bytes ÷ 4), and report the figure to the user. Then choose a route, in preference order:

- **(a) A fresh subagent** on the strongest available Claude model, launched with only the Chairman prompt + inputs and no orchestration history — preferred wherever the surface supports subagents and the inputs fit. Same independence as a fresh chat, no manual copy-paste hop (every manual transfer is a place an artifact can be silently truncated — a failure observed live), and the output lands in the dossier folder directly.
- **(b) A fresh Claude.ai web chat** — the Step 5.2 hand-off. The default when (a) is unavailable.
- **(c) This session inline — permitted only if BOTH hold:** few phases actually ran in this context (low contamination), AND the budget check shows the input set demonstrably fits the remaining window. State both conditions to the user before proceeding.

#### Step 5.1 — Build the Chairman prompt

Read from `./references/`:
- `01-prompts-library.md` → Chairman prompt template
- The relevant overlay → "Phase 5 — output format block"

Compose the full Chairman prompt:
1. Role + rules from the universal Chairman template
2. Inputs: paste contents of all `02-*.md`, `03-conflict-map.md`, `04-verified-sources.md`, `04-rejected.md` — plus `02b-debate-*.md` and `04a-redteam-*.md` when those passes ran, and the ground-truth block (with tag semantics) when claims exist
3. Output format block from the use-case overlay — for decision research (use case 8), or when overlay 13 is layered, this is the Decision Brief format from `./references/13-overlay-deliberation-modes.md`

Sizing comes from the input-budget check above; if the set exceeds the chosen route's window, chunk by sub-question rather than by agent, and surface that to the user first.

#### Step 5.2 — Hand off to the fresh-context Chairman

**Route (a) — fresh subagent:** launch it with the composed Chairman prompt as its entire task, no orchestration history. Save its output to `<dossier-root>/<topic-slug>/05-dossier.md` directly.

**Route (b) — fresh Claude.ai web chat:** output the full prompt + instruction:

> "Open a fresh Claude.ai chat (a research Project is optional — the prompt below carries its full input set). Set extended thinking to maximum effort. Paste the prompt below. The output is your final dossier.
>
> When the dossier is ready, save it back to `<dossier-root>/<topic-slug>/05-dossier.md` and tell me 'Phase 5 complete.'"

Pause.

**Route (c) — inline:** restate the two conditions and the token estimate, then run the Chairman prompt in this session and save `05-dossier.md`.

#### Step 5.3 — Optional CoVe self-check

After user returns with `05-dossier.md`, optionally offer to run the Chain-of-Verification self-check (prompt in `./references/01-prompts-library.md`) as a final pass. Recommended for high-stakes deliverables.

If user accepts: surface the CoVe prompt for them to paste into the same Claude.ai chat. Save the revised output as `05-dossier.md` (overwrite previous).

### Phase 6 — Output routing

Read the relevant overlay's "Phase 6 — output routing" section. Walk the user through the use-case-specific routing.

For spec-driven dev specifically:

#### Step 6.1 — Migrate dossier into repo

Copy `<dossier-root>/<topic-slug>/05-dossier.md` to `<repo>/docs/research/<topic-slug>.md` and commit it (on shell surfaces — bash and PowerShell equivalents:)

```bash
cp <dossier-root>/<topic-slug>/05-dossier.md \
   <repo>/docs/research/<topic-slug>.md
cd <repo>
git add docs/research/<topic-slug>.md
git commit -m "research: <topic-slug>"
```

```powershell
Copy-Item <dossier-root>\<topic-slug>\05-dossier.md <repo>\docs\research\<topic-slug>.md
Set-Location <repo>
git add docs/research/<topic-slug>.md
git commit -m "research: <topic-slug>"
```

If GitHub MCP is available, this can be a single tool call.

#### Step 6.2 — Hand off to Spec Kit / Kiro / cc-sdd

Per the overlay, output the next commands:

```bash
# In Claude Code, in the repo:
/speckit.constitution    # one-time per repo
/speckit.specify         # paste docs/research/<topic-slug>.md as input
/speckit.plan
/speckit.tasks
/speckit.implement       # or hand off to agentic mode
```

Or for Kiro: open Kiro IDE, paste dossier "Problem statement" + "Constraints" + "Chosen option", flow through Requirements → Design → Tasks.

For YouTube / presentation / ebook / WordPress / health / deck+screencast / decision research: follow the overlay's Phase 6 instructions.

#### Step 6.3 — Update dossier folder status

Append to `00-context.md`:

```
## Status
Pipeline complete. Dossier published to: <destination>
Date: <timestamp>
```

---

## Resume mid-pipeline

If the user invokes this skill with "Resume research on `<topic-slug>`", first run Step 0.0 to resolve the dossier root, then read `00-context.md` from `<dossier-root>/<topic-slug>/`. Identify which phase was last completed. Pick up from the next phase.

If no folder named `<topic-slug>` exists under `<dossier-root>` (e.g. the dossier was created on another machine or under an older location), ask the user where that dossier folder lives rather than failing.

If `00-context.md` shows ambiguous state, ask the user to clarify which phase they're returning from.

---

## Skills + MCP integration

If the following are available, use them:

| Tool | Used in | How |
|---|---|---|
| `research-requirements-check` skill | Phase 0.5 | Auto-invoke when requirements file present |
| Firecrawl MCP | Steps 0.6, 3.1, 4.2 | Ground-truth verification + programmatic URL verification |
| GitHub MCP | Phase 6.1 (spec-dev) | Commit dossier, open PR |
| Context7 MCP | Phase 5 (optional) | Fresh vendor doc verification during Chairman synthesis |
| Memory MCP | Across phases | Persist context between Cowork sessions if conversation spans days |

---

## Failure modes to watch

1. **User wants to skip Phase 4** — soft refuse if deliverable will be published or carries weight. Explain why; let them override consciously.
2. **User asks for a single-agent dossier** — defeats the methodology. Explain that the multi-agent fan-out and contradiction matrix are the value; if they want single-agent output they should just use that agent directly.
3. **User has vague research question** — pause and run a sharpening pre-step. A vague question produces a vague dossier.
4. **Phase 2 outputs missing or partial** — don't proceed to Phase 3 with <3 agent outputs. Ask user to complete fan-out first.
5. **Phase 5 inputs exceed context window** — chunk by sub-question rather than by agent. Surface to user before attempting.
6. **User runs the orchestrator in a project type not covered by overlays 02-08 and 13** — ask if they want to adapt the closest overlay or stop and define a new overlay.
7. **`research-config.md` deleted or moved mid-project** — re-run Step 0.0 to re-resolve the dossier root; do not assume the previous root still applies.
8. **An active overlay declares a mandatory mechanism with no wired step** — halt and surface it (see the overlay contract). Silent skipping is a defect: a control that appears to exist but never runs is worse than a missing one, because nobody notices it's gone.

---

## State management

The skill is stateless within a session beyond what's in `<dossier-root>/<topic-slug>/00-context.md`. Each invocation reads that file to determine current phase. Updates are written immediately so the skill is resumable across sessions.

If running in Cowork (no cross-session memory), this state file is the only continuity mechanism. Treat it as the source of truth.

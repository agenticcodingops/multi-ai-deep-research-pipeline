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

This skill does NOT itself execute Phases 1, 3, or 5 (the cognitive phases) when running in Cowork or Claude Code with default models. It prepares inputs and hands off to Claude.ai web for those phases when model quality matters. It DOES execute Phases 0, 2 (preparation), 4 (verification), and 6 (routing) directly.

---

## Prerequisites

Before this skill runs, verify:

1. **Bundled reference integrity.** This skill ships its methodology artifacts inside the skill at `./references/` — 14 files, `00-master-methodology.md` through `13-overlay-deliberation-modes.md`. Confirm the folder exists and contains, at minimum: `00-master-methodology.md`, `01-prompts-library.md`, overlays `02-` through `07-`, `08-overlay-deck-and-screencast.md`, `12-project-startup-checklist.md`, and `13-overlay-deliberation-modes.md`. If any expected file is missing, **halt and report exactly which file is missing** — the installation is incomplete and the user should reinstall the plugin. Never degrade silently to a partial overlay set.
2. **Requirements-check availability.** The `research-requirements-check` skill ships in the same plugin as this skill. Check by skill availability (invoke it by name when Step 0.5 needs it), not by filesystem path — installed skill locations differ per surface. If it is unavailable, warn the user that requirements auditing will be skipped; the rest of the pipeline still runs.
3. **Agent access.** The user needs access to Claude.ai web (with extended thinking) for the cognitive phases, plus deep-research-capable access to Perplexity, Gemini, and Grok for Phase 2 — and, for the decorrelated lane, a DeepSeek route (web UI, Western-hosted API, or self-hosted; see Step 2.2). Confirm in the opening message if uncertain.

If prerequisite 1 fails, halt. If prerequisite 3 is uncertain, surface it and let the user decide.

---

## Procedure

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

**Layering note:** overlay 13 also **layers on top of another overlay** when a dossier under any use case supports a decision (go/no-go, build/buy, launch, investment). Keep the primary overlay from the table and apply overlay 13 additionally — it is an additive Phase-2/Phase-3 pass, never an alternative primary. Record both overlays in `00-context.md`.

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
> 4. Existing inputs: any files you want me to use as input? (Requirements docs, prior research, brand guidelines, etc.)
> 5. Confidentiality: does this research involve confidential material (internal architecture, client code, business-sensitive context), or is it non-confidential/public? This determines how the decorrelated research lane is routed in Phase 2 — web UI, Western-hosted API, or self-host (see Step 2.2)."

If a requirements file is mentioned, store the path for Step 0.5. Record the confidentiality answer — it is written to `00-context.md` and consumed at Step 2.2.

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

### Phase 1 — Decomposition

#### Step 1.1 — Determine where Phase 1 will run

Phase 1 runs best on the strongest available Claude model with extended thinking (Claude.ai web). Ask the user:

> "Phase 1 decomposition runs best in Claude.ai web (strongest available Claude model + extended thinking at maximum). Two options:
> 1. I generate the Phase 1 prompt now and you paste it into a fresh Claude.ai chat in your research project. You bring the JSON output back here, I save it as 01-decomposition.md.
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
5. **NEW (Phase 1 upgrade): customised Phase 2 prompts**: Add to the JSON output spec the requirement to also output `phase_2_prompts` — an array of `{sub_question_id, agent, ready_to_paste_prompt}` where each prompt is fully formed (no placeholders) and ready to copy directly into the assigned agent's interface in Phase 2. The agent set includes the DeepSeek decorrelated lane; for confidential work its route changes (Western-hosted API or self-host) rather than the lane being dropped, and it is omitted only when no compliant route is available (Step 0.3 / Step 2.2).

#### Step 1.3 — Execute Phase 1

If user chose option 1: output the prompt + instruction *"Paste this into a fresh Claude.ai chat in your research project. Set extended thinking to maximum. When the JSON output is ready, paste it back here."* Pause.

If user chose option 2: send the prompt to the local Claude model. Capture JSON output.

#### Step 1.4 — Save Phase 1 output

Save the JSON to `<dossier-root>/<topic-slug>/01-decomposition.md`. Update `00-context.md` status: "Phase 1 complete."

### Phase 2 — Parallel fan-out (preparation only — execution is manual by user)

#### Step 2.1 — Surface the customised Phase 2 prompts

Read `01-decomposition.md`. Extract the `phase_2_prompts` array. Write each prompt to a per-agent file:

```
<dossier-root>/<topic-slug>/
  02a-prompts-perplexity.md    # all sub-questions assigned to Perplexity, prompts ready to paste
  02a-prompts-gemini.md        # same for Gemini
  02a-prompts-grok.md          # same for Grok
  02a-prompts-claude.md        # same for Claude.ai web search
  02a-prompts-deepseek.md      # decorrelated lane — omit if skipped per Step 2.2
  02a-prompts-chatgpt.md       # optional sixth lane — only if Phase 1 assigned it
  02a-prompts-notebooklm.md    # if NotebookLM assigned
```

#### Step 2.2 — Instruct the user

**Decorrelated-lane decision point.** The governing question is **where the prompt data goes, not whose model it is** — the lane stays in the fan-out whenever a compliant route exists, because it is the highest-leverage quality gate in the pipeline. Read the confidentiality answer from Step 0.3 / `00-context.md` (ask now if missing), then choose the route:

- **Non-confidential work** — the **DeepSeek web UI** in DeepThink (reasoning) mode. This is the default; the China-hosted consumer service is fine when the prompt data is not sensitive.
- **Confidential work, compliant route available** — keep the lane, but not through the consumer web UI (China-hosted: the prompt would leave the jurisdiction). Use either:
  - a **Western-hosted API** serving the same open weights — data stays in-region, acceptable subject to the provider's terms; have the user confirm the hosting region, or
  - **self-hosted inference** — no third-party exposure, always acceptable for confidential work.
- **Confidential work, no compliant route available** — only then skip the lane. Log in `00-context.md`: "Decorrelated lane skipped: confidential material, no in-region route available; correlated-error risk accepted." Phase 2 runs with four agents; adjust the instructions below accordingly.

The choice is about the **route**, not whether to run the lane; skipping is the last resort, not the default for confidential work.

Output (with the DeepSeek lines and the five/four counts matching the decision):

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

If Phase 1 assigned **ChatGPT** as the optional sixth lane (per the master methodology's agent inventory — useful for enterprise/regulated-industry contrast):

> "Additionally open **ChatGPT** (Deep Research): paste contents of `02a-prompts-chatgpt.md`. Submit. Save output as `02-chatgpt.md`."

Pause.

### Phase 3 — Cross-examination

#### Step 3.1 — Verify Phase 2 outputs are saved (sanity check with quality gates)

When the user resumes, check that a `02-<agent>.md` file exists and is non-empty for every agent that ran — five, or four if the decorrelated lane was skipped per `00-context.md` (plus NotebookLM and/or the optional ChatGPT sixth lane if assigned). If any are missing or empty, ask the user.

Then run two quality gates on each agent file:

1. **Live-URL paste-check.** Spot-open 3 citations per agent file — via Firecrawl MCP or web fetch if available on this surface; otherwise ask the user to open them in a browser and report. If the citations are dead links, bare reference markers, footnote numbers, or tool-internal citation tokens rather than live resolvable URLs, the file FAILS: the user must re-export or re-run that agent before Phase 3 proceeds.
2. **Confidence-tag check.** Every finding must carry a [HIGH]/[MEDIUM]/[LOW] confidence tag. A file with untagged findings FAILS: re-run that agent with the tagging requirement restated from `./references/01-prompts-library.md`.

Do not proceed to Phase 3 while any file is in a failed state. Record gate results in `00-context.md`.

#### Step 3.2 — Build Phase 3 prompt

Use the contradiction-matrix prompt from `./references/01-prompts-library.md`. Inline the contents of all `02-*.md` files into the prompt's `<*_output>` blocks.

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

#### Step 4.5 — Save outputs

Save to:
- `<dossier-root>/<topic-slug>/04-verified-sources.md` — citations that survived
- `<dossier-root>/<topic-slug>/04-rejected.md` — citations that failed (audit trail)

Update `00-context.md`.

Optionally, before Phase 5: run the methodology's Phase 4.5 eval gate (a 5–10 question golden-set regression — see `./references/00-master-methodology.md`, Decision rules) as calibration; skip freely for low-stakes dossiers.

### Phase 5 — Consolidation (Chairman synthesis)

**Phase 5 always runs in Claude.ai web with the strongest available Claude model, extended thinking at maximum.** This is non-negotiable for the quality bar.

#### Step 5.1 — Build the Chairman prompt

Read from `./references/`:
- `01-prompts-library.md` → Chairman prompt template
- The relevant overlay → "Phase 5 — output format block"

Compose the full Chairman prompt:
1. Role + rules from the universal Chairman template
2. Inputs: paste contents of all `02-*.md`, `03-conflict-map.md`, `04-verified-sources.md`, `04-rejected.md`
3. Output format block from the use-case overlay — for decision research (use case 8), or when overlay 13 is layered, this is the Decision Brief format from `./references/13-overlay-deliberation-modes.md`

If the prompt is very large (>100K tokens of inputs), consider chunking — but for most projects, paste directly.

#### Step 5.2 — Hand off to Claude.ai web

Output the full prompt + instruction:

> "Open a fresh Claude.ai chat in your research project. Set extended thinking to maximum effort. Paste the prompt below. The output is your final dossier.
>
> When the dossier is ready, save it back to `<dossier-root>/<topic-slug>/05-dossier.md` and tell me 'Phase 5 complete.'"

Pause.

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
| Firecrawl MCP | Phase 3.1, 4.2 | Programmatic URL verification |
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

---

## State management

The skill is stateless within a session beyond what's in `<dossier-root>/<topic-slug>/00-context.md`. Each invocation reads that file to determine current phase. Updates are written immediately so the skill is resumable across sessions.

If running in Cowork (no cross-session memory), this state file is the only continuity mechanism. Treat it as the source of truth.

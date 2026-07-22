# Software Development Research — Operational Runbook

**Owner:** AgenticCodingOps
**Status:** v1.1 — distilled from the pilot project + methodology v1.1 updates (decorrelated lane, confidence tags, live-URL rule, optional eval gate)
**Reads with:** project knowledge artifacts 00–08 (overlays), 09 (Cowork/skills setup), 12 (project startup checklist); CHANGELOG-v1.1.md for the rationale behind v1.1 additions

---

## Purpose

This is the playbook for running multi-AI research against a new software development project — greenfield or brownfield. It captures what actually worked on the pilot project, including the deviations from the standard 6-phase methodology that real projects required.

For non-coding work (YouTube, ebooks, presentations, WordPress, health, decision research), use the relevant overlay file (03–08, or 13 for decision research) plus 12-project-startup-checklist.md. The content runbook is `11-content-research-runbook.md`.

---

## Pre-flight (one-time setup, done already — verify before each new project)

These are foundational and should already be in place. Re-check only if something feels off.

| Item | Expected state | How to verify |
|---|---|---|
| Project knowledge in this Claude project | Artifacts 00–09 uploaded; project description + custom instructions reflect AgenticCodingOps research role | Open project settings, confirm files listed and instructions match those in `09-cowork-skills-setup.md` |
| Skills installed (plugin model) | The `multi-ai-research` plugin installed from the marketplace; it carries `research-kickoff-builder`, `research-orchestrator`, and `research-requirements-check` with the methodology bundled | `/plugin marketplace add …` + `/plugin install multi-ai-research@agenticcodingops` per `09-cowork-skills-setup.md`; then in a fresh session: *"What skills do you have available?"* — all three should be listed |
| Local methodology folder | `<research-stack>\` contains 00–09 as local reference copies | Optional but recommended for Cowork sessions; lets Cowork read methodology directly when needed |
| Dossier root | `<code-workspace>\dossiers\` exists | `dir <code-workspace>\dossiers` |
| MCPs in Claude Code | Firecrawl, GitHub, Context7 installed (high priority); Filesystem if you work outside Cowork | `claude mcp list` |
| Active subscriptions | a paid Claude plan, Perplexity Pro, Gemini Pro / Google AI Pro, SuperGrok | Open each service's billing page on the day of the project |

---

## The 6-phase pipeline in one diagram

```
PHASE 0  → Setup: dossier folder + Cowork session + requirements quality gate
   ↓
PHASE 1  → Decomposition (or prompt-improvement, for repeat projects)
   ↓
PHASE 2  → Parallel fan-out: 4-6 agents in browser tabs
   ↓
PHASE 3  → Contradiction matrix (Cowork or this Claude project)
   ↓
PHASE 4  → Citation verification (Firecrawl MCP + manual + SwanRef)
   ↓
PHASE 5  → Chairman synthesis (Claude.ai web in this project, max thinking)
   ↓
NotebookLM → Source-grounding sanity check (10-min add-on)
   ↓
PHASE 6  → Migrate dossier into repo → handoff to Claude Code
   ↓
SPEC KIT + KIRO → Implementation per the pilot project implementation-guide pattern
```

Total wall-clock from kick-off to Spec Kit input: typically 90–150 min including ~25 min unattended Phase 2 fan-out.

---

## Phase 0 — Setup

### 0.1 — Identify project shape

Three sub-cases for software dev research:

| Project shape | Signals | What changes |
|---|---|---|
| **Greenfield, no prior research** | New idea, no existing repo, no requirements file | Standard pipeline — run all 6 phases including full Phase 1 decomposition |
| **Greenfield, prior requirements draft** | New idea but Claude Code or similar has already produced a requirements markdown | Pipeline with requirements-check skill at Phase 0.5; possible Phase 1 prompt-improvement instead of decomposition (Pattern B) if implementation guide exists |
| **Brownfield, existing repo + requirements** | Change to existing system; repo workspace matters; pre-existing implementation guide likely | NotebookLM with repo docs uploaded becomes important; Phase 1 must surface existing-system constraints; dossier eventually migrates back to repo `docs/research/` |

The pilot project was the second case. Most of your future projects will be either case 2 or case 3.

### 0.2 — Decide which environment leads

| Environment | Use for | Reason |
|---|---|---|
| **Claude Desktop / Cowork session** | Project setup, file operations, brownfield repo reading, Phase 0/4/6 routing, optionally Phase 3 | Has filesystem access; auto-loads skills; can read `<code-workspace>\` workspace |
| **Claude.ai web (this project)** | Phase 5 Chairman synthesis (always); Phase 1 decomposition (preferred); Phase 3 if Cowork's model tier isn't sufficient | Has project knowledge access; the strongest available Claude model with extended thinking exposed here |
| **Browser tabs** | Phase 2 fan-out only | The only way to reach Perplexity / Gemini / Grok / ChatGPT |
| **Claude Code** | Phase 6 handoff onwards (`/speckit.specify` → implementation) | Tight loop with codebase; shares skills with Cowork |

Default: Cowork-led from Phase 0–4 and 6, with explicit handoff to Claude.ai web for Phase 5.

### 0.3 — Open Cowork with the right folder access

When starting a fresh Cowork session, grant access to **all three folders up front** — Cowork doesn't let you add folders mid-session:

- `<code-workspace>\` (full workspace — gives Cowork brownfield context for any repo)
- `<code-workspace>\dossiers\` (where research artifacts will live)
- `<research-stack>\` (local methodology copy — useful if Cowork needs to consult 00-master-methodology or 01-prompts-library mid-flow)

If you forget to add the third, it's usually fine — the skill carries enough context — but start with all three to avoid friction.

### 0.4 — Confirm or create the requirements file

Greenfield with no prior requirements: skip to Phase 1.

Greenfield with prior requirements from Claude Code: locate the file, decide whether to run the requirements-check skill. For documents that have been refined over multiple revisions (like the pilot project's v1.4), expect GREEN and proceed.

Brownfield: same as above, plus identify the repo paths Cowork should read for context.

### 0.5 — Requirements quality gate (skip only if confirmed GREEN)

If unsure about the file's quality, ask Cowork:

```
Run the research-requirements-check skill against <file path>.
Tell me the verdict (GREEN/AMBER/RED) and if AMBER/RED, generate a Claude Code 
fix prompt I can run in the repo to enrich it.
```

Three outcomes:

- **GREEN** → proceed to Phase 1
- **AMBER** → decide whether to fix first or accept gaps as Phase 1 sub-questions
- **RED** → run the Claude Code fix prompt in the repo, then re-audit

The pilot project was GREEN. Many of your existing requirements drafts will be too if they went through multiple revisions with Claude Code.

---

## Phase 1 — Decomposition or prompt-improvement

### Pattern A — Full decomposition (default, for projects with no prior research prompts)

Use this when:
- No prior research has been done on the topic
- No implementation guide exists with custom prompts
- Greenfield project starting from a clean slate

Phase 1 produces:
- 4–7 atomic sub-questions
- Agent assignments per sub-question
- **Phase 2 prompts pre-built per agent** (the Phase 1 upgrade in `01-prompts-library.md` — Claude generates ready-to-paste prompts, not just sub-questions)
- Disqualifying sources
- Success criteria
- Known traps

Where to run: **Claude.ai web in this project**, fresh chat, extended thinking maximum.

### Pattern B — Prompt improvement (for repeat projects with prior research)

Use this when:
- The project's requirements file or implementation guide already contains research prompts that have been run once
- You want a deeper, differentiated second pass rather than starting from scratch

This was the pilot project's path. The implementation guide had four prompts for Perplexity/ChatGPT/DeepSeek/Grok plus a cost prompt. We treated those as the decomposition and asked Cowork to improve them.

When asking Cowork to improve prompts, the load-bearing instruction is the **five quality criteria** that distinguish genuine improvement from cosmetic rewrites. From the pilot project prompt:

```
For each existing prompt, produce an improved version that:
(a) Explicitly asks for evidence NOT covered in the requirements file
(b) Adds project-specific architectural constraints (e.g., provider-agnostic)
(c) Adds "what would change your recommendation" prompting for contradiction
(d) Demands inline source URLs and [UNVERIFIED] tags
(e) Requires explicit "what this answer does NOT cover" coverage gaps
```

If your project has constraints that bias the research (the pilot project had "must be provider-agnostic"), state them once at the top of the prompt and demand they're applied throughout. Vague constraints get vague answers.

### Phase 1 outputs to save

Either pattern produces files in `<code-workspace>\dossiers\<topic-slug>\`:

- `00-context.md` — project metadata
- `01-decomposition.md` — sub-questions and agent assignments (Pattern A) OR a list of improvements made (Pattern B)
- `02a-prompts-<agent>.md` — one file per agent, containing the ready-to-paste prompt(s)

**Before Phase 2: spot-check the prompts.** Read at least the heaviest two yourself. If a prompt looks like a longer version of the original rather than substantively different framing, push back: *"Prompt 3 doesn't surface coverage gaps — rewrite criterion (e)."* Two iterations max.

---

## Phase 2 — Parallel fan-out

### Tools and assignments (default for software dev)

| Tab | Tool | What to enable | Save output as |
|---|---|---|---|
| 1 | Perplexity Pro | Deep Research mode | `02-perplexity.md` |
| 2 | Gemini | Deep Research mode | `02-gemini.md` |
| 3 | Grok (SuperGrok) | DeepSearch toggle | `02-grok.md` |
| 4 | Claude.ai web (separate tab, NOT in this project) | Web search enabled | `02-claude.md` |
| 5 | **🆕 Decorrelated lane: DeepSeek (chat.deepseek.com web UI)** | **DeepThink (reasoning) mode** | `02-deepseek.md` |
| 6 (optional) | ChatGPT (free-tier Deep Research is sufficient) | Deep Research mode | `02-chatgpt.md` |
| 7 (optional) | Perplexity Pro (second session) | Deep Research, for cost-only multi-provider tables | `02-cost-perplexity.md` |
| 8 (brownfield only) | NotebookLM with repo docs uploaded | — | `02-notebooklm.md` |

**Confidentiality caveat for the decorrelated lane (Tab 5):** `chat.deepseek.com` is China-hosted, so the consumer web UI sends your prompt out of jurisdiction. The governing question is **where the prompt data goes, not whose model it is** — so for confidential code research (internal architecture, code snippets, or otherwise business-sensitive context) the answer is to **keep the lane and change the route**, not to drop it:

- **Western-hosted API** serving the same open weights (e.g. OpenRouter, Fireworks, Together.ai) — data stays in-region; acceptable subject to the provider's terms, and confirm the hosting region;
- **self-hosted inference** on an internal VPS — no third-party exposure.

Skip the lane entirely **only when neither route is available**; then log the reason in `00-context.md` and explicitly accept the correlated-error risk in the dossier's quality section. For open-source / methodology / personal projects, the web UI is fine.

The pilot project used six tabs (the full set above except NotebookLM). For most projects, four or five is plenty; add the cost-dedicated Perplexity session only when you need multi-provider cost comparison tables.

### Agents to skip for software dev

- **Elicit** — academic literature, not relevant unless your project intersects empirical research questions
- **Consensus** — peer-reviewed yes/no/maybe consensus signals; same constraint
- **Felo** — multilingual; only useful for non-English source corpora

These three are mandatory for health content overlay (07) and irrelevant for software dev. If Cowork suggests adding them for a software project, push back — refer to the "Elicit and Consensus belong to the health overlay" rule.

### Execution

Open all tabs side-by-side. Paste each agent's prompt from `02a-prompts-*.md`. **Start all within 60 seconds**, then let them run in parallel. Most agents finish in 3–15 minutes.

While waiting, you can prepare the dossier folder structure or read the input files yourself.

### Saving outputs

When each agent finishes, save its full output to the dossier folder. Either:

- Paste each output back into the Cowork chat with file name, and let Cowork save to disk
- Or save manually via copy-paste into a text editor

The second is faster if you have many tabs open.

### Pre-Phase-3 sanity checks (3 minutes — non-negotiable)

Before triggering Phase 3, open each `02-*.md` file and verify:

1. **No truncation.** Deep Research outputs occasionally cut off mid-paragraph. If truncated, re-run that agent.
2. **Required structure present.** TL;DR, findings with URLs, "what would change your recommendation," "what this answer does NOT cover" — these are the four sections the improved prompts demanded.
3. **Citation density.** Pick three random factual claims per file. If a fifth or more are bare assertions without URLs, that file is unreliable.
4. **🆕 Live-URL paste-check.** Spot-open three citations per file in browser. If they're dead reference markers (e.g., ChatGPT's `【n†…】`) or don't resolve, the file fails — re-export or re-run that agent before Phase 3. This catches the failure mode where citations exist as text but can't be followed.
5. **🆕 Confidence tags present.** Each finding should be tagged [HIGH] / [MEDIUM] / [LOW]. Files without confidence tagging fail.
6. **Project-specific constraints honoured.** Provider-agnostic claims actually multi-provider, etc.

If any check fails for a file, re-run just that agent before Phase 3.

---

## Phase 3 — Contradiction matrix

### Where to run

Either Cowork (faster turnaround, default model) or Claude.ai web (better model but requires copy-pasting inputs). Phase 3 is mechanical comparison rather than deep reasoning — Cowork is usually sufficient.

### Prompt template

```
Phase 2 fan-out is complete. The N agent outputs are saved at:
- <code-workspace>\dossiers\<topic-slug>\02-<agent>.md (list all of them)

Resume the research-orchestrator skill at Phase 3 (cross-examination / 
contradiction matrix).

Read all N agent output files. Run the Phase 3 contradiction matrix prompt 
over them. Output structured markdown with five sections — AGREEMENT, 
CONFLICT, SINGLE-SOURCE, GAPS, and SUSPECT-CITATIONS — per the methodology 
in 01-prompts-library.md.

[Add any project-specific Phase 3 instructions here — e.g., separate cost 
contradiction matrix if you ran a cost-dedicated agent, or evidence-strength 
flags if relevant.]

Save the output as <code-workspace>\dossiers\<topic-slug>\03-conflict-map.md.

Update 00-context.md status to "Phase 3 complete".

Do not proceed to Phase 4 until I confirm.
```

### What to read first when the matrix comes back

In order of importance:

1. **CONFLICT** — the most valuable section. These contradictions become `[CONTESTED]` markers in Phase 5, and they're the things `/speckit.clarify` should ask you to resolve.
2. **SUSPECT-CITATIONS** — anything flagged here gets verified or rejected in Phase 4.
3. **GAPS** — sub-questions no agent answered well. If a gap is material, either run a targeted re-prompt or document it explicitly as a known limitation in Phase 5.
4. **SINGLE-SOURCE** — read these to spot anything load-bearing that only one agent claimed. Flag for Phase 4 verification.
5. **AGREEMENT** — high-confidence material; skim only.

---

## Phase 4 — Citation verification

### The four-step verification

1. **Programmatic (Firecrawl MCP if installed)** — Cowork batch-fetches every URL in the conflict map, verifies the page exists and the claim text appears in or is supported by the content. Marks each URL: VERIFIED / NOT_FOUND / CONTENT_MISMATCH / NEEDS_HUMAN_REVIEW.

2. **Plausibility check (always)** — flag URLs with implausible structure: sequential arxiv IDs, suspicious round numbers, domain mismatches, generated-looking paths. Reject any that fail.

3. **SwanRef batch (for academic citations)** — paste the URL list into swanref.org for cross-check against CrossRef, Google Scholar, OpenAlex. For software dev research this catches relatively few issues since most citations are vendor docs, but worth doing if you have any academic refs.

4. **Manual deep-check (always — the 10-minute highest-value step)** — open the top 5 most load-bearing citations directly in your browser. Read the relevant section. Confirm the source actually says what the agent claimed.

### Outputs

- `04-verified-sources.md` — citations that survived
- `04-rejected.md` — citations that failed (this is your audit trail — keep it)

For client work or anything published externally, `04-rejected.md` is itself a deliverable. It shows due diligence.

### Prompt template

```
Phase 3 complete and conflict map reviewed. Proceed to Phase 4 citation 
verification.

1. Extract all URLs from 03-conflict-map.md grouped by section.
2. Use Firecrawl MCP (if available) to verify each URL resolves and content 
   matches the claim.
3. Run plausibility check on URL structures — flag any suspect.
4. Surface the top 5 most load-bearing citations for me to manually verify 
   in browser.

Save survivors to 04-verified-sources.md and rejects (with reasons) to 
04-rejected.md.

Wait for my "manual verification complete" before Phase 5.
```

---

## Phase 4.5 — Eval gate (OPTIONAL — calibration only; shares the Phase 4.5 slot with overlay 13's Red Team mode, independently of it)

This is **not a mandatory phase**. Use only when you've made a material change to the methodology (e.g., adding a new agent, changing a Phase 1 prompt, updating a quality bar) and want to verify the change didn't silently degrade output quality.

### When to skip (most projects)

For standard project execution, skip this phase. The other quality gates (Phase 2 sanity check, Phase 3 contradiction matrix, Phase 4 verification, Phase 5 CoVe self-check) are sufficient.

### When to run

- You just added or removed an agent from Phase 2
- You changed a Phase 1 decomposition prompt
- You changed the Chairman prompt
- A recent dossier produced unexpectedly weak output and you want to isolate why
- You're calibrating the methodology against a known baseline

### How to run (20 minutes, one-off)

1. Maintain a golden set at `<research-stack>/eval-baseline/golden-set-v1.md` — 3-5 questions with known-good answers from prior dossiers
2. Run those questions through the current methodology (Phase 1 → 2 → 3 → 5, abbreviated)
3. Compare current outputs to known-good outputs
4. If divergence is unexpected: investigate which methodology change caused it; revert or accept consciously

The golden set itself needs maintenance — refresh it annually or when significant methodology changes accumulate.

---

## Phase 5 — Chairman synthesis

### Where this runs (non-negotiable)

**Claude.ai web in this project, fresh chat, extended thinking maximum.**

Not Cowork. Not Claude Code. The Chairman role wants the strongest available Claude model with full extended thinking, and the project knowledge gives it the methodology and overlays at runtime. Phase 5 is the one phase where model quality matters most.

### Procedure

In a fresh Claude.ai web chat in this project:

```
Begin Phase 5 — Chairman synthesis for the research project at 
<code-workspace>\dossiers\<topic-slug>\.

Apply the Chairman prompt from 01-prompts-library.md using the spec-driven 
dev output format from 02-overlay-spec-driven-dev.md.

I'll paste the inputs below — agent outputs, conflict map, verified sources, 
rejected sources. Produce 05-dossier.md per the spec-dev overlay's output 
format block, with these additional instructions:

[Project-specific output format adjustments — e.g., for the pilot project the format was 
the implementation guide's 9-section structure rather than the standard ADR 
shape. State any deviation here.]

[Paste all 02-*.md, 03-conflict-map.md, 04-verified-sources.md, 04-rejected.md 
inline below.]
```

Then paste the inputs.

### Chairman discipline reminders

The Chairman prompt enforces these automatically, but worth re-stating:

- Every claim tagged `[VERIFIED]` / `[SINGLE-SOURCE]` / `[CONTESTED]`
- Chain-of-Verification self-check before final output
- ≤15-word quotes from any single source
- No claims introduced from training knowledge
- Disagreements preserved, not smoothed

If the output looks too clean (too few `[CONTESTED]` markers given the conflict map content), the Chairman over-smoothed. Re-run with the CoVe prompt from `01-prompts-library.md` as a follow-up.

### Save the output

Paste the dossier back into Cowork to save to disk, or save manually:

```
<code-workspace>\dossiers\<topic-slug>\05-dossier.md
```

---

## NotebookLM sanity check (10 minutes — strongly recommended for high-stakes dossiers)

After Phase 5, before Phase 6.

1. Open NotebookLM (included in your Gemini Pro / Google AI Pro subscription).
2. Create a new notebook for this project.
3. Upload as sources:
   - The input files (requirements, alignment report, implementation guide if any)
   - All `02-*.md` agent outputs
   - `03-conflict-map.md`
   - `04-verified-sources.md`
   - `05-dossier.md`
4. Run two queries:

   **Query 1 — hallucination check:**
   ```
   For each numbered claim in 05-dossier.md, identify which uploaded source 
   supports it. Flag any claim that cannot be traced to an uploaded source.
   ```

   **Query 2 — drop check:**
   ```
   What's in the agent outputs (sources starting with 02-) that did NOT make 
   it into the dossier? Highlight any material claim that was dropped.
   ```

Query 1 catches Chairman hallucinations — claims that drifted in from training rather than from inputs. Query 2 catches Chairman over-pruning. Both are cheap and materially raise dossier quality.

If either query surfaces issues, return to Phase 5 with the findings and ask for a targeted revision.

---

## Phase 6 — Migrate to repo and hand off to Claude Code

### Phase 6 use-case selection — note

For software dev projects, Phase 6 routes to Spec Kit / Kiro / Claude Code per the implementation guide pattern (below). This runbook does not change for that handoff.

For the rare software dev project that ALSO needs a presentation deliverable (e.g., architecture review with both spec docs AND a presentation deck to stakeholders), use overlay `08-overlay-deck-and-screencast.md` for the presentation half. The dossier produced by this runbook feeds both the Spec Kit handoff AND overlay 08's Phase 6 routing.

### Migrate

```
Resume the research-orchestrator skill at Phase 6.

Copy <code-workspace>\dossiers\<topic-slug>\05-dossier.md to:
<code-workspace>\<primary-repo>\specs\<topic-slug>\phase0\insights-digest.md

(or whatever path matches the project's implementation guide convention)

Commit to the repo on a feature branch:
- branch: feature/<topic-slug>
- commit message: "research: <topic-slug> phase 0 digest"

Then output the exact prompt I should paste into a fresh Claude Code session 
inside <primary-repo> to begin /speckit.specify per the project's 
implementation guide.

Update 00-context.md status to "Phase 6 complete — dossier migrated".
```

### Handoff to Claude Code

Open Claude Code inside the repo. Paste the next-action prompt Cowork generated. The implementation guide's Phase 1 takes over from here:

1. `/speckit.specify` with the dossier as input
2. Kiro Spec mode in parallel (separate session)
3. Merge prompt comparing Spec Kit and Kiro outputs
4. `/speckit.clarify` to resolve `[CONTESTED]` markers and other ambiguities
5. Optional `/interview-me` for blind-spot detection
6. `/speckit.plan` and Kiro Design phase in parallel; merge
7. `/speckit.tasks` and Kiro Tasks phase; merge
8. `/speckit.taskstoissues` to push to GitHub Issues
9. `/speckit.implement` per-repo, lowest-blast-radius first

The research dossier is no longer the focus from this point — it's input. The implementation guide takes over.

---

## Lessons captured from the pilot project

These are non-obvious things the pilot project surfaced. Internalise them.

### 1. Existing prompts get a deeper second pass, not a re-run

When a project's implementation guide already contains research prompts that have been used once, don't run them verbatim. Cowork's "prompt improvement" with the five quality criteria (a–e in Phase 1) produces materially deeper output than re-running the originals. This was the pilot project's biggest leverage move.

### 2. The provider-agnostic constraint must be stated load-bearingly

For any architectural research where "we shouldn't lock in to one vendor" matters, put that constraint at the top of the orchestrator prompt AND in the Phase 1 prompt-improvement instructions AND in the Phase 5 output format. State it three times. Otherwise agents drift toward single-vendor recommendations.

### 3. Don't over-rely on multi-agent — add only when each agent's fit is real

The pilot project used six agents. We considered adding NotebookLM (skipped because corpus was minimal), Consensus (skipped because academic literature wasn't the right evidence base), and Elicit (same reason). The pattern: an extra agent costs 10–15 minutes for fan-out and another 5 minutes in Phase 3. Add only when the agent contributes evidence the existing set doesn't cover.

### 4. The orchestrator skill biases toward inclusion — override when needed

When Cowork suggests adding an agent, ask whether the agent's specific strength matches the project's evidence shape. For software dev, the evidence shape is vendor docs + regulatory text + practitioner sources. Tools that surface academic literature (Elicit, Consensus) don't fit that shape unless the research question intersects empirical claims.

### 5. Spot-check Phase 2 outputs before Phase 3

The four-point sanity check (no truncation, structure present, citation density, project-specific constraints honoured) catches problems cheaply. Skipping this check lets bad data into the contradiction matrix and the cleanup is expensive.

### 6. Don't write to non-existent repos in Phase 6

If the project plan includes a new repo (one the dossier proposes but which does not exist yet), defer the new-repo copy until implementation. Phase 6 only migrates the dossier to repos that already exist.

### 7. The conflict map's CONFLICT section is the dossier's most valuable output

The places where agents disagreed are exactly the places where the spec is silently resting on weak ground. Treat CONFLICT findings as the highest-priority `[CONTESTED]` markers in Phase 5, and as direct inputs to `/speckit.clarify` after spec generation.

### 8. NotebookLM at Phase 5 is the strongest source-grounding pass available

Skipping it costs 10 minutes saved at the cost of undetected Chairman hallucinations. For high-stakes dossiers (client work, anything published, anything that drives architecture decisions), the cost-benefit is overwhelmingly in favour of running it.

### 9. The decorrelated lane is the most evidence-backed quality gate (v1.1 addition)

The 2026 meta-research dossier identified that Western-lineage models make correlated errors. Five same-lineage agents agreeing is not five independent confirmations — it's roughly two effective votes' worth of signal. Adding DeepSeek (different training lineage, MoE architecture, different cultural context) as Tab 5 in Phase 2 is the single highest-leverage quality improvement in v1.1.

For confidential work, keep the lane via a Western-hosted API or self-host — the route is what changes, not whether the lane runs; skip it only when neither is available, and then document the reason. For non-confidential work, never skip it.

Evidence: arXiv 2506.07962 (correlated errors), arXiv 2605.29800 (panel diversity), arXiv 2603.00039 (CARE).

---

## Quick-reference: prompts to paste at each phase

For a new project, in sequence. Replace `<topic-slug>` and other placeholders.

### Phase 0 kickoff (in Cowork)

```
Run the research-orchestrator skill for a [greenfield/brownfield] spec-driven 
dev project.

Context:
- Project: <one-line project name>
- Workspace: <code-workspace>\
- Primary repo: <code-workspace>\<repo-name>
- Requirements file: <path or "to be created in Phase 1">
- Related files: <list any alignment reports, implementation guides, prior 
  research>
- Dossier folder: <code-workspace>\dossiers\<topic-slug>\

[List any deviations from standard pipeline — see the pilot project prompt as template]

Load-bearing constraint to factor into all research: <state the architectural 
constraint that should govern Phase 2 and Phase 5>

Begin Phase 0 setup: copy inputs to dossier folder, create 00-context.md, 
then proceed to Phase 1.
```

### Phase 3 (in Cowork)

```
Phase 2 fan-out is complete. The N agent outputs are saved at:
- <list all 02-*.md paths>

Resume the research-orchestrator skill at Phase 3.

[Add project-specific Phase 3 instructions if any]

Save output as 03-conflict-map.md. Do not proceed to Phase 4 until I confirm.
```

### Phase 4 (in Cowork)

```
Phase 3 complete and conflict map reviewed. Proceed to Phase 4 citation 
verification.

1. Extract URLs from 03-conflict-map.md.
2. Use Firecrawl MCP for programmatic verification.
3. Plausibility check on URL structures.
4. Surface top 5 load-bearing citations for my manual verification.

Save survivors to 04-verified-sources.md and rejects to 04-rejected.md.
```

### Phase 5 (in Claude.ai web — this project, fresh chat, max thinking)

```
Begin Phase 5 — Chairman synthesis for the project at 
<code-workspace>\dossiers\<topic-slug>\.

Apply the Chairman prompt from 01-prompts-library.md using the spec-driven 
dev output format from 02-overlay-spec-driven-dev.md.

[Project-specific output format adjustments]

[Paste all inputs inline below — 02-*.md, 03-conflict-map.md, 
04-verified-sources.md, 04-rejected.md]
```

### NotebookLM check (in NotebookLM)

```
Query 1: For each numbered claim in 05-dossier.md, identify which uploaded 
source supports it. Flag any claim that cannot be traced to an uploaded source.

Query 2: What's in the agent outputs (02-*) that did NOT make it into the 
dossier? Highlight any material claim that was dropped.
```

### Phase 6 (in Cowork)

```
Resume at Phase 6. Copy 05-dossier.md to <code-workspace>\<repo>\specs\<topic-slug>\
phase0\insights-digest.md. Commit on feature/<topic-slug> branch.

Then output the exact prompt I should paste into a fresh Claude Code session 
inside <repo> to begin /speckit.specify per the project's implementation 
guide.
```

### Claude Code handoff

Use the prompt Cowork generates in Phase 6. Then proceed per the project's implementation guide (or the standard pattern in `02-overlay-spec-driven-dev.md` if no project-specific guide exists).

---

## Maintenance

Update this runbook when:

- A new pattern emerges from a real project (capture under "Lessons captured")
- The toolchain changes materially (new MCPs, new agent options, Anthropic product changes)
- Phase timing drifts significantly from the 90–150 min target

Version-control with the rest of the AgenticCodingOps methodology. When the document is meaningfully revised, increment the version and date at the top.

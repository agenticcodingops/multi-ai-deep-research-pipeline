# How to Run a Research Project — Step-by-Step (Content Use Case)

> The operations guide. [SETUP.md](../SETUP.md) covers *installing* the machinery (do that once, first); this covers *running a project*, start to finish, with a worked example: **"What's the best keyboard and mouse for software engineers?"** Typical wall-clock: **90–120 minutes**, most of it unattended. Examples show Windows paths (`C:\research\`); on macOS/Linux read them as `~/research/` etc.

---

## First: who does what (the one-screen answer)

Three environments are involved. People mix these up, so pin this first:

| Environment | Role | When you touch it |
|---|---|---|
| **Cowork session** (Claude Desktop, with folder access) or **Claude Code** | **The conductor.** Runs the orchestrator skill, creates the dossier folder, writes every artifact, builds the contradiction matrix, verifies citations, routes outputs. **This is where you paste the kickoff prompt.** | Start here; return here after the fan-out |
| **Browser tabs** (Perplexity, Gemini, Grok, Claude.ai, DeepSeek — plus ChatGPT if assigned) | **The researchers.** Phase 2 only — you paste one prepared prompt per tab and let their Deep Research modes run in parallel | Phase 2 only (~25 min, mostly waiting) |
| **Claude project on claude.ai (web)** — e.g. "Multi-AI Research Consolidator" | **The quality lane.** Holds the methodology in its Knowledge for web sessions; Phase 5 (Chairman synthesis) always runs on the web app's strongest model with extended thinking, and Phase 1 can too | Phase 5 (and Phase 1 if you choose the high-quality option) |

> **You do NOT start in the web project.** Start in Cowork. The web project can't see your local files; Cowork can. The methodology travels with the installed plugin — the orchestrator carries its own bundled copy.

---

## Step 0 — One-time setup (skip if done)

Complete [SETUP.md](../SETUP.md): subscriptions, Claude Desktop and/or Claude Code, the plugin (§3 — both skills install with two commands), Firecrawl MCP, a workspace folder, and the decorrelated lane.

## Step 1 — Prepare your kickoff prompt (5 min, any text editor)

Fill the template (full version in the content runbook, `methodology/11-content-research-runbook.md`). Worked example:

```
Run the research-orchestrator skill for a content research project (NOT a software project).

Context:
- Use case: WordPress SEO article (market/product research; affiliate links possible)
- Topic: Best keyboard and mouse for software engineers in 2026 — mechanical vs low-profile,
  wired vs wireless, ergonomics, long-session comfort, availability in my region
- Audience: software engineers and desk professionals; assume technical fluency
- Decision context: publish a ~2,500-word SEO article recommending a top-5 with honest
  pros/cons per pick; affiliate links possible, so intensify citation verification
- Time horizon: this week
- Existing inputs: none

Skip Phase 0.5 requirements check (no requirements file — this is a topic).
Run Pre-Phase-1 keyword research.
Begin Phase 0 setup and proceed to Phase 1 (Pattern A — full decomposition).
Show me the Phase 1 decomposition + the staged Phase 2 prompts before I run the fan-out.
```

You don't specify folder paths: the orchestrator asks where dossiers should live the first time you use a workspace, remembers the answer in `research-config.md`, and creates `<dossier-root>/<topic-slug>/` itself (here: `dossiers/best-keyboard-mouse-2026/`). It will also ask whether the research involves confidential material — that decides how the DeepSeek lane is routed (see Step 5).

Tips that raise quality: state the *decision context* in one sentence; demand verdicts ("top-5 with pros/cons"), not surveys; declare affiliate intent so verification is intensified; always ask it to **pause for your spot-check** before the fan-out.

**Friction-saver — let Claude write this for you.** Two patterns: **(a)** in any Claude chat, say *"Draft my kickoff prompt from the content runbook's template — topic: X, use case: Y, audience: Z, deliverables: …"* and paste the result here; or **(b)** skip the prepared prompt entirely — open Cowork and say *"Run the research-orchestrator skill for a content project on \<topic\> — interview me for the kickoff details,"* and answer its questions. For big projects a detailed written brief is still worth authoring — but save it as a **file** in the workspace and have your kickoff prompt point Cowork at it (Cowork reads files), rather than pasting thousands of words into chat.

**If you accidentally started in the web project instead:** nothing is lost. Save whatever it produced (e.g. the decomposition) as a file, then open Cowork with a short kickstart that says "read the brief at \<path\> and the existing decomposition at \<path\>; validate and adopt it, don't re-derive" — and continue from there.

## Step 2 — Open Cowork and grant folder access (1 min)

Claude Desktop → new **Cowork** session → when asked for folder access, select your research workspace (e.g. `C:\research\`). Grant the **workspace root**: you can't add folders mid-session (still true as of July 2026 — restoring this is an open feature request), so a too-narrow grant means restarting the session. (Claude Code users: just open Claude Code in the workspace folder.)

## Step 3 — Paste the kickoff prompt (then watch Phases 0–1 happen)

The orchestrator will: resolve the dossier root (asking once if this workspace has no `research-config.md`) → create the dossier folder + `00-context.md` → run keyword/SERP research (for SEO articles) → produce `01-decomposition.md` (sub-questions, each mapped to a section and ending in a verdict) → stage **ready-to-paste prompts, one file per research agent** (`02a-prompts-*.md`) → **pause** for your review.

## Step 4 — Spot-check the plan (5 min — don't skip)

Read the decomposition. Check: Is the keyword right? Does every sub-question demand a **verdict** (recommend/reject/compare), not a description? Do the agent assignments make sense? Tell Cowork what to change, or say "approved."

## Step 5 — Phase 2: the fan-out (your only manual research step, ~25 min)

1. Open one browser tab per agent — the standard five: **Perplexity** (Deep Research ON) · **Gemini** (Deep Research) · **Grok** (DeepSearch) · **Claude.ai** (web search ON — a *plain* chat, separate tab) · **DeepSeek** (DeepThink mode — the decorrelated lane). For confidential work the orchestrator routes this lane through a Western-hosted API or a self-hosted endpoint instead of the China-hosted web UI, and drops it only if neither is available — the question is where your prompt data goes, not whose model it is. Open **ChatGPT** (Deep Research) too if Phase 1 assigned it as the optional sixth lane.
2. Paste each agent's prepared prompt from its `02a-prompts-*.md` file. **Start all tabs within ~a minute** so they run in parallel (3–15 min each).
3. As each finishes, copy its full output into the dossier folder as `02-perplexity.md`, `02-gemini.md`, `02-grok.md`, `02-claude.md`, `02-deepseek.md` (and `02-chatgpt.md` if it ran).
4. Quick eyeball per file — the same two **v1.1 quality gates** the orchestrator enforces before Phase 3:
   - **Live URLs:** citations must be real, resolvable links. A file whose citations are dead links, bare reference markers, or footnote numbers **fails** — re-export or re-run that tab.
   - **Confidence tags:** every finding must carry a **[HIGH] / [MEDIUM] / [LOW]** tag. A file with untagged findings **fails** — the orchestrator re-runs that lane with the tagging requirement restated.

## Step 6 — Back to Cowork: contradiction matrix (Phase 3)

Say: *"Phase 2 outputs are saved — proceed to Phase 3."* The orchestrator runs the two gates above (spot-opening three citations per file), then builds `03-conflict-map.md`: where agents agree, where they **conflict** (for product research, conflicts become your honest pros/cons), single-source claims, and suspicious citations. Read the CONFLICT section — it's the most valuable thing the pipeline produces.

## Step 7 — Citation verification (Phase 4)

Say: *"Proceed to Phase 4."* Cowork (with Firecrawl) resolves the cited URLs and checks the load-bearing claims; you manually open the **top 5** most important sources (for product research: confirm each recommended product's price, availability, and that reviews say what was claimed). Outputs: `04-verified-sources.md` + `04-rejected.md` (keep the rejects — that's your audit trail).

## Step 8 — Chairman synthesis (Phase 5) — always on the web app

Phase 5 runs in **Claude.ai web with the strongest available model and extended thinking at maximum** — the orchestrator treats this as non-negotiable, because synthesis is the load-bearing phase. Ask Cowork to *stage the Chairman prompt*, paste it into a **fresh chat** (in your Claude web project if you made one), then save the result back as `05-dossier.md` and tell Cowork "Phase 5 complete."

## Step 9 — Routing (Phase 6): turn the dossier into deliverables

Say what you want: *"Produce the WordPress publish pack from 05-dossier.md"* (or the LinkedIn carousel, YouTube script, etc.). One research pass feeds every format — never re-research per format. Publish, then archive the dossier folder.

---

## When the dossier supports a decision: the deliberation modes

If the project exists to settle a **decision** — go/no-go, build vs buy, which role, which tool — rather than to produce a write-up, add the v1.1 deliberation modes on top of the normal pipeline (tell the orchestrator it's decision research, or just phrase the kickoff as "Should I …?" and it routes there itself):

- **First Principles** at Phase 1 — when convention looks suspect, decomposition strips the question to axioms and rebuilds, instead of pattern-matching how everyone else does it.
- **Debate** as an extra pass between Phases 2 and 3 — agents are assigned FOR/AGAINST and argue the strongest case for their side. Hard constraint: **the decorrelated lane must be present and assigned to one side** — same-lineage models debating each other just amplify their shared bias.
- **Red Team** as an extra pass after Phase 4, once a draft recommendation exists — six attack vectors (technical, financial, market, regulatory, operational, edge cases), findings ranked by severity.
- **The Decision Brief** replaces the standard Phase 5 dossier format: one recommended direction with a confidence level, the unresolved disagreements classified by type, the risks only one agent spotted, a correction ledger, and exactly one next action.

Detail, ready-to-paste prompts, and the mode-selector table: `methodology/13-overlay-deliberation-modes.md`.

## Need both a slide deck and a screencast?

Don't run the presentation and video overlays as two projects. Use case 7 (**deck + screencast**, overlay `methodology/08-overlay-deck-and-screencast.md`) produces **one Markdown source that renders to both** from a single research pass — that's exactly the duplicated-effort failure the overlay exists to prevent.

---

## Checkpoints where the pipeline pauses for you
1. After Phase 1 (approve the plan) · 2. During Phase 2 (you run the tabs) · 3. After Phase 3 (read the conflicts) · 4. During Phase 4 (manually verify top 5) · 5. After Phase 5 (read the dossier before publishing).

## Quick troubleshooting
- **"Skill not found"** → confirm the marketplace was added and the plugin installed: in Claude Code `/plugin` lists both, and re-running the two install commands from [SETUP.md](../SETUP.md) §3 is safe to do on any surface. Then restart Claude Desktop / Claude Code.
- **The skill behaves strangely or seems stale** → check you don't have **two versions installed at once**: an old ZIP-uploaded or hand-copied skill plus the new plugin. Remove any pre-plugin copy (claude.ai settings → capabilities for uploaded skills; delete any hand-copied skill folders), keep only the plugin.
- **An agent's output has no clickable URLs** → re-export/re-run that tab; dead citations can't be verified and the file fails the Phase 3 gate.
- **An agent's findings have no [HIGH]/[MEDIUM]/[LOW] tags** → re-run that lane; the orchestrator restates the tagging requirement from the prompts library.
- **Two agents flatly disagree** → that's a feature; the conflict goes in the article as honest trade-off, or gets settled by a primary source in Phase 4.
- **Resuming next day** → new Cowork session, same folder grant, say: *"Resume research on `<topic-slug>` — read 00-context.md for state."* The dossier folder is the memory. (If `research-config.md` was deleted, the orchestrator simply asks where dossiers live again.)

---

*Why so much structure? Because models that agree can be wrong together (correlated errors), confident answers are often the wrong ones, and fabricated citations are common. The phases exist to catch exactly those three failures — the evidence is in `methodology/00-master-methodology.md`.*

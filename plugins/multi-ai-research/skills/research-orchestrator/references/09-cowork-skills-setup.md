# Cowork, Skills, and MCP Setup Guide

**Owner:** AgenticCodingOps  
**Reads with:** All other artifacts in this methodology (00–13) and the two skill files

---

## Why this document exists

The artifacts 00–13 describe the methodology. Uploaded to a Claude project's knowledge base they serve Claude.ai web sessions — but **Cowork cannot access Claude Projects knowledge**. This is a documented Anthropic constraint as of January 2026.

The right architecture is hybrid: artifacts in project knowledge for Claude.ai web sessions, and the installed **`multi-ai-research` plugin** for Cowork and Claude Code sessions — the plugin's orchestrator skill carries its own bundled copy of all 14 artifacts at `./references/`, so nothing on the file-system side depends on a separate download.

This document specifies how to set that up.

---

## The hybrid architecture in one diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AgenticCodingOps Research System                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────────┐
│   Claude.ai Web (this        │  │   Cowork (Desktop)               │
│   project)                   │  │   Claude Code                    │
│                              │  │                                  │
│   Reads:                     │  │   Reads:                         │
│   • 00-13 project knowledge  │  │   • installed plugin skills      │
│                              │  │   • Folders you authorize        │
│   Best for:                  │  │   • Bundled references (auto)    │
│   • Phase 1 decomposition    │  │                                  │
│   • Phase 3 contradiction    │  │   Best for:                      │
│   • Phase 5 Chairman         │  │   • Phase 0 file setup           │
│     (extended thinking)      │  │   • Brownfield repo reading      │
│                              │  │   • Phase 4 verification (MCP)   │
│                              │  │   • Phase 6 routing              │
└──────────┬───────────────────┘  └──────────────┬───────────────────┘
           │                                     │
           │       Handoff via dossier files     │
           └─────────────────┬───────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │ <dossier-root>/<topic-slug>/ │
              │  Numbered artifact files     │
              │  (the canonical record)      │
              └──────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  External browser tabs       │
              │  (Phase 2 only)              │
              │  • Perplexity                │
              │  • Gemini Deep Research      │
              │  • Grok DeepSearch           │
              │  • Claude.ai (web search)    │
              │  • DeepSeek (decorrelated)   │
              └──────────────────────────────┘
```

---

## One-time setup

### Step 1 — Install the plugin

Both skills — and the bundled methodology — ship in the `multi-ai-research` plugin. In Claude Code or Cowork:

```
/plugin marketplace add https://github.com/agenticcodingops/multi-ai-deep-research-pipeline
/plugin install multi-ai-research@agenticcodingops
```

No ZIP handling or file copying is involved, and one install serves both Cowork and Claude Code. Restart Claude Desktop / Claude Code after installing.

Verify: in a fresh Cowork or Claude Code session, ask: *"What skills do you have available?"* — `research-orchestrator` and `research-requirements-check` should be listed. If you previously installed pre-plugin copies (ZIP upload, or SKILL.md files copied into a skills folder), remove them — two installed versions produce stale, confusing behaviour.

### Step 2 — (Optional) keep a local reading copy of the methodology

The orchestrator does not need one: it reads its own bundled artifacts at `./references/`. Clone the public repo only if you want to read or search the methodology outside a Claude session — `<research-stack>` below refers to this optional reading copy:

```bash
git clone https://github.com/agenticcodingops/multi-ai-deep-research-pipeline
```

### Step 3 — Let the orchestrator place the dossiers

Don't pre-create a dossiers folder. On first run in a workspace the orchestrator asks *"Where should dossiers for this workspace live?"*, writes the answer to `research-config.md` at the workspace root, and from then on creates `<dossier-root>/<topic-slug>/` per project automatically.

### Step 4 — Grant Cowork the right folders

In Claude Desktop / Cowork settings, grant access to:
- Your research **workspace root** (the folder that contains — or will contain — the dossier root)
- Any specific repo folders you want to do brownfield research on (grant per-session)
- `<research-stack>/` only if you keep the optional reading copy and want Cowork to quote from it

Grant the workspace root up front — folders cannot be added mid-session.

### Step 5 — Install MCPs

Recommended MCPs in priority order (install via Claude Desktop → Settings → Connectors → Browse, or via `claude mcp add` for Claude Code):

#### High priority

**Firecrawl MCP** — Phase 4 URL verification.

Install via Claude Desktop → Settings → Connectors (browse for Firecrawl), or in Claude Code via `claude mcp add` — see Firecrawl's MCP documentation for the exact command and API-key setup.

What it does in this workflow: when verifying citations, Firecrawl fetches the actual URL contents so Claude can confirm whether the agent's claim matches what the source actually says. Cuts manual deep-check from 10 min to 2 min per dossier.

**GitHub MCP** — Phase 6 spec-driven-dev handoff.

What it does: lets Claude Code commit `05-dossier.md` into the project repo, create the `docs/research/` folder if missing, open PRs with research-basis citations in the description, link to GitHub Issues for spec.md tasks.

**Context7 MCP** — Fresh documentation during Phase 5.

What it does: Claude can fetch current vendor docs (Microsoft, AWS, Terraform Registry) during Phase 5 to cross-check claims from Phase 2 outputs. Catches stale documentation references.

#### Medium priority

**Filesystem MCP** — Only for Claude Code outside Cowork.

What it does: gives Claude Code direct file read/write outside of Cowork's VM. Skip if you do all file work in Cowork.

**Memory MCP** — Cross-session context.

What it does: persists state between Cowork sessions (which have no native memory). Useful if you split research across multiple Cowork sessions over days.

#### Skip these

**Playwright MCP**: Could drive Perplexity/Gemini/Grok browsers automatically, but anti-automation measures and ToS exposure make it fragile. The marginal time savings don't justify the risk.

**Perplexity MCP / API**: You already have Perplexity Pro web ($20/mo). The MCP is additive API spend on top. Only worth it if you scale past 5 dossiers/week.

---

## Operational modes — when to use which environment

### Mode A — Cowork-led (most projects)

Best for: spec-driven dev (especially brownfield), ebook chapter production, WordPress article production, anything where file operations are heavy.

Workflow:

1. Open Cowork, grant access to your workspace root (plus the repo workspace if brownfield).
2. Invoke the orchestrator skill: *"Run the research-orchestrator skill. New project: <topic>. Use case: <use case>. Inputs: <files or none>."*
3. Cowork runs the orchestrator skill which:
   - Confirms inputs and use case
   - Runs requirements-check skill if requirements file present
   - Creates `<dossier-root>/<topic-slug>/` with the canonical folder structure
   - Generates Phase 1 decomposition prompt (you copy to Claude.ai web for execution OR Cowork itself runs Phase 1 if Cowork's available model tier is sufficient — see "Where Phase 1 / 3 / 5 should run" below)
   - Saves output as `01-decomposition.md`
4. Phase 2: Cowork stages the customised prompts one file per agent (`02a-prompts-*.md`) for you to copy into browser tabs — five in the standard set. For confidential work the decorrelated lane stays in via a Western-hosted API or self-host (only the route changes); it drops to four lanes only when neither route is available. You run Phase 2 manually in the tabs. Cowork waits.
5. You return with the agent outputs. Cowork saves them as `02-perplexity.md`, `02-gemini.md`, `02-grok.md`, `02-claude.md`, `02-deepseek.md` (plus `02-chatgpt.md` / `02-notebooklm.md` when assigned).
6. Phase 3: Cowork (or you switch to Claude.ai web for max model quality) runs the contradiction matrix. Cowork saves as `03-conflict-map.md`.
7. Phase 4: Cowork uses Firecrawl MCP to batch-verify URLs, generates `04-verified-sources.md` and `04-rejected.md`. You manual-check the top 5 load-bearing.
8. Phase 5: Switch to Claude.ai web for Chairman synthesis with extended thinking enabled. Paste all inputs. Save output back into `<dossier-root>/<topic-slug>/05-dossier.md` (Cowork can do this if it's running concurrently).
9. Phase 6: Cowork executes use-case-specific routing — for spec-dev, copies `05-dossier.md` into repo's `docs/research/`, commits via GitHub MCP, opens PR.

### Mode B — Claude.ai web-led (lighter projects)

Best for: YouTube scripts, presentations, exploratory research where file management is minimal.

Workflow:

1. Open a new chat in your Claude.ai research project (the one with the methodology in its Knowledge).
2. State: *"New project. Use case: <X>. Topic: <Y>. Begin kickoff routine."*
3. The chat orchestrates all 6 phases. You manually save artifacts to `<dossier-root>/<topic-slug>/` (no Cowork in the loop).
4. Use Cowork or Claude Code only for Phase 6 routing if needed.

### Mode C — Claude Code-led (deep into a repo)

Best for: brownfield projects where the research is tightly coupled to existing code.

Workflow:

1. Open Claude Code in the repo.
2. The installed plugin's orchestrator skill auto-loads.
3. Same flow as Mode A but Claude Code reads/writes directly inside the repo.
4. Phase 5 still benefits from Claude.ai web (strongest available model with max effort), but Phase 1 / 3 can stay in Claude Code.

---

## Where Phase 1 / 3 / 5 should run — quality vs convenience trade-off

The cognitive phases (Phase 1, 3, 5) involve the strongest available Claude model with extended thinking for best results. Cowork and Claude Code typically run a lower default model tier than Claude.ai web exposes.

**Recommendation:**
- **Phase 1 (decomposition):** Either environment is fine. Cowork's default model produces acceptable decompositions.
- **Phase 3 (contradiction matrix):** Either is fine. The job is mechanical comparison; not deeply reasoning-bound.
- **Phase 5 (Chairman synthesis):** **Always Claude.ai web with the strongest available Claude model + extended thinking.** This is the load-bearing phase; the marginal model quality matters.

When the orchestrator skill reaches Phase 5, it explicitly hands off to Claude.ai web by:
1. Generating a single message you paste into a fresh Claude.ai chat in this project
2. The message contains all inputs + the Chairman prompt + the relevant overlay's output format block
3. You run Phase 5 there
4. You paste the output back into `<dossier-root>/<topic-slug>/05-dossier.md` via Cowork or manually

---

## Brownfield repo specifics

For projects on existing repos:

1. In Cowork, grant access to the repo workspace folder when starting the session.
2. The orchestrator skill detects brownfield by checking for `.git/`, `README.md`, code files, etc., in the workspace.
3. It adapts decomposition to ask the brownfield-specific sub-questions (existing-system compatibility, migration risks, what's in the repo's prior ADRs).
4. NotebookLM agent in Phase 2 is mandatory for brownfield: upload the repo's `docs/`, `terraform/` READMEs, prior ADRs, and the requirements file itself. NotebookLM gives source-grounded answers about *your actual codebase*, which the open web cannot.
5. In Phase 6, the dossier migrates to `<repo>/docs/research/<topic-slug>.md` rather than living in a separate folder.

---

## Updating the project description and instructions

The Claude.ai project's description and custom instructions should be updated to reflect this new operational reality. Draft the text from the key behavioral changes below and paste it into Project Settings.

The key behavioral changes:
- Claude in this project should run the kickoff routine when a new research chat opens
- Claude should reference specific artifact files by number when guiding through phases
- Claude should soft-refuse to skip Phase 4 verification for published deliverables
- Claude should treat the operator as a senior engineer (no fundamentals over-explanation)
- Claude should search Anthropic docs before answering questions about Cowork / Claude Code / Skills capabilities (those evolve faster than knowledge cutoff)

---

## Maintenance triggers

Update this stack when:

| Trigger | Action |
|---|---|
| New use case emerges (e.g., podcast, conference paper) | Add new overlay file (e.g., `14-overlay-podcast.md`); update `12-project-startup-checklist.md` Step 1 table |
| Anthropic product changes (Cowork, Skills, Claude Code) | Web-search Anthropic docs to verify; update this file |
| New MCP becomes valuable | Add to MCP recommendation table above |
| A specific prompt produces consistently better results | Update `01-prompts-library.md`; commit to local Git |
| You buy a new tool (Suprmind, Elicit Pro, etc.) | Update `00-master-methodology.md` agent inventory |
| Quality bar tightens based on output review | Update relevant overlay's "Quality bar specific to..." section |

---

## Limitations to acknowledge

1. **Cowork has no cross-session memory.** Each session starts fresh. The orchestrator skill mitigates this by reading dossier folder state to resume mid-pipeline.

2. **Cowork can use computer-use to drive browsers**, but this is research preview and unreliable for AI-service tabs (anti-automation). Phase 2 fan-out stays manual.

3. **Project knowledge in Claude.ai is invisible to Cowork.** This is the fundamental constraint. Skills + local artifact copies bridge it.

4. **Skills work in Cowork and Claude Code but not Claude.ai web.** This project's knowledge artifacts are the equivalent for Claude.ai web sessions.

5. **MCP installation is per-machine, per-application.** If you switch laptops, you re-install. Keep a one-line setup script if this happens often.

6. **Skill changes don't auto-propagate.** Skills are distributed via the plugin: update or reinstall the plugin to pick up new versions, then restart Claude Desktop / Claude Code. Don't hand-edit installed copies — the next plugin update overwrites them.

7. **The hybrid model has more moving parts than either pure-Cowork or pure-Claude.ai-web.** The trade-off is necessary because no single environment covers all phases at the quality bar set in `00-master-methodology.md`.

# Setup & Prerequisites — Run This Multi-AI Research Pipeline Yourself

> The getting-started guide: from a clean machine to your first finished dossier. Install once here, then run projects with [docs/how-to-run-a-project.md](docs/how-to-run-a-project.md). Examples show Windows paths (`C:\research\`) and macOS/Linux paths (`~/research/`) side by side where they differ; everything else is identical across platforms.

---

## Does this actually work?

Fair question — this guide asks for real money across several subscriptions before you see any value. Two instances from the pipeline's own shakedown project (a 2026 survey of multi-AI research tooling, run through all six phases):

- **Phase 4 caught a fabricated citation.** One research agent supported a claim about evaluation with an arXiv ID that looked entirely plausible — and resolved to an unrelated urban-planning paper. The agent had hallucinated a real-looking ID. Citation verification caught it before publication; it went into the rejected-sources log, which is kept as an audit trail.
- **The contradiction matrix caught an unreplicated number the pack repeated.** A widely cited "90.2% improvement" figure for a multi-agent architecture was echoed uncritically by most lanes; one lane surfaced counter-evidence that single agents match multi-agent systems under equal token budgets. The claim shipped as CONTESTED with both sides shown — instead of as fact.

That second one is the core mechanic: models that agree can be wrong together. The pipeline's job is to make the disagreement visible and make every load-bearing citation prove itself.

---

## TL;DR — two tiers

- **Minimum viable (free–cheap, ~30 min):** Claude (with the plugin installed — §3) + any two other research lanes. You can run the core pipeline today; the contradiction matrix just has less to cross-examine.
- **Full setup (~1–2 hrs):** all five standard lanes + the decorrelated lane route + the Firecrawl MCP for automated citation checks.

Start minimal; add pieces as the value proves itself. You do **not** need everything below to begin.

---

## 1. Accounts & subscriptions

The pipeline fans one question out to several "deep research" tools, then synthesises. You need at least **three lanes** for the contradiction matrix to be meaningful; the standard set is five, with ChatGPT as an optional sixth.

> **Prices checked July 2026.** Every figure below will drift — verify against each vendor's current pricing before subscribing. Stale pricing is the fastest way for a setup guide to lose your trust, so treat this table as shape, not gospel.

| Lane / service | Role in the pipeline | Tier needed | ~Cost (2026-07; verify) |
|---|---|---|---|
| **Claude** (Anthropic) | Chairman synthesis + a fan-out lane; runs Cowork / Claude Code | Pro, or a higher tier for heavy use | $20+/mo |
| **Perplexity** | Fan-out lane — citation-dense, SERP-style | Pro | $20/mo |
| **Gemini** (Google) | Fan-out lane — breadth, long context; also NotebookLM | Pro | $20/mo |
| **Grok** (xAI) | Fan-out lane — recency, X/community signal | paid tier with DeepSearch | ~$30/mo |
| **DeepSeek** — the decorrelated lane | **The key upgrade** — a non-Western-lineage model whose errors don't correlate with the others' | free web UI; or Western-hosted API / self-hosted | $0–20/mo |
| *Optional 6th:* **ChatGPT** (OpenAI) | Extra fan-out lane — enterprise/regulated-industry contrast; paid tier fixes free-tier truncation | paid tier | $20+/mo |
| *Optional:* NotebookLM | Source-grounded sanity check over your own documents (free with Gemini) | included | $0 |

**Minimum to start:** Claude + any 2 of the others. **Standard:** the five lanes. **Full:** five + ChatGPT.

> ⚠️ **Jurisdiction rule:** DeepSeek, Kimi, and Qwen are China-hosted. What matters is where your prompt data goes, not whose model it is — so for anything sensitive, keep the decorrelated lane but route it through self-hosted or Western-hosted inference instead of the consumer web UI (see §7). Italy's data regulator restricted DeepSeek's consumer service in 2025; check your own jurisdiction's stance.

---

## 2. Apps to install

1. **Claude Desktop** (Windows or macOS) — gives you **Cowork**, the file-aware assistant that runs the orchestrator. *(Download from Anthropic; sign in with your Claude account.)* **Or Claude Code** (CLI, all platforms) if you prefer a terminal — the plugin works in both.
2. **A browser** — Phase 2 (the fan-out) runs in browser tabs of each AI service. This stays manual by design: driving these tabs with automation is fragile and against some terms of service.
3. *Optional, for a private decorrelated lane:* **Docker** + a small VPS to self-host DeepSeek weights, or an OpenRouter account for pay-as-you-go API access.

---

## 3. Install the plugin (the skills)

The two skills — **research-orchestrator** (walks you through all six phases) and **research-requirements-check** (audits a requirements file before research) — ship as one plugin, with the entire methodology bundled inside it. Install from the marketplace by typing these two commands into the chat input of a Claude Code or Cowork session:

```
/plugin marketplace add https://github.com/agenticcodingops/multi-ai-deep-research-pipeline
/plugin install multi-ai-research@agenticcodingops
```

This works in **both Claude Code (Terminal, not VS Code Extension) and Cowork**. No ZIP handling, no file copying, no skills folder to create. Restart the app after installing, then verify in a fresh chat: *"What skills do you have available?"* — both skills should appear.

---

## 4. Optional: clone this repo (for reading, not running)

The methodology documents ship **inside the plugin** — the orchestrator reads its own bundled copies, and nothing you run depends on a local clone. Clone the repo only if you want to *read* the methodology (`docs/methodology/00-master-methodology.md` is the spine; `13-overlay-deliberation-modes.md` is the decision-research overlay):

```bash
git clone https://github.com/agenticcodingops/multi-ai-deep-research-pipeline
```

---

## 5. Install MCP connectors

In **Claude Desktop → Settings → Connectors** (or `claude mcp add` for Claude Code — see each connector's own docs for the exact command):

| MCP | Priority | Why |
|---|---|---|
| **Firecrawl** | **High** | Phase 4 — fetches cited URLs so Claude can confirm the source actually says what was claimed. Cuts manual citation checking dramatically. |
| **GitHub** | Optional | Phase 6 — commit dossiers into a repo (spec-driven dev). |
| **Context7** | Optional | Phase 5 — pull fresh vendor docs to cross-check claims. |

> Security note: if you ever add an open-source research agent as an extra lane, containerise it and never expose it publicly — some carry remote-code-execution CVEs. Pin any inference gateway you self-host to a known-clean release.

---

## 6. Workspace and dossier folders

1. Pick (or create) a **workspace folder** for research — e.g. `C:\research\` on Windows, `~/research/` on macOS/Linux. One folder per ongoing project lives under it.
2. In Claude Desktop, **grant Cowork access to that folder** when you start a session (Claude Code: just open it there).
3. **Don't pre-create a dossiers folder.** On first run the orchestrator asks *"Where should dossiers for this workspace live?"* — accept the suggestion (e.g. `dossiers/`, relative to the workspace) or give your own path. It remembers the answer in a `research-config.md` file at the workspace root and never asks again.
4. *Optional (for Claude.ai web sessions):* create a **Claude Project** and upload the methodology files to its Knowledge — useful for the reasoning-heavy phases (1, 3, 5) on the web app. A Claude web project can't see your local files, and Cowork can't see project knowledge; the dossier folder is the bridge between them.

---

## 7. Set up the decorrelated lane (the one step people skip)

This is the highest-leverage piece: one lane from a *different training lineage*, so its errors decorrelate from the Western frontier stack.

- **Easiest:** the DeepSeek web UI in DeepThink (reasoning) mode — free, and fine for non-confidential research.
- **Private:** access DeepSeek through a Western-hosted API provider (e.g. via OpenRouter), or self-host the open weights on a VPS with Docker.
- **Confidential work:** keep the lane, change the route. The governing rule is where the prompt data goes, not whose model it is — so use a **Western-hosted API** (data stays in-region, subject to the provider's terms; confirm the hosting region) or **self-hosted inference** (no third-party exposure) rather than the China-hosted web UI. The orchestrator asks about confidentiality during setup and skips the lane **only** when neither route is available, logging the accepted correlated-error risk.

---

## 8. Your first dossier (the 10-minute test run)

1. Open Cowork (or Claude Code) in your workspace folder.
2. Say: *"Run the research-orchestrator skill. New research project. Topic: `<your question>`."*
3. It asks where dossiers should live (first run only), which use case you're running, and a handful of context questions — then builds the decomposition and stages ready-to-paste prompts, one file per lane.
4. Open your AI tabs, paste each prompt (enable each tool's Deep Research / DeepSearch mode), run them in parallel, save each output back into the dossier folder as `02-<agent>.md`.
5. Say *"Phase 2 outputs are saved"* — it checks the outputs against two quality gates, builds the contradiction matrix, verifies citations (Firecrawl), and walks you to the final dossier.
6. Route the dossier wherever you need it (blog, video, slides, decision brief).

The full walkthrough with a worked example is [docs/how-to-run-a-project.md](docs/how-to-run-a-project.md).

---

## 9. Cost summary (as of July 2026 — verify)

- **Truly minimal:** $0–20/mo (free tiers + one paid lane + the free DeepSeek web UI).
- **Standard:** ~$80–110/mo (Claude Pro + Perplexity Pro + Gemini Pro + Grok's paid tier), plus a few dollars if you route DeepSeek through an API.
- **Skip** turnkey multi-model "consolidation" subscriptions — they duplicate what you already pay for and can't trigger each tool's own deep-research mode.

---

## 10. Common gotchas

- **Don't skip the contradiction matrix or citation verification** — that's where confident-but-wrong answers get caught.
- **Cowork has no cross-session memory** — the dossier folder *is* the memory; the orchestrator resumes from it (`"Resume research on <topic-slug>"`).
- **Plugins and MCPs are per-machine** — re-run the §3 install commands when you switch computers.
- **Run at least 3 lanes, and add the decorrelated one** — fewer than that and the matrix has nothing to cross-examine.
- **If you previously installed the skills from a ZIP or by copying files**, remove that copy — two installed versions produce confusing, stale behaviour (see the run guide's troubleshooting section).

---

*This guide is the on-ramp. The why-it-works — the evidence behind decorrelation, the contradiction matrix, and the quality gates — is in `docs/methodology/00-master-methodology.md`; the full prompts are in `docs/methodology/01-prompts-library.md` (both also ship inside the plugin).*

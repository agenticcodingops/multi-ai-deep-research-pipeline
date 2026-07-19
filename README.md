# Multi-AI Deep Research Pipeline

A six-phase methodology — packaged as a Claude plugin — for research you can defend: **decompose** a question into sub-questions that demand verdicts, **fan out** to five independent deep-research AI lanes in parallel, build a **contradiction matrix** from their answers, **verify** every load-bearing citation, have a Chairman model **synthesise** a dossier under strict rules, then **route** that one dossier into whatever deliverables you need.

The design premise: models that agree can be wrong together. So the pipeline includes a decorrelated lane from a different training lineage, preserves disagreement instead of averaging it away, and makes every important citation prove itself — the fabricated ones go in a rejected-sources log you keep.

## Install

In Claude Code or Claude Cowork (Claude Desktop):

```
/plugin marketplace add https://github.com/agenticcodingops/multi-ai-deep-research-pipeline
/plugin install multi-ai-research@agenticcodingops
```

That installs both skills — `research-orchestrator` (walks you through all six phases) and `research-requirements-check` (audits a requirements file before you research) — with the full methodology bundled inside. No file copying.

## What it costs to run

Roughly **$80–110/month** for the standard five-lane setup (Claude, Perplexity, Gemini, Grok, plus a free or cheap DeepSeek route), or nearly free at minimum viable with three lanes. Dated price table and tiers: [SETUP.md](SETUP.md).

## Where to start

1. **[SETUP.md](SETUP.md)** — accounts, apps, the plugin, folders. Once.
2. **[docs/how-to-run-a-project.md](docs/how-to-run-a-project.md)** — running a project end to end, with a worked example ("best keyboard and mouse for software engineers") and the checkpoints where the pipeline pauses for you.
3. **[docs/methodology/](docs/methodology/)** — the methodology itself: `00-master-methodology.md` is the spine; overlays `02`–`08` adapt it per deliverable; `13-overlay-deliberation-modes.md` adds Red Team / Debate / First Principles passes and the Decision Brief for decision-shaped research.

A typical content project takes 90–120 minutes wall-clock, most of it unattended while the research tabs run.

## Licence

Free for any non-commercial use; commercial rights reserved. See [LICENSE](LICENSE) (PolyForm Noncommercial 1.0.0).

Copyright (c) 2026 Syed Hassan Abbas.

# Master Methodology — Multi-AI Research Pipeline

**Owner:** AgenticCodingOps  
**Status:** Living document — update when the toolchain changes  
**Version:** 1.2 (2026-07-21 — adds ground-truth verification, deliberation-mode phase slots (2.5/4.5), lane roles + agent-access inventory, capability-gated Chairman; see the plugin CHANGELOG. v1.1 (2026-06-01) added the decorrelated lane, eval gate, automation defaults, correlated-error floor)  
**Reads with:** `01-prompts-library.md` (mandatory), one or more overlay files (`02-` through `08-`, or `13-` for decision research) per project

---

## When to use this document

This is the methodological spine for any multi-AI research project. It should be loaded as background context for **every** research chat in this Claude project. Use-case overlays specify deltas to this spine; the spine is universal.

If this is the first time using the stack in a fresh chat, also read `12-project-startup-checklist.md` first — it walks through the kickoff questions.

---

## The artifact convention

Every research project produces a folder of numbered markdown artifacts on disk:

```
<dossier-root>/<topic-slug>/
├── 00-context.md           # Original question, decision context, attached source materials
├── 01-decomposition.md     # Phase 1 output: sub-questions + agent assignments (JSON)
├── 02-<agent>.md           # Phase 2: one per agent (perplexity, gemini, grok, claude, chatgpt, + decorrelated lane)
├── 03-conflict-map.md      # Phase 3: contradiction matrix + agreements + gaps
├── 04-verified-sources.md  # Phase 4: surviving citations
├── 04-rejected.md          # Phase 4: fabricated/unsupported citations (audit trail)
└── 05-dossier.md           # Phase 5: final consolidated publication-ready output
```

Treat dossier folders like Terraform modules: version-control them, commit them, reuse them. The folder is a deliverable, not scratch space.

For software projects, after Phase 5 the `05-dossier.md` file migrates into the project repo at `docs/research/<topic-slug>.md` to feed Spec Kit / Kiro. The original dossier folder stays in `<dossier-root>/` as the immutable research record.

---

## The 6-phase pipeline

| Phase | Tool | What you do | Wall-clock | Output artifact |
|---|---|---|---|---|
| **1. Decomposition** | Claude, strongest available model (this project) | Run decomposition prompt with research question | 5 min | `01-decomposition.md` |
| **2. Parallel fan-out** | Perplexity + Gemini + Grok + Claude **+ ≥1 decorrelated lane** — the five standard lanes (separate tabs) ± ChatGPT (optional sixth) ± NotebookLM | Submit assigned sub-questions simultaneously to all agents | 25 min wall (5–15 min per agent, parallel) | `02-<agent>.md` × 5–7 |
| **3. Cross-examination** | Claude, strongest available model (fresh chat in this project) | Paste all agent outputs, run contradiction matrix prompt | 10 min | `03-conflict-map.md` |
| **4. Citation verification** | Firecrawl + manual + Claude URL-plausibility check | Verify URLs; deep-check 5 load-bearing claims | 15 min | `04-verified-sources.md` + `04-rejected.md` |
| **4.5 Eval gate** *(NEW; optional)* | Cowork/Claude Code | Optional calibration: run a small golden-set regression check before synthesis (see Decision rules) | 5 min | inline note in `00-context.md` |
| **5. Consolidation** | Claude, strongest available model (fresh chat, max effort) | Run Chairman prompt with use-case-specific output format from overlay | 15 min | `05-dossier.md` |
| **6. Output routing** | Use-case specific (Spec Kit, video record, WordPress, etc.) | Move dossier into target system | 10–30 min | Final deliverable |

**Between-phase slots (v1.2):** **Phase 2.5** holds the Debate mode and **Phase 4.5** holds the Red Team mode when `13-overlay-deliberation-modes.md` selects them — a selected mode is mandatory and blocking, not advisory (see overlay 13, Modes 1–2). Phase 4.5 is also the slot for the optional eval gate (row above); the two share the slot and are independent of each other.

**Total wall-clock for a typical dossier: 90–120 min.** Most of Phase 2 is unattended.

---

## Agent inventory

Use this table to assign sub-questions in Phase 1 and to weight agents in Phase 2. Use-case overlays may override these defaults.

| Tool | Best at | Use when sub-question requires | Cost |
|---|---|---|---|
| **Perplexity Pro Deep Research** | Inline-cited web research, fast turnaround, vendor docs and pricing data | Citations needed, current state of a topic, comparison tables | $20/mo |
| **Gemini Deep Research** | Source volume (100+ pages), Google ecosystem, multimodal, native charts | Maximum breadth, scientific literature, Drive/Docs integration | Included in Gemini Pro |
| **Grok DeepSearch (SuperGrok)** | Real-time web + X/Twitter, breaking news, recent vendor announcements | Latest releases (last 30 days), social signal, GitHub/community sentiment | $30/mo |
| **Claude (strongest available model) + web search** | Self-verification, careful long-context reasoning over uploaded files, synthesis | Cross-cutting / synthesis sub-questions; uploaded reference docs | Bundled in paid Claude plans |
| **ChatGPT Deep Research** | Enterprise/regulated case studies, long written reports | **Optional sixth lane** — enterprise contrast, regulated-industry patterns | ChatGPT Pro — Pro Deep Research (avoids the free-tier truncation + dead-citation issue) |
| **🆕 Decorrelated lane (DeepSeek self-hosted; Kimi/Qwen optional)** | **Error decorrelation** via non-Western training lineage + cheap reasoning | **EVERY fan-out** — to break model monoculture (see Quality bar) | Self-host VPS / API cents |
| **NotebookLM** (optional) | Source-grounded RAG over your own corpus — cannot hallucinate beyond uploaded sources | You have a private corpus the public web doesn't index well | Free with Gemini Pro |
| **Elicit / Consensus** (optional) | Structured extraction / consensus over academic papers | Health, biohacking, peer-reviewed claims only | Free tiers |

**Phase 5 Chairman is always the strongest available Claude model.** Reasons: very large context window, instruction-following literalness, self-verification step, zero marginal cost on a flat-rate Claude plan.

**🆕 Decorrelated-lane rule (load-bearing — v1.1):** every fan-out must include **at least one model from a different training lineage** than the Western frontier stack (default: DeepSeek, self-hosted). Its outputs need not be "more correct" — they exist to surface errors the Western bloc shares. **Jurisdiction guardrail:** China-hosted models (DeepSeek/Kimi/Qwen) are **self-host or Western-host only**; never route client/confidential data through their consumer APIs (Italy's Garante banned DeepSeek's consumer service on GDPR grounds, 30 Jan 2025).

---

## Quality bar — claim classifications + the monoculture floor

Every claim that appears in `05-dossier.md` must be classified as one of:

- **VERIFIED** — supported by ≥2 *independent* agents, OR by 1 agent with a verified primary-source URL
- **SINGLE-SOURCE** — appears in exactly 1 agent output and is not corroborated; **flag, do not discard**
- **DISPUTED** — agents disagree; present both positions; do **not** pick a winner unless one side has an authoritative primary source and the other does not

**🆕 The correlated-error caveat (v1.1):** "supported by 2+ agents" is weaker than it looks when the agents share a training lineage. Frontier models make *correlated* errors — agreement among same-lineage models can be false consensus, not corroboration. Therefore:
- Count corroboration as strongest when it spans **genuinely different lineages** (e.g., a Western model + the decorrelated lane).
- When all corroborating agents are Western-lineage, tag as **VERIFIED (correlated-risk)** and prefer a primary-source check in Phase 4.
- *Evidence:* "Correlated Errors in LLMs" (arXiv 2506.07962, ICML 2025); "Nine Judges, Two Effective Votes" (arXiv 2605.29800); CARE (arXiv 2603.00039).

The Chairman prompt enforces these classifications automatically. Never silently smooth over disagreements — disagreement is the most valuable signal multi-agent research produces.

---

## Decision rules

**When to skip phases:**
- Skip Phase 4 (citation verification) only if no factual claims will be published, billed for, or carry legal/medical/financial weight. For published/billed/health/client content: **never skip**.
- Skip Phase 3 contradiction matrix only if running ≤2 agents. For ≥3 agents: always run. **Do not replace the matrix with a consensus-seeking peer-review panel** — it votes away the divergence that is the deliverable (see `01-prompts-library.md`, Phase 3 note).

**🆕 Phase 4.5 — eval gate (v1.1; optional calibration, not a mandatory phase):** before Phase 5, run a small golden-set regression: keep 5–10 questions with known-good answers from prior dossiers; confirm the current run's agents/prompts still get them right. Catches silent prompt/model drift. This was the most common under-engineering gap identified in the 2026 state-of-practice review.

**🆕 Confidence/abstention (v1.1):** Phase-2 agents must tag each finding HIGH/MEDIUM/LOW confidence and are explicitly permitted to answer "insufficient evidence." The Chairman carries these through. Forces uncertainty to the surface instead of confident confabulation.

**When to add agents:**
- The decorrelated lane is **not optional** (see inventory). Add NotebookLM when you have a curated private corpus. Add Elicit/Consensus only for health/peer-reviewed topics.

**🆕 When to escalate to DIY orchestration (v1.1 — automation defaults):**
- **AUTOMATE-NOW:** a provider-agnostic gateway (LiteLLM + OpenRouter). OpenRouter is pass-through priced (no per-token markup; 5.5% fee on credit purchases). **Pin LiteLLM to the official Docker image / a clean release (v1.83.0+)** — malicious `litellm 1.82.7/1.82.8` shipped on PyPI on 24 Mar 2026.
- **AUTOMATE-NOW (mechanical only):** Phase-4 citation liveness/refetch (Firecrawl) + metadata cross-checks.
- **KEEP-MANUAL:** Phase 3 contradiction matrix and Phase 5 chairman — the analytic core.
- **AUTOMATE-LATER:** n8n as scheduling/glue, past ~5 dossiers/week. Karpathy `llm-council` is a *sandbox* for base-model council runs only — it is UI-bound with no headless API and does not pay off as pipeline infrastructure.
- **Provider-agnostic rule:** any automation must work across ≥3 major providers.

---

## The Chairman role (Phase 5)

Claude in Phase 5 is acting as **Chairman of a research council** — synthesis from inputs, not ideation.

**Chairman discipline rules:**
1. Use only claims present in the inputs. Do not introduce claims from training knowledge.
2. Tag every claim: `[VERIFIED — 2+ sources]`, `[VERIFIED (correlated-risk)]`, `[SINGLE-SOURCE — flag]`, or `[DISPUTED — A says X, B says Y]`.
3. Paraphrase always. Quote ≤15 words from any single source. Never string two short quotes from the same source.
4. Every numerical claim names its source inline.
5. Run Chain-of-Verification before final output: 5 verification questions on the most load-bearing claims, answered from scratch, then revise.
6. Mark single-source non-verified claims explicitly.
7. Do not smooth over disagreements. Present both positions with their sources.

The full Chairman prompt template is in `01-prompts-library.md`.

---

## Cross-references

| When you need… | Read… |
|---|---|
| The exact prompts for each phase | `01-prompts-library.md` |
| Overlay: software development | `02-overlay-spec-driven-dev.md` |
| Overlay: YouTube script | `03-overlay-youtube-script.md` |
| Overlay: PowerPoint / talk | `04-overlay-presentation.md` |
| Overlay: ebook | `05-overlay-ebook.md` |
| Overlay: WordPress + Elementor SEO | `06-overlay-wordpress-seo.md` |
| Overlay: health content | `07-overlay-health-content.md` |
| 🆕 Overlay: deck + screencast single-source-of-truth | `08-overlay-deck-and-screencast.md` |
| Overlay: deliberation modes / decision research (use case 8) | `13-overlay-deliberation-modes.md` |
| Starting a new chat in this project | `12-project-startup-checklist.md` |

---

## Hallucination + correlation floor — keep this calibrated

In 2026, frontier models still hallucinate at material rates on document-grounded tasks (Vectara-style RAG leaderboards). Implication: reasoning-mode outputs carry higher hallucination risk than non-reasoning-mode in document-grounded RAG; for verification (Phase 4) and high-stakes single-source claims, prefer grounded checks (NotebookLM) or non-reasoning variants.

**🆕 The bigger 2026 finding is correlation, not just rate (v1.1):** across 350+ models, more accurate models have *more highly correlated* errors even across different providers (arXiv 2506.07962). Judge/aggregation panels inherit this — a 9-model panel carries only ~2 independent votes' worth of information, and a single strong judge can match the panel (arXiv 2605.29800). Practical consequence: **diversity must be engineered via training-lineage diversity (the decorrelated lane), not assumed from running several same-lineage products.** Citation verification and the decorrelated lane are not optional for any output that will be published, billed for, or carries weight.

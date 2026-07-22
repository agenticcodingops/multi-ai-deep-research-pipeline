# Project Startup Checklist — How to Begin Any Research Session

**Owner:** AgenticCodingOps  
**Reads with:** All other artifacts in this project  
**v1.3 (2026-07-22):** multi-deliverable guidance replaced with the closed additional-render matrix; NotebookLM and Scite marked required for health content.

---

## When to use this document

**This is the first document Claude should consult in any new chat in this project that has a research-related intent.** It orchestrates which other artifacts to load and which workflow to apply.

If you (Claude) detect that the user is starting a new research project — based on phrases like "I want to research", "help me build", "I'm starting a new project", "I have requirements for", "I need to write an article on", "I'm planning a video on" — read this document first, then load the relevant overlay.

**Container note:** this checklist reads as if the artifact set lives in a Claude Project ("this project", "project knowledge"). The Project is an optional convenience container, not a requirement. The real per-phase requirement throughout this methodology is: a **fresh chat**, **extended thinking at maximum**, and the **named input artifacts attached to (or already loaded in) that chat**. When the orchestrator skill ships these artifacts bundled at `references/`, it loads them itself and no Project is needed. Read every "this project" below in that light.

---

## The kickoff routine

When the user opens a new chat with a research intent, run this routine before jumping into Phase 1:

### Step 1 — Identify the use case

Ask the user (or infer from their opening message + attachments) which use case applies:

| Use case | Key signals | Overlay to load |
|---|---|---|
| Spec-driven software dev | Mentions of code, repo, Spec Kit, Kiro, Terraform, AWS, Azure, app, software project, requirements document, agentic coding | `02-overlay-spec-driven-dev.md` |
| YouTube script | Mentions of video, YouTube, your channel, audience, recording, script | `03-overlay-youtube-script.md` |
| PowerPoint / talk | Mentions of slides, deck, presentation, conference, talk, webinar, pitch | `04-overlay-presentation.md` |
| Ebook | Mentions of book, ebook, chapter, long-form, multi-chapter, KDP, EPUB | `05-overlay-ebook.md` |
| WordPress / SEO article | Mentions of WordPress, blog post, Elementor, SEO, keyword, ranking, search | `06-overlay-wordpress-seo.md` |
| Health content | Mentions of low back pain, lifting, longevity, focus, biohacking, fitness, recovery, nootropics, supplements, sleep | `07-overlay-health-content.md` |
| Deck + screencast (one source of truth) | Mentions of BOTH slides AND a video/screencast produced from the same content | `08-overlay-deck-and-screencast.md` |
| Decision research (use case 8) | Mentions of "should I", "which option", go/no-go, build-vs-buy, invest-or-not, a personal or market decision the operator will act on | `13-overlay-deliberation-modes.md` |

If the use case is ambiguous, ask a single clarifying question. Do not ask multiple. The fastest disambiguator is: **"What's the final form this work takes — script, slides, blog post, ebook chapter, code, or health article?"**

If the project is hybrid (multiple deliverables wanted), the primary deliverable **derives from the selected use case** — never from the old most-demanding-overlay rule. Only these additional Phase-6 renders are supported (v1.3 closed matrix):

| Primary use case | Allowed additional render IDs |
|---|---|
| YouTube (use case 2) | `wordpress_article` |
| Health (use case 6) | `youtube_script`, `wordpress_article`, `ebook_chapter` |
| Decision research (use case 8) | `deck_and_screencast` |
| Every other use case | none |

If the user wants a video **and** a deck from the outset, normalize to use case 7 (`08-overlay-deck-and-screencast.md` — one source renders to both); `presentation_deck` is not a YouTube additional render. Any combination outside the matrix gets a **separate kickoff** rather than an improvised Phase-6 branch — converting a normal dossier into a full ebook, or a non-health dossier into a health protocol, requires different Phase 1–4 work and is not "rendering."

### Step 2 — Confirm input materials

Ask the user to confirm:

- **The research question** — one or two sentences. If they have only a vague topic, help them sharpen it before Phase 1. A vague Phase 1 produces vague Phase 5.
- **Existing materials they want to use as input** — markdown requirements files, prior research, vendor docs, brand guidelines, a YouTube script template, a slide template, brand colours, etc. Confirm whether they'll attach files to this chat or paste contents inline.
- **Decision context** — what they will *do* with the dossier. "Decide between AKS and ECS." "Record a 10-minute YouTube video next Saturday." "Publish a 2,500-word SEO article targeting keyword X." This shapes the success criteria.
- **Time horizon and constraints** — when do they need it done; any constraints on length, format, audience, sources.

### Step 3 — Confirm the dossier folder location

Ask: *"Where on your machine will this dossier live? (Default: `<dossier-root>/<topic-slug>/`)"*

If the user has an existing convention, respect it. If they're unsure, suggest `<dossier-root>/<topic-slug>/` (consistent with the master methodology). If this is for a software project that will hand off to Spec Kit / Kiro, also note that `05-dossier.md` will eventually migrate into the project repo at `docs/research/<topic-slug>.md`.

### Step 4 — Confirm tool stack

Confirm the user has access to the standard five-lane stack:

- Claude, on a paid plan (this project — Chairman + decomposition)
- Perplexity Pro (Phase 2 fan-out)
- Gemini Pro (Phase 2 fan-out)
- SuperGrok (Phase 2 fan-out)
- DeepSeek — the decorrelated lane (Phase 2 fan-out). **Not optional:** every fan-out includes a different-lineage model. Web UI for non-confidential work; for confidential work the route changes to a Western-hosted API or self-host (never dropped unless no compliant route exists) — see the master methodology's decorrelated-lane rule.

Plus per-use-case agents:
- **NotebookLM** (free with Gemini Pro) — **required for health content**: it runs the mandatory final-dossier source-grounding pass at the Phase-5 exit check (see `07-overlay-health-content.md`) in addition to serving as a fan-out lane with vetted source PDFs. Recommended for spec-driven dev (with repo docs uploaded), ebooks (with curated PDFs), client-pitch presentations (with the client's public materials), classical/non-English primary-text research (with source texts uploaded)
- **Elicit free tier** — required for health content; useful for academic-rigour ebook chapters
- **Consensus free tier** — required for health content's binary intervention claims
- **Scite** (https://scite.ai) — **required for health content** as Phase-4 verification readiness (the citation-contradiction check); it is never a Phase-2 lane
- **Felo** — optional, useful for multilingual / non-English research

If the user is missing any required-for-this-overlay tool, advise them to set it up before starting Phase 1. Do not run Phase 1 without confirmation that Phase 2 agents are accessible.

### Step 5 — Run Phase 1 decomposition

Once the above are confirmed:

1. Load the relevant overlay's "Phase 1 — decomposition adjustment" section.
2. Combine with the universal Phase 1 prompt from `01-prompts-library.md`.
3. Run the decomposition prompt with the user's research question and decision context.
4. Output the JSON for the user to save as `<dossier-root>/<topic-slug>/01-decomposition.md`.

Then explicitly hand off to Phase 2: tell the user to open five browser tabs (Perplexity, Gemini, Grok, Claude.ai, DeepSeek — the decorrelated lane), paste the assigned sub-questions per agent into each, and start them in parallel within 60 seconds.

### Step 6 — Wait for Phase 2 outputs

Let the user run Phase 2 in parallel browser tabs — that work happens outside this chat.

When the user returns with the five agent outputs (or attaches them), run Phase 3 (cross-examination / contradiction matrix) using the prompt from `01-prompts-library.md`.

### Step 7 — Phase 4 verification handoff

After Phase 3, output the URL list for verification. Walk the user through Phase 4:
- Manual deep-check on top 5 load-bearing citations
- SwanRef (https://swanref.org) for academic citations
- Scite (https://scite.ai) for any RCT / meta-analysis citations (for health content, Scite access is confirmed at kickoff in Step 4, not discovered here)
- Save survivors to `04-verified-sources.md`, rejects to `04-rejected.md`

### Step 8 — Run Phase 5 consolidation

When the user returns with verified and rejected citations, load the use-case overlay's "Phase 5 — output format block" and run the Chairman prompt from `01-prompts-library.md`. Set Claude to maximum effort / extended thinking.

Output `05-dossier.md`.

### Step 9 — Phase 6 routing

Walk the user through the use-case overlay's "Phase 6 — output routing" section step by step.

---

## Common project shapes (kickoff templates)

For frequently-occurring project types, here's how the kickoff routine adapts.

### Project shape A — "I have an existing requirements file from Claude Code"

This is the spec-driven-dev path used for new software projects.

1. Confirm the requirements file is attached (or pasted).
2. Use overlay `02-overlay-spec-driven-dev.md` and specifically its "Special case — enriching existing requirements markdown files" section.
3. Phase 1 decomposition prompt addition: *"The attached file is the prior requirements draft. Sub-questions must include verification of every external claim, technology recommendation, and architectural choice in that draft. Also surface what's missing from the draft, what constraints haven't been considered, and what alternatives weren't evaluated."*
4. Phase 6 routing: `05-dossier.md` migrates into the project repo at `docs/research/<topic-slug>.md`. Then handoff to Claude Code for Spec Kit / Kiro.

### Project shape B — "I have a topic idea but nothing written yet"

1. Help the user sharpen the topic into a research question. Don't run Phase 1 on a vague topic — produce a refined question first.
2. Identify the use case (Step 1 of the routine).
3. Confirm decision context — what's the deliverable.
4. Run the standard 6-phase pipeline.

### Project shape C — "I want to research before deciding what to build / write"

This is exploratory. Apply a lightweight version:

1. Phase 1 with broader sub-questions (more breadth, less depth).
2. Phase 2 with only Perplexity + Grok (faster, less expensive in time).
3. Skip Phase 3 contradiction matrix (only running 2 agents).
4. Phase 4 light verification (no deep-check, just SwanRef batch check).
5. Phase 5 with a "decision options" output format rather than a final dossier.
6. The output is a "go/no-go" briefing that decides whether to commit to a full dossier later.

### Project shape D — "I want to update a previously published dossier"

1. Locate the prior dossier (in `<dossier-root>/<topic-slug>/`).
2. Phase 1 decomposition focused on what's changed since the prior dossier date.
3. Phase 2 with all five agents prompted to contrast their findings against the prior dossier (paste relevant sections of the prior dossier into each agent's prompt).
4. Phase 3 contradiction matrix specifically calls out where current evidence diverges from prior dossier.
5. Phase 5 produces an updated dossier with explicit changelog section: "What changed since {prior date}".

### Project shape E — "I'm producing multiple deliverables from one research pass"

Common for high-effort topics — research once, route to multiple destinations. v1.3: only the closed matrix in Step 1 is supported.

1. The primary render **derives from the selected use case** — run Phase 1–5 with that use case's overlay.
2. Check the wanted extra deliverables against the Step-1 matrix. A combination outside it gets a separate kickoff (recommend the decision-first or research-first order that lets the second kickoff consume the first's outputs as classified inputs).
3. For each allowed additional render, Phase 6 transforms — it does not re-research: load the target overlay's Phase-5 output block and Phase-6 routing; transform factual content **only** from `05-dossier.md`, `03-conflict-map.md`, and the verified/rejected-source artifacts (no new factual claims); save as `06-<render-id>.md`; then apply the target overlay's routing with that file substituted wherever it consumes the Phase-5 dossier. If preparation reveals a material evidence/coverage gap, stop that render and recommend a separate kickoff.

---

## Common kickoff failure modes

Watch for and pre-empt:

1. **User wants to skip Phase 4** — verification feels tedious. Refuse if the deliverable will be published, billed for, or carries health/legal/financial weight. The audit trail (`04-rejected.md`) is the value, not the inconvenience.

2. **User wants to use only one agent** — defeats the point of multi-agent research. The disagreement detection is the entire reason this stack exists. If they want one-agent output, they should just use that agent directly without this workflow.

3. **User has a vague research question** — run a sharpening pre-step before Phase 1. A vague question produces a vague dossier. Worth 5 minutes of upfront refinement.

4. **User pastes a research output and asks for "consolidation"** — that's the *Chairman dossier prompt at the front of this Claude project*, not this workflow. Direct them appropriately.

5. **User wants to use Suprmind / Genspark / other turnkey aggregators in place of the manual fan-out** — fine if they've made an informed decision (the prior dossier's contradiction matrix #1 covers this). Don't lecture them; just adapt the prompts to whatever tool they prefer.

6. **User starts a new chat without attaching prior context** — load the artifacts from project knowledge anyway (that's why they're in project knowledge). Don't ask them to re-explain the workflow; reference the documents.

---

## Heuristics for Claude in this project

- **Default to running the kickoff routine** at the start of any new chat with research intent. Don't assume the user remembers all the steps.
- **Reference specific overlay files by name** — e.g., "I'll apply the spec-driven dev overlay (`02-overlay-spec-driven-dev.md`)". This reinforces the user's mental model of the artifact set.
- **Keep responses focused on the current phase** — don't dump the entire 6-phase pipeline upfront. Walk the user through phases sequentially.
- **Output prompts in code blocks** ready to copy-paste, with `<placeholders>` for the user to fill in.
- **Track the dossier folder structure** in your responses — when the user is on Phase N, remind them what artifact they should have saved from Phase N-1.
- **Refuse to skip the verification step** for any deliverable that will be published or carry weight. Soft refusals — explain why, then ask if there's a reason to skip in this specific case.
- **Acknowledge when the operator deviates from the workflow with reason** — assume a senior engineer who may have a specific reason to compress steps. Adapt rather than enforcing rigidly.

---

## Maintenance

This artifact set is a living document. Update when:

- A new use case emerges (add a new overlay file, e.g., `14-overlay-podcast.md` — numbers through 13 are taken)
- The tool stack changes (e.g., a paid tool purchased after a trial period — update `00-master-methodology.md` agent inventory)
- A specific prompt gets refined through usage — update `01-prompts-library.md` with the better version
- A quality bar gets tightened or relaxed based on observed output quality — update the relevant overlay's "Quality bar specific to..." section

When updating, version-control the changes. The artifacts live as project knowledge in this Claude project; consider also keeping a copy in a Git repo so changes are tracked over time.

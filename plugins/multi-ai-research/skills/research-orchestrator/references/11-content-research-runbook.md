# Content & Product Research — Operational Runbook

**Owner:** AgenticCodingOps
**Status:** v1.1 — companion to `10-software-dev-research-runbook.md`; includes methodology v1.1 updates (decorrelated lane, confidence tags, live-URL rule, deck+screencast SSOT overlay)
**Reads with:** project knowledge artifacts 00–01, overlays 02–08, runbook 09 (Cowork/skills setup), 12 (project startup checklist); CHANGELOG-v1.1.md for v1.1 rationale

---

## Purpose

This is the playbook for running multi-AI research against any non-coding project — content for YouTube, WordPress articles, presentations, ebooks, market/product research, health protocols, biohacking routines, and personal-life research projects.

For coding projects, use `10-software-dev-research-runbook.md` instead.

The two runbooks share the same 6-phase pipeline, the same skills (`research-orchestrator`, `research-requirements-check`), and the same Claude project knowledge base. They differ in:
- Phase 0 setup (different workspace folder, no repo)
- Phase 1 decomposition (use-case-specific via overlays 03–07)
- Phase 2 agent stack (often includes Elicit + Consensus for health; excludes them for software)
- Phase 5 output format (set by overlay, not by ADR template)
- Phase 6 routing (publishing/recording instead of `/speckit.specify`)

---

## When to use which runbook

| Project type | Runbook | Primary overlay | Final deliverable |
|---|---|---|---|
| Software project (greenfield or brownfield) | 10-software-dev-research-runbook.md | 02-overlay-spec-driven-dev.md | Spec Kit / Kiro input → code |
| Conference talk (slides ONLY) | This runbook | 04-overlay-presentation.md | PowerPoint / slides + speaker notes |
| 🆕 Deck + video combined (presentation + screencast / YouTube + slide content) | This runbook | 08-overlay-deck-and-screencast.md | Single Markdown source → Marp deck + Descript screencast |
| YouTube video (script ONLY, no slides) | This runbook | 03-overlay-youtube-script.md | Recordable script + companion blog |
| Ebook (long-form, multi-chapter) | This runbook | 05-overlay-ebook.md | EPUB / PDF / Kindle |
| WordPress + Elementor SEO blog article | This runbook | 06-overlay-wordpress-seo.md | Published blog post |
| Health content (back pain, longevity, biohacking, focus) | This runbook | 07-overlay-health-content.md | Evidence-graded protocol → any output format |
| Market / product research with affiliate links | This runbook | 06 (primary) + 03 (if also YouTube) | Blog + video with affiliate links |
| Personal research (best laptop, life decisions, travel) | This runbook | Match nearest overlay; usually 06 for write-up | Notes for personal use or content |

If a project has multiple output formats (e.g., hair-product research → blog + YouTube + LinkedIn post), pick the **most demanding overlay as primary** and route the dossier through other overlays in Phase 6. WordPress SEO is usually the strictest (keyword discipline, top-10 SERP analysis); ebook chapters are second strictest (word count discipline, footnoted citations). See "Multi-deliverable projects" below.

---

## Directory architecture — separate workspaces for code and content

Code projects and content projects live in separate root directories. Reason: Cowork sees every file in a granted folder; mixing code and content workspaces means Cowork drifts into unrelated context. Keep them apart.

```
<code-workspace>\                  ← CODE workspace (existing)
├── <repo-1>\
├── <repo-2>\
├── (other repos)
└── dossiers\                      ← software-project dossiers (the pilot project lives here)

<content-workspace>\               ← CONTENT workspace (new)
├── content-research\              ← active content dossiers
│   ├── example-product-research\
│   ├── example-health-topic\
│   └── (one folder per content project)
├── archive\                       ← completed dossiers moved here after publishing
└── shared\                        ← reusable assets across projects:
                                   ─   brand voice docs
                                   ─   YouTube channel templates
                                   ─   affiliate disclosure templates
                                   ─   NotebookLM source corpora (health PDFs, etc.)
                                   ─   keyword research from prior projects
```

**Cowork access rules:**
- For software project Cowork sessions: grant `<code-workspace>\` (+ optionally `<research-stack>\`)
- For content project Cowork sessions: grant `<content-workspace>\` (+ optionally `<research-stack>\`)
- **Never grant both** in the same session — defeats the context isolation

**Why this works:**
- One folder to remember per project type (`<content-workspace>\` for all content, `<code-workspace>\` for all code)
- The `archive\` sub-folder keeps the active workspace lean — move dossier folders there once published
- The `shared\` sub-folder is where assets get reused across projects (your brand voice doc gets uploaded once; every Cowork session can read it without re-uploading)

---

## Pre-flight (one-time setup, beyond software-dev pre-flight)

Verify before your first content research project.

| Item | Expected state | How to verify |
|---|---|---|
| Content workspace root | `<content-workspace>\` exists with `content-research`, `archive`, `shared` sub-folders | `dir <content-workspace>` — if not, run:<br>`mkdir <content-workspace>\content-research`<br>`mkdir <content-workspace>\archive`<br>`mkdir <content-workspace>\shared` |
| Elicit free-tier account | Active; 100 paper extractions/month available | Sign in at elicit.com; only required if you'll do health content; skip otherwise |
| Consensus free-tier account | Active; 25 searches/month available | Sign in at consensus.app; only required for health content |
| NotebookLM accessible | Included with Gemini Pro subscription | Open notebooklm.google.com |
| Felo account | Free tier sufficient | Only required for non-English / multilingual research |

Software-dev pre-flight items (skills, MCPs, methodology folder) carry over identically — see runbook 10 for those.

---

## The 6-phase pipeline (same shape, content-specific deltas)

```
PHASE 0  → Setup: content workspace folder + use-case identification + 
            decision context + (optional) keyword research for SEO articles
   ↓
PHASE 1  → Decomposition mapped to deliverable structure (chapters / H2s / 
            video chapters / slide sections / FAQ items)
   ↓
PHASE 2  → Parallel fan-out: 4-6 agents (varies by overlay)
   ↓
PHASE 3  → Contradiction matrix
   ↓
PHASE 4  → Citation verification (intensified for health content)
   ↓
PHASE 5  → Chairman synthesis with use-case-specific output format
   ↓
NotebookLM → Source-grounding sanity check (10-min add-on)
   ↓
PHASE 6  → Use-case-specific routing: record video / publish WP / generate 
            EPUB / build slide deck
```

Total wall-clock: typically 90–120 min for a single-deliverable project; longer for ebooks (per-chapter runs) and multi-deliverable projects.

---

## Phase 0 — Setup

### 0.1 — Open Cowork with the right folder access

For content projects, you need only:
- `<content-workspace>\content-research\` (workspace — dossiers and inputs live here)
- `<research-stack>\` (methodology copy — optional but helpful)

Do **not** grant Cowork access to `<code-workspace>\` (your code workspace) for content projects. Less context = sharper focus.

### 0.2 — Identify the use case and the deliverable shape

Cowork's orchestrator skill will ask this; have the answers ready:

- **Primary use case:** YouTube / presentation / ebook / WordPress SEO / health / market research
- **Output formats:** Single deliverable, or multi (blog + video + carousel)?
- **Decision context in one sentence:** *"Publish a 2,500-word WordPress article with affiliate links recommending top 5 hair products"* / *"Record a 12-minute YouTube video on Terraform agentic coding patterns"* / *"Write chapters 3 and 4 of the spec-driven dev ebook"* / *"Personal decision — which laptop to buy for local LLMs"*
- **Time horizon:** This week / this month / no deadline
- **Audience:** Specific persona description, not vague
- **Existing inputs:** Any prior research, brand guidelines, channel style guides, keyword data

### 0.3 — Skip the requirements quality check (in most cases)

The requirements-quality-check skill assumes a markdown requirements file from Claude Code. For content projects, there usually isn't one — you're starting from a topic, not a spec.

Skip Phase 0.5 explicitly in your kickoff prompt for content projects. State this so the orchestrator doesn't pause to look for a non-existent file.

Exception: if you have a detailed brief (e.g., a client gave you a content brief, or you have a YouTube script template you're building on), point Cowork at it and run the check.

### 0.4 — For WordPress SEO articles only: keyword research as Pre-Phase-1

The WordPress overlay (06) requires keyword research before Phase 1 decomposition. The orchestrator will surface this; have ready:

- **Primary keyword:** the search query you want to rank for
- **Search intent:** informational / commercial / transactional
- **Target word count:** 1500 / 2500 / 4000
- **Secondary keywords:** 3-5 related terms

If you don't have these yet, Cowork's first Phase-2 sub-question can run a separate "top 10 Google UK results for X" query in Perplexity standard mode to surface what existing content uses. Then refine.

For non-WordPress content projects, skip keyword research.

---

## Phase 1 — Decomposition

Use Pattern A (full decomposition) by default for content projects — most don't have prior research prompts to improve.

Decomposition shape varies by overlay:

| Overlay | Sub-questions map to | Typical count |
|---|---|---|
| YouTube (03) | Video chapters of ~90 sec each | 5–7 |
| Presentation (04) | Talk sections (containing 4–7 slides each) | 4–6 |
| Ebook (05) | Sections within a chapter (run separately per chapter) | 4–7 per chapter |
| WordPress SEO (06) | H2 headings + FAQ items | 5–8 |
| Health (07) | Evidence-strength clusters: STRONG / MODERATE / WEAK + protocol + red flags | 5–7 |

The orchestrator's Phase 1 output produces ready-to-paste Phase 2 prompts per agent. Spot-check at least the heaviest two before fan-out.

---

## Phase 2 — Parallel fan-out (varies by overlay)

### Default content agent stack (5 agents) — v1.1

| Tab | Tool | Strength | Default save |
|---|---|---|---|
| 1 | Perplexity Pro Deep Research | Citation density, current state, comparison tables | `02-perplexity.md` |
| 2 | Gemini Deep Research | Source volume, ingredient/topic depth | `02-gemini.md` |
| 3 | Grok DeepSearch (SuperGrok) | Reddit, X community sentiment, recent reviews | `02-grok.md` |
| 4 | Claude, strongest available model (web search, separate tab from this project) | Cross-cutting synthesis, contrarian framing | `02-claude.md` |
| 5 | **🆕 DeepSeek (chat.deepseek.com web UI, DeepThink mode)** | **Error decorrelation — non-Western training lineage** | `02-deepseek.md` |

For non-confidential content research (which is most content projects — hair products, health, biohacking, methodology), the DeepSeek web UI is the right tool. For any confidential content (client data, HIPAA-equivalent material, business-sensitive context), the question is where the prompt data goes, not whose model it is — keep the lane but change the route: a Western-hosted DeepSeek API (confirm the hosting region) or self-hosted inference. Drop the lane only when neither route is available.

### Additional agents per overlay

**WordPress SEO (06):**
- 6th agent (on top of the 5-agent base): Perplexity in STANDARD (not Deep Research) mode — runs the "top 10 Google UK results for <primary keyword>" query to surface what competitors say. Output as `02-serp-analysis.md`. Critical for differentiation.
- ChatGPT free-tier Deep Research (7th, optional) — adds another perspective at zero cost

**Market / product research with affiliate links:**
- Same as WordPress SEO above
- Add: Trustpilot / Reddit r/<niche> manual scan if Grok doesn't cover well
- Add: explicit search for "ingredients to avoid" or "common failure modes" — surfaces what reviews miss

**YouTube script (03):**
- The 5-agent base stack (including the decorrelated lane) is the default
- Optional 6th: NotebookLM with your channel's prior videos (if you have a corpus) — keeps tone and audience consistent

**Health content (07) — different stack:**
- Tab 1: **Elicit** (mandatory) — structured extraction from RCTs and meta-analyses
- Tab 2: **Consensus** (mandatory) — yes/no/maybe consensus on binary intervention questions
- Tab 3: **Perplexity Pro Deep Research** — citations + recent practical applications
- Tab 4: **Gemini Deep Research** — PubMed and journal coverage
- Tab 5: **NotebookLM** with curated PDFs (McGill, Attia, etc.) uploaded
- Tab 6: Grok DeepSearch (low weight — community signal only, clearly tagged)
- Tab 7: **🆕 DeepSeek — the decorrelated lane** (DeepThink, low-to-medium weight) — error decorrelation against the Western-model consensus on the framing/synthesis sub-questions. Health research routinely touches HIPAA-equivalent or client data, so route via a Western-hosted API or self-host per the base-stack rule, never the consumer web UI.
- Claude (strongest available model) in web search — for synthesis questions only

For health content, the Phase 1 decomposition prompt **must** demand evidence-strength tagging (STRONG / MODERATE / WEAK). This is what makes the health overlay valuable.

**Ebook (05) — varies by chapter type:**
- How-to chapters: WordPress-style — the 5-agent base plus the optional SERP pass
- Narrative chapters: Grok + Perplexity for case studies; NotebookLM with interview transcripts
- Health chapters: full health-content stack
- Theoretical chapters: Claude Opus heavier weight

**Presentation (04):**
- Same 5-agent base stack (including the decorrelated lane)
- Add Gemini Deep Research second pass specifically for chart-generation requests (Gemini outputs Mermaid / matplotlib code natively)

### What NOT to add (content-specific)

These show up as Cowork suggestions and need to be overridden when wrong:

- **Elicit / Consensus** for non-health content. They surface academic literature; product research, market analysis, YouTube content, and most blog topics aren't evaluated on RCT-grade evidence. Override unless the topic intersects empirical research questions.
- **Felo** unless you're researching non-English sources. Even then, default Felo for free; pay only if hitting limits.
- **Suprmind / Genspark / multi-model aggregators.** You have the five-lane manual fan-out working; aggregator subscriptions don't add value at your volume.

### Phase 2 sanity check (3 minutes — same as software dev)

Open each `02-*.md` and verify:
1. No truncation
2. Required structure: TL;DR, findings with URLs, "what would change your recommendation," "what this answer does NOT cover"
3. Citation density adequate
4. **🆕 Live-URL paste-check.** Spot-open three citations per file in browser. If they're dead reference markers (e.g., ChatGPT's `【n†…】`) or don't resolve, the file fails — re-export or re-run that agent before Phase 3. This catches the failure mode where citations exist as text but can't be followed.
5. **🆕 Confidence tags present.** Each finding should be tagged [HIGH] / [MEDIUM] / [LOW]. Files without confidence tagging fail.
6. Project-specific constraints honoured (e.g., UK availability, evidence-strength tagging for health)

Re-run any agent whose file fails a check before Phase 3.

---

## Phase 3 — Contradiction matrix (same as software dev)

The contradiction matrix is the most valuable output of the whole exercise for content projects. The places where agents disagree about product effectiveness, ingredient safety, or claim strength are exactly the places where your content's defensibility rests on weak ground.

For product/market research specifically, **the CONFLICT section becomes your honest "pros and cons" basis** — products where one agent rated highly and another flagged issues belong in your "considered but rejected" or "best for X, worse for Y" tiers, not in unqualified recommendations.

For health content, the CONFLICT section maps directly to **`[MIXED EVIDENCE]` flags** in Phase 5 — claims where literature is split don't get smoothed into yes/no recommendations.

Save as `03-conflict-map.md`.

---

## Phase 4 — Citation verification (intensified for health and product research)

### Standard content verification

Same as software dev: Firecrawl batch + plausibility check + manual deep-check on top 5.

### Health content additions (overlay 07)

- **Scite (https://scite.ai)** for every RCT / meta-analysis citation — confirms whether later papers contradicted the cited finding. Non-negotiable for health content.
- **NotebookLM cross-check** with curated PDFs uploaded — strongest source-grounding pass for health claims
- **Read methods sections** (not just abstracts) for any claim with effect-size numbers — abstracts often overstate

### Product / affiliate marketing additions (overlay 06)

- **Trustpilot manual check** for any product getting a top-3 recommendation — confirm verified-purchase reviews exist, scan negative reviews for failure modes
- **Manufacturer claim verification** — open the brand's product page and confirm the agent didn't fabricate or misquote ingredient lists, certifications, or performance claims
- **UK availability check** — manually open Amazon UK, Boots, Superdrug, or specialist retailer to confirm each product is purchasable at the time of writing (prices change; sometimes products go EOL)
- **Affiliate link existence** — if you'll use affiliate links, confirm the product is available in your affiliate network (Amazon Associates UK, Awin, etc.) before recommending

Save survivors to `04-verified-sources.md`, rejects to `04-rejected.md`. Rejected list becomes important for affiliate marketing — shows due diligence if anyone questions a recommendation.

---

## Phase 5 — Chairman synthesis (Claude.ai web, this project, max thinking)

Same procedure as software dev, but the `<output_format>` block in the Chairman prompt comes from the use-case overlay (03–07), not from the spec-dev overlay.

### Common Phase 5 prompt template for content

In a fresh Claude.ai web chat in this project:

```
Begin Phase 5 — Chairman synthesis for the content research project at 
<content-workspace>\content-research\<topic-slug>\.

Apply the Chairman prompt from 01-prompts-library.md using the 
<06-overlay-wordpress-seo.md / 03-overlay-youtube-script.md / 
07-overlay-health-content.md / etc.> output format.

If this is a multi-deliverable project: produce the dossier in the PRIMARY 
overlay's format (the most demanding one). Secondary overlays will be 
handled in Phase 6 by routing the same dossier through each one.

[Paste all 02-*.md, 03-conflict-map.md, 04-verified-sources.md, 
04-rejected.md inline below]
```

### Output format reminders

- **WordPress SEO (06):** primary keyword in the top-level heading (`<h1>`) and first 150 words; H2s match decomposition sub-questions; FAQ section with PAA-style questions; schema markup; meta description; URL slug; internal linking suggestions
- **YouTube script (03):** hook + chapters + closing CTA; on-screen sources per chapter; thumbnail/title alternatives; description with timestamps; pinned-comment text
- **Health content (07):** STRONG/MODERATE/WEAK evidence-strength tagging on every claim; practical protocol; red flags; disclaimer block; sources organised by evidence strength
- **Presentation (04):** slide-by-slide plan with headline + body + visual spec + speaker notes; Q&A prep; backup slides
- **Ebook (05):** per chapter — thesis, hook, sections, summary, reader action, footnoted citations

Save as `05-dossier.md`.

### NotebookLM sanity check (same as software dev)

Upload all inputs + agent outputs + conflict map + verified sources + dossier. Run the hallucination check and drop check queries from runbook 10. Especially valuable for affiliate marketing dossiers — fabricated product features create liability.

---

## Phase 6 — Routing per overlay

### WordPress + Elementor SEO publishing

1. Copy article body from `05-dossier.md`
2. Paste into Gutenberg block editor (markdown converts cleanly)
3. Switch to Elementor edit mode; apply your standard template
4. Paste JSON-LD schema block in Custom HTML widget at bottom
5. Set primary keyword + meta description + URL slug via Yoast/Rank Math
6. Featured image from prompt in dossier (DALL-E / Midjourney / Unsplash)
7. Internal linking pass (3-5 from existing site)
8. Affiliate link insertion (if applicable) — disclose per UK ASA/CMA requirements
9. Publish + submit URL to Google Search Console for indexing
10. Post-publish distribution per dossier checklist

### YouTube video production

1. Read script aloud once for cadence; adjust any AI-pattern phrases
2. Optional sanity check: paste script into NotebookLM, generate Audio Overview
3. Record straight from script (or as teleprompter)
4. Edit per normal pipeline
5. Use dossier description template
6. After publish, lightly edit the "companion blog post outline" section of the dossier and publish to your blog as written companion (or use overlay 06 for full SEO treatment)

### Presentation production

1. Pull dossier's slide-by-slide plan
2. Open Gemini Deep Research, ask it to generate Mermaid/matplotlib code for each chart slide
3. Open PowerPoint / Keynote with your standard template
4. For each slide: headline → title, bullets → content, visual → paste image, speaker note → notes pane
5. Manual visual polish pass
6. Two full rehearsals before presenting; three if paid keynote
7. One-page handout from "Talk arc" + "Q&A prep" sections

### Ebook chapter production

1. Each chapter dossier copies into your Scrivener / Word / Pandoc workspace
2. After all chapter dossiers complete, run book-level meta-Phase-5 (preface + cross-chapter consistency + index + bibliography)
3. Concatenate: `cat 00-book-meta.md chapter-*/05-dossier.md > book-manuscript.md`
4. Generate EPUB via pandoc command in overlay 05
5. Generate PDF via pandoc command in overlay 05
6. Kindle: pandoc to docx, upload to KDP
7. Optional audiobook draft: NotebookLM Audio Overview per chapter

### Health content / personal-use protocol

1. Save dossier to your personal Obsidian / Notion / NotebookLM for ongoing reference
2. If publishing: use the appropriate output overlay (WordPress SEO, YouTube, ebook) — health overlay's evidence-strength discipline carries through
3. Personal application: follow the practical protocol section; track via the metrics specified
4. Re-run the dossier annually as literature evolves

### Multi-deliverable projects

Pattern: produce one Phase 5 dossier in the most demanding overlay's format, then route through other overlays' Phase 6.

**🆕 Special case — combined deck + screencast (v1.1):** If your project needs BOTH a slide deck AND a screencast/YouTube video from the same content (which is most of your presentations going forward), use the unified `08-overlay-deck-and-screencast.md` from the start. Don't run overlays 03 and 04 separately — overlay 08 produces a single Markdown source that renders to both formats and eliminates drift. Marp renders the deck; Descript captures and edits the screencast.

**For all other multi-deliverable projects (e.g., hair-product → blog + YouTube short + LinkedIn carousel):**

1. Run Phase 6 for primary overlay (e.g., WordPress publish)
2. Take the same 05-dossier.md
3. In a new Claude.ai chat in this project, ask for re-formatting per the secondary overlay:
   ```
   Re-format this dossier from WordPress SEO output into a YouTube video script 
   per 03-overlay-youtube-script.md. Preserve all source citations and disputed 
   claims; restructure for spoken delivery in 90-second chapters.
   ```
4. Save as `05-dossier-youtube.md`
5. Run YouTube Phase 6 (record + publish)
6. Repeat for any other deliverable formats

The single Phase 1-5 research effort feeds multiple deliverables without re-researching.

---

## Lessons specific to content / product research

### 1. The use case is the overlay, not the output channel

YouTube and WordPress are output channels. The *research overlay* is determined by the research's structural constraints: keyword discipline (WordPress SEO), spoken-chapter cadence (YouTube), word-count chapter discipline (ebook), evidence-strength tagging (health), slide-density compression (presentation). Pick the overlay with the strictest constraints as primary.

### 2. Product research is fundamentally affiliate-defensibility research

If you'll add affiliate links, the dossier serves a different purpose than a generic comparison article. It must support a recommendation you'd defend publicly. The CONFLICT section becomes your "honest pros and cons" basis. The `04-rejected.md` file becomes your due-diligence audit trail. Treat affiliate marketing as if you'll be asked to justify each recommendation in writing — because regulators (UK ASA / CMA) increasingly do.

### 3. Health content has the strictest verification — never skip Scite

The Scite citation-contradiction check is the difference between health content that ages well and content that contradicts what newer papers show. A 2019 RCT supporting intervention X may have been refuted by a 2023 meta-analysis; Scite catches this. Non-negotiable.

### 4. NotebookLM is more valuable for content than software dev

Content claims (product features, health protocols, historical facts, ingredient research) are easier to hallucinate than software API names. Run the NotebookLM source-grounding pass for every content dossier, especially if affiliate / health / client-published.

### 5. WordPress SEO articles need top-10 SERP analysis as a separate Phase 2 query

Every other agent researches the topic; one agent specifically researches **the competition**. Differentiation hooks are won by surfacing what the top 10 don't say. Don't skip this query.

### 6. Multi-deliverable projects share one Phase 1-5; only Phase 6 branches

Don't run separate research for the YouTube video and the WordPress article on the same topic. Produce one dossier in the strictest overlay's format; reformat in Phase 6 for the secondary deliverables. Saves 60-90% of the research time.

### 7. Don't add academic-literature agents (Elicit / Consensus) to non-health content

Same rule as software dev. They surface peer-reviewed papers, which don't help with product recommendations, YouTube scripts, blog articles, or market analysis. Health content only.

### 8. The personal-research case (best laptop, life decisions) is still worth a dossier

When the deliverable is "I'll decide myself," the dossier is for *you*, not for publication. Use the WordPress SEO overlay's structure (it's the most decision-oriented) but skip Phase 6 publishing. The contradiction matrix and verified-sources list are exactly what you need to make a good decision yourself.

### 9. Deck + screencast = one source of truth, not two (v1.1 addition)

The 2026 methodology research surfaced this as the most operationally significant change. Before v1.1, you'd run overlay 03 (YouTube) and overlay 04 (presentation) separately for the same content, then manually keep them in sync. After v1.1, overlay 08 produces a single Markdown source where speaker notes ARE the screencast script. Marp renders slides; Descript captures the video; both branch only at render time. No drift, no manual sync.

Use overlay 08 by default for any project that involves both a presentation and a video. Use 03 or 04 alone only when you genuinely need just one format.

---

## Quick-reference: kickoff prompt template

For a new content project, paste into Cowork:

```
Run the research-orchestrator skill for a content research project (NOT a 
software project).

Context:
- Use case: <YouTube / presentation / ebook / WordPress SEO / health / 
  market research>
- Topic: <one or two sentences>
- Audience: <specific persona>
- Decision context: <one sentence — what gets produced and for what purpose>
- Time horizon: <when>
- Workspace: <content-workspace>\content-research\
- Dossier folder: <content-workspace>\content-research\<topic-slug>\
- Existing inputs: <none / file paths>
- Output format(s): <single deliverable or list of deliverables>

[For multi-deliverable: state which overlay is primary; others will be 
routed in Phase 6]

[For affiliate marketing: state this explicitly so verification is intensified]

[For health content: state any prior research, curated PDFs you have, 
specific subpopulation focus]

[Project-specific constraints — see hair-product example for shape]

Skip Phase 0.5 requirements check (no requirements file).

Begin Phase 0 setup and proceed to Phase 1 (Pattern A — full decomposition).

[For WordPress SEO: include "Run Pre-Phase-1 keyword research" instruction]

Show me the Phase 1 decomposition + staged Phase 2 prompts before fan-out.
```

---

## Phase 3 / 4 / 5 / 6 prompts

Same templates as runbook 10 (software dev), with these substitutions:

- `<topic-slug>` paths point to `<content-workspace>\content-research\` not `<code-workspace>\dossiers\`
- Phase 5 output format reference is the use-case overlay (03–07), not the spec-dev overlay (02)
- Phase 6 routing is publishing/recording/printing, not `/speckit.specify`
- No Claude Code handoff at the end

Refer to runbook 10's "Quick-reference: prompts to paste at each phase" section, modify as above.

---

## Maintenance

Update this runbook when:
- A new overlay is added (e.g., podcast script, course curriculum, newsletter)
- An overlay's quality bar changes based on observed dossier outputs
- The agent stack for an overlay changes (e.g., a new tool becomes standard)
- A specific pattern from a real project warrants codifying in "Lessons captured"

Version-control with the rest of the AgenticCodingOps methodology. When meaningfully revised, increment version and date at top.

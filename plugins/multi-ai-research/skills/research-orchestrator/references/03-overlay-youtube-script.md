# Overlay — YouTube Scripts (Agentic Coding / Engineering Content)

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`
**Superseded-by:** `08-overlay-deck-and-screencast.md` — for this overlay's Phase-6 section whenever a slide deck is also produced (see the v1.1 note below)

---

> **v1.1 note:** If your project also produces a slide deck for the same content, use `08-overlay-deck-and-screencast.md` instead. Use this overlay only when producing a YouTube script with NO accompanying slide deck.

---

## When to use this overlay

Apply when the dossier feeds a YouTube video script for your audience: senior engineers, DevSecOps practitioners, platform engineers, and technical consultants. Content domains include agentic coding, DevOps tooling, cloud architecture (Azure / AWS), Terraform, GitHub Actions, AI for engineers, and Claude/AI tooling reviews.

This overlay produces a video script that can be recorded directly. It also produces a written companion piece (a published markdown dossier alongside the video) — that's a key differentiator for this audience.

---

## Phase 1 — decomposition adjustment

Add this paragraph to the Phase 1 prompt:

```
This is a YouTube video research project for your channel. 
Audience: senior engineers, DevSecOps, platform engineering — assume technical fluency, 
do not over-explain DevOps fundamentals. Tone: opinionated, evidence-based, willing to 
challenge vendor marketing.

Sub-questions must map to video chapters. Aim for 5-7 sub-questions = 5-7 chapters of 
~90 seconds each. Each sub-question must be answerable in 60-120 seconds of spoken script. 
Total video length target: 7-12 minutes (sweet spot for technical YouTube).

Required focus areas in decomposition:
(i) The hook — one specific concrete problem the viewer has right now
(ii) The "what's actually changed" angle — what's new, recent, or contrarian about this topic
(iii) The "show your work" angle — verifiable evidence, benchmarks, demos
(iv) The "what to do Monday" angle — concrete actionable next steps

Disqualified sources: thought-leadership LinkedIn posts, vendor marketing, AI-generated 
listicles, anything where the author has a financial interest in the conclusion (unless 
explicitly framed as such).
```

---

## Phase 2 — agent weighting

| Agent | Weight | Why |
|---|---|---|
| **Grok DeepSearch** | High | Real-time vendor announcements, GitHub Actions/Terraform updates, X engineering community sentiment, breaking news in the AI tooling space |
| **Perplexity Pro Deep Research** | High | Citation-backed claims you'll show on screen as receipts; comparison tables |
| **Gemini Deep Research** | Medium | Benchmark data, comparison tables, multi-source breadth |
| **Claude (strongest available model) + web search** | Medium | Cross-cutting trade-off framing; useful for the "what's actually changed" sub-question |
| **🆕 DeepSeek — the decorrelated lane (DeepThink)** | Medium | The v1.1 mandatory fifth lane: a non-Western training lineage whose errors don't correlate with the Western stack, so its disagreements are real signal. For confidential work, route via a Western-hosted API or self-host rather than the consumer web UI. |

**Optional sixth agent:** ChatGPT free tier (or via OpenRouter) for a contrarian counter-prompt — sometimes useful to pressure-test a strong narrative before committing.

---

## Phase 5 — output format block

Insert this into the Chairman prompt's `<output_format>` block:

```
# {Topic} — YouTube Video Script

## Video meta
- Working title: ...
- Target length: {7-12 min}
- Audience: senior engineers, DevSecOps, platform engineering
- One-sentence thesis: ...
- Differentiation hook: <what does this say that the existing top-10 search results don't>

## Hook (90 seconds, ~225 words)

[SCRIPT]
- Cold open with a specific concrete problem your viewer has right now
- Promise of what the video delivers (specific, measurable)
- Authority signal — one specific verified claim with on-screen source

[ON-SCREEN]: <text overlay or graphic>
[SOURCE TO CITE ON SCREEN]: <URL>

## Chapter 1: {sub_question_1 reframed as compelling chapter title}

[SCRIPT — ~225 words for ~90 seconds spoken at 150 wpm]
...

[ON-SCREEN SOURCE]: <URL — verified in Phase 4>
[B-ROLL PROMPT]: <description for editor or AI b-roll generator>
[EVIDENCE-STRENGTH]: VERIFIED / SINGLE-SOURCE / DISPUTED 
  (if DISPUTED, present both positions in script)

## Chapter 2: ... 
(same structure)

## Chapter N: ...

## Closing CTA (30 seconds)

[SCRIPT]
- Recap of one key actionable
- "If you found this useful, the written dossier is linked below — sources, 
  contradictions, the works"
- Subscribe / comment hook
- Next video tease

## Thumbnail concepts (3 alternatives)
1. Concept A: <description>
2. Concept B: <description>
3. Concept C: <description>

## Title alternatives (3, each ≤60 chars, primary keyword in first 30 chars)
1. ...
2. ...
3. ...

## Description (≤300 words)

```
{Compelling first paragraph}

Chapters:
0:00 Hook
0:90 Chapter 1: {title}
{timestamps for each chapter}

Sources cited in this video:
- {URL 1}
- {URL 2}
...

Companion written dossier: <will paste GitHub link after publish>

#<your-channel-tag> #devops #ai
```

## Pinned comment
{The single most useful tip from the video, in one paragraph}

## Companion blog post outline
(Same content as script but reformatted as a written dossier — the Chairman 
should produce this AS WELL AS the script, since the written companion is 
the differentiator)
```

---

## Phase 6 — output routing

### Recording

1. Open `05-dossier.md` (the script form). Read the script aloud once for cadence — adjust any sentence that doesn't sound like you talking. Aim to remove any AI-pattern phrases.
2. **Sanity check (optional but recommended):** Paste the script into NotebookLM and generate an Audio Overview. Listen back — if the narrative arc holds when read by a synthetic voice, it'll hold when you read it. If anything feels stilted in the Audio Overview, fix that section.
3. Record straight from the script (or use it as a teleprompter).
4. Edit using your normal pipeline.

### Companion written dossier (the differentiator)

After publishing the video:

1. Take the "Companion blog post outline" section from `05-dossier.md`.
2. Lightly edit it for written tone (more nuance, longer sentences than the script).
3. Add the five agents' raw outputs as collapsed appendices for the truly nerdy readers.
4. Publish to GitHub Pages, your blog, or paste into a LinkedIn article.
5. Link from the YouTube description.

This published dossier — with the contradiction matrix, verified sources list, and rejected-citations log all visible — is what differentiates your channel from the AI-summary-blog crowd. Senior engineers will read it before subscribing.

### Cross-promotion

The same dossier can be re-routed through:
- `04-overlay-presentation.md` for a conference talk version
- `06-overlay-wordpress-seo.md` if hosting on a WP blog with SEO intent

---

## Quality bar specific to YouTube content

Reject any draft of `05-dossier.md` that:

1. Cites the same source for >2 claims (over-reliance signals weak research).
2. Has a chapter that can't be defended in 60 seconds of spoken script (chapter is too dense; split it or remove).
3. Contains any vendor's marketing claim without an independent corroboration or explicit `[VENDOR-CLAIM]` tag.
4. Has fewer than 2 disputed claims surfaced — for technical topics in this audience, "everyone agrees" is a sign you didn't dig hard enough.
5. Doesn't have a specific concrete problem in the hook (vague problem statements lose viewers in the first 10 seconds).

---

## Practitioner notes

- Know your audience's baseline (e.g., senior engineers already fluent in Terraform, AWS, Azure, GitHub Actions, C#) and don't waste runtime on fundamentals.
- Opinionated framing converts; safe framing doesn't. The contradictions surfaced in Phase 3 are the sharpest content — feature them.
- The published dossier alongside the video is a moat. Generic AI-content YouTube channels can't easily replicate the "here's the audit trail" deliverable because they don't run a multi-agent pipeline.
- Sponsorship-relevant claims (e.g., a tool review where you might later be sponsored) should be flagged in the dossier as `[POTENTIAL-COI]` so future-you remembers when negotiating sponsorship terms.

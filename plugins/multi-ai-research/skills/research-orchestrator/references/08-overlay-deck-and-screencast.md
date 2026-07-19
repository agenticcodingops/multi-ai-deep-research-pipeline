# Overlay — Deck + Screencast (Single Source of Truth)

**New in v1.1 (2026-06-01).** **Reads with:** `00-master-methodology.md` and `01-prompts-library.md`.
**Supersedes:** the Phase-6 sections of `03-overlay-youtube-script.md` and `04-overlay-presentation.md` whenever you need *both* a slide deck and a screencast/talking-head video from one research pass. Use 03 or 04 alone only when you genuinely need just one format.

---

## Why this overlay exists

Maintaining a YouTube script and a slide deck as separate artifacts causes drift: edit one, the other goes stale. The 2026 creator consensus (4 of 6 agents in the `multi-ai-research-workflow` dossier) is a **single Markdown file where the speaker notes ARE the screencast script**, rendered to slides with Marp (or Slidev) and recorded/edited in Descript. The deck is *generated from* the dossier; it is never hand-maintained in parallel. [VERIFIED — multi-agent]

---

## Pre-Phase-1 — decide the format envelope

- Deck length ≈ 1 content slide/minute + 3 framing slides (title/agenda/close).
- Video length: 7–12 min for technical YouTube; chapters ≈ 90 s each.
- One thesis the audience must remember 24h later.

## Phase 1 — decomposition adjustment

Add to the Phase 1 prompt:

```
This research feeds ONE Markdown source of truth that renders to BOTH a slide deck and a
screencast video. Sub-questions must map to talk/video sections (4-6 sections, each = a
chapter ≈ 90s of narration AND a slide cluster). For each sub-question, the decomposition
must surface: (i) the one-sentence claim (slide headline), (ii) the evidence/visual the slide
needs, (iii) the 90-second narration beat (speaker note / script). Assume the audience is
technically fluent; no fundamentals.
```

## Phase 2 / 3 / 4 — unchanged

Run the standard fan-out (incl. the decorrelated lane), contradiction matrix, and citation verification per the spine. The deck+screencast format only changes the Phase-5 output shape and Phase-6 routing.

## Phase 5 — output format block (paste into the Chairman `<output_format>`)

```
# {Title} — Deck + Screencast Source of Truth

## Meta
- Audience · Deck length (slides) · Video length (min) · One-sentence thesis · Differentiation hook

## The single-source-of-truth file (Marp Markdown)
Produce a complete Marp markdown document. For EACH slide:

---
marp: true
paginate: true
---
# [SLIDE HEADLINE = one-sentence claim]
[≤3 body bullets, ≤10 words each]
[VISUAL: chart data table | mermaid sketch | screenshot description]
<!-- SPEAKER_NOTES
[Full narration, ~225 words ≈ 90s at 150 wpm — this IS the screencast script, verbatim]
SCENARIO: [SLIDE-CAST | TALKING-HEAD | SCREENSHARE | B-ROLL: description]
SOURCE: [verified https URL from 04-verified-sources.md]
EVIDENCE: [VERIFIED | CONTESTED | SINGLE-SOURCE]
-->

## Title/thumbnail options (3 each, video) · Description with chapter timestamps · Pinned comment
## Q&A prep (5 anticipated questions, each with a sourced answer)
```

Rules carried from the spine: ≤3 bullets/slide; every chart slide includes its data table; ≥2 surfaced contradictions if the topic has trade-offs; every Q&A answer sourced; speaker notes defensible in ≤90s.

## Phase 6 — routing (the payoff: one artifact → both formats)

1. **Save** the Chairman output as `05-dossier.md` (it's already valid Marp markdown).
2. **Deck:** `marp 05-dossier.md --pdf` (and `--pptx` if you need editable). Apply your template; the headline→title, bullets→body, VISUAL→image, SPEAKER_NOTES→notes pane mapping is 1:1.
3. **Screencast:** `marp 05-dossier.md --html`, open in browser, record the screenshare in **Descript**. Because the transcript = your speaker notes, edit the video by editing text; cut filler by cutting words.
4. **Talking-head / B-roll:** follow the `SCENARIO:` markers per slide to know when to cut to camera, screenshare, or B-roll.
5. **YouTube companion:** the chapter timestamps + description block are already in the dossier. Publish; link the raw dossier (the "receipts").
6. **Sanity check (optional):** paste the narration into NotebookLM, generate an Audio Overview; if the arc holds read by a synthetic voice, it holds when you read it.

**Tooling verdicts (from the dossier):** ADOPT Marp (free, MIT) as the default render target; Slidev if you want Vue-powered animations/code demos; Descript for transcript-based screencast editing; Gamma for a fast exec-facing variant. REJECT reveal.js and Arcade for this use case (no native notes→narration path / wrong tool). [VERIFIED — multi-agent]

---

## Quality bar

Reject any `05-dossier.md` that: has a slide headline that isn't a complete claim; has >3 bullets or any bullet >10 words; has a chart slide without its data table; has speaker notes that can't be read in ≤90s; lacks `SCENARIO:` markers (the editor can't cut without them); or hand-maintains the deck separately from the Markdown source (defeats the overlay).

## Practitioner notes

- This replaces running the YouTube (03) and presentation (04) overlays separately for the same topic — produce once here, branch only in rendering. Saves the 60–90% re-research the old multi-deliverable pattern wasted.
- For LinkedIn carousels: export the deck to PDF, drop speaker notes — the headline+3-bullets+visual structure compresses natively.
- Keep the `.md` git-tracked; it diffs cleanly and survives any SaaS shutdown.

# Overlay — PowerPoint / Conference Talk Presentations

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`
**Superseded-by:** `08-overlay-deck-and-screencast.md` — for this overlay's Phase-6 section whenever a screencast or video is also produced (see the v1.1 note below)

---

> **v1.1 note:** If your project also produces a screencast or YouTube video from the same slide content, use `08-overlay-deck-and-screencast.md` instead. Use this overlay only when producing a presentation with NO accompanying screencast or video.

---

## When to use this overlay

Apply when the dossier feeds a slide deck for:

- A conference talk or technical meetup
- A client pitch or capability presentation (consultancy)
- An internal training session or workshop
- A webinar or YouTube live presentation
- A LinkedIn carousel post (treat as a 6–10 slide deck)

Different from the YouTube overlay because slides demand **density compression** — every slide is one claim with one chart or visual, supported by a longer speaker note. The dossier produces both the slide content and the speaker notes.

---

## Phase 1 — decomposition adjustment

Add this paragraph to the Phase 1 prompt:

```
This is a conference/talk slide-deck research project.

Talk meta:
- Audience: <who — engineers / executives / clients / mixed>
- Duration: <minutes — typical 20/30/45/60>
- Setting: <conference / client pitch / webinar / internal>
- One-sentence thesis I want them to remember 24 hours later: <thesis>

Estimate slide count: roughly 1 content slide per minute + 3 framing slides 
(title, agenda, Q&A). For a 30-min talk, target 27 content slides + 3 framing = 30 slides.

Sub-questions must map to talk sections, not individual slides. A typical talk has 4-6 
sections, each containing 4-7 slides. Sub-questions should be sized accordingly.

Required focus areas:
(i) The one specific thing the audience must remember (the thesis)
(ii) Three pieces of irrefutable evidence supporting the thesis
(iii) The strongest counter-argument and how the talk addresses it
(iv) Three concrete actions the audience can take after the talk
(v) The visual: which claims need a chart, diagram, or screenshot

Disqualified sources: marketing decks, vendor demos, anything where the source has a 
financial interest in the conclusion (unless explicitly framed as such).
```

---

## Phase 2 — agent weighting

| Agent | Weight | Why |
|---|---|---|
| **Gemini Deep Research** | High | Native chart generation — useful for Phase 6 visual generation |
| **Perplexity Pro Deep Research** | High | Citation density — slides need on-screen source attribution for credibility |
| **Grok DeepSearch** | Medium-High | If the talk involves recent industry shifts, news, or community sentiment |
| **Claude (strongest available model) + web search** | Medium | Synthesis sub-questions; counter-argument identification |

For client pitches specifically: **add a NotebookLM agent** with the client's existing public-facing materials (their website, their blog posts, their case studies, any RFP they sent). This grounds the deck in their language and surfaces what they already believe.

---

## Phase 5 — output format block

Insert this into the Chairman prompt's `<output_format>` block:

```
# {Talk Title} — Slide-by-Slide Plan

## Talk meta
- Audience: ...
- Duration: ... minutes
- Setting: ...
- One-sentence thesis: ...
- Total slide count: ...

## Talk arc
- Section 1 (slides 1-N): {section title}
- Section 2 (slides N-M): ...
... etc.

## Slide deck (slide-by-slide)

### Slide 1 — Title
- Title: {compelling, ≤8 words}
- Subtitle: {clarifying, ≤12 words}
- Speaker name + affiliation
- Speaker note (~30 seconds): cold open, hook, why-now

### Slide 2 — Agenda
- 4-6 bullets corresponding to talk sections
- Speaker note (~30 seconds): roadmap

### Slide 3 — {first content slide}
- Headline: (one sentence claim — the slide title)
- Body: ≤3 bullets, ≤7 words each
- Visual: {chart type / image / diagram / code snippet} 
  - If chart: include exact data table for chart generator
  - If diagram: include ASCII or Mermaid sketch
  - If screenshot: describe what's pictured
- Speaker note (~60-90 seconds): full prose covering the claim, the evidence, the so-what
- Source: {verified URL}
- Evidence strength: VERIFIED / SINGLE-SOURCE / DISPUTED

... repeat for all content slides ...

### Slide N (final) — Summary + CTA
- One-sentence recap of thesis
- 3 concrete next steps for the audience
- Contact info / where to find more (companion dossier link)
- Speaker note (~60 seconds): close

## Q&A preparation
Five questions you should anticipate, with sourced answers:
1. Q: ...
   A: ... (source)
2. Q: ... 
... (etc.)

## Backup slides (3-5 slides for unanticipated questions)

## Speaker rehearsal notes
- Pacing target: <X words/min — typically 130-150 for technical content>
- Likely problem slides: <slides where you'll need to compress>
- Fallback if running short: <slides safe to skip>
- Fallback if running long: <slides that can absorb extra time>
```

---

## Phase 6 — output routing

### Slide generation

The dossier from Phase 5 is structured but not yet visualised. Two paths:

**Path A — Manual / mostly-AI assisted**

1. Open Gemini Deep Research one more time. Paste your slide-by-slide plan. Ask:
   ```
   For each slide marked Visual: chart, generate the Mermaid diagram code or 
   Python matplotlib code to produce that visual. Output all snippets as a 
   single markdown file with one section per slide.
   ```
   Gemini's chart generation is genuinely useful here.

2. For diagrams, paste Mermaid code into a Mermaid live editor (mermaid.live) and export as PNG/SVG.

3. For matplotlib charts, run the Python code in a notebook, save as PNG.

4. Open PowerPoint / Google Slides / Keynote. Apply your standard template.

5. For each slide:
   - Headline → slide title
   - Body bullets → slide content
   - Visual → paste the image
   - Speaker notes → paste the speaker note

6. Manual visual polish pass — your taste matters more than the AI's. Audit colour, font hierarchy, alignment.

**Path B — Bulk AI generation (faster, less polished)**

1. Use Microsoft Copilot in PowerPoint, Gemini in Google Slides, or a tool like Gamma/Beautiful.ai. Paste the structured plan. Generate first-draft slides.
2. Manual polish pass: fix anything that misrepresents the source (AI tools tend to over-simplify claims when generating slides).
3. Speaker notes still come straight from the dossier — those are usually fine without modification.

### Speaker rehearsal

1. Read the entire deck aloud at intended pace. Time it.
2. If long: mark fallback slides to skip.
3. If short: mark slides that can absorb extra time without losing structure.
4. Two full rehearsals minimum. Three if it's a paid keynote.

### Companion artifacts

Most talks benefit from giving the audience a takeaway:

1. Generate a one-page handout from the "Talk arc" + "Q&A preparation" sections.
2. Convert the dossier into a written companion essay (similar to the YouTube overlay's companion blog).
3. Pre-print or QR-link the companion essay so the audience can dig deeper after the talk.

---

## Quality bar specific to presentations

Reject any draft of `05-dossier.md` that:

1. Has any slide with more than 3 body bullets or any bullet >10 words.
2. Has a slide where the headline isn't a complete claim sentence.
3. Has a chart slide where the data table isn't included for verification.
4. Has fewer than 2 surfaced contradictions when the topic genuinely involves trade-offs.
5. Has Q&A preparation answers that aren't sourced.
6. Lacks a clear thesis sentence in the Talk meta section.

---

## Practitioner notes

- For consultancy client pitches: include a "What I'd actually do for you" slide near the end. Generic talks don't have this; consultancy pitches do. The dossier provides the evidence; this slide is the bridge to a sales conversation.
- For conference talks: budget time for the audience to take photos of charts. Each chart slide needs to be readable from the back of the room — minimum 24pt body text.
- For LinkedIn carousels: treat as 6-10 slides, no speaker notes needed. The "Headline + 3 bullets + Visual" structure compresses naturally to a carousel format.

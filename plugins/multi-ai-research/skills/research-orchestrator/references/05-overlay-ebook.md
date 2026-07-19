# Overlay — Ebook (Long-form, Multi-chapter)

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`

---

## When to use this overlay

Apply when the dossier feeds a long-form ebook publication: 8–15 chapters, 30k–80k words total. Distribution targets: PDF, EPUB, Kindle, Apple Books, Gumroad, or your own site as a paid download.

This is the **only overlay where Phase 1–5 run repeatedly** (once per chapter), with a meta-Phase 5 at the end consolidating the book. Don't try to research a whole ebook in one dossier — context-window pressure degrades quality, and chapters need different agent weightings.

---

## Phase 0 (ebook-specific) — book-level decomposition

Before running per-chapter Phase 1, run a one-time book-level decomposition prompt:

```
You are a book editor. I am writing an ebook on: <BOOK TOPIC>

Target audience: <description>
Reader's prior knowledge: <assumed baseline>
Reader's intended takeaway: <what should they be able to do after reading>
Target length: <30k / 50k / 80k words>
Target chapter count: <8-15>
Format: <how-to / narrative / reference / hybrid>

Output:
1. A book-level thesis (one sentence — the spine that every chapter must support)
2. A chapter outline: chapter number, title, one-sentence chapter thesis, target word count
3. A reader journey: which chapter introduces what concept, where dependencies are
4. A decomposition strategy: for each chapter, indicate whether it primarily needs:
   - Vendor docs / official sources
   - Peer-reviewed academic literature
   - Real-world case studies / interviews
   - Primary texts (e.g., classical works in their original language)
   - Statistical / market data
   This determines which agent weighting to use per chapter.

Save this output as `00-book-outline.md` in the dossier folder root. Each chapter then 
becomes a sub-folder: `<dossier-root>/<book-slug>/chapter-01/`, `chapter-02/`, etc.
```

Then run Phase 1–5 independently for each chapter, with Phase 1 for each chapter scoped to that chapter's sub-questions only.

---

## Phase 1 — per-chapter decomposition adjustment

Add this paragraph to the Phase 1 prompt (run once per chapter):

```
This is chapter {N} of an ebook on <BOOK TOPIC>.
Chapter thesis: <single sentence>
Target chapter word count: <2k-6k>
Section count: 4-7 (each section will become a Phase-2 sub-question)

Sub-questions must:
- Be answerable in 800-1500 words each (chapter sections)
- Cover the chapter thesis without overlapping other chapters in the book outline
- Include one "what's contested" sub-question per chapter to surface debates
- Include one "what the reader will do" sub-question for actionable content

Required focus areas vary by chapter type:
- How-to chapters: step-by-step procedure with verified examples
- Narrative chapters: case studies and stories with sourced details
- Reference chapters: comprehensive coverage with authoritative sources
- Theoretical chapters: frameworks with grounded examples

Disqualified sources: AI-summary blogs, content farms, anything not relevant to the 
book's specific level of rigour.
```

---

## Phase 2 — agent weighting (varies by chapter type)

The chapter type from the book outline determines weighting:

| Chapter type | Primary agents | Optional agents |
|---|---|---|
| **How-to / technical** | Perplexity Pro (citations), Gemini (volume) | NotebookLM with vendor docs uploaded |
| **Narrative / case study** | Grok (real-time, X discussions), Perplexity Pro | NotebookLM with prior interviews/transcripts |
| **Reference / encyclopedic** | Gemini (volume), Perplexity Pro (citations) | Elicit for academic claims |
| **Theoretical / framework** | Claude, strongest available model (synthesis), Gemini (depth) | Perplexity Pro for examples |
| **Health / longevity** | Elicit (papers), Consensus (binary), Perplexity Pro | NotebookLM with curated PDFs (McGill, Attia, etc.) |
| **Classical / non-English primary texts** | NotebookLM with vetted original-language and English texts uploaded, Felo (multilingual), Perplexity Pro | Claude (strongest available model) for cross-language synthesis |

The book outline document specifies per-chapter weighting. Update it whenever a chapter's plan changes.

---

## Phase 5 — output format block (per chapter)

Insert this into the Chairman prompt's `<output_format>` block, run once per chapter:

```
# Chapter {N}: {Chapter title}

## Chapter thesis (one sentence — must align with book thesis)

## Chapter at a glance (3-5 bullets — what this chapter delivers)

## Hook (200-400 words)
{Story / anecdote / stake-setting / surprising claim}

## Section 1: {sub_question_1 reframed as section heading}
{800-1500 words, with inline citations as markdown footnotes [^1] [^2]}

## Section 2: ...
... continue for all sub-questions ...

## Chapter summary (3-5 bullets)

## Reader action — what to do with this
{Specific, concrete takeaways the reader can apply}

## What this chapter does NOT cover
{Explicit list — sets up the next chapter or marks scope boundaries}

## Footnotes / chapter sources
[^1]: <verified URL or citation>
[^2]: ...

## Cross-references to other chapters
- See chapter X for {topic Y}
- See chapter Z for {topic W}
```

---

## Phase 5 (meta) — book-level consolidation

After all chapter dossiers are complete, run one final Chairman pass to ensure book-level coherence:

```
You are the book editor. Inputs: all chapter dossiers from <book slug> + the 
00-book-outline.md.

Produce:

1. **Book-level introduction (Preface)** — 800-1500 words
   - Why this book, why now
   - Who the book is for
   - How to read this book (linear vs reference vs cherry-picking)
   - The book's thesis as a one-page argument

2. **Cross-chapter consistency check**
   - Flag any chapter that contradicts another chapter's claims
   - Flag any chapter that repeats material from another (suggests merging or trimming)
   - Flag any cross-reference that points to wrong chapter
   - Verify the book's thesis is consistently supported across all chapters

3. **Index of key claims**
   - Every numbered or significantly-sourced claim with chapter:section pointer
   - For non-fiction reference books, this is the searchable backbone

4. **Bibliography**
   - All footnotes deduped across chapters
   - Formatted in {Chicago / APA / Harvard / informal-with-URLs}
   - Live-linked URLs for digital editions

5. **Table of contents**
   - Auto-generated from chapter titles + section H2s

6. **Acknowledgments / methodology note**
   - Brief description of the research process (which gives the book legitimacy)
   - Optional: brief note on the AI-assisted research methodology (some readers care)

Save as `00-book-meta.md` in the dossier root.
```

---

## Phase 6 — output routing (ebook production)

### From dossier folder to publishable ebook

```bash
# In <dossier-root>/<book-slug>/
ls
# 00-book-outline.md
# 00-book-meta.md
# chapter-01/05-dossier.md
# chapter-02/05-dossier.md
# ...

# Concatenate chapters in order
cat 00-book-meta.md chapter-*/05-dossier.md > book-manuscript.md
```

### EPUB generation

```bash
pandoc book-manuscript.md \
  -o book.epub \
  --metadata title="<Book Title>" \
  --metadata author="<author>" \
  --metadata lang="en" \
  --toc \
  --toc-depth=2 \
  --epub-cover-image=cover.jpg \
  --css=ebook-style.css
```

### PDF generation (for paid PDF distribution or print-on-demand)

```bash
pandoc book-manuscript.md \
  -o book.pdf \
  --pdf-engine=xelatex \
  --metadata title="<Book Title>" \
  --metadata author="<author>" \
  --toc \
  --toc-depth=2 \
  --highlight-style=tango \
  -V geometry:margin=1in \
  -V documentclass=book \
  -V mainfont="Source Serif Pro" \
  -V monofont="JetBrains Mono"
```

### Kindle Direct Publishing

1. `pandoc book-manuscript.md -o book.docx --toc --toc-depth=2`
2. Open in Word, manually verify formatting (Kindle is fussy)
3. Upload to KDP, fill in metadata, set price
4. Use the verified-sources file as the basis for the back-matter "Sources" section

### Audiobook draft

1. Upload `book-manuscript.md` (or per-chapter dossiers) to NotebookLM
2. Generate Audio Overview per chapter
3. Use as audiobook draft — needs human re-recording for production quality, but the script timing and emphasis are useful

### Companion landing page (WordPress + Elementor)

Use the `06-overlay-wordpress-seo.md` overlay to produce a sales/landing page from the book's preface + chapter list + 1–2 sample chapter excerpts.

---

## Quality bar specific to ebooks

Reject any chapter dossier that:

1. Repeats more than ~10% material from another chapter (suggests poor decomposition; either merge chapters or trim).
2. Has a section under 600 words (under-developed) or over 2000 words (split into sub-sections or split chapter).
3. Lacks a "what this chapter does NOT cover" section (this is the chapter scope discipline).
4. Has fewer than 5 footnoted citations (under-sourced for a published book).
5. Cites the same source for >3 claims (over-reliance signal).

Reject any book-level meta document that:

1. Has chapters whose theses don't ladder up to the book thesis.
2. Has cross-chapter contradictions that aren't acknowledged in the relevant chapters.
3. Has a bibliography with broken or unverified URLs.
4. Lacks a methodology note (legitimacy signal for non-fiction).

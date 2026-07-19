# Overlay — WordPress + Elementor SEO Articles

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`

---

## When to use this overlay

Apply when the dossier feeds a search-optimised article published on a WordPress site (Elementor or any block-builder). Targets:

- Your blog (technical audience)
- Health/biohacking articles for general audience sites
- A consultancy blog (B2B authority content)
- Any keyword-driven content where ranking on Google is the goal

This overlay is distinct from the YouTube and ebook overlays because the primary success metric is **organic search ranking** — which constrains structure (H2-driven), keyword placement, length, and internal linking strategy.

---

## Pre-Phase-1 — keyword research (do this BEFORE decomposition)

A WordPress article is keyword-led. Before running Phase 1, gather:

1. **Primary keyword** — the search query you want to rank for. One per article.
2. **Search intent** — informational, commercial, or transactional. Determines structure and CTA strategy.
3. **Top-10 SERP analysis** — what the existing top results look like. Use Perplexity or Grok in normal (non-Deep) mode for this:
   ```
   What are the current top 10 Google search results for the keyword "<keyword>"? 
   For each result, give me the URL, title, word count estimate, and the main angle.
   ```
4. **Differentiation hook** — what your article will say that the top 10 don't.
5. **Article length target** — match or exceed top-10 average. Typical: 1500 / 2500 / 4000 words.
6. **Secondary keywords** — 3–5 related terms for natural inclusion.

Save this as `00-keyword-brief.md` in the dossier folder. It feeds into Phase 1.

---

## Phase 1 — decomposition adjustment

Add this paragraph to the Phase 1 prompt:

```
This is a WordPress SEO article for {site name / audience}.

Primary keyword: <keyword>
Search intent: <informational / commercial / transactional>
Target word count: <1500 / 2500 / 4000>
Differentiation hook: <what this article says that the top 10 don't>

Sub-questions must map to H2 headings in the final article. Aim for 5-8 H2s — 
which is also 5-8 sub-questions. Each H2 should answer a specific question a 
searcher might have.

Required focus areas:
(i) Direct answer to the primary keyword (must appear in first ~150 words)
(ii) Sub-questions that the top-10 results address (so we cover the basics)
(iii) Sub-questions the top-10 results address POORLY or NOT AT ALL (the 
     differentiation — this is where ranking is won)
(iv) FAQ section sourced from People Also Ask
(v) Related-keyword H2s for capturing long-tail traffic

Disqualified sources: AI-summary content farms (which rank but provide no value), 
press release distributors, anything that's been republished verbatim across multiple 
sites (ranking spam).
```

---

## Phase 2 — agent weighting

| Agent | Weight | Why |
|---|---|---|
| **Perplexity Pro Deep Research** | High | Citation density for "show your work" articles; SERP-style structure |
| **Gemini Deep Research** | High | Source volume for comprehensive coverage |
| **Grok DeepSearch** | Medium | Real-time / recent angles competitors haven't picked up yet |
| **Claude (strongest available model) + web search** | Medium | Synthesis / framework sub-questions |
| **Perplexity in standard mode** (additional) | High | Run a separate query for "top 10 results for <keyword>" — surfaces what competitors are saying so the dossier can deliberately exceed/differentiate |

For **commercial intent** keywords (where searchers are evaluating products): add explicit Phase-2 sub-questions for vendor pricing, feature comparison, and recent reviews. Use the dossier as the basis for an evidence-based comparison rather than affiliate-link spam.

For **transactional intent** keywords (where searchers are ready to buy): the article exists to support a CTA. Phase 2 should surface specific objections the searcher would have at this stage, so the article addresses them.

---

## Phase 5 — output format block

Insert this into the Chairman prompt's `<output_format>` block:

```
# {Article Title — incorporates primary keyword, ≤60 chars}

## SEO meta (above-the-fold for editor reference)

- Primary keyword: <keyword>
- Search intent: informational / commercial / transactional
- Secondary keywords: <3-5>
- Target word count: <1500/2500/4000>
- Meta description (≤155 chars): ...
- URL slug: <kebab-case, ≤4 words, includes primary keyword>
- Featured image alt text: ...
- Schema type: Article / HowTo / FAQ / Review / Recipe (pick one)

## Article body

{The body of the article — see structure below}

### <h1>: {Primary keyword reframed as compelling title}

### Hook (first paragraph, must include primary keyword in first sentence, 80-150 words)

The hook directly answers the primary keyword's intent. For informational queries: 
state the answer immediately, then explain. For commercial: name the top 3 options 
and the criteria you used. For transactional: name the recommendation and link.

### H2: {sub_question_1 reframed as keyword-rich heading}

200-400 words. Conversational. Inline links to verified sources from `04-verified-sources.md`. 
One image or visual per major H2 (specify in [IMAGE: ...] tags).

### H2: {sub_question_2}
...

### H2: {sub_question_N}

### H2: Frequently Asked Questions

(Generate 5-7 FAQ items from People Also Ask scraping — Perplexity can do this. 
Each Q+A is short, ~50-100 words, optimised for featured-snippet capture.)

- **Q: ...**  
  A: <50-100 word answer>
- **Q: ...**  
  A: ...

### Conclusion (recap + CTA)

100-200 words. Recap the differentiation hook. Soft CTA matched to search intent.

---

## Internal linking suggestions (3-5 from the existing site, manual)

| Anchor text in this article | Linked page | Reason |
|---|---|---|
| <anchor 1> | <internal URL> | <semantic relationship> |
| ... | ... | ... |

## External authoritative links (3-5 verified)

- <URL> — <one-sentence reason>
- ...

## Schema markup (FAQ schema JSON-LD ready to paste)

{Auto-generate JSON-LD from the FAQ section above. The Chairman can produce this 
verbatim using the standard schema.org/FAQPage structure.}

## Featured image prompt

For DALL-E / Midjourney / stock search:
"<descriptive prompt — ≤30 words>"

If using stock: keyword for Unsplash/Pexels search: "<keyword>"

## Distribution checklist (post-publish)

- [ ] Submit URL to Google Search Console for indexing
- [ ] Add to internal linking from the 3 highest-authority existing pages
- [ ] Share to LinkedIn (carousel from key claims)
- [ ] Share to relevant subreddit / community (only if natively useful)
- [ ] Add to email newsletter
- [ ] Re-purpose the differentiation hook as a Twitter/X thread
```

---

## Phase 6 — output routing (WordPress + Elementor)

### Step-by-step publish workflow

1. **Open WordPress admin → Posts → Add New.**

2. **Switch to the Block Editor (Gutenberg) initially**, even if the final layout will use Elementor:
   - Paste the article body markdown into a single Markdown block (or use a Markdown plugin).
   - Gutenberg auto-converts H2/H3/lists/links to native blocks. 
   - This is faster than building Elementor blocks one at a time.

3. **Save as draft, then switch to Elementor edit mode:**
   - Apply your standard Elementor template (typography, hero, CTA blocks).
   - Wrap the body content in your standard layout (sidebar, breadcrumbs, related posts).
   - Drag-and-drop image blocks where `[IMAGE: ...]` markers exist; replace with actual images.

4. **Schema markup:**
   - Add a Custom HTML widget at the bottom of the post.
   - Paste the JSON-LD block from `05-dossier.md`.

5. **SEO plugin (Yoast / Rank Math):**
   - Set primary keyword = the keyword from `00-keyword-brief.md`.
   - Set meta description from the dossier.
   - Set URL slug from the dossier.
   - Set focus keyphrase, validate green-light score (target 80+).

6. **Featured image:**
   - Generate via DALL-E / Midjourney using the prompt in the dossier, OR
   - Source from Unsplash/Pexels using the keyword.
   - Set alt text from the dossier.

7. **Internal linking pass:**
   - Use the 3-5 internal links from the dossier's "Internal linking suggestions".
   - Plus reverse: edit those linked pages to add a link back to this new article (mutual linking helps both pages).

8. **Publish.**

9. **Submit URL to Google Search Console** for fast indexing.

10. **Post-publish distribution:** work through the checklist in the dossier.

### For high-stakes content (consultancy authority articles)

Add a publishing-day quality pass:

- Have one human (you or a colleague) read the article cold for tone and accuracy.
- Run the article URL through one final Perplexity Pro query: *"Summarise the article at <URL> and check for any factual claims that don't match current sources."* This catches anything that's drifted between research and publish.

---

## Quality bar specific to WordPress SEO articles

Reject any draft of `05-dossier.md` that:

1. Has H2s that don't include the primary keyword or a close variant somewhere in the H2 text.
2. Doesn't directly answer the primary keyword's intent in the first 150 words.
3. Has fewer than 3 differentiation claims vs the top-10 SERP.
4. Lacks an FAQ section (these capture featured-snippet traffic; non-negotiable for informational keywords).
5. Has internal-linking suggestions that point to non-existent pages on your site.
6. Has fewer than 5 verified external citations (under-sourced — Google's helpful-content updates penalise this).
7. Is shorter than 80% of the top-10 SERP average word count (Google interprets short content as thin).
8. Cites the same source for >2 claims (over-reliance signal).

---

## Practitioner notes

- Your blog content can mostly recycle dossiers from the YouTube overlay — produce both deliverables from the same research pass. The YouTube companion blog post is essentially this overlay's output; the SEO overlay just adds more keyword discipline.
- For health content sites: the FAQ schema is especially valuable — health queries have the highest People Also Ask coverage in Google.
- For consultancy content: the dossier becomes a legitimate authority asset. Publish with author byline showing your professional credentials. The audit trail (verified sources, rejected sources, contradictions surfaced) is implicit but you can make it explicit by linking to the raw dossier on GitHub for the rare reader who wants to see your work.
- WordPress AI plugins (Bertha, AI Engine, etc.) are not substitutes for this workflow — they generate but don't research. The differentiation of this overlay is the multi-agent research that produces the dossier; the WP step is just routing.

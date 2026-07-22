# Overlay — Health Content (Low Back Pain, Longevity, Focus, Biohacking)

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`  
**v1.3 (2026-07-22):** the final-dossier NotebookLM source-grounding pass moved from Phase 4 (where `05-dossier.md` does not yet exist) to a mandatory, blocking Phase-5 exit check with SHA256 invalidation on overwrite.

---

## When to use this overlay

Apply when the dossier covers any health-related topic where you make claims that affect what readers do with their bodies. This includes:

- Low back pain protocols for lifters / weightlifters / CrossFit athletes
- Longevity interventions (supplements, fasting, sleep, exercise modalities)
- Focus / cognition / nootropics
- Recovery, mobility, sleep optimisation
- General biohacking / "body optimisation" content

This is the **highest-stakes overlay** in the stack. Health misinformation harms readers. The verification discipline is correspondingly stricter, the agents weighted differently, and Phase 4 is non-negotiable.

---

## Phase 1 — decomposition adjustment

Add this paragraph to the Phase 1 prompt:

```
This is a health/biohacking research project. The output may influence what readers 
do with their bodies. The verification bar is therefore higher.

Required disciplines:

(1) EVIDENCE STRENGTH TAGGING. Every claim must be tagged with one of:
    - STRONG: meta-analysis or RCT (randomised controlled trial)
    - MODERATE: cohort study, controlled study, prospective observational
    - WEAK: case report, anecdote, mechanism-only reasoning, n-of-1, expert opinion 
      without empirical backing

(2) RECENCY. Reject any source older than 2020 unless it's a foundational text 
    (e.g., Stuart McGill's spine work, peer-reviewed exercise science textbooks). 
    Health science evolves; old "common knowledge" gets overturned routinely.

(3) DOMAIN AUTHORITY. Required source domains: 
    - PubMed (pubmed.ncbi.nlm.nih.gov)
    - Cochrane Reviews
    - Major medical journals (BMJ, Lancet, NEJM, JAMA, JOSPT for ortho)
    - Peer-reviewed exercise science journals
    - Authoritative practitioners with citation chains (McGill, Attia, etc.)
    
    Disqualified: Healthline / Verywell / WebMD (aggregators, not primary), random blogs, 
    YouTube fitness influencers without citation chains, supplement-company white papers, 
    Reddit anecdote threads.

(4) DISCLAIMER REQUIREMENT. The dossier must end with a non-negotiable disclaimer block 
    distinguishing information from medical advice and recommending clinician consultation 
    for personal application.

(5) MECHANISM vs OUTCOME. Distinguish claims about why something works (mechanism) from 
    claims about whether it works in humans (outcome). Mechanism evidence does not 
    establish outcome.

Sub-questions must include:
- What the strongest evidence (STRONG-tagged) actually shows for this intervention
- What's commonly claimed but only weakly supported (WEAK-tagged, with explicit caution)
- Where the strong evidence and popular claims diverge
- Specific protocols that pass the STRONG/MODERATE bar
- Red flags / when to stop / when to see a clinician
```

---

## Phase 2 — agent weighting (specialised health stack)

| Agent | Weight | Why |
|---|---|---|
| **Elicit (free tier)** | **High — mandatory** | Structured data extraction across 138M+ academic papers; pulls effect sizes, sample sizes, study design from RCTs in one pass |
| **Consensus (free tier)** | **High — mandatory** | Yes/no/maybe consensus signals across peer-reviewed literature for binary intervention questions |
| **Perplexity Pro Deep Research** | High | Citation density; cross-checks recent practical applications |
| **Gemini Deep Research** | Medium-High | Source volume across PubMed and journal coverage |
| **NotebookLM with curated PDFs** | High | Upload PDFs of foundational sources you've personally vetted (Stuart McGill's "Back Mechanic" / "Ultimate Back Fitness", Peter Attia's "Outlive" + his peer-reviewed papers, specific RCTs) — gives source-grounded answers within your trusted corpus |
| **Grok DeepSearch** | Low | X health discussion is predominantly anecdote; useful only for community signal annex (clearly tagged) |
| **Claude (strongest available model) + web search** | Medium | Synthesis of contradictory findings; mechanism vs outcome distinction |

**One-time setup for health research:**

1. Sign up Elicit free tier (100 paper extractions/month — sufficient for most projects).
2. Sign up Consensus free tier (25 searches/month — Pro at ~$9/mo if you exceed).
3. Build NotebookLM corpora per topic:
   - **Low back pain corpus:** Stuart McGill's books (PDFs you own), key RCTs on resistance training + back pain (NSCA, JOSPT, Spine), Beyond the Pain papers, specific protocol papers
   - **Longevity corpus:** Peter Attia's published papers, Valter Longo's papers, key fasting RCTs, sleep science (Walker), zone 2 training papers
   - **Focus / cognition corpus:** Andrew Huberman's cited primary sources (not Huberman's podcast — the *papers* he cites), nootropic systematic reviews

These corpora are reusable across multiple projects in the same domain.

---

## Phase 5 — output format block

Insert this into the Chairman prompt's `<output_format>` block:

```
# {Health topic} — Evidence-Based Protocol

## TL;DR (3 bullets, with evidence-strength tag on each)
- [STRONG] Claim 1
- [MODERATE] Claim 2
- [WEAK] Claim 3 (caveat included)

---

## What the strongest evidence shows ([STRONG] only)

For each claim:
- The claim, in plain English
- The evidence: study type, N (sample size), effect size, year
- The source citation (PubMed URL or DOI)
- The practical implication

Example:
> Resistance training reduces chronic low back pain disability scores. 
> [STRONG: meta-analysis of 18 RCTs, N=2,394, Searle et al. 2015 + replications 
> 2020-2024]
> Source: <URL>
> Implication: Strength training is a first-line intervention.

## What moderate evidence suggests ([MODERATE])

(same structure, but with cohort/observational tags)

## What's commonly claimed but only weakly supported ([WEAK])

For each weak claim, name it explicitly with the caution:
> [WEAK — anecdote / mechanism-only / single small study]
> Common claim: "<the popular claim>"
> Why it's weak: <e.g., based on n=8 case series, no RCT, contradicted by 2023 review>
> Don't base decisions on this alone.

## Practical protocol (translated from STRONG evidence to a usable plan)

### Daily / weekly routine
- Frequency: ...
- Duration: ...
- Specific exercises / interventions: ...
- Progression rules: ...

### What to track
- Objective metrics: ...
- Subjective metrics: ...
- Weekly review questions: ...

### Red flags — stop and see a clinician
- Symptom A: ...
- Symptom B: ...
- Symptom C: ...

### What this protocol does NOT address
- (Be explicit about scope limits — e.g., "not for acute injury < 6 weeks; 
  not for diagnosed disc herniation without imaging")

## Open scientific questions

Where current evidence is genuinely uncertain:
- Question 1: <status of evidence>
- Question 2: ...

## What I'm NOT covering and why

- Topic A: <why excluded — e.g., "supplements with insufficient evidence">
- Topic B: ...

## Disclaimer block (non-negotiable)

> The information in this article is for educational purposes only and is not medical 
> advice. The author is not a medical professional. The protocol described is based 
> on published research as of {date}. Individual circumstances vary; consult a qualified 
> clinician (general practitioner, physiotherapist, sports medicine doctor as appropriate) 
> before starting any new intervention, especially if you have an existing medical 
> condition, are pregnant, are taking medications, or have had recent injury or surgery. 
> The author assumes no liability for outcomes resulting from application of this 
> information.

## Sources (verified, organised by evidence strength)

### STRONG evidence (RCTs, meta-analyses)
- Citation 1 [URL] [year] [study type] [N]
- ...

### MODERATE evidence (cohort, controlled, observational)
- ...

### Foundational texts and authoritative practitioners
- McGill SM. Back Mechanic. (2015). [book reference]
- ...

### Excluded sources (with reasons)
- Source X — excluded because: <reason>
```

---

## Phase 4 — citation verification (intensified for health)

In addition to the standard Phase 4 procedure:

1. **Every RCT or meta-analysis citation** must be verified by:
   - Confirming the paper exists in PubMed (not just CrossRef)
   - Reading the abstract (or methods + results if abstract is ambiguous)
   - Confirming the study population matches the claim's target population (e.g., "RCT in elderly women" doesn't generalise to "young male lifters")
   - **Running through Scite** (https://scite.ai) — this is the critical step. Scite shows whether later papers *contradicted* the cited finding. A 2018 RCT supporting intervention X may have been refuted by a 2023 meta-analysis; Scite catches this.

2. **Every effect size or numerical claim** must trace back to a specific paper, not to a secondary source. "Studies show 30% reduction in pain" without a paper attached gets rejected.

3. **For supplement / pharmacological claims:** verify safety data alongside efficacy. Many supplements have weak efficacy and meaningful side effects; surface both.

4. Move surviving citations to `04-verified-sources.md`. Move rejected/contradicted/unsupported citations to `04-rejected.md` with explicit reasons.

The final-dossier NotebookLM source-grounding pass runs **after Phase 5 produces `05-dossier.md`** — see the Phase 5 exit check below. Phase 4 itself remains mandatory and intensified exactly as above.

---

## Phase 5 exit check — final-dossier NotebookLM source-grounding (mandatory, blocking)

Runs **after** the Chairman writes `05-dossier.md` and after the Step-5.3 CoVe decision (including any CoVe-driven overwrite), and **before any Phase 6 routing**:

1. **Upload `05-dossier.md` plus all the original source PDFs to NotebookLM.** Ask: "For each claim in the dossier, identify which uploaded source supports it, and flag any claim that cannot be traced to an uploaded source." This is the strongest source-grounding pass available.
2. This check inspects the **final dossier** for claims introduced during consolidation — the Chairman can introduce phrasing or synthesis not present in any verified source. `03-conflict-map.md` is **not** a substitute: the stated control targets the consolidated output, not the pre-consolidation conflict map.
3. Record the result in `00-context.md`: `health_phase5_exit_check: PASS` plus the SHA256 hash of the exact `05-dossier.md` that was checked.
4. **Invalidation rule:** any subsequent change to `05-dossier.md` invalidates the recorded check — the recorded hash no longer matches. Re-run this exit check against the new file before Phase 6.
5. **An unsupported claim blocks Phase 6.** Either trace it to a verified source, rewrite it to what the sources support, or delete it; then re-run the check.

---

## Phase 6 — output routing (per content type)

Health content typically branches into multiple deliverables from one dossier:

### YouTube video
Use `03-overlay-youtube-script.md` to transform the dossier. Key adaptation: keep the disclaimer in the video script itself (verbal mention), not just the description. The audience reaches you via search; some won't read the description.

### WordPress article
Use `06-overlay-wordpress-seo.md` overlay. Key adaptations:
- Schema type: `MedicalWebPage` rather than `Article` (Google prioritises authoritative medical content with proper schema)
- Author byline: include your credentials honestly (e.g., "<your profession> interested in evidence-based fitness, not a medical professional")
- Disclaimer: visible above-the-fold, not buried at the bottom
- Linked sources: every claim should have a clickable citation

### Ebook chapter
Use `05-overlay-ebook.md`. The health overlay's evidence-strength discipline carries over verbatim; the chapter just expands each STRONG/MODERATE/WEAK section into prose.

### Personal use (your own protocol notes)
Save `05-dossier.md` to your personal Obsidian / Notion / NotebookLM. Re-run the dossier annually as the literature evolves.

### Sponsored / supplement-related content
**If a deliverable involves a sponsorship or affiliate relationship:** 
- Tag the relevant claims with `[POTENTIAL-COI]` in the dossier
- Disclose the sponsorship transparently in the final deliverable
- Apply stricter rejection: the dossier can mention sponsored products only if they pass STRONG or MODERATE evidence; never WEAK
- This protects your audience and your long-term credibility

---

## Quality bar specific to health content

Reject any draft of `05-dossier.md` that:

1. Has any [STRONG] claim without a verified RCT or meta-analysis citation.
2. Has any practical protocol step not supported by [STRONG] or [MODERATE] evidence.
3. Lacks the disclaimer block.
4. Lacks "red flags / when to see a clinician" section.
5. Cites a Healthline / Verywell / WebMD / random blog for any load-bearing claim.
6. Has supplement or pharmacological claims without paired safety data.
7. Generalises from a study population to a different population without explicit caveat (e.g., elderly RCT applied to young athletes).
8. Has any claim where Scite check would show contradicting later evidence (this is why Scite verification is non-negotiable).

---

## Practitioner notes

- For injury/rehab content aimed at a training population: the differentiation vs the existing market is *applying STRONG evidence to that specific population* (e.g., lifters who have tried conservative care and want to keep training), not the general population. Many studies enroll sedentary adults; their results don't directly transfer. Phase 1 should explicitly surface the population question.
- For longevity content: the field is full of WEAK evidence dressed up as STRONG. The Chairman discipline of evidence-strength tagging is the single most valuable filter. If a topic has no STRONG evidence, say so explicitly — that itself is differentiated content.
- For focus / cognition: most nootropic claims are WEAK or based on tiny RCTs. Be especially strict here.
- **Never recommend a specific dose, drug, or supplement protocol without explicit "talk to your doctor" framing.** The legal exposure for getting this wrong is non-trivial in many jurisdictions (e.g. the UK).

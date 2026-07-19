# Prompts Library — Multi-AI Research Pipeline

**Owner:** AgenticCodingOps  
**Version:** 1.1 (2026-06-01 — Phase-2 output structure adds confidence + "what would change" + live-URL rule; Phase-3 adds the keep-matrix / no-default-peer-review note; see the project changelog)  
**Reads with:** `00-master-methodology.md`

---

## When to use this document

Every phase of the research pipeline uses one or more prompts from this library. The prompts are the load-bearing artifacts of the workflow — small changes in prompt wording produce large changes in output quality. Don't paraphrase; copy the prompt blocks verbatim and fill in `<placeholders>`.

---

## Phase 1 — Decomposition prompt

**Tool:** Claude, strongest available model (this project, fresh chat) · **Output:** `01-decomposition.md` · **Time:** ~5 min

```
You are a research architect. The research question is:

<RESEARCH_QUESTION>

Decision context: <one sentence — what will I do with this dossier?>
Time horizon: prioritise sources from 2024-2026 unless the question is intrinsically historical.

Output strict JSON with these keys:
- sub_questions: array of 4-8 atomic, independently researchable questions
- agent_assignments: array of {sub_question_id, primary_agent, secondary_agent, source_type_required}
  where primary_agent ∈ [Perplexity, Gemini, Grok, Claude, ChatGPT, DecorrelatedLane, NotebookLM, Elicit, Consensus]
  and source_type_required ∈ [official_docs, peer_reviewed, news_recent, social_signal, primary_text, vendor_pricing, repo_docs]
- disqualifying_sources: array of source patterns to reject
- success_criteria: array of bullets — what a publishable answer must include
- known_traps: array of likely failure modes for this specific topic

Do not answer the questions. Plan only.
```

**Adaptation per use case:** Each overlay file (`02-` through `08-`) adds one or two extra instructions. Apply them additively.

---

## Phase 2 — Fan-out prompt (universal across agents)

**Tools:** Perplexity, Gemini, Grok, Claude+web, ChatGPT, **+ the decorrelated lane** (DeepSeek self-hosted), optionally NotebookLM · **Run:** all in parallel browser tabs within 60s · **Output:** `02-<agent>.md`

```
Research question: <SUB_QUESTION>

Requirements:
- Cite every factual claim with a LIVE, resolvable URL (https://…). Do NOT use bare reference
  markers, footnote numbers, or tool-internal citation tokens — they do not survive copy-paste
  and make the source unverifiable. If you cannot produce a real URL, mark the claim [UNVERIFIED].
- Prioritise primary sources (vendor docs, peer-reviewed papers, official announcements) over
  secondary commentary.
- Tag each finding with a confidence level: [HIGH] / [MEDIUM] / [LOW]. You are explicitly
  permitted — and expected — to answer "insufficient evidence" rather than guess.
- Where multiple sources conflict, present both positions; do not pick a winner.
- Do not include marketing copy or vendor self-promotion as evidence.

Output structure (markdown):
1. TL;DR (3 bullets, each a verdict)
2. Findings (numbered, each with inline [https://URL] + a [HIGH/MEDIUM/LOW] confidence tag)
3. Conflicts and uncertainties
4. What would change your recommendation (the specific evidence that would flip each verdict)
5. Sources consulted (full live URL list)
6. Coverage gaps: explicit "this response does NOT cover X, Y, Z"
```

> 🆕 v1.1 changes: added the **live-URL rule** (§ requirement 1), the **confidence/abstention tag** (§ requirement 3), and section **4 "What would change your recommendation."** Rationale in CHANGELOG (#3, #7).

**Tab-by-tab procedure:**
1. **Perplexity Pro:** "Deep Research" mode. Paste Perplexity-tagged sub-questions. Submit. Next tab.
2. **Gemini Deep Research:** Deep Research mode. Paste Gemini-tagged sub-questions. Submit.
3. **Grok (SuperGrok):** DeepSearch toggle. Submit.
4. **Claude.ai (separate tab, not this project):** web search on. Submit.
5. **ChatGPT:** Deep Research mode. Submit.
6. **🆕 Decorrelated lane (DeepSeek, self-hosted/Western-hosted):** reasoning/deep mode. Point it at the analytical sub-questions; ask it to flag where it diverges from the likely Western-model consensus. Submit.
7. **NotebookLM (optional):** upload private corpus first, then run.

**🆕 Phase 2 sanity check (3 min — now includes a paste-check):**
1. No truncation. 2. Required 6-section structure present. 3. Citation density adequate. 4. **Live-URL paste-check: spot-open 3 citations per file. If they're dead markers or won't resolve, the file fails — re-export or re-run that agent before Phase 3.** 5. Confidence tags present. 6. Project constraints honoured.

---

## Phase 3 — Cross-examination / contradiction matrix prompt

**Tool:** Claude, strongest available model (this project, fresh chat) · **Output:** `03-conflict-map.md` · **Time:** ~10 min

```
Below are independent research outputs on the question: <RESEARCH_QUESTION>

<perplexity_output>…</perplexity_output>
<gemini_output>…</gemini_output>
<grok_output>…</grok_output>
<claude_output>…</claude_output>
<chatgpt_output>…</chatgpt_output>
<decorrelated_lane_output>…</decorrelated_lane_output>

Your job:
1. AGREEMENT: every claim in 2+ outputs, with which sources support it. Flag where ALL
   supporting agents share a training lineage (possible correlated-error false consensus).
2. CONFLICT: every claim where outputs disagree. Present each side with its sources.
   Do NOT pick a winner. The conflict is the value.
3. SINGLE-SOURCE: claims in only one output. Flag, don't discard.
4. GAPS: sub-questions none answered well.
5. SUSPECT-CITATIONS: URLs with implausible structure — sequential/round arxiv IDs,
   unrecognised domains, dead reference markers, auto-generated-looking paths.

Output strict markdown with those five sections. Do not synthesise yet.
```

> 🆕 v1.1: AGREEMENT step now flags same-lineage corroboration (correlated-error risk).

### 🆕 Phase 3 note — keep the matrix; do NOT add a default Phase 3.5 peer-review (v1.1)

A recurring temptation (from Karpathy's `llm-council`) is to insert an anonymized LLM-judge **peer-review/ranking** stage before the matrix. **Don't, by default.** The evidence:
- A 9-judge panel provides only ~**2 independent votes'** worth of information; its accuracy falls **8–22 points** short of the independent-voting ideal, and the **best single judge matches or beats the full panel** (arXiv 2605.29800).
- Scaling the panel or changing the aggregation algorithm doesn't fix it — the bottleneck is **correlated judges** (arXiv 2506.07962; CARE 2603.00039).
- Anonymization mitigates **self-preference** bias but does nothing for correlated errors.

A contradiction matrix is preferred because it **preserves divergence** (the deliverable) instead of voting toward consensus.

**The only sanctioned cross-rating variant — "decorrelated leave-one-out pre-sort":** if you want a pre-sort signal, have the **decorrelated lane** (DeepSeek/MoE) rate the Western models' outputs, and a Western model rate the decorrelated lane's — never a same-lineage panel rating itself. Use it as a cheap pre-sort, never as the synthesis basis. This keeps the only kind of judge diversity that the evidence says actually adds information.

---

## Phase 4 — Citation verification helper prompt

**Tool:** Claude, strongest available model · **Output:** `04-verified-sources.md` + `04-rejected.md` · **Time:** ~15 min (this prompt + manual)

```
Below is the URL list from <conflict_map>. For each URL:
1. Rate domain plausibility for the claim: HIGH / MEDIUM / LOW.
2. Flag fabrication patterns: sequential/round arxiv IDs, placeholder slugs, domain mismatches,
   dead reference markers, generated-looking paths.
3. For HIGH/MEDIUM, do not verify content — the human deep-checks the top 5 load-bearing.
4. For LOW, recommend rejection.
Output a markdown table: URL | Plausibility | Verdict | Notes.
```

**Manual verification (the highest-value 10 minutes):** open the top 5 load-bearing citations; for any specific stat or paper, **resolve the primary** (arXiv ID, DOI) and confirm it says what was claimed; for academic claims use a cross-check service. Move survivors to `04-verified-sources.md`, rejects to `04-rejected.md` (keep as audit trail).

> 🆕 v1.1 lesson: dead reference markers (e.g., `【n†…】`) and suspiciously sequential arxiv IDs were the two fabrication patterns that actually fired this cycle — weight them heavily.

---

## Phase 5 — Chairman prompt (the load-bearing prompt)

**Tool:** Claude, strongest available model (fresh chat, max effort / extended thinking) · **Output:** `05-dossier.md`

```
<role>
You are the Chairman of a multi-AI research council. You synthesise N independent research
reports into one publication-ready document. You follow instructions LITERALLY. You verify
before responding.
</role>

<inputs>
<query>{ORIGINAL_RESEARCH_QUESTION}</query>
<perplexity_report>…</perplexity_report>
<gemini_report>…</gemini_report>
<grok_report>…</grok_report>
<claude_report>…</claude_report>
<chatgpt_report>…</chatgpt_report>
<decorrelated_lane_report>…</decorrelated_lane_report>
<conflict_map>…</conflict_map>
<verified_sources>…</verified_sources>
<rejected_sources>…</rejected_sources>
</inputs>

<rules>
- Use only claims supported by 2+ independent reports OR a single report with a verified primary
  source. Treat agreement among same-lineage models as weaker than cross-lineage agreement;
  tag such claims [VERIFIED (correlated-risk)] and prefer a primary-source check.
- Mark contested claims: [CONTESTED — A says X (source); B says Y (source)]
- Mark single-source non-verified claims: [SINGLE-SOURCE — flag]
- Carry through each finding's HIGH/MEDIUM/LOW confidence tag where it affects a verdict.
- Use chain-of-verification: after drafting, list 5 verification questions on the most
  load-bearing claims, answer them from scratch, then revise to match.
- Paraphrase. Quote ≤15 words from any single source. Never string two short quotes.
- Every numerical claim names its source inline.
- Do NOT smooth over disagreements. Disagreement is the value.
- Do not introduce claims absent from the inputs. Do not cite any URL rejected in Phase 4.
</rules>

<output_format>
{INSERT THE USE-CASE-SPECIFIC OUTPUT FORMAT FROM THE RELEVANT OVERLAY — see 02-08}
</output_format>
```

> 🆕 v1.1: rules now include the correlated-risk tag and confidence carry-through.

Set Claude to maximum effort / extended thinking before submitting. Phase 5 is where rigour matters most.

---

## Phase 5 add-on — Chain-of-Verification (CoVe) self-check

```
You produced a dossier above. Now run Chain-of-Verification:
Step 1 (PLAN): List exactly 5 verification questions whose answers, if wrong, would invalidate
the most load-bearing claims. Frame them answerable without seeing the draft.
Step 2 (ANSWER): Without re-reading your dossier, answer each from the inputs only.
Step 3 (RECONCILE): For every disagreement, replace the dossier claim with the VQ-grounded
version and mark [VERIFIED] or [CORRECTED].
Output the revised dossier + a numbered list of corrections.
```

---

## Phase 6 — Output routing prompts

Use-case-specific. See the relevant overlay (`02-08`). For deck + screencast, use the unified `08-overlay-deck-and-screencast.md` (supersedes the Phase-6 sections of `03` and `04`).

---

## Prompt-tuning principles

1. **Don't paraphrase the rules block.** Literal wording enforces the quality bar.
2. **Always specify the time horizon.** "2024–2026 sources only" prevents outdated data.
3. **Always specify disqualifying sources.** Explicit rejection lists raise quality.
4. **For technical topics, name primary-source domains** (docs.microsoft.com, registry.terraform.io, github.com over blog domains).
5. **For health topics, demand evidence-strength tagging.**
6. **For consultancy/client deliverables, set the Chairman to maximum effort.**
7. **🆕 Engineer diversity via lineage, not count.** Adding more same-lineage agents adds correlated error, not signal — always include the decorrelated lane and weight cross-lineage agreement higher (arXiv 2506.07962, 2605.29800).

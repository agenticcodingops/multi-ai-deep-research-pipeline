# Prompts Library — Multi-AI Research Pipeline

**Owner:** AgenticCodingOps  
**Version:** 1.3 (2026-07-22 — Phase-2 gains the machine-checked OUTPUT FORMAT skeleton; sub-question range widens to 4-12; ground truth admits operator-private markers; deferred-prompt key spec named. v1.2 (2026-07-21) made the Phase-1 spec canonical (lane roles, ground truth, contaminant audits, deferred placeholders), added the Phase-2 output sentinel + ground-truth block and the Phase-3 sentiment-lane rule + conditional DCI tally; see the plugin CHANGELOG. v1.1 (2026-06-01) added confidence + "what would change" + live-URL rule + the keep-matrix note)  
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

Output strict JSON with these keys (this is the canonical Phase 1 output spec, v1.2 / schema_version 2):
- schema_version: 2
- sub_questions: array of 4-12 atomic, independently researchable questions, each an object
  {id ("SQ1"…), question, verdict_forced, falsifiable} — verdict_forced states the decision the
  answer must land on (a recommendation plus a confidence level, never a summary); falsifiable
  must be true. Reject any sub-question whose best possible answer is a summary.
- lane_roles: array of {lane_id, agent, role, lineage, execution_surface}
  where lane_id is the lowercase slug used in the dossier filenames (02a-prompts-<lane_id>.md)
  and must match ^[a-z0-9][a-z0-9_-]{0,63}$ (never a Windows reserved device name),
  role ∈ [evidence, sentiment, synthesis, decorrelated],
  lineage ∈ [Anthropic, OpenAI, Google, xAI, decorrelated, mixed],
  and execution_surface is a named product (where the operator runs the prompt), or one of:
  browser-agent, orchestrator-local, manual
- phase_2_prompts: array of {sub_question_id, agent, lane_id, ready_to_paste_prompt} — the
  CANONICAL statement of who researches what; each prompt fully formed, zero placeholders,
  and carrying the COMPLETE Phase 2 contract in its own text: the sentinel instruction
  (the token ===BEGIN LANE OUTPUT=== named inline in a sentence, never on its own line),
  all six output section names, the confidence-tag, live-URL, primary-source and
  coverage-gaps rules, the literal OUTPUT FORMAT skeleton (reproduced at the end of this
  prompt — copy it into every prompt verbatim), and the filled ground-truth block when
  claims exist. A prompt that
  merely references the contract will fail the Phase 2 gate when the agent, following only
  what it was pasted, omits the sentinel or the section structure.
- agent_assignments: array of {sub_question_id, primary_agent, secondary_agent, source_type_required}
  where primary_agent ∈ [Perplexity, Gemini, Grok, Claude, ChatGPT, DecorrelatedLane, NotebookLM, Elicit, Consensus]
  and source_type_required ∈ [official_docs, peer_reviewed, news_recent, social_signal, primary_text, vendor_pricing, repo_docs]
  — DERIVED from phase_2_prompts and required to agree with it exactly: every (sub-question,
  agent) pair implied by a non-null assignment has exactly one prompt, and no prompt lacks an
  assignment
- lanes_unavailable: array — one line per useful lane skipped because the operator lacks access
- inputs / input_audits (when input files were supplied): inputs is an array of {input_id, name,
  classification ∈ [trusted, under_scrutiny], contaminants (optional array of strings the
  operator does not want propagated)}; input_audits holds one audit block per under-scrutiny
  input, keyed by input_id. Two-tier contaminant rule: an audit block MUST be able to name the
  contaminant it reports; NO ready_to_paste_prompt may carry it.
- ground_truth (when the operator recorded ground-truth claims): array of {claim_id ("GT1"…),
  statement, metric_definition, status ∈ [verified, asserted], source_url (https; or null /
  an operator-provenance marker such as "operator-private-sample" when the claim derives
  from an operator-private dataset — such claims are always status asserted)} — carried
  verbatim from 00-context.md, tags as verified at Step 0.6
- deferred_phase_prompts (optional): prompts for later passes. Only two phases may defer
  (2.5 Debate, 4.5 Red Team). Each entry is an object {phase, prompt_template,
  declared_placeholders}: phase is the JSON number 2.5 or 4.5 (a number, never the string
  "2.5"), prompt_template is the complete prompt text as a single string (this exact key
  name — never ready_to_paste_prompt, which is reserved for staged Phase-2 prompts), and
  declared_placeholders must list exactly the tokens the template carries (delimiters
  included) — and that set may contain nothing else. The ONLY sanctioned placeholder token
  is "<DRAFT_RECOMMENDATION>", permitted solely on the phase-4.5 Red Team entry (filled at
  Step 4.5 before hand-off).
- disqualifying_sources: array of source patterns to reject
- success_criteria: array of bullets — what a publishable answer must include
- known_traps: array of likely failure modes for this specific topic

Assignment rule: maximise distinct training lineages before adding depth within a lineage, and
assign against the operator's real agent-access inventory (provided in this prompt), never an
assumed stack. Justify in one line any available lineage left unused. Every sub-question needs
at least 2 evidence-bearing lanes (role evidence or decorrelated); a sentiment lane may carry
community-signal sub-questions but never a load-bearing evidence question alone.

The OUTPUT FORMAT skeleton every ready_to_paste_prompt must carry verbatim:
OUTPUT FORMAT (machine-checked — follow literally):
===BEGIN LANE OUTPUT===   <- exactly this, alone, as your very first line
## TL;DR
- <verdict bullet — three of these>
## Findings
1. [HIGH] <one-sentence finding>. Source: https://example.com/evidence
2. [MEDIUM] <next finding>. Source: https://example.org/report
3. [LOW] <third finding — at least 3 findings items>. Source: https://example.net/data
## Conflicts and uncertainties
## What would change your recommendation
## Sources consulted
- <at least 3 distinct https URLs, one per line>
## Coverage gaps
Headings are plain full lines with nothing after the name. Findings are plain "1." lines —
at least three of them, no blockquotes, no code fences anywhere in the answer — each with
its own [HIGH]/[MEDIUM]/[LOW] tag and a live https URL.

Do not answer the questions. Plan only.
```

**Adaptation per use case:** Each overlay file (`02-` through `08-`, or `13-` for decision research) adds one or two extra instructions. Apply them additively.

---

## Phase 2 — Fan-out prompt (universal across agents)

**Tools:** Perplexity, Gemini, Grok, Claude+web, ChatGPT, **+ the decorrelated lane** (DeepSeek self-hosted), optionally NotebookLM · **Run:** all in parallel browser tabs within 60s · **Output:** `02-<agent>.md`

```
Research question: <SUB_QUESTION>

Requirements:
- Begin your response with the exact line ===BEGIN LANE OUTPUT=== on its own line, before
  anything else — including before any restatement of this prompt. Everything before that line
  is treated as echoed prompt and ignored by the quality gate.
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

OUTPUT FORMAT (machine-checked — follow literally):
===BEGIN LANE OUTPUT===   <- exactly this, alone, as your very first line
## TL;DR
- <verdict bullet — three of these>
## Findings
1. [HIGH] <one-sentence finding>. Source: https://example.com/evidence
2. [MEDIUM] <next finding>. Source: https://example.org/report
3. [LOW] <third finding — at least 3 findings items>. Source: https://example.net/data
## Conflicts and uncertainties
## What would change your recommendation
## Sources consulted
- <at least 3 distinct https URLs, one per line>
## Coverage gaps
Headings are plain full lines with nothing after the name. Findings are plain "1." lines —
at least three of them, no blockquotes, no code fences anywhere in the answer — each with
its own [HIGH]/[MEDIUM]/[LOW] tag and a live https URL.
```

> 🆕 v1.1 changes: added the **live-URL rule** (§ requirement 1), the **confidence/abstention tag** (§ requirement 3), and section **4 "What would change your recommendation."** Rationale in CHANGELOG (#3, #7).
> v1.2: added the **output sentinel** (first requirement). Agents routinely restate the prompt before answering; because the prompt itself quotes the confidence tags and standing rules, any check run over the whole file passes on the echo alone. All structural gates score only what follows the sentinel.

### Ground-truth block (v1.2 — prepend to every Phase 2 prompt when claims exist)

When the orchestrator recorded ground-truth claims (Step 0.3, verified at Step 0.6), prepend this block to every `ready_to_paste_prompt`, filled from `00-context.md`:

```
<ground_truth>
The operator asserts the following claims. Tag semantics:
[GROUND-TRUTH-VERIFIED] — re-checked against its source URL this session. This overrides your
research: if your findings contradict it, REPORT the contradiction explicitly, tagged
[CONTRADICTS-GROUND-TRUTH], with your source — but do not substitute your own figure.
[GROUND-TRUTH-ASSERTED] — operator-supplied, not re-verified this session. Treat as a strong
prior: you may contradict it, but only with a cited primary source. Claims from the
operator's own private dataset carry operator-private-sample in place of a source URL;
they are always ASSERTED.
Each claim states its metric definition. Verify against that definition — not a lookalike
metric (a rank change is not a volume change).
Claims (one per line): claim_id | statement | metric definition | source URL | tag
</ground_truth>
```

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

> v1.2 — how these checks are scored: every structural check (2, 3, 5) is computed on the **answer only** — the text after the `===BEGIN LANE OUTPUT===` sentinel — never on the whole file, because an echoed prompt satisfies every substring check by itself. Dead markers include `[n]`, `[^n]` (Perplexity's default export), `【n†…】`, and references concealed in hidden `<span style="display:none">` blocks; escaped tags like `\[HIGH\]` count as tags after normalisation. The orchestrator skill runs these checks mechanically (`scripts/gate_phase2.py`) and treats "the output claims a section the structural check cannot find" as a failure in its own right.

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
   A sentiment lane (role "sentiment" in lane_roles) may NEVER constitute one of the 2+
   outputs required for AGREEMENT. Report sentiment-lane concurrence separately as
   [SENTIMENT-CONCUR], which is not corroboration.
2. CONFLICT: every claim where outputs disagree. Present each side with its sources.
   Do NOT pick a winner. The conflict is the value.
3. SINGLE-SOURCE: claims in only one output. Flag, don't discard.
4. GAPS: sub-questions none answered well.
5. SUSPECT-CITATIONS: URLs with implausible structure — sequential/round arxiv IDs,
   unrecognised domains, dead reference markers, auto-generated-looking paths.
6. DCI TALLY (only when overlay 13 is active): three integers — contradictions, corrections,
   unique insights. No commentary.

Output strict markdown with those sections — five, six when the DCI tally is requested.
Do not synthesise yet.
```

The six input blocks shown are the standard set: include one `<lane_id>_output` block for every lane that actually ran (project-specific lanes included), plus one `<lane_id>_debate_output` block per lane when the Debate pass (Phase 2.5) ran.

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
<ground_truth>… (when recorded — include the tag semantics block)</ground_truth>
<debate_reports>… (when the Phase 2.5 Debate pass ran)</debate_reports>
<red_team_findings>… (when the Phase 4.5 Red Team pass ran)</red_team_findings>
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
- Honour ground-truth tags where a <ground_truth> block is present: [GROUND-TRUTH-VERIFIED]
  claims override contradicting reports — carry any [CONTRADICTS-GROUND-TRUTH] finding into
  the dossier as a flagged contradiction, never silently substitute either figure.
  [GROUND-TRUTH-ASSERTED] claims are strong priors that a cited primary source may overturn.
- Do not introduce claims absent from the inputs. Do not cite any URL rejected in Phase 4.
</rules>

<output_format>
{INSERT THE USE-CASE-SPECIFIC OUTPUT FORMAT FROM THE RELEVANT OVERLAY — see 02-08, or 13 (Decision Brief) for decision research}
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

Use-case-specific. See the relevant overlay (`02`–`08`, or `13` for decision research). For deck + screencast, use the unified `08-overlay-deck-and-screencast.md` (supersedes the Phase-6 sections of `03` and `04`).

---

## Prompt-tuning principles

1. **Don't paraphrase the rules block.** Literal wording enforces the quality bar.
2. **Always specify the time horizon.** "2024–2026 sources only" prevents outdated data.
3. **Always specify disqualifying sources.** Explicit rejection lists raise quality.
4. **For technical topics, name primary-source domains** (docs.microsoft.com, registry.terraform.io, github.com over blog domains).
5. **For health topics, demand evidence-strength tagging.**
6. **For consultancy/client deliverables, set the Chairman to maximum effort.**
7. **🆕 Engineer diversity via lineage, not count.** Adding more same-lineage agents adds correlated error, not signal — always include the decorrelated lane and weight cross-lineage agreement higher (arXiv 2506.07962, 2605.29800).

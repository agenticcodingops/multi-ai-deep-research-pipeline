# Overlay — Deliberation Modes (decision pressure-testing)

**New in v1.1 (2026-06-01); v1.3 (2026-07-22) adds the legal-layering rule and the layered-base Phase-6 transform contract.** **Reads with:** `00-master-methodology.md` and `01-prompts-library.md`.
**Supersedes:** the pre-v1.1 routing of personal/decision research (use case 8) through `06-overlay-wordpress-seo.md` (runbook 11, lesson 8).
**Origin:** patterns adapted from Suprmind's orchestration modes + Adjudicator (studied as *patterns*, not endorsed as a product — its self-published benchmarks remain vendor content per Phase-4 hygiene). Reimplemented as manual prompt templates for our existing fan-out.

> **Numbering note:** originally drafted as `09-`, which collided with `09-cowork-skills-setup.md`; renamed to `13-overlay-deliberation-modes.md` on merge for a clean sequence.

---

## When to use this overlay

Apply on top of the normal pipeline when the dossier supports a **decision** (go/no-go, build/buy, strategy, launch, investment) rather than a pure write-up. These modes are *additional between-phase passes*, not replacements: Debate runs at **Phase 2.5** (between fan-out and the contradiction matrix), Red Team at **Phase 4.5** (between citation verification and the Chairman, sharing that slot with the optional eval gate). They pair naturally with the WordPress/YouTube overlays when the content itself is a decision piece.

**Legal layering (v1.3):** this overlay may be **layered** on a base overlay only for use cases 1–3 and 5–7 (spec-driven dev, YouTube, presentation, WordPress SEO, health, deck+screencast), and only when the work is genuinely decision-shaped and the operator confirms it. **Never layer it on ebook (use case 4):** the ebook overlay runs Phases 1–5 once per chapter and produces no single book-level `05-dossier.md` for a Decision Brief to consolidate. If a decision and an ebook are both wanted, run two linked kickoffs — the decision first, then the ebook consuming its outputs as classified inputs. For use case 8 (decision research) this overlay is the **primary**, not a layer (next section); layering it on use case 8 is redundant and illegal.

**What we already have (do NOT re-import):** Suprmind's *Super Mind* = our Phase-2 fan-out + Phase-3 contradiction matrix + Phase-5 chairman; *Research Symphony* = our full 6-phase pipeline; *Sequential* (each AI reads the prior) is **rejected as a default** — our verified evidence shows sequential hand-offs degrade planning tasks and amplify correlated error (arXiv 2506.07962, 2605.29800; Google scaling synthesis). We fan out in parallel on purpose. *Targeted/@mentions* = our deep/light agent assignment.

**The three genuinely new patterns worth adopting:** Red Team, Debate (decorrelated), First Principles — plus the **Adjudicator-style Decision Brief** output and an optional **DCI** score.

---

## When 13 is the primary overlay

Use case 8 (personal / market decision research) runs this overlay as the **primary**, not as a layer on another overlay. The orchestrator resolves the three sections below by name.

### Phase 1 — decomposition adjustment

Use the First Principles prompt (see the First Principles mode below) as the decomposition variant whenever convention is suspect. Sub-questions must map to the **decision's real axes** — cost, risk, reversibility, fit against the operator's actual constraints — rather than to a survey of the topic. Every sub-question must demand a **verdict, not a description**: phrase each so its answer is a recommendation plus a confidence level, and reject any sub-question whose best possible answer is a summary.

### Phase 5 — output format block

Use the Adjudicator-style Decision Brief schema from the "Output — Adjudicator-style Decision Brief (Phase-5 Chairman variant)" section below as the Chairman's output format block, including the disagreement-classification rules that precede it.

### Phase 6 — output routing

The Decision Brief is the **terminal artifact**: it exists to settle the operator's own decision, and routing ends when the operator records the GO / NO-GO / GO-WITH-CONDITIONS verdict and executes the Next Action. Where a secondary deliverable is wanted (sharing or presenting the decision), route the same `05-dossier.md` through another overlay's Phase 6 rather than re-researching — `08-overlay-deck-and-screencast.md` is the common case when the decision needs a deck.

---

## When 13 is layered on a base overlay — Phase 6 transform contract (v1.3)

When this overlay is legally **layered** on a base use case (1–3 or 5–7), Phase 5 still uses the Decision Brief output format below — but the base use case **keeps ownership of the primary Phase-6 render**. The Decision Brief does not replace it. The transform is mandatory, not an optional extra render:

1. **Load the base overlay's Phase-5 output block as the target schema.** That block defines what the base deliverable's source document must contain.
2. **Transform** from the Decision Brief (`05-dossier.md`) plus `03-conflict-map.md` and the verified/rejected-source artifacts (`04-verified-sources.md`, `04-rejected.md`) into the base overlay's Phase-5 schema. **No new factual claims** may be introduced — every claim in the transformed document must be traceable to those inputs.
3. **Save the result as `06-<primary-render-id>.md`** (the base use case's primary render ID).
4. **Apply the base overlay's existing Phase-6 routing with the transformed file substituted wherever that routing consumes the Phase-5 dossier — whether it names `05-dossier.md` literally or refers to it descriptively** (some overlays say "the dossier from Phase 5" without naming the file). Never route the Decision Brief directly through the base routing as though it already had the base schema.
5. Target settings already collected by the base profile (durations, keywords, format envelope, etc.) remain authoritative for the transformed deliverable.

---

## Mode 1 — Red Team (adversarial stress-test) — runs at Phase 4.5

**Use for:** pre-launch validation, investment/strategy pre-mortems, risk assessment. Run AFTER you have a draft recommendation; the flow is **Debate → Red Team → Decision**.

**Ready-to-paste fan-out prompt** (give each agent one or two attack vectors; the decorrelated lane is mandatory here — confirmation bias is the enemy):

```
RED TEAM this plan. Do NOT validate or agree — attack it. Your job is to find what kills it.

Plan/decision: <one paragraph, with your key assumptions stated explicitly>
Context: <stage, numbers, constraints — be specific; vague input gets vague attacks>

Attack from these six vectors (cover all; go deepest on the 1-2 assigned to you):
1. TECHNICAL  — feasibility, architecture, scalability, integration, performance
2. FINANCIAL  — unit economics, CAC/LTV, runway, pricing, margin at scale
3. MARKET     — competitor response, demand assumptions, positioning, timing
4. REGULATORY — compliance, jurisdiction, data-residency, legal landmines
5. OPERATIONAL— team, dependencies, execution risk, what breaks under load
6. EDGE CASES — viral spikes, misuse/abuse, cannibalisation, international/cultural

For each finding: state the failure, its severity (KILL / MAJOR / MANAGEABLE), and the
evidence or reasoning. Cite a live URL where the claim is factual; tag reasoning as
[REASONED]. End with the single most likely cause of failure.
```

**Processing the output (manual):** 1) sort findings by severity (KILL > MAJOR > MANAGEABLE); 2) flag the ones you hadn't considered — those are the real blind spots; 3) ask the fan-out (normal mode) "given these red-team findings, how would you fix the top 3?"; 4) capture into the Decision Brief (below); 5) revise and re-red-team.

---

## Mode 2 — Debate (decorrelated, position-assigned) — runs at Phase 2.5

**Use for:** "should we?" decisions with legitimate trade-offs, thesis stress-testing, confirmation-bias checks.
**Hard constraint (ours, not Suprmind's):** run debate **only with the decorrelated lane in the room.** Verified evidence shows debate among same-lineage models amplifies shared bias rather than correcting it (Nine Judges, arXiv 2605.29800; correlated errors, 2506.07962). Judge **argument quality, not vote count** — 3 models on one side ≠ correct.

**Ready-to-paste prompt** (assign FOR to ~half the agents incl. one lineage, AGAINST to the others incl. the decorrelated lane):

```
DEBATE this decision. You are assigned the position: <FOR | AGAINST>. Argue the STRONGEST
case for your assigned side even if you'd lean otherwise — I need the best case for each side,
not your default opinion.

Decision: <statement>
My current leaning (so counter-arguments are targeted): <if any>

Begin your response with the exact line ===BEGIN LANE OUTPUT=== on its own line, then on the
next line write exactly Position: FOR or Position: AGAINST (your assigned side), then produce:
(1) your position statement; (2) evidence + reasoning (cite live https URLs; tag [REASONED]);
(3) rebuttal to the strongest opposing argument; (4) the one fact that, if true, would flip you.
After both sides: name the KEY TENSION and the COMMON GROUND.
```

---

## Mode 3 — First Principles (assumption teardown)

**Use for:** highest-stakes decisions where convention is suspect, or novel problems with no good precedent. Best as a **Phase-1 decomposition variant**.

**Ready-to-paste prompt:**

```
Analyse this from FIRST PRINCIPLES. Do not pattern-match to how others do it.
Question: <the decision/problem>

Steps: (1) list every assumption baked into how this is normally approached; (2) strip to the
underlying axioms — what is actually, physically/economically true here; (3) rebuild the analysis
from those axioms only; (4) state where the conventional approach is wrong or unnecessary, and
where it's right. Flag each rebuilt claim [VERIFIED w/ URL] or [REASONED].
```

---

## Output — Adjudicator-style Decision Brief (Phase-5 Chairman variant)

For decision dossiers, replace (or append to) the normal Chairman output with this structure. Our Chairman already plays the adjudicator role; this just fixes the schema. **Classify each disagreement by type before resolving it:**

- **Factual dispute** → resolve ONLY if one side has a cited primary source the other lacks; if both/neither cite, mark **UNRESOLVED-FACTUAL** + the verification method. (Never resolve on which model sounded more confident — confident language correlates with being *wrong*.)
- **Strategic dispute** → do not pick a winner; expose the differing assumptions and let the operator choose on their real constraints.
- **Implementation dispute** → name the deciding constraint (e.g., team size) and resolve conditionally.
- **Segmentation dispute** → name the audiences/segments and recommend a priority.

```
<output_format> — DECISION BRIEF
1. RECOMMENDED DIRECTION — one verb-first action + confidence (HIGH/MED/LOW). Not a list.
2. WHY THIS DIRECTION — which agreements and which specific disagreements were decisive (name the models).
3. UNRESOLVED DISAGREEMENTS — genuine conflicts, classified by type; do not fake consensus.
4. UNCONTESTED RISKS — blind spots only ONE agent surfaced that no one rebutted (source + mitigation).
5. CORRECTION LEDGER — every factual error one agent caught in another: issue / source / severity / action.
6. NEXT ACTION — exactly one concrete, executable step.
+ Carry all Chairman discipline rules (claim tags, ≤15-word quotes, no rejected URLs, CoVe self-check).
</output_format>
```

This is the GO / NO-GO / GO-WITH-CONDITIONS verdict + risk register, in prose form.

---

## Optional — DCI (Disagreement/Correction Index)

A lightweight quantitative layer on the Phase-3 contradiction matrix: per round, count (a) explicit contradictions, (b) corrections where one agent caught another's error, (c) unique insights only one agent surfaced. **Read it as:** high contradiction + apparent consensus = stress-test the consensus (it may be false); zero contradiction = the matrix already has what you need. Don't over-build this — a 3-number tally per dossier is enough.

---

## Mode selector (quick reference)

| Situation | Mode |
|---|---|
| Standard research write-up | Normal pipeline (fan-out → matrix → chairman) |
| Yes/no decision with real trade-offs | **Debate** (decorrelated) → then Decision Brief |
| Pre-launch / investment / pre-mortem | **Red Team** → Decision Brief |
| Convention looks wrong / novel problem | **First Principles** at Phase 1 |
| High-stakes go/no-go for sign-off | Debate → Red Team → **Decision Brief** output |
| Quick shareable answer | Normal Super-Mind-equivalent (fan-out + chairman), skip the extra passes |

**These rows are the normative source for the kickoff builder's derived mode recommendation (v1.3):** when the operator does not explicitly choose modes, the builder takes the **union of every matching row** above, then normalizes to pipeline order (`first-principles`, `debate`, `red-team`) and presents the result for explicit confirmation or override. Standard low-stakes research with no stronger signal derives no modes. Debate or Red Team must **never** be silently selected when the access inventory shows no compliant decorrelated route — surface the route blocker together with the recommendation.

**A mode selected here is mandatory and blocking, not advisory.** The orchestrator wires Debate to Phase 2.5 (its Step 2.5) and Red Team to Phase 4.5 (its Step 4.5) and may not proceed past those points while a selected mode has not run. Skipping a selected mode is a pipeline defect, not an option; cancelling one requires an explicit operator decision logged in `00-context.md`.

## Quality bar
Reject a decision dossier that: resolves a factual dispute without a cited source; "resolves" a strategic dispute by picking the more confident model; lacks an Uncontested-Risks section (the blind-spot catch is the whole point); or ran Debate without the decorrelated lane present.

## Practitioner notes
- These modes suit decision-oriented dossiers and client-facing consultancy work especially well — the Decision Brief is a client-ready artifact.
- The Adjudicator/DCI ideas are borrowed *patterns*; no commercial deliberation tool is required (this methodology's Phase-4 verdict on such tools: SKIP as pipeline components). You already run the only thing that makes them work — genuinely independent models, now including the decorrelated lane.

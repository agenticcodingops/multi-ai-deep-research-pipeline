# Overlay — Spec-Driven Software Development

**Reads with:** `00-master-methodology.md` and `01-prompts-library.md`

---

## When to use this overlay

Apply this overlay when the dossier feeds into:

- A new software project (greenfield) before any code is written
- A new feature on an existing project where architecture decisions are being made
- A migration (e.g., Azure App Service → AKS, ECS → Kubernetes, Terraform module restructuring)
- An ADR (Architecture Decision Record) where multiple options must be compared
- Any work that will be processed by GitHub Spec Kit or Amazon Kiro
- Any agentic-coding session that needs grounded context before implementation

If you already have a markdown requirements file from a prior Claude Code session: **this overlay is the right one**. The existing requirements file becomes input to Phase 1 decomposition; the dossier produced enriches and validates those requirements before they hit Spec Kit.

---

## Phase 1 — decomposition adjustment

Add this paragraph to the Phase 1 prompt (in addition to the universal version in `01-prompts-library.md`):

```
This is a software development research project. Frame sub-questions to cover:
(i) what does the official vendor documentation say about the relevant APIs/services/patterns
(ii) what do real-world implementations look like — open-source repos, recent Stack Overflow 
     answers, GitHub issues, X/Twitter discussions in the engineering community
(iii) what are the known anti-patterns, pitfalls, and incidents associated with this approach
(iv) what are the architectural alternatives and their trade-offs
(v) what does the research need to verify against the user's existing requirements doc

Required source domains for vendor questions: docs.microsoft.com, aws.amazon.com, 
registry.terraform.io, github.com, learn.microsoft.com, kubernetes.io, official RFC sites.
Disqualified: AI summary blogs, content farms, Medium posts older than 2024 unless they 
are first-party announcements.
```

If a prior requirements markdown file is being used as input, attach it to the Claude conversation in Phase 1 and add: *"The attached file is the prior requirements draft. Sub-questions must include verification of any external claims, recommended technologies, or architectural choices made in that draft."*

---

## Phase 2 — agent weighting

| Agent | Weight | Why |
|---|---|---|
| **Perplexity Pro Deep Research** | High | Best citation density for vendor docs and pricing data |
| **Grok DeepSearch** | High | Real-time GitHub issues, X engineering community, recent vendor announcements (last 30 days) |
| **Gemini Deep Research** | Medium | Source volume; useful for architectural pattern surveys |
| **Claude (strongest available model) + web search** | Medium | Synthesis-style sub-questions, cross-cutting trade-off analysis |
| **NotebookLM (highly recommended)** | High | Upload your existing repo's docs, ADRs, prior requirements files, Terraform module READMEs — gives source-grounded answers about your actual codebase context |

**NotebookLM setup specific to this overlay:** Before Phase 2, upload to a NotebookLM notebook:
- The prior requirements markdown file (if any)
- The repo's existing `docs/` folder contents
- Any existing ADRs (`docs/adr/*.md`)
- The current `terraform/` module READMEs
- Architectural diagrams as images (NotebookLM accepts these)
- Any vendor SDK reference PDFs you've collected

This gives you a fifth Phase-2 agent that answers within the boundary of *your actual project*, not the open web.

---

## Phase 5 — output format block

Insert this into the Chairman prompt's `<output_format>` block:

```
# {Topic} — Architecture Decision Record

## TL;DR (3 bullets)
- The decision in one sentence
- The biggest risk being accepted
- The biggest alternative rejected and why

## Problem statement and decision context

## Constraints (functional and non-functional)
- Performance:
- Security:
- Cost:
- Operational complexity:
- Compliance / regulatory:
- Existing-system compatibility:

## Verified findings (claims with 2+ source agreement)
- [VERIFIED] Claim with inline citation
- ...

## Disputed claims and how I'm choosing
- [DISPUTED] Claim X: 
  - Position A: Source A says ...
  - Position B: Source B says ...
  - Choice: <which position> 
  - Rationale: <why> 

## Single-source claims (flagged, not load-bearing)
- [SINGLE-SOURCE] Claim with citation

## Architectural options considered

### Option A — {name}
- Description
- Pros (with sourced rationale)
- Cons (with sourced rationale)
- Cost estimate (sourced)
- Operational burden

### Option B — {name}
(same structure)

### Option C — {name}
(same structure)

## Chosen option

- Decision: Option <X>
- Primary rationale: ...
- Trade-offs accepted: ...
- Reversibility: <one-way door / two-way door — Bezos framing>

## Open questions for the design phase
- ...

## Sources (verified URLs only)
- All citations from `04-verified-sources.md`, organised by claim
```

---

## Phase 6 — output routing

### Path A — GitHub Spec Kit (default for greenfield, framework-flexible projects)

```bash
# in the project repo
specify init --ai claude  # one-time per project

# in Claude Code, with 05-dossier.md committed to docs/research/
/speckit.constitution     # one-time per repo — captures non-negotiables
                          #   from dossier "Constraints" section
/speckit.specify          # paste full dossier as input context
                          #   generates spec.md from "Verified findings" + 
                          #   "Chosen option"
/speckit.plan             # generates research.md (mirrors dossier), 
                          #   data-model.md, contracts/, quickstart.md
/speckit.tasks            # generates tasks.md with parallelisable [P] tasks
# human review pass
/speckit.implement        # OR hand to Claude Code agentic mode
```

**Constitution content** comes from the dossier's "Constraints" section — these are the non-negotiables that should govern all subsequent decisions:

```markdown
# constitution.md
## Article I — Infrastructure
All cloud infrastructure is defined in Terraform. No manual portal changes 
in production. (Source: dossier section "Constraints — Operational complexity")

## Article II — Testing
Test-first for all business logic. Integration tests required for all 
external dependencies. (Source: dossier section "Constraints")

## Article III — Spec Format
Requirements in EARS notation: WHEN [condition] THE SYSTEM SHALL [behavior].
... etc.
```

### Path B — Amazon Kiro (preferred for AWS-native projects)

1. Open Kiro IDE in the project workspace.
2. Paste `05-dossier.md` "Problem statement", "Constraints", and "Chosen option" sections into Kiro chat.
3. Kiro generates `requirements.md` in EARS notation. Review.
4. Click "Move to design phase" — Kiro generates `design.md` with sequence diagrams and component breakdown.
5. Click "Move to implementation plan" — Kiro generates `tasks.md`.
6. Implement via Kiro's agent or hand back to Claude Code with the spec set committed.

### Path C — cc-sdd (for editor-portable workflows)

If you switch between Claude Code, Cursor, Copilot, Gemini CLI, Windsurf, or Antigravity:

```bash
npm install -g @gotalab/cc-sdd  # or check current install instructions
```

Then `/kiro:` slash commands work across all those editors with consistent behavior. Useful when client engagements force you onto a specific editor.

---

## Special case — enriching existing requirements markdown files

Procedure:

**Step 1:** In the project repo, locate the existing requirements markdown file.

**Step 2:** Cleanup pass (5 min): ensure it has at minimum: problem statement, target users, core capabilities, known constraints, any pre-decided technology choices. Don't worry about polish — the dossier produces the polished version.

**Step 3:** Open this Claude.ai project, click "New chat".

**Step 4:** Attach the requirements file to the new chat.

**Step 5:** Use this kickoff prompt:

```
I have an existing requirements draft (attached). It was generated by a prior Claude Code 
session and I want to research-validate it before running it through Spec Kit/Kiro.

Apply the spec-driven development research workflow from project knowledge.

Start with Phase 1 decomposition. Requirements:
- The decomposition must include explicit verification of every external claim, 
  technology recommendation, and architectural choice in the attached draft.
- Sub-questions should also surface: what's missing from the draft, what constraints 
  haven't been considered, what alternatives weren't evaluated.

Output the JSON to save as 01-decomposition.md.
```

**Step 6 onwards:** Continue with the standard 6-phase pipeline. The Chairman prompt's `<output_format>` is the ADR block above. The resulting `05-dossier.md` becomes the validated input to Spec Kit / Kiro, replacing the raw requirements draft.

**Step 7 (handoff to Claude Code):** Copy `05-dossier.md` into the project repo at `docs/research/<topic-slug>.md`. Commit. Switch to Claude Code in the repo and run the Spec Kit / Kiro flow above.

---

## Quality bar specific to spec-driven dev

Reject any draft of `05-dossier.md` that:

1. Cites a Stack Overflow answer for a load-bearing technology choice without also citing the official documentation.
2. Recommends a paid SaaS without citing the current pricing page (pricing volatility makes this critical).
3. Contains any Terraform/IaC pattern not verifiable against `registry.terraform.io` or the relevant cloud provider's official docs.
4. Cites a GitHub repo without the commit SHA or a recent release tag (unstable references rot fast).
5. Recommends an architectural choice without naming at least one rejected alternative.

If any of these fail, run a targeted Phase 2.5 — re-prompt the offending sub-question through Perplexity Pro Deep Research with explicit primary-source domain filters, then re-run Phase 5.

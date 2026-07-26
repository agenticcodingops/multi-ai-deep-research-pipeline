# Changelog — multi-ai-research plugin

Plugin versions track enforcement releases. The methodology documents carry their own
version line (the master methodology and corrected overlays are v1.3 as of plugin
1.3.0; docs 01 and 11 were already v1.3 since plugin 1.2.0); the two tracks are
independent — a plugin release may bump one, the other, or both.

## 1.3.1 — 2026-07-26 — pipeline defect-fix release

No features. A second live run of 1.3.0 (all six phases plus Debate, Red Team and a
mid-run top-up) produced 35 process findings; the 19 MAJOR are fixed here. The
dominant class was **silent failure** — gates reporting PASS on the wrong question —
and the second was **no sanctioned route** for anything arriving after its phase had
closed. Methodology docs 00, 01 and 13 go to v1.4. Suites: orchestrator 80 → 155,
builder 216 → 229.

**This release was itself adversarially reviewed before export**, and the review
found twelve material defects in the first cut of these fixes — several of them the
same silent-failure shape the release exists to remove. The corrections are folded
into the entries below rather than listed as a separate release, because the flawed
versions never shipped; where a correction reversed a mechanism (marker repair) the
entry says so plainly. The headline lessons: a repair route authorized by a detector
is only as safe as the detector's ability to prove a negative, and a test written by
the author of the code inherits the author's blind spots — the review's exploits are
now regression tests, and every new detector was mutation-checked (disable the
mechanism, prove its test goes red).

**Gates that were passing the wrong thing.**

- **PF-07 — G5 could not see square-bracket placeholders.** `[SUB_QUESTION]` in a
  staged prompt produced an all-PASS matrix and exit 0, so an unfilled prompt reached
  the operator's browser with nothing between it and the lane; the Phase-2 gate then
  scored a well-formed answer to the wrong question. Square brackets are the commonest
  placeholder convention in prompt engineering, so this was the likeliest way for a
  decomposer to emit an unfilled slot. Adds a bracket placeholder kind (broadened
  after review to separator shapes — `[DATE/TIME]`, `[KEY: VALUE]`, `[URL(S)]`,
  `[YES | NO]` — and one-character slots) plus `SEMANTIC_BRACKET_TAGS`, the tag
  vocabulary the pipeline emits by construction, because exempting only the six
  tokens visible in the fixtures would have failed every YouTube, health or spec-dev
  project on its first real run. Fill-shaped schema slots (`[URL]`,
  `[SOURCE TO CITE ON SCREEN]`, `[N]`, `[IMAGE: ...]`, `[HIGH/MEDIUM/LOW]`, `[P]`,
  `[VERIFIED | CONTESTED | SINGLE-SOURCE]`) are **context-bound, not globally
  exempt**: they pass only on a line that exists verbatim in the shipped reference
  corpus — "The operator supplied [URL]" in free prose is an unfilled placeholder and
  fails. The census test uses an independent finder, never the production regex (it
  promptly found a doc token the production regex could not see).
- **PF-25 — the Debate gate did not require a side.** `DEBATE_ELEMENTS[0]` matched any
  short line containing the word "position", so an output with no FOR/AGAINST anywhere
  PASSED. That defeats the defining property of position-assigned debate: nothing
  downstream could distinguish a complying lane from one that argued its own preferred
  opinion, and the Chairman would read two lanes' genuine views as a staged debate.
  The element now requires exactly one side per position line — a line naming both
  ("Position: FOR or Position: AGAINST") is the template's unresolved choice and
  declares nothing — and **new check C8** compares the declared side against the side
  the staged prompt assigned. After review, a staged debate prompt that assigns **no
  single side is itself a C8 failure**, never "not applicable": the generic
  explanation line in the shipped template used to erase the assignment and switch
  the check off. Phase 1 enforces the same contract upstream — a staged Debate needs
  exactly one FOR and one AGAINST template, each carrying every element the output
  gate scores (rebuttal, flip fact, two-URL floor included), with side spellings
  parity-locked between the two gates so Phase 1 never blocks what Phase 2 accepts.
- **PF-13 — G6 never walked `deferred_phase_prompts`.** Debate and Red Team templates
  are staged verbatim and their *outputs* are gated at Step 3.1, but the templates
  themselves were checked by nothing, so a template missing KEY TENSION was discovered
  only after running the pass on six surfaces. Adds per-phase needle sets, reported in
  the matrix's GLOBAL column.
- **PF-12 — multi-assignment lane files.** A lane handed several prompts in one paste
  can answer each separately; the split took the last, discarding the rest as echo and
  reporting a clean PASS on a fraction of the research with nothing recording the loss.
  More than one sentinel is now a C1 failure, and Step 2.1 carries a canonical preamble
  for multi-assignment lane files.
- **PF-34 — no manifest.** The gate scored the files it found, so a staged-but-never-run
  lane was invisible. Adds `--expect`, with a `debate:` prefix because lane ids collide
  across kinds. After review the manifest is strict: an empty component (`--expect ,`)
  is a usage error, never silently dropped — a lost lane id would convert the
  completeness contract into best-effort — and only a file under its **canonical**
  name satisfies an expectation (an explicitly passed `x.md` is gated ad hoc and
  leaves `initial:x` missing).
- **PF-35 — absence asserted from inability.** A lane declared capabilities ABSENT ten
  times after stating it could not read the repository, manufacturing gaps rather than
  finding them. C6 fails that combination; the Phase-2 contract requires
  `[UNVERIFIED — could not access]` instead. The detector was rebuilt after review
  showed the first cut wrong in both directions: it is now sentence-scoped with
  either-order inability/source co-location (an access-verb is required, so "cannot
  agree with the sources" is not an admission), case-insensitive on the verdict, and
  exempts negated meta-statements ("it would be wrong to report ABSENT"), the
  bracketed UNVERIFIED form, and absence claims carrying their own citation —
  inability to reach source A no longer invalidates an absence evidenced from
  source B. The PR review then hardened it twice more: heading text is scanned as a
  claim (an admission or verdict written as a section title used to vanish with the
  heading boundary), and the meta exemption binds to the verdict token it governs —
  "I cannot claim it is present; it is ABSENT" no longer exempts the affirmative
  ABSENT because an unrelated negation shares its sentence.
- **PF-20 / PF-21 — C1's echo diagnostic, and the death of marker repair.** The
  diagnostic defect stands as found: mandated section headings appear in prompt and
  answer by construction, so every clean-but-unmarked export was reported as an echo;
  there are now two verdicts with different diagnoses. The first cut of this release
  also added a **marker-repair route** — prepend the missing sentinel when the gate's
  echo numbers read zero — and the adversarial review killed it with a working
  forgery: blockquote the echoed prompt, change one punctuation mark, and exact-line
  comparison reports 0/0 while inviting the repair that then passes the whole gate.
  **There is no repair route.** Echo comparison now canonicalizes renderer
  transformations (blockquote/list prefixes, case, trailing punctuation) and adds a
  word-shingle measure that survives reflow; the gate also checks for staged-prompt
  echo **inside the answer region even when a sentinel is present**, so the historical
  forgery fails C1 outright. A dropped marker means a re-run — the diagnostics are
  published, and they authorize nothing.

**Deliberate fixture changes** (a tightened gate legitimately invalidates an old pass):
the phase-4.5 deferred template in nine phase-1 fixtures now carries the contract PF-13
checks, and overlay 13's Mode 1 fence gains the sentinel line and "resolvable https URL"
so the shipped template can satisfy it. `test_deferred_bad_token_fails` was narrowed to
its subject; no assertion was weakened.

**A validator for `research-config.md` (PF-02).** The format has three states and a
documented trap — legacy `none` means *unknown*, not confirmed-unavailable — and no
validator anywhere, so an operator writing `- NotebookLM: none` to mean "I don't have
this" was silently recorded as unknown and re-asked sessions later. `validate_config.py`
classes every entry `v1 | legacy | invalid | missing`. Legacy is loud and **not** fatal:
Step 0.3 offers to normalize and never rewrites, and a red gate would coerce acceptance
of any rewrite offered. After review the reader and the writer share one grammar: HTML
comments **and fenced code blocks** are masked (a fenced `Dossier root: decoy/` was
active configuration, and a fenced fake heading could hide the real section) — and
after the PR review the scan is left to right, whichever opener comes first claiming
text through its own closer, so a stray ``` inside a comment (or a `<!--` inside a
fence) is inert instead of poisoning the mask through EOF and hiding the real
configuration from both the validator and merge-config. The
secret scan runs over the **whole raw file** — comments, fences, and legacy values
included, with every match redacted so no report echoes the credential it is flagging
— duplicate JSON keys are rejected exactly as the approved writer rejects them, and
`kickoff_io merge-config` now matches only active lines, so it can no longer rewrite a
bullet inside a comment, report MERGED, and leave the entry missing on the next
validation. Dossier-root scope is classified after resolution, so `../outside` and
symlink escapes report `outside_workspace`, not "relative".

**Routes for what arrives late** (PF-16/17/19/21/33, as one doctrine). A new "re-gate
rule" section: any artifact admitted by a gate and then changed by hand must pass that
gate again, and the second pass is recorded — the window closes at the first lane
output, not at the phase. Step 1.5 route (c) targeted patch; Step 2.1a late seed
addition; Step 2.1b late input arrival with the new `scoping_only` class; Step 4.8
targeted top-up. (A Step 3.1 marker-repair route was in the first cut of this list and
was removed — see PF-20/PF-21 above.) After review, Step 4.8 also **reconciles**: a
top-up appends a `## Top-up delta` section to the conflict map, records whether the
post-top-up evidence changes the draft recommendation, and — when it does and a
blocking mode was selected — re-runs each affected mode once against the updated draft
before Phase 5 (per selected mode, per top-up: a top-up that invalidates both Debate
and Red Team refreshes both, never either twice). Superseded outputs are preserved as
`.superseded-<n>.md` audit copies whose name still matches a bare `04a-redteam-*`
pattern — so every consumer names the exclusion instead of trusting a glob. Without
this, a
cost-gap top-up could flip the recommendation from A to B after Red Team had attacked
A, and Phase 5 would proceed with the blocking mode having run on the wrong question.

**Evidence posture** (PF-29/30/32/18). Step 4.2 fetches and compares before it considers
resolution and adds `RESOLVES_ONLY`, because the dominant fabrication is a real,
resolving URL with invented content — four of four checked social citations on one run,
including the sole citation behind that dossier's central verdict. A source class that
cannot be verified on this surface is carried `[UNVERIFIED]` for the whole run. New
BLOCKING Step 4.7 disposes of every declared gap before Phase 5, and the Decision Brief
gains STATED LIMITATIONS. Doc 00 gains "Orchestrator findings are not evidence" — no
gate can reach a fact the chair injects into a prompt — plus the AI-chat-transcript
input hazard and the provider export-quirks table.

**PF-36 — `html_report` joins the closed matrix for use case 8**, with two constraints in
the matrix entry (it reproduces the stated limitations and confidence level; it carries
no `LOCAL-ONLY` string) and the matrix's sole extension exception,
`06-html_report.html`. **Breaking, by design:** the uc8 interview question becomes
multi-select, so `question_catalog_digest` and `sheet_instance_digest` move and every
previously issued headless answer sheet is stale.

**Adjacent fixes** the above would otherwise leave broken: Phase 5's input lists
enumerate canonical names and exclude `02-<lane>.raw-export.md` (a historical
marker-repair audit copy would enter the synthesis as a duplicate lane report — the
correlated-evidence failure the pipeline exists to prevent), and after review the
runbooks' own "paste all `02-*.md`" instructions were replaced with the same canonical
enumerations, locked by a drift test, since a glob in a runbook feeds a repaired lane
twice into Phase 5 or NotebookLM no matter what the orchestrator says;
`--project-rules extra_contaminants` is wired into Step 1.5, making
scoping-only contaminants machine-enforced; `_split_boundary`'s prompt-tail can no longer
split on a mandated heading; Step 0.0 writes the ten `unknown` entries; `--check-urls` is
documented at last, as a liveness smoke test conferring no VERIFIED status.

**Deferred, deliberately.** PF-26 part 2 (a renderer-proof sentinel form) is a contract
migration touching `SENTINEL_RE`, both skeleton copies, overlay 13's cue-locked fence and
every Phase-2 fixture; it needs its own release with a dual-accept window. PF-07b
(underscore/`XXX_` placeholders) needs a raw-text detection path, because `normalize()`
strips `__x__` before any detector sees it and a screaming-snake regex would flag
`SPEAKER_NOTES`. G5 still cannot see lowercase angle placeholders, so a deferred template
can ship with `Decision: <statement>` unfilled — PF-08's prose requires both debate
entries to be complete and says plainly that the gate cannot check it.

## 1.3.0 — 2026-07-22 — kickoff-builder release

A third skill plus a versioned input interface: the pipeline can now start from a
mechanically validated kickoff brief instead of a fresh interview.

- **A third skill builds the kickoff.** `research-kickoff-builder` conducts an
  Expand→Converge interview (three modes: build / refine / validate-only), drives it
  from a shipped 64-record question catalog with a closed `when`-predicate AST, and
  produces `00-kickoff.md` with an authoritative sentinel-delimited JSON control
  block (`kickoff_schema_version: 1`). A headless two-invocation answer-sheet flow
  (SHA256 catalog + instance digests) replaces any pretend interactive session.
- **Two new stdlib-only scripts enforce it.** `validate_kickoff.py` runs gates
  K1–K8 (structure/parity, core intent + provenance bijection, profile union,
  modes, lane readiness, inputs/paths, ground-truth/privacy, slug/output safety)
  against an embedded JSON Schema Draft 2020-12 machine contract evaluated by a
  closed-vocabulary interpreter; `kickoff_io.py` owns every write — deterministic
  render, atomic hard-link no-clobber publication, lock/hash/backup refine
  promotion, and an approval-gated `research-config.md` merge.
- **The orchestrator consumes prepared kickoffs.** A prepared-kickoff adapter runs
  before Step 0.0: untrusted read, embedded consumer-side type/enum/path map, zero
  redundant Step 0.0–0.4 questions for a valid brief, targeted questions only for
  current-session external state, Steps 0.5/0.6 always preserved, and six new
  deterministic `00-context.md` sections. New consumer hooks: Step 1.0 (SEO
  pending → `00-keyword-brief.md`), venue preferences at Steps 1.1/3.3/5.1,
  expected-lane seeding at Step 1.2, the blocking Step 5.4 health exit check, the
  layered-base Phase-6 transform, and Step 6.3 additional renders.
- **Methodology v1.3 corrections.** The master methodology's decorrelated-route
  rule now matches the rest of the stack (consumer DeepSeek web UI for
  non-confidential work; Western-hosted/self-hosted for confidential); the health
  overlay's final-dossier NotebookLM pass moved from Phase 4 (impossible — the
  dossier does not exist yet) to a mandatory Phase-5 exit check with SHA256
  invalidation on overwrite; overlay 13 gained the legal-layering rule (use cases
  1–3/5–7 only, never ebook) and the layered-base Phase-6 transform contract; the
  old most-demanding-overlay multi-deliverable advice in checklist 12 and runbook
  11 is replaced by the closed additional-render matrix with the use-case-7
  normalization and separate-kickoff rule.
- **Ten-key three-state access inventory.** `research-config.example.md` and Step
  0.3 now carry `unknown|available|unavailable` compact-JSON entries for ten tools
  (Scite added as health Phase-4 verification readiness, never a lane), with
  conservative legacy migration (`none` = unknown) and a never-persist-transient
  rule.
- **Release verification runner.** `release/verify.ps1` (both unittest suites,
  `claude plugin validate`, portability grep, four anchors, exact 14-name twin
  set + hashes, golden validator CLI) now runs as Gate 3.5 inside
  `export-public.ps1` before anything is staged. Tests 80 → 295 (80 orchestrator +
  215 builder, including contract-drift and golden-loop suites).

## 1.2.2 — 2026-07-22 — second-loop lock

- **The skeleton round-trips its second consumer.** 1.2.1 locked the prompt →
  `validate_phase1.py` loop; the OUTPUT FORMAT skeleton's other consumer is
  `gate_phase2.py` — lane outputs follow the skeleton and are then judged by
  C1–C7, so skeleton drift would reject users who follow it verbatim. A minimal
  verbatim fill of the shipped skeleton was proven to pass the gate as-is (no
  drift found), and the loop is now locked generatively:
  `test_skeleton_fill_round_trips_gate` re-derives the fill from the shipped doc
  on every run, `pass_skeleton_fill.md` is asserted byte-identical to that
  regeneration, and `pass_debate_template_fill.md` plus a cue-parity check do
  the same for overlay 13's Mode 2 template against the debate gate. Tests
  77 → 80. No gate or contract behaviour changed.

## 1.2.1 — 2026-07-22 — loop-closure patch

Operator-directed validation of 1.2.0 surfaced one real defect and produced the proof
the release was missing.

- **The decomposition prompt now shows the skeleton it obligates.** 1.2.0 required
  every ready prompt to carry the literal OUTPUT FORMAT skeleton, but the Phase-1
  prompt only *referenced* it ("from the Phase-2 fan-out prompt") — a decomposer
  pasted only the Phase-1 prompt could not reproduce a block it was never shown, so a
  compliant decomposer would hard-fail G6: the 1.2.0 false-rejection class in reverse.
  The skeleton is now embedded verbatim in the decomposition prompt, and a parity test
  asserts the doc's two copies stay byte-identical, demonstrate the ≥3-findings floor,
  and survive G5/G6 when embedded in any staged prompt.
- **Golden happy-path fixture locks the prompt→gate loop.** `pass_golden_loop.json` is
  a decomposition produced by following the composed Phase-1 prompt end-to-end (4 SQs,
  10 prompts, each carrying the full contract plus the doc's literal skeleton); the
  suite asserts it passes with zero findings. The gate had previously been proven only
  against synthetic fixtures and the pre-fix live decomposition — the elicitation
  direction was untested. Tests 75 → 77.

## 1.2.0 — 2026-07-22 — live-run repair release

A full six-phase live run (use case 8 / overlay 13) exercised every 1.1.x gate against
real deep-research exports for the first time. The fourteen 1.1.0 repairs all held — no
regressions — but the run surfaced eleven MAJOR defects, headlined by the Phase 2 gate
false-rejecting **all four** real web lanes on formatting alone. All fixed; regression
coverage grows from 57 to 71 tests, and every gate change was verified against the run's
archived raw exports (all four lanes now pass unmodified; every fail-closed path
unchanged).

- **Phase 2 gate accepts real-world formatting.** Real lanes emit parenthesised numbered
  headings (`(1) TL;DR`, bold-wrapped variants), blockquoted headings and findings
  (`> 1. …`), and compound confidence tags (`[HIGH, GROUND-TRUTH-ASSERTED (GT11)]`,
  `[MEDIUM — qualifier]`, `[HIGH confidence]`). All were rejected on formatting despite
  complete, correctly-cited content — the failure most likely to teach an operator to
  switch the gate off. `_H_PRE`, `ITEM_RE`, and `TAG_RE` now accept them; pseudo-tags
  (`[HIGHLY]`, `[High]`, `[MEDIUM-TERM]`) still fail; the fail-closed answer boundary,
  concealment masking, and https-only citation credit are untouched.
- **Debate gate accepts the header form of a position statement.** `(1) POSITION
  STATEMENT — FOR: …` (a real lane's output) now satisfies the `position` element; bare
  "position" in running prose still does not. Overlay 13's Mode 2 template now also
  instructs a literal `Position: FOR|AGAINST` line so template and gate cannot
  contradict each other.
- **The Phase 2 contract now shows the machine-checked format.** Root cause of the false
  rejections: lanes were told the section NAMES but never the exact form the gate
  parses, so every lane guessed a different decoration and every one failed. The fan-out
  prompt gains a literal `OUTPUT FORMAT (machine-checked — follow literally)` skeleton
  (sentinel first line, plain `## <Name>` headings, plain `1.` findings — at least 3 —
  standalone tags, ≥3 https sources) that every ready prompt must carry verbatim, and
  G6 now fails any staged prompt missing the skeleton's OUTPUT FORMAT title.
- **Sub-question ceiling raised to 12.** Use case 8 mandates 8 sub-question areas, so
  any justified split breached the old 4–8 bound and forced a lossy merge. G1, the
  library spec, and the manual checklist now agree on 4–12; counts of 3 and 13 still
  fail — now test-locked (the old bound had no test at all).
- **Ground truth can hold an operator-private prior.** G8 required https on every claim,
  so hand-coded priors from the operator's own dataset could not live in the array and
  were shunted to `known_traps`. An `asserted` claim may now carry `source_url: null` or
  an operator-provenance marker (e.g. `operator-private-sample`); `verified` still
  requires https, and a claim with a missing or invalid status falls into the https
  branch — fail closed. Step 0.6 gains the matching rule: operator-private-dataset
  claims are ASSERTED by definition, never VERIFIED.
- **G6 standing-rule matching accepts stronger phrasings.** "resolvable https URL"
  satisfies the resolvable-URL rule; hyphenated `ground-truth` or a `<ground_truth>`
  block satisfies the ground-truth mention. A prompt with no URL-resolvability
  instruction at all still fails.
- **Deferred-prompt spec and gate can no longer drift.** The library now names the key
  (`prompt_template` — never `ready_to_paste_prompt`, which is reserved for staged
  Phase-2 prompts) and the type (`phase` is the JSON number 2.5/4.5); the validator
  reports all field defects per entry and hints the rename when it sees the alias. On
  the live run the key mismatch was a latent failure hidden behind the phase-type
  failure.
- **Decomposer self-reports are declared noise.** Step 1.5 now states that a
  decomposer's "self-validation passed" narration is not the gate — on the live run it
  declared all checks passed while `validate_phase1.py` found 27 failures.
- **"Research project" defined as optional.** Steps 1.1/1.3/5.2 and the startup
  checklist now state the real per-phase requirement — fresh chat, extended thinking at
  maximum, named inputs attached to that chat — and a Claude Project is an optional
  convenience container. The Phase-2 Claude-lane "separate tab, not the project"
  decorrelation note is unchanged.
- **Deliberation mode is a set.** `first-principles+debate+red-team` — the combined
  flow the live run selected (the selector's high-stakes row maps to `debate+red-team`;
  First Principles joins from its own row) — is now recordable as a `+`-joined set;
  Steps 2.5 and 4.5 trigger on set membership. No script reads this field.
- **Phase-1 prompt artifact named.** The composed prompt is saved as
  `01a-phase1-prompt.md` before hand-off, so a Step 1.5 gate failure re-runs from the
  file with the failure list appended instead of rebuilding from scratch.
- **Specialist-lane guidance sharpened** (runbook 11): light interpretation is
  acceptable in an empirical lane while its verdicts stay descriptive; an
  `orchestrator-local` lane always shares the orchestrator's own Anthropic lineage, so
  its agreement with a Claude reasoning lane is never independent corroboration.
- Fixture policy: all new acceptance fixtures are synthetic and content-free; the live
  run's raw exports remain outside the plugin as a private local verification corpus.
- **Post-review hardening (same release).** An adversarial review of this release's own
  diff found and closed: a TAG_RE rubric-echo bypass (`[HIGH, MEDIUM, or LOW]` — the
  unfilled template form — no longer counts as an assigned tag); phantom findings items
  from numbered lists quoted inside a plain finding (blockquoted items now count only in
  a fully blockquoted section); a vacuous ground-truth mention check (the GT tag
  literals alone no longer satisfy it); newline acceptance in the operator-provenance
  marker; blockquoted TL;DR bullets not counting toward the bullet floor; and a
  skeleton example demonstrating 2 findings where the gate requires 3.

## 1.1.1 — 2026-07-21 — review-hardening release

An adversarial code review of the 1.1.0 gates found fifteen ways they could pass what
they should fail (or fail what they should pass). All fixed; each entry states the
bypass it closes.

- **Phase 2 gate fails closed on boundaries.** A truncated or diluted prompt echo could
  fall below the old 30% heuristic and get the whole file scored as an answer. Now: when
  a staged prompt exists, only the sentinel or the prompt's uniquely-matching final line
  establishes the answer boundary; anything else fails C1. Whole-file scoring survives
  only when no staged prompt is available, and says so. An explicitly supplied missing
  `--prompt`/`--prompts-dir` is a usage error, not a silent downgrade.
- **Concealment detection rebuilt on an HTML parser.** The old regex missed nested,
  unclosed, class-based (`sr-only` etc.), `visibility:hidden`, and comment-wrapped
  hiding — and false-failed on hidden content inside the echoed prompt. Now a single
  parser pass tracks nesting depth, treats unclosed hidden containers as automatic
  failures, inspects HTML comments, exempts the pre-boundary region, and masks all
  concealed content out of every other check so it can never earn credit.
- **Citation accounting: https only, ties lose.** http URLs no longer count; a lane now
  fails when dead markers merely EQUAL its https URL count; compound (`[1, 2]`, `[3-4]`)
  and named (`[^note]`) markers are recognised; confidence/ground-truth tags are never
  counted as markers. Gate thresholds are validated (negative/NaN/infinite values are
  usage errors).
- **Debate outputs get a Debate gate.** `02b-debate-*` files were being judged against
  the six-section research contract they were never asked to produce. They now gate on
  overlay 13's actual Mode 2 contract (position, evidence with `[REASONED]`, rebuttal,
  flip-fact, KEY TENSION, COMMON GROUND) with boundary, concealment, and https-citation
  checks retained; the Mode 2 prompt template now instructs the output sentinel.
- **Phase 1 validator is a real schema-v2 validator.** `schema_version` must equal 2;
  types, enums (agents, source types, roles, lineages, statuses), id uniqueness, and
  cross-references are vetted before any later gate; lane ids must be safe filename
  slugs (they become dossier filenames); malformed input yields structured failures and
  clean JSON output, never a crash.
- **Assignment consistency counts multiplicity.** Duplicate assignment or prompt pairs,
  identical primary/secondary agents, and prompts whose agent contradicts their lane's
  declared agent (the lane-swap that routes a prompt to the wrong surface) all fail.
- **Ready prompts must carry the full Phase 2 contract.** The gate now proves every
  staged prompt contains the sentinel instruction (inline, never as a standalone line),
  all six section names, the standing rules, and — when ground truth exists — the
  filled per-claim block (id, statement, metric definition, https source, all three tag
  semantics). Previously the words "ground truth" plus a claim id were enough.
- **Project rules can only strengthen gates.** `min_evidence_lanes` floors at 2; the
  placeholder allowlist can excuse only the bare words TODO/TBD, never a delimited
  token; deferred prompts are restricted to `<DRAFT_RECOMMENDATION>` on the Red-Team
  phase-4.5 entry alone.
- **Contaminant matching normalises first.** `Hugo**Max**`, zero-width splits, and case
  variants no longer evade the scan; the manual checklist now correctly permits the
  declaration site as well as audit blocks.
- **Red Team wiring closed.** The pass now triggers on `debate+red-team` as well as
  `red-team`, mirrors Debate's restore-or-explicitly-cancel rule for the mandatory
  decorrelated lane, requires every staged lane's output non-empty before Phase 5, and
  runs every new red-team URL through the Phase 4 verification ledger — the Chairman
  can no longer cite unverified post-Phase-4 evidence.
- **Optional URL liveness check hardened.** Credential-bearing URLs, localhost/.local
  hosts, and any address resolving to loopback/private/link-local/multicast/reserved
  space or the cloud metadata endpoint are rejected before any connection; the
  connection object lifecycle bug (uncaught constructor failure) is fixed. The check
  remains optional and warn-only.
- **Namespace repair.** Overlay 02's remedial "targeted Phase 2.5" is renamed a
  "targeted Phase-2 rerun" (Phases 3–5 re-run after it) — Phase 2.5 means Debate,
  everywhere.
- Fixture policy: the ground-truth shape fixture no longer carries an `http://` URL;
  fixtures use a non-URL sentinel to test URL rejection.

## 1.1.0 — 2026-07-21 — enforcement release

Fourteen defects surfaced by a full live pipeline run (use case 8, overlay 13 primary).
Nearly all were one failure wearing different clothes: **the methodology's prose was ahead
of its mechanism** — features described in the overlays were enforced nowhere in the
orchestrator's procedure, so they only happened when an operator improvised them. The two
worst were controls that reported green while doing nothing. Each entry below states the
change and the observed failure it prevents.

- **Ground-truth verification (new Steps 0.3 q7 + 0.6; tag semantics in the prompts
  library).** Operator-supplied ground truth must be re-verified against its source URL —
  and its metric definition, not a lookalike metric — before it gains override authority;
  unverified claims are downgraded to a contradictable prior. Prevents: a misread figure
  (a rank change read as a volume change) seeded into every lane, immune to correction by
  construction.
- **Phase 2 gate scores the answer, not the file (new `scripts/gate_phase2.py`; sentinel
  rule in the Phase 2 prompt; Step 3.1 rewritten).** Every lane output is split into
  echoed-prompt and answer, and all metrics run on the answer only; citation patterns
  cover `[n]`, `[^n]`, `【n†…】`, and hidden-span reference blocks; escaped tags count
  after normalisation; an output claiming sections the structural check cannot find fails
  on that alone. Prevents: a lane file with no findings body passing every gate on the
  strength of its own echoed prompt.
- **Phase 1 validation gate (new Step 1.5, `scripts/validate_phase1.py`, blocking).**
  Structure, verdict discipline, assignment consistency, lane coverage, placeholders,
  standing rules, contaminant containment, ground-truth shape — eight gates with a
  per-lane matrix, plus a cognitive decomposition-gaps review. Prevents: a 165KB Phase 1
  output nobody can check by eye generating every downstream prompt unvalidated.
- **Deliberation modes wired (new Steps 2.5 and 4.5; old Step 4.5 renumbered 4.6).**
  Debate and Red Team are formally Phase 2.5 and Phase 4.5 (the latter shared with the
  optional eval gate); a mode selected via overlay 13 is mandatory and blocking. Prevents:
  an operator following the skill literally silently skipping both modes on a dossier that
  chose overlay 13 to get them.
- **Phase 5 capability gate (Step 5 rewritten).** The Chairman requires the strongest
  Claude model, maximum extended thinking, and a fresh context — any surface meeting all
  three qualifies, with a fresh subagent preferred, a fresh Claude.ai web chat as default,
  and inline permitted only with low contamination and a passing input-budget check.
  Prevents: a contaminated orchestrator context acting as Chairman, and forced manual
  copy-paste round trips that silently truncate artifacts.
- **Decision research routes to overlay 13 (runbook 11 lesson 8 + routing table;
  Supersedes/Superseded-by headers on overlays 03, 04, 13).** Prevents: personal-decision
  projects routed to the WordPress SEO overlay and losing the Decision Brief format
  entirely.
- **Agent-access inventory (Step 0.3 q6; `research-config.md` `## Agent access`; lineage
  assignment rule in the Phase 1 prompt; `lanes_unavailable`).** Lanes are assigned
  against the operator's real stack — maximise distinct lineages before depth — and every
  unused available lineage needs a one-line justification. Prevents: a whole training
  lineage (the only OpenAI lane) silently dropped on every run because "optional" meant
  "never".
- **Execution surfaces (lane_roles gains `execution_surface`; Step 2.2 renders per-lane
  instructions; specialist-lanes section in runbook 11).** Prevents: an operator handed a
  13KB prompt for a named role with no tool bound to it and nowhere to paste it.
- **Assignment consistency contract (`phase_2_prompts` canonical, `agent_assignments`
  derived; gate G3).** Prevents: two conflicting answers to "who researches what" with
  neither declared canonical.
- **Lane roles as mechanism (`lane_roles` block; ≥2 evidence-bearing lanes per
  sub-question; `[SENTIMENT-CONCUR]` rule in the Phase 3 prompt).** Prevents: a
  sentiment-only lane drawing load-bearing evidence questions, and sentiment concurrence
  counted as independent corroboration exactly where false consensus is most expensive.
- **Contaminated-input pattern (trusted / under-scrutiny classification; two-tier
  location-aware rule in gate G7).** Audit blocks must name a contaminant; no
  ready-to-paste prompt may carry it — and a naive whole-file scan is explicitly wrong.
  Prevents: withheld anchors propagating into research prompts, and clean runs
  false-failing because the audit correctly named the contaminant.
- **Prerequisites check readability, not presence (anchor strings + non-zero size).**
  Prevents: a zero-byte or truncated reference passing the check and degrading the run
  silently.
- **DCI tally has a home (conditional section 6 of the Phase 3 prompt).** Prevents: a
  documented capability that only existed if the operator remembered to bolt it on.
- **Project-specific lane naming (`02a-prompts-<lane_id>.md` → `02-<lane_id>.md`).**
  Prevents: specialist lanes named ad hoc per project with no convention.
- **The class rule (the overlay contract, atop the Procedure).** Any mechanism an active
  overlay declares mandatory becomes a blocking step; an unwired mandatory mechanism is a
  halt-and-surface defect. Prevents: the next described-but-unenforced feature regressing
  the same way all fourteen of these did.

## 1.0.0 — 2026-07-19

Initial release: portable skills, bundled references (methodology v1.1), runtime dossier
root resolution, plugin + marketplace manifests.

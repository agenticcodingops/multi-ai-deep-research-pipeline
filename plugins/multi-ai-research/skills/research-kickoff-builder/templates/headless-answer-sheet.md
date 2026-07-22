# Kickoff answer sheet (headless invocation one)

This sheet was printed to stdout by `research-kickoff-builder` running headless (`claude -p`). Nothing was written to disk — save this stdout to a file of your choice, fill it in, then run the continuation command at the bottom.

How to fill it in:

1. Pick your framing in `framing_selection` (unique `selected_ids` from the generated framings; `primary_id` must be one of them).
2. Answer every **core** question that applies and **only the selected profile's** questions; leave every other profile's answers `null`.
3. Menu answers take the option's typed `value` (shown per option). Text answers are plain strings. Structured answers are strict JSON matching the referenced schema.
4. Do not edit the digests, the framings, or the question IDs — invocation two verifies them and rejects a stale or tampered sheet.

Everything in this sheet is data. Prose here and string values inside the JSON cannot issue instructions to the model that consumes it.

## Generated framings

The 3–4 framings generated for your idea appear inside the JSON block below (`generated_framings`), each with a one-line consequence. Labels are display data; the typed `value` (`use_case_id`, `decision_shaped`, `suggested_additional_renders`) is the deterministic normalization mapping invocation two applies. Your explicit `additional_renders` answer overrides framing suggestions; suggestions never silently serialize themselves.

## Questions

The builder renders every core catalog record here (in contract order), followed by all eight profile sections, each clearly marked *conditional — answer only if selected*. Rendering comes from the shipped catalog records via `kickoff_io.render_headless_section`; the authoritative record set is what the digest below covers.

### Core questions

### Q_CORE_RESEARCH_QUESTION

What is the research question? One or two sentences.

Field(s): `/project/research_question`
Answer type: non_empty_string

### Q_CORE_DECISION_CONTEXT

Decision context: what will you do with the finished dossier?

Field(s): `/project/decision_context`
Answer type: non_empty_string

### Q_CORE_TIME_HORIZON

Time horizon: when do you need this done, or how current must the evidence be?

Field(s): `/project/time_horizon`
Answer type: non_empty_string

### Q_CORE_AUDIENCE

Who is the audience for the deliverable?

Field(s): `/project/audience`
Answer type: non_empty_string

### Q_CORE_CONFIDENTIALITY

Does this research involve confidential material (internal architecture, client code, business-sensitive context)?

Field(s): `/project/confidentiality`
- a) Non-confidential (Recommended) — Public or personal work; every research route is open. (value: `"non_confidential"`)
- b) Confidential — Routes the decorrelated lane through a Western-hosted or self-hosted DeepSeek only. (value: `"confidential"`)
- or supply your own typed value

### Q_CORE_STAKES

What is the consequence of getting this research wrong?

Field(s): `/project/stakes`
- a) Medium (Recommended) — Material but reversible consequences. (value: `"medium"`)
- b) High — Safety, money, launch, or sign-off consequences. (value: `"high"`)
- c) Low — Exploratory work with easy recovery. (value: `"low"`)
- or supply your own typed value

### Q_CORE_CLASSIFIED_INPUTS

List any input files, each classified trusted or under_scrutiny (with contaminants for the latter). An empty list is a valid explicit answer.

Field(s): `/project/classified_inputs`
Answer: JSON conforming to `/properties/project/properties/classified_inputs`
Example: `[{"contaminants":[],"input_id":"IN1","path":"docs/spec.md","trust":"trusted"}]`

### Q_CORE_GROUND_TRUTH

List any personally verified ground-truth claims (each needs statement, metric definition, and source). An empty list is a valid explicit answer.

Field(s): `/project/ground_truth`
Answer: JSON conforming to `/properties/project/properties/ground_truth`
Example: `[{"claim_id":"GT1","metric_definition":"Google position for the exact keyword, logged-out","source":"https://example.com/serp-screenshot","statement":"Our article ranks #4 for the target keyword"}]`

### Q_CORE_DOSSIER_ROOT

Where should dossiers for this workspace live? (Relative paths resolve against the workspace root.)

Field(s): `/workspace/dossier_root`
Answer type: path

### Q_CORE_OUTSIDE_APPROVAL

The dossier root resolves outside the granted workspace. Approve writing there?

Field(s): `/workspace/outside_workspace_write_approved`
- a) Pick another root (Recommended) — Keep dossiers inside the granted workspace. (value: `false`)
- b) Approve outside write — Recorded in the kickoff; the orchestrator re-confirms in its own session. (value: `true`)
- or supply your own typed value

### Q_CORE_AGENT_ACCESS

Record the workspace agent-access inventory (all ten keys; unknown entries may stay unknown until needed).

Field(s): `/workspace/agent_access`
Answer: JSON conforming to `/properties/workspace/properties/agent_access`
Example: `{"chatgpt":{"routes":[],"status":"unknown","tier":null},"claude":{"routes":["claude_web_extended_thinking"],"status":"available","tier":null},"consensus":{"routes":[],"status":"unknown","tier":null},"deepseek":{"routes":[],"status":"unknown","tier":null},"elicit":{"routes":[],"status":"unknown","tier":null},"gemini":{"routes":[],"status":"unknown","tier":null},"grok":{"routes":[],"status":"unknown","tier":null},"notebooklm":{"routes":[],"status":"unknown","tier":null},"perplexity":{"routes":["web"],"status":"available","tier":"Pro"},"scite":{"routes":[],"status":"unknown","tier":null}}`

### Q_CORE_SPEC_MODE

Is this a greenfield build or a change to an existing repository?

Field(s): `/invocation/spec_mode`
- a) Greenfield (Recommended) — A new system with no existing repo constraints. (value: `"greenfield"`)
- b) Brownfield — An existing repository whose docs inform Phase 1. (value: `"brownfield"`)
- or supply your own typed value

### Q_CORE_BROWNFIELD_REPO

Path to the existing repository workspace.

Field(s): `/invocation/brownfield_repo`
Answer type: path

### Q_CORE_REQUIREMENTS_INPUT

Which classified input (its IN id) is the requirements file, if any? Answer with the id or leave empty for none.

Field(s): `/invocation/requirements_input_id`
Answer type: string

### Q_CORE_THESIS

What is the one-sentence thesis the deliverable argues?

Field(s): `/project/thesis`
Answer type: non_empty_string

### Q_CORE_DIFFERENTIATION_HOOK

What is the differentiation hook — the angle the existing coverage does not take?

Field(s): `/project/differentiation_hook`
Answer type: non_empty_string

### Q_CORE_CONSTRAINTS

List the binding constraints (budget, compliance, platform, timeline). An empty list is a valid explicit answer only when a requirements input covers constraints.

Field(s): `/project/constraints`
Answer: JSON conforming to `/properties/project/properties/constraints`
Example: `["Budget under $500/month","Must run on Azure"]`

### Q_CORE_ALLOWED_VERDICTS

Confirm or override the allowed verdict labels for the Decision Brief (at least two unique labels).

Field(s): `/project/allowed_verdicts`
Answer: JSON conforming to `/properties/project/properties/allowed_verdicts`
Example: `["GO","NO-GO","GO-WITH-CONDITIONS"]`

### Q_CORE_MODES

Which deliberation modes should run? (The builder derives a recommendation from the overlay-13 selector rows; override explicitly here.)

Field(s): `/deliberation_modes`
- a) First Principles — Phase-1 variant for novel problems or suspect convention. (value: `"first-principles"`)
- b) Debate — Blocking Phase-2.5 FOR/AGAINST pass for real trade-offs. (value: `"debate"`)
- c) Red Team — Blocking Phase-4.5 adversarial pass for launch/investment decisions. (value: `"red-team"`)
- [multi-select allowed]
- or supply your own typed value

### Q_CORE_TITLE

Confirm or override the derived project title.

Field(s): `/project/title`
Answer type: non_empty_string

### Q_CORE_TOPIC_SLUG

Confirm or override the derived topic slug (lowercase kebab-case, max 64 chars).

Field(s): `/project/topic_slug`
Answer type: non_empty_string

### Q_CORE_PHASE1_VENUE

Where should Phase 1 decomposition run?

Field(s): `/preferences/phase_1_venue`
- a) Auto (Recommended) — High stakes resolves to fresh Claude web; low/medium to local. (value: `"auto"`)
- b) Fresh Claude web — Strongest model with extended thinking at maximum. (value: `"fresh_claude_web"`)
- c) Local session — The locally available Claude model. (value: `"local"`)
- or supply your own typed value

### Q_CORE_PHASE3_VENUE

Where should Phase 3 cross-examination run?

Field(s): `/preferences/phase_3_venue`
- a) Auto (Recommended) — Local by default; fresh Claude web for high stakes or oversized inputs. (value: `"auto"`)
- b) Fresh Claude web — Strongest model in a fresh chat. (value: `"fresh_claude_web"`)
- c) Local session — Acceptable for most projects. (value: `"local"`)
- or supply your own typed value

### Q_CORE_PHASE5_ROUTE

Which Chairman route should Phase 5 prefer?

Field(s): `/preferences/phase_5_route`
- a) Auto (Recommended) — Resolves after the capability/input-budget gate: fresh subagent, then fresh Claude web, then inline. (value: `"auto"`)
- b) Fresh subagent — Preferred when available: fresh context on the strongest model. (value: `"fresh_subagent"`)
- c) Fresh Claude web — Default when a fresh subagent is unavailable. (value: `"fresh_claude_web"`)
- d) Inline — Legal only when freshness and context-fit conditions both pass. (value: `"inline"`)
- or supply your own typed value

### Q_CORE_EXPECTED_LANES

Confirm or override the derived expected Phase-2 lane plan (agent/route/role, canonical inventory order).

Field(s): `/preferences/expected_lanes`
Answer: JSON conforming to `/properties/preferences/properties/expected_lanes`
Example: `[{"agent":"perplexity","role":"evidence","route":"web"},{"agent":"gemini","role":"evidence","route":"web"},{"agent":"grok","role":"sentiment","route":"web"},{"agent":"claude","role":"synthesis","route":"claude_web_extended_thinking"},{"agent":"deepseek","role":"decorrelated","route":"consumer_web"}]`

### Q_CORE_ADDL_RENDERS_UC2

Should Phase 6 also derive a WordPress article from the same dossier?

Field(s): `/preferences/additional_renders`
- a) No additional renders (Recommended) — The YouTube script is the only deliverable. (value: `[]`)
- b) Add WordPress article — Transformed from the dossier in Phase 6; requires a normal-web SERP provider. (value: `["wordpress_article"]`)
- or supply your own typed value

### Q_CORE_ADDL_RENDERS_UC6

Which additional renders should Phase 6 derive from the health protocol?

Field(s): `/preferences/additional_renders`
- a) No additional renders (Recommended) — The health protocol is the only deliverable. (value: `[]`)
- b) YouTube script — Spoken-format derivative with the disclaimer kept in the script. (value: `"youtube_script"`)
- c) WordPress article — MedicalWebPage-schema derivative; requires a normal-web SERP provider. (value: `"wordpress_article"`)
- d) Ebook chapter — One chapter using overlay 05's prose schema only — not a book project. (value: `"ebook_chapter"`)
- [multi-select allowed]
- or supply your own typed value

### Q_CORE_ADDL_RENDERS_UC8

Should Phase 6 also derive a deck + screencast from the Decision Brief?

Field(s): `/preferences/additional_renders`
- a) No additional renders (Recommended) — The Decision Brief is the terminal artifact. (value: `[]`)
- b) Add deck + screencast — One Marp source rendered to both formats for sharing the decision. (value: `["deck_and_screencast"]`)
- or supply your own typed value

### Q_CORE_STANDING_INSTRUCTIONS

Any standing instructions to carry into the run? (Free text; empty is fine. The orchestrator quotes them and asks before activating.)

Field(s): `/standing_instructions`
Answer type: string

### Q_CORE_SEED_AREAS

Seed areas the decomposition should be sure to cover (maximum 8; empty is fine).

Field(s): `/seed_areas`
Answer: JSON conforming to `/properties/seed_areas`
Example: `["pricing models","migration cost"]`

### Q_CORE_OUT_OF_SCOPE

Anything explicitly out of scope? (Empty is fine.)

Field(s): `/out_of_scope`
Answer: JSON conforming to `/properties/out_of_scope`
Example: `["mobile clients"]`

### Q_CORE_KNOWN_TRAPS

Known traps the research must avoid? (Empty is fine.)

Field(s): `/known_traps`
Answer: JSON conforming to `/properties/known_traps`
Example: `["vendor benchmarks are marketing content"]`

### Q_CORE_DECORRELATED_EXCEPTION

Only when no compliant decorrelated route exists and neither Debate nor Red Team is selected: record the last-resort exception (otherwise leave null).

Field(s): `/conduct/decorrelated_exception`
Answer: JSON conforming to `/$defs/decorrelated_exception`
Example: `{"active":true,"reason":"No compliant DeepSeek route exists in this workspace","risk_accepted":true}`

### profile-01-spec-driven-dev — *conditional — answer only if selected*

### Q_P01_TARGET_USERS

Who are the product's target users?

Field(s): `/use_case_profile/product_target_users`
Answer: JSON conforming to `/$defs/profile_spec_driven_dev/properties/product_target_users`
Example: `["Platform engineers at mid-size SaaS companies"]`

### Q_P01_REQUIREMENTS_COVERAGE

For the selected requirements input, attest per item whether it already covers target users and constraints (the operator answers, never the file).

Field(s): `/use_case_profile/requirements_coverage`
Answer: JSON conforming to `/$defs/profile_spec_driven_dev/properties/requirements_coverage`
Example: `{"constraints":false,"product_target_users":true}`

### profile-02-youtube — *conditional — answer only if selected*

### Q_P02_DURATION

Target video length in minutes?

Field(s): `/use_case_profile/video_duration_minutes`
- a) 10 minutes (Recommended) — The overlay's 7-12 minute sweet spot. (value: `10`)
- b) 7 minutes — Tight single-thesis video. (value: `7`)
- c) 12 minutes — Roomier treatment; keep chapters at ~90 seconds. (value: `12`)
- or supply your own typed value

### profile-03-presentation — *conditional — answer only if selected*

### Q_P03_DURATION

Talk duration in minutes?

Field(s): `/use_case_profile/talk_duration_minutes`
- a) 30 minutes (Recommended) — Typical conference slot. (value: `30`)
- b) 20 minutes — Short slot or lightning-plus. (value: `20`)
- c) 45 minutes — Extended session. (value: `45`)
- d) 60 minutes — Workshop-length talk. (value: `60`)
- or supply your own typed value

### Q_P03_SETTING

What is the setting? (conference / client pitch / webinar / internal — free text; examples, not an enum)

Field(s): `/use_case_profile/setting`
Answer type: non_empty_string

### Q_P03_CLIENT_PITCH

Is this a client pitch or capability presentation?

Field(s): `/use_case_profile/client_pitch`
- a) No (Recommended) — A general talk, webinar, or internal session. (value: `false`)
- b) Yes — client pitch — Activates the NotebookLM readiness rule and client material inputs. (value: `true`)
- or supply your own typed value

### Q_P03_CLIENT_MATERIALS

Which classified inputs (IN ids) hold the client's public materials / RFP? (At least one.)

Field(s): `/use_case_profile/client_material_input_ids`
Answer: JSON conforming to `/$defs/profile_presentation/properties/client_material_input_ids`
Example: `["IN1"]`

### profile-04-ebook — *conditional — answer only if selected*

### Q_P04_PRIOR_KNOWLEDGE

What prior knowledge can the reader be assumed to have?

Field(s): `/use_case_profile/prior_knowledge`
Answer type: non_empty_string

### Q_P04_TAKEAWAY

What should the reader be able to do after finishing the book?

Field(s): `/use_case_profile/intended_takeaway`
Answer type: non_empty_string

### Q_P04_WORD_TARGET

Total word target for the book?

Field(s): `/use_case_profile/total_word_target`
- a) 50k words (Recommended) — Mid-length practical book. (value: `50000`)
- b) 30k words — Compact book / long guide. (value: `30000`)
- c) 80k words — Full-length treatment. (value: `80000`)
- or supply your own typed value

### Q_P04_CHAPTERS

Target chapter count (8-15)?

Field(s): `/use_case_profile/chapter_count`
- a) 10 chapters (Recommended) — Comfortable per-chapter research passes. (value: `10`)
- b) 8 chapters — Minimum the overlay supports. (value: `8`)
- c) 12 chapters — Finer-grained structure. (value: `12`)
- d) 15 chapters — Maximum the overlay supports. (value: `15`)
- or supply your own typed value

### Q_P04_FORMAT

Which book format?

Field(s): `/use_case_profile/format`
- a) How-to (Recommended) — Practical, protocol-driven chapters. (value: `"how_to"`)
- b) Narrative — Story-driven through-line. (value: `"narrative"`)
- c) Reference — Look-up structure; chapters stand alone. (value: `"reference"`)
- d) Hybrid — Mixed narrative and reference sections. (value: `"hybrid"`)
- or supply your own typed value

### profile-05-wordpress-seo — *conditional — answer only if selected*

### Q_P05_SITE_NAME

Which site is this article for?

Field(s): `/use_case_profile/site_name`
Answer type: non_empty_string

### Q_P05_PRIMARY_KEYWORD

What is the primary keyword?

Field(s): `/use_case_profile/primary_keyword`
Answer type: non_empty_string

### Q_P05_BRIEF_STATUS

Is a keyword brief already prepared?

Field(s): `/use_case_profile/keyword_brief/status`
- a) Pending (Recommended) — The orchestrator runs the SERP research pre-Phase-1 and writes 00-keyword-brief.md. (value: `"pending"`)
- b) Provided — You supply the brief as a classified input with its SERP numbers. (value: `"provided"`)
- or supply your own typed value

### Q_P05_SERP_PROVIDER

Which provider runs the top-10 SERP analysis in normal web mode?

Field(s): `/use_case_profile/keyword_brief/serp_provider`
- a) Perplexity (Recommended) — Standard (non-Deep) web mode. (value: `"perplexity"`)
- b) Grok — Normal browser search mode. (value: `"grok"`)
- or supply your own typed value

### Q_P05_BRIEF_INPUT

Which classified input (IN id) is the provided keyword brief?

Field(s): `/use_case_profile/keyword_brief/input_id`
Answer type: non_empty_string

### Q_P05_SERP_AVG

Average word count of the current top-10 SERP results (from the provided brief)?

Field(s): `/use_case_profile/keyword_brief/serp_average_word_count`
Answer: JSON conforming to `/$defs/profile_wordpress_seo/properties/keyword_brief/properties/serp_average_word_count`
Example: `2400`

### Q_P05_SEARCH_INTENT

What is the search intent for the primary keyword?

Field(s): `/use_case_profile/search_intent`
- a) Informational (Recommended) — The searcher wants to understand something. (value: `"informational"`)
- b) Commercial — The searcher is comparing options to buy. (value: `"commercial"`)
- c) Transactional — The searcher is ready to act/purchase. (value: `"transactional"`)
- or supply your own typed value

### Q_P05_TARGET_WC

Target article word count (must be at least the SERP average)?

Field(s): `/use_case_profile/target_word_count`
- a) 2500 words (Recommended) — Typical competitive informational article. (value: `2500`)
- b) 1500 words — Lean article for a weak SERP. (value: `1500`)
- c) 4000 words — Pillar-length article. (value: `4000`)
- or supply your own typed value

### Q_P05_SECONDARY_KW

The 3-5 unique secondary keywords from the provided brief.

Field(s): `/use_case_profile/secondary_keywords`
Answer: JSON conforming to `/$defs/profile_wordpress_seo/properties/secondary_keywords`
Example: `["ergonomic keyboard","mechanical switches","wrist strain"]`

### profile-06-health — *conditional — answer only if selected*

### Q_P06_POPULATION

Which population must the evidence cover? (The studied population, not necessarily the reader.)

Field(s): `/use_case_profile/evidence_population`
Answer type: non_empty_string

### Q_P06_INTERVENTION

What intervention or exposure is being researched?

Field(s): `/use_case_profile/intervention_or_exposure`
Answer type: non_empty_string

### Q_P06_OUTCOMES

Which outcomes matter? (At least one.)

Field(s): `/use_case_profile/intended_outcomes`
Answer: JSON conforming to `/$defs/profile_health/properties/intended_outcomes`
Example: `["reduced low-back pain during training"]`

### Q_P06_SAFETY_SCOPE

What is the safety scope — which harms/contraindications must be surfaced alongside efficacy?

Field(s): `/use_case_profile/safety_scope`
Answer type: non_empty_string

### Q_P06_COMMERCIAL

Any commercial relationship touching this content?

Field(s): `/use_case_profile/commercial_relationship`
- a) None (Recommended) — No sponsorship or affiliate ties. (value: `"none"`)
- b) Sponsorship — Activates [POTENTIAL-COI] tagging and disclosure. (value: `"sponsorship"`)
- c) Affiliate — Activates [POTENTIAL-COI] tagging and disclosure. (value: `"affiliate"`)
- d) Both — Sponsorship and affiliate; strictest evidence rules. (value: `"both"`)
- or supply your own typed value

### profile-07-deck-screencast — *conditional — answer only if selected*

### Q_P07_SLIDES

Target slide count? (If you give deck minutes instead, the builder derives a suggestion from overlay 08's ~1 content slide/minute + 3 framing formula and confirms it.)

Field(s): `/use_case_profile/deck_slide_target`
Answer: JSON conforming to `/$defs/profile_deck_screencast/properties/deck_slide_target`
Example: `33`

### Q_P07_DURATION

Target screencast length in minutes?

Field(s): `/use_case_profile/video_duration_minutes`
- a) 10 minutes (Recommended) — Overlay 08's 7-12 minute band, chapters ~90s. (value: `10`)
- b) 7 minutes — Tight technical screencast. (value: `7`)
- c) 12 minutes — Roomier screencast. (value: `12`)
- or supply your own typed value

### profile-08-decision — *conditional — answer only if selected*

### Q_P08_OPTIONS

What are the decision options? (At least two, genuinely distinct.)

Field(s): `/use_case_profile/decision_options`
Answer: JSON conforming to `/$defs/profile_decision/properties/decision_options`
Example: `["Buy the managed service","Self-host the open-source version"]`

### Q_P08_REVERSIBILITY

How reversible is this decision? (Free text — one-way/two-way door framing welcome; no closed enum.)

Field(s): `/use_case_profile/reversibility`
Answer type: non_empty_string

### Q_P08_LEANING

Do you currently lean toward an option? (Optional; the Red Team attacks it if given.)

Field(s): `/use_case_profile/current_leaning`
Answer type: string

## Answers

<!-- BEGIN KICKOFF-ANSWER-SHEET v1 -->
```json
{
  "answer_sheet_schema_version": 1,
  "question_catalog_digest": "83c528fe4983c9d937c6b9f1632494e0a679a4ba8f7e94762d739074f08182f6",
  "generated_framings": [],
  "framing_selection": {
    "selected_ids": [],
    "primary_id": null
  },
  "sheet_instance_digest": "b9d083c79b2b452eda971ee0b2be22534a627f3e76f097b60b1630e9ae26240b",
  "answers": {
    "Q_CORE_RESEARCH_QUESTION": null,
    "Q_CORE_DECISION_CONTEXT": null,
    "Q_CORE_TIME_HORIZON": null,
    "Q_CORE_AUDIENCE": null,
    "Q_CORE_CONFIDENTIALITY": null,
    "Q_CORE_STAKES": null,
    "Q_CORE_CLASSIFIED_INPUTS": null,
    "Q_CORE_GROUND_TRUTH": null,
    "Q_CORE_DOSSIER_ROOT": null,
    "Q_CORE_OUTSIDE_APPROVAL": null,
    "Q_CORE_AGENT_ACCESS": null,
    "Q_CORE_SPEC_MODE": null,
    "Q_CORE_BROWNFIELD_REPO": null,
    "Q_CORE_REQUIREMENTS_INPUT": null,
    "Q_CORE_THESIS": null,
    "Q_CORE_DIFFERENTIATION_HOOK": null,
    "Q_CORE_CONSTRAINTS": null,
    "Q_CORE_ALLOWED_VERDICTS": null,
    "Q_CORE_MODES": null,
    "Q_CORE_TITLE": null,
    "Q_CORE_TOPIC_SLUG": null,
    "Q_CORE_PHASE1_VENUE": null,
    "Q_CORE_PHASE3_VENUE": null,
    "Q_CORE_PHASE5_ROUTE": null,
    "Q_CORE_EXPECTED_LANES": null,
    "Q_CORE_ADDL_RENDERS_UC2": null,
    "Q_CORE_ADDL_RENDERS_UC6": null,
    "Q_CORE_ADDL_RENDERS_UC8": null,
    "Q_CORE_STANDING_INSTRUCTIONS": null,
    "Q_CORE_SEED_AREAS": null,
    "Q_CORE_OUT_OF_SCOPE": null,
    "Q_CORE_KNOWN_TRAPS": null,
    "Q_CORE_DECORRELATED_EXCEPTION": null,
    "Q_P01_TARGET_USERS": null,
    "Q_P01_REQUIREMENTS_COVERAGE": null,
    "Q_P02_DURATION": null,
    "Q_P03_DURATION": null,
    "Q_P03_SETTING": null,
    "Q_P03_CLIENT_PITCH": null,
    "Q_P03_CLIENT_MATERIALS": null,
    "Q_P04_PRIOR_KNOWLEDGE": null,
    "Q_P04_TAKEAWAY": null,
    "Q_P04_WORD_TARGET": null,
    "Q_P04_CHAPTERS": null,
    "Q_P04_FORMAT": null,
    "Q_P05_SITE_NAME": null,
    "Q_P05_PRIMARY_KEYWORD": null,
    "Q_P05_BRIEF_STATUS": null,
    "Q_P05_SERP_PROVIDER": null,
    "Q_P05_BRIEF_INPUT": null,
    "Q_P05_SERP_AVG": null,
    "Q_P05_SEARCH_INTENT": null,
    "Q_P05_TARGET_WC": null,
    "Q_P05_SECONDARY_KW": null,
    "Q_P06_POPULATION": null,
    "Q_P06_INTERVENTION": null,
    "Q_P06_OUTCOMES": null,
    "Q_P06_SAFETY_SCOPE": null,
    "Q_P06_COMMERCIAL": null,
    "Q_P07_SLIDES": null,
    "Q_P07_DURATION": null,
    "Q_P08_OPTIONS": null,
    "Q_P08_REVERSIBILITY": null,
    "Q_P08_LEANING": null
  }
}
```
<!-- END KICKOFF-ANSWER-SHEET v1 -->

## Continuation

After saving this completed sheet, run invocation two (replace the placeholder safely — quote the path for your shell):

> claude -p "Use the research-kickoff-builder skill: continue from the completed headless answer sheet at <saved-sheet-path>. Verify its digests, evaluate the applicable questions, and build the kickoff only when no must_ask value remains; if the sheet is incomplete or stale, emit a delta sheet and make no artifact or config change."

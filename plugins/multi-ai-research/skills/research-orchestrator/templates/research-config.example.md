# Research configuration

This file tells the research skills where to store research dossiers for
this workspace, and which research agents you have access to. Copy it to
the ROOT of your workspace folder as `research-config.md` (the skills also
write it for you on first run).

Dossier root: dossiers/

## Agent access

- Perplexity: {"status":"unknown","tier":null,"routes":[]}
- Gemini: {"status":"unknown","tier":null,"routes":[]}
- Grok: {"status":"unknown","tier":null,"routes":[]}
- ChatGPT: {"status":"unknown","tier":null,"routes":[]}
- Claude: {"status":"unknown","tier":null,"routes":[]}
- DeepSeek route: {"status":"unknown","tier":null,"routes":[]}
- NotebookLM: {"status":"unknown","tier":null,"routes":[]}
- Elicit: {"status":"unknown","tier":null,"routes":[]}
- Consensus: {"status":"unknown","tier":null,"routes":[]}
- Scite: {"status":"unknown","tier":null,"routes":[]}

<!--
How the skills read this file:
- On every run they look for `research-config.md` at the workspace root,
  read the single line beginning "Dossier root:", and create each research
  project as <dossier root>/<topic-slug>/. A relative path (like
  `dossiers/`) resolves against the workspace root — recommended, it
  travels with the workspace. An absolute path also works but is
  machine-specific. If this file is missing, the skill asks once and
  writes your answer here.
- The "## Agent access" section is a workspace-level inventory: one line
  per entry in the form `- <Label>: <compact JSON>` with the exact shape
  {"status":"unknown|available|unavailable","tier":<string|null>,"routes":[...]}.
  Three states:
  * unknown      — not yet asked; the skills ask when a project needs the
                   entry, then record the answer.
  * available    — requires at least one route; tier is an optional short
                   descriptive string (plan name), never credentials,
                   account identifiers, or endpoints.
  * unavailable  — explicitly confirmed absent; not re-asked every
                   project.
- Routes per entry: Claude uses claude_web_extended_thinking|local;
  DeepSeek route uses consumer_web|western_hosted_api|self_hosted; every
  other entry uses web|api. For Perplexity and Grok, "web" means ordinary
  browser search mode is confirmed selectable (needed for SERP work), not
  only a deep-research workflow.
- Scite is Phase-4 verification readiness (required for health content);
  it is never a Phase-2 research lane.
- Legacy free-text lines (e.g. "- Perplexity: Pro" or "none") are read
  conservatively: "none" means unknown, NOT confirmed unavailable. A
  legacy line is left byte-for-byte unchanged until a valid normalized
  entry is ready and you approve persisting it; transient states
  (available without routes, unknown with a tier) are never written.
- Phase 1 assigns research lanes against what you actually hold, per this
  inventory.
- Everything else in this file is ignored by the parsers and preserved by
  updates. To change anything later, edit the lines by hand.
-->

# Research configuration

This file tells the research-orchestrator skill where to store research
dossiers for this workspace, and which research agents you have access to.
Copy it to the ROOT of your workspace folder as `research-config.md` (the
skill also writes it for you on first run).

Dossier root: dossiers/

## Agent access

- Perplexity: none
- Gemini: none
- Grok: none
- ChatGPT: none
- Claude: none
- DeepSeek route: none
- NotebookLM: none
- Elicit: none
- Consensus: none

<!--
How the skill reads this file:
- On every run it looks for `research-config.md` at the workspace root.
- It reads the single line beginning "Dossier root:" and creates each
  research project as <dossier root>/<topic-slug>/.
- It also reads the "## Agent access" section — one line per agent in the
  form "- <agent>: <tier / route / none>" (e.g. "- Perplexity: Pro",
  "- ChatGPT: Pro, Deep Research", "- DeepSeek route: web UI"). This is a
  workspace-level inventory: Phase 1 assigns research lanes against what
  you actually hold, and the skill asks (Step 0.3) only about agents still
  marked "none" or missing, then writes your answers back here.
- Everything else in this file is ignored.
- A relative dossier-root path (like `dossiers/`) resolves against the
  workspace root. Recommended: it travels with the workspace. An absolute
  path also works but is machine-specific.
- If this file is missing, the skill asks once — "Where should dossiers
  for this workspace live?" — and writes your answer here.
- To change anything later, edit the lines by hand.
-->

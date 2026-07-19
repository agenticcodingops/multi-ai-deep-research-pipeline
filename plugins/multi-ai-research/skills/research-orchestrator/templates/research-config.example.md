# Research configuration

This file tells the research-orchestrator skill where to store research
dossiers for this workspace. Copy it to the ROOT of your workspace folder
as `research-config.md` (the skill also writes it for you on first run).

Dossier root: dossiers/

<!--
How the skill reads this file:
- On every run it looks for `research-config.md` at the workspace root.
- It reads the single line beginning "Dossier root:" and creates each
  research project as <dossier root>/<topic-slug>/. Everything else in
  this file is ignored.
- A relative path (like `dossiers/`) resolves against the workspace root.
  Recommended: it travels with the workspace. An absolute path also works
  but is machine-specific.
- If this file is missing, the skill asks once — "Where should dossiers
  for this workspace live?" — and writes your answer here.
- To change the location later, edit the "Dossier root:" line by hand.
-->

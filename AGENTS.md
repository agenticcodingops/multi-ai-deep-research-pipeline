# Agent instructions

## Commit and PR authorship policy (MANDATORY)

Corporate policy prohibits third-party vendor names in version-control
metadata. This repository is public; commit metadata is permanent and
world-readable. This file applies to **every** coding agent and contributor,
regardless of vendor.

**Never write any of the following into a commit message, commit trailer, tag
message, branch name, PR title, or PR body:**

- The name of any AI vendor, assistant product, or model
- `Co-Authored-By:` trailers naming any AI tool or vendor
- `Generated with ...`, `Assisted-By:`, session/permalink URLs to a vendor
- The 🤖 emoji or any equivalent tool-attribution marker

**Authorship rule:** every commit is authored **and** committed by the human
git identity configured in `git config user.name` / `user.email`, and that
address must appear in `.githooks/allowed-authors.txt`. Never set, spoof, or
add an additional author, co-author, or committer. Never pass `--author`.

Write commit messages in the imperative mood, describing only the change.

### Naming files and paths in messages

Some paths in this repository legitimately contain a vendor name (the plugin
manifest directory, the code-review workflow files). Do not name those paths
verbatim in a commit message — refer to them descriptively, e.g. "the plugin
manifest" or "the code-review workflow".

### Enforcement

Enforced mechanically at four layers. Do not attempt to bypass any of them:

| Layer | File | Bypassable? |
|---|---|---|
| Attribution disabled at source | `.claude/settings.json` | n/a |
| Local commit check | `.githooks/commit-msg` | `--no-verify` |
| Local push check | `.githooks/pre-push` | `--no-verify` |
| **Server-side CI** | `.github/workflows/commit-hygiene.yml` | **no** |

Enable the local hooks once per clone:

```sh
sh .githooks/install.sh
```

**Never use `git commit --no-verify` or `git push --no-verify`, and never edit
or disable the hooks to get a commit through.** If a hook blocks you, rewrite
the message. Server-side CI enforces the same rule and will fail the build.

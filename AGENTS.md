# Agent instructions

## Commit and PR authorship policy (MANDATORY)

Corporate policy prohibits third-party vendor names in version-control
metadata. This repository is public; commit metadata is permanent and
world-readable. This file applies to **every** coding agent and contributor,
regardless of vendor.

The purpose of the policy is that no AI vendor, tool or model ever appears as a
contributor to this project.

**Never write any of the following into a commit message, commit trailer, tag
message, branch name, PR title, or PR body**, apart from the
[code-review tool exception](#exception-code-review-tools) for PR titles and bodies:

- The name of any AI vendor, assistant product, or model
- `Co-Authored-By:` trailers naming any AI tool or vendor
- `Generated with ...`, `Assisted-By:`, session/permalink URLs to a vendor
- The 🤖 emoji or any equivalent tool-attribution marker

**Authorship rule:** every commit is authored **and** committed by the human
git identity configured in `git config user.name` / `user.email`, and that
address must appear in `.githooks/allowed-authors.txt`. Never set, spoof, or
add an additional author, co-author, or committer. Never pass `--author`.

**Co-authors:** GitHub lists every co-author of a default-branch commit as a
contributor. The hooks and CI therefore reject any `Co-authored-by` line whose
address is not in `.githooks/allowed-authors.txt`, whatever name it carries.

Write commit messages in the imperative mood, describing only the change.

### Exception: code-review tools

A tool whose product is specifically code review, for example CodeRabbit, may be
named in a PR title or PR body. This includes the summary such a tool adds to a
PR body, with its links and its "auto-generated comment" markers. Leave that
summary in place.

The exception goes no further:

- It does not cover general-purpose AI assistants, coding agents or models, for
  example Claude, Codex, Copilot or Gemini, even when they review code. If a
  review tool's summary names one, remove that name.
- It does not cover `Generated with ...` or `Assisted-By:` lines, even for a
  review tool. CI rejects "generated with", so reword such a line.
- It does not cover commit messages, trailers, tags or branch names.
- No tool, code-review tools included, may be an author, committer or co-author.
  Do not use a "Commit suggestion" button or let a tool push a fix: both can
  make the tool a contributor. Make the change and commit it under the
  configured human identity.

The automated checks do not recognize every tool's name or email address. A
passing check is not permission: follow this policy as written.

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
| **Server-side CI** | `.github/workflows/commit-hygiene.yml` | Not by `--no-verify`, but see below |

The CI check is not a merge gate. `master` has no branch protection, so a direct
push lands before CI runs, and CI then only reports the failure. CI also runs
the guard from the commit under test, so a change to `.githooks/` is reviewed
like any other code change. `tests/test_branding_guard.py` tests the co-author
check, and CI runs it first.

Enable the local hooks once per clone:

```sh
sh .githooks/install.sh
```

**Never use `git commit --no-verify` or `git push --no-verify`, and never edit
or disable the hooks to get a commit through.** If a hook blocks you, rewrite
the message. Server-side CI enforces the same rule and will fail the build.

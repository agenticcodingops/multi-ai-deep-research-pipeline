"""Tests for the authorship guard shared by the hooks and CI.

The guard is a deny list of AI assistants. It blocks an AI assistant as a
commit author, committer or Co-authored-by co-author, and an AI attribution
line (co-author line or "Generated with/by" byline) in PR text. Every other
identity and all other text pass.

Each test builds a throwaway repository holding copies of the real guard and
hooks, so the code under test is the code that ships. Needs git and a POSIX sh.
Run: python3 -I tests/test_branding_guard.py -v
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".githooks"
DEV = "dev@example.org"
ZERO = "0" * 40

# Identities of AI assistants: each must be blocked as author, committer
# and co-author.
AI_IDENTITIES = {
    "general assistant": "Claude <noreply@anthropic.com>",
    "assistant workflow bot": "claude[bot] <209825114+claude[bot]@users.noreply.github.com>",
    "coding agent": "Codex <codex@openai.com>",
    "chat assistant": "ChatGPT <chatgpt@example.com>",
    "copilot agent": "Copilot <198982749+Copilot@users.noreply.github.com>",
    "copilot swe bot": "copilot-swe-agent[bot] <198982749+copilot-swe-agent[bot]@users.noreply.github.com>",
    "editor agent": "Cursor Agent <cursoragent@cursor.com>",
    "terminal agent": "aider <aider@aider.chat>",
    "model vendor": "Gemini <gemini-code-assist@google.com>",
    "build agent": "Grok Build <build@x.ai>",
    "ide agent": "Antigravity <agent@example.com>",
    "async agent": "google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>",
    "hosted agent": "devin-ai-integration[bot] <158243242+devin-ai-integration[bot]@users.noreply.github.com>",
    "spec agent": "kiro-agent[bot] <1+kiro-agent[bot]@users.noreply.github.com>",
    "model name": "Opus 4.1 <x@example.com>",
    "versioned model": "GPT-5 <x@example.com>",
    "spaced model version": "GPT 5 <x@example.com>",
    "vendor only in address": "Bot <noreply@anthropic.com>",
    "vendor domain only": "Agent <x@openai.com>",
    "upper-case name": "CLAUDE <x@example.com>",
}

# Identities that are not AI assistants: each must pass.
OTHER_IDENTITIES = {
    "configured human": f"Dev <{DEV}>",
    "unlisted human": "Teammate <teammate@example.org>",
    "human noreply": "Teammate <12345+teammate@users.noreply.github.com>",
    "human named Devin": "Devin Smith <devin@example.org>",
    "human named Jules": "Jules Verne <jules@example.org>",
    "review bot": "coderabbitai[bot] <136622811+coderabbitai[bot]@users.noreply.github.com>",
    "dependency bot": "dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
    "workflow bot": "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>",
    "web-flow merge": "GitHub <noreply@github.com>",
    "fix-loop bot": "auto-code-scanning-autofix[bot] <autofix@auto-code-scanning.invalid>",
    "scanner bot": "semgrep-app[bot] <1+semgrep-app[bot]@users.noreply.github.com>",
}


class GuardRepo:
    """A temporary repository with the shipped guard and hooks."""

    def __init__(self, name="Dev", email=DEV):
        self.dir = Path(tempfile.mkdtemp(prefix="guard-test-"))
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith("GIT_"):
                del self.env[key]
        self.env.update({
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
        })
        self.git("init", "-q")
        hooks = self.dir / ".githooks"
        hooks.mkdir()
        for hook in ("branding-guard.sh", "commit-msg", "pre-push"):
            shutil.copy(HOOKS / hook, hooks / hook)
            # Git ignores a hook without the executable bit, and the tracked
            # hooks do not carry it (install.sh sets it in each clone).
            (hooks / hook).chmod(0o755)
        self.git("config", "core.hooksPath", ".githooks")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.dir, env=self.env,
                              capture_output=True, text=True, check=check)

    def run_guard(self, script, stdin=""):
        """Source the guard, run a shell snippet; return (exit code, stderr)."""
        proc = subprocess.run(
            ["sh", "-c", ". ./.githooks/branding-guard.sh; " + script],
            cwd=self.dir, env=self.env, input=stdin.encode("utf-8"),
            capture_output=True)
        return proc.returncode, proc.stderr.decode("utf-8", "replace")

    def coauthor(self, message):
        return self.run_guard('coauthor_check "test"', message)

    def identity(self, ident):
        """Run identity_check on "Name <email>"; return (exit code, stderr)."""
        proc = subprocess.run(
            ["sh", "-c", '. ./.githooks/branding-guard.sh; identity_check "$1" author test',
             "sh", ident],
            cwd=self.dir, env=self.env, capture_output=True)
        return proc.returncode, proc.stderr.decode("utf-8", "replace")

    def pr_text(self, body):
        return self.run_guard('attribution_scan "PR body"', body)

    def commit(self, message, **env):
        """Make a real commit through the commit-msg hook; return the exit code."""
        (self.dir / "file.txt").write_text(message, encoding="utf-8")
        self.git("add", "file.txt")
        proc = subprocess.run(["git", "commit", "-q", "-m", message], cwd=self.dir,
                              env={**self.env, **env}, capture_output=True, text=True)
        return proc.returncode

    def pre_push(self, localref, head, base):
        proc = subprocess.run(
            ["sh", ".githooks/pre-push", "origin", "https://example.invalid/r.git"],
            cwd=self.dir, env=self.env, capture_output=True,
            # bytes, so Windows text mode cannot turn the newline into CRLF
            input=f"{localref} {head} refs/heads/main {base}\n".encode())
        return proc.returncode, proc.stderr.decode("utf-8", "replace")

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class RepoTest(unittest.TestCase):

    def setUp(self):
        self.repo = GuardRepo()

    def tearDown(self):
        self.repo.close()


class CoauthorCheckTests(RepoTest):

    def assertPasses(self, message):
        code, err = self.repo.coauthor(message)
        self.assertEqual(code, 0, err)

    def assertBlocks(self, message):
        code, err = self.repo.coauthor(message)
        self.assertEqual(code, 1, f"expected a block for: {message!r}")
        self.assertIn("co-author is an AI assistant", err)

    def test_message_without_coauthor_passes(self):
        self.assertPasses("fix: correct a typo\n\nLonger body.\n")

    def test_every_ai_coauthor_is_blocked(self):
        for label, ident in AI_IDENTITIES.items():
            with self.subTest(label):
                self.assertBlocks(f"fix: x\n\nCo-authored-by: {ident}\n")

    def test_every_other_coauthor_passes(self):
        for label, ident in OTHER_IDENTITIES.items():
            with self.subTest(label):
                self.assertPasses(f"fix: x\n\nCo-authored-by: {ident}\n")

    def test_coauthor_without_address_passes_unless_ai(self):
        self.assertPasses("fix: x\n\nCo-authored-by: Someone\n")
        self.assertBlocks("fix: x\n\nCo-authored-by: Claude\n")

    def test_trailer_key_variants_are_recognized(self):
        ident = AI_IDENTITIES["coding agent"]
        for key in ("co-authored-by:", "CO-AUTHORED-BY:", "   Co-authored-by:",
                    "Coauthored-by:", "Co-Authored-By :"):
            with self.subTest(key):
                self.assertBlocks(f"fix: x\n\n{key} {ident}\n")

    def test_one_bad_line_among_good_ones_blocks(self):
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <{DEV}>\n"
                          f"Co-authored-by: {AI_IDENTITIES['coding agent']}\n")

    def test_crlf_message(self):
        self.assertPasses(f"fix: x\r\n\r\nCo-authored-by: Dev <{DEV}>\r\n")
        self.assertBlocks(f"fix: x\r\n\r\nCo-authored-by: {AI_IDENTITIES['coding agent']}\r\n")

    def test_comment_lines_are_ignored(self):
        self.assertPasses(f"fix: x\n\n# Co-authored-by: {AI_IDENTITIES['coding agent']}\n")

    def test_tool_names_in_free_text_pass(self):
        # Only co-author trailers are checked; subjects and bodies may name tools.
        for message in (
            "ci: bump claude-code-action to v1.0.300\n",
            "fix: correct the review workflow\n\nTouches .claude-plugin/plugin.json"
            " and claude.yml.\n",
            "docs: compare Codex, Copilot, Gemini and Cursor\n",
            "chore: note\n\nGenerated with a script, reviewed by Claude.\n",
            "docs: describe the robot emoji \U0001F916 marker\n",
        ):
            with self.subTest(message):
                self.assertPasses(message)

    def test_other_trailers_are_not_checked(self):
        # A DCO sign-off is not contributor credit, even with a noreply address.
        self.assertPasses("fix: x\n\nSigned-off-by: Dev <1+dev@users.noreply.github.com>\n")
        self.assertPasses("fix: x\n\nReviewed-by: coderabbitai[bot] <r@example.com>\n")


class IdentityCheckTests(RepoTest):

    def test_every_ai_identity_is_blocked(self):
        for label, ident in AI_IDENTITIES.items():
            with self.subTest(label):
                code, err = self.repo.identity(ident)
                self.assertEqual(code, 1, f"expected a block for {ident!r}")
                self.assertIn("is an AI assistant", err)

    def test_every_other_identity_passes(self):
        for label, ident in OTHER_IDENTITIES.items():
            with self.subTest(label):
                code, err = self.repo.identity(ident)
                self.assertEqual(code, 0, err)


class AttributionScanTests(RepoTest):

    def test_ai_attribution_lines_are_blocked(self):
        for body in (
            "Summary.\n\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)\n",
            "Summary.\n\nGenerated with Claude Code\n",
            "Summary.\n\n_Generated by Copilot_\n",
            "Summary.\n\n> Generated by Gemini Code Assist\n",
            "Summary.\n\nCo-authored-by: Claude <noreply@anthropic.com>\n",
            "Summary.\r\n\r\nCo-Authored-By: Codex <codex@openai.com>\r\n",
            "Summary.\n\nGenerated with GPT 5\n",
        ):
            with self.subTest(body):
                code, err = self.repo.pr_text(body)
                self.assertEqual(code, 1, f"expected a block for {body!r}")
                self.assertIn("AI attribution line", err)

    def test_other_text_passes(self):
        for body in (
            "",
            "Bumps anthropics/claude-code-action and the Claude review workflow.\n",
            "Fix: ci: bump claude-code-action\n\nAsked Codex and Gemini for review.\n",
            "This file is generated with make docs.\n",
            "Generated with make docs\n",
            "Co-authored-by: Teammate <teammate@example.org>\n",
            "Signed-off-by: Dev <1+dev@users.noreply.github.com>\n",
            "<!-- This is an auto-generated comment: release notes by coderabbit.ai -->\n"
            "## Summary by CodeRabbit\n- Chores: bump the review action\n",
        ):
            with self.subTest(body):
                code, err = self.repo.pr_text(body)
                self.assertEqual(code, 0, err)


class HookTests(RepoTest):

    def test_commit_msg_hook_blocks_ai_coauthor(self):
        self.assertEqual(
            self.repo.commit(f"fix: x\n\nCo-authored-by: {AI_IDENTITIES['coding agent']}\n"), 1)

    def test_commit_msg_hook_passes_names_and_human_coauthor(self):
        self.assertEqual(self.repo.commit("ci: bump claude-code-action\n"), 0)
        self.assertEqual(
            self.repo.commit(f"fix: y\n\nCo-authored-by: {OTHER_IDENTITIES['review bot']}\n"), 0)

    def test_commit_msg_hook_blocks_ai_author(self):
        code = self.repo.commit("fix: z\n", GIT_AUTHOR_NAME="claude[bot]",
                                GIT_AUTHOR_EMAIL="209825114+claude[bot]@users.noreply.github.com")
        self.assertEqual(code, 1)

    def test_commit_msg_hook_blocks_ai_committer(self):
        code = self.repo.commit("fix: z\n", GIT_COMMITTER_NAME="Claude",
                                GIT_COMMITTER_EMAIL="noreply@anthropic.com")
        self.assertEqual(code, 1)

    def test_commit_msg_hook_passes_bot_author(self):
        code = self.repo.commit("chore(deps): bump x\n", GIT_AUTHOR_NAME="dependabot[bot]",
                                GIT_AUTHOR_EMAIL="49699333+dependabot[bot]@users.noreply.github.com")
        self.assertEqual(code, 0)

    def _two_commits(self, second_message, **env):
        self.assertEqual(self.repo.commit("chore: base\n"), 0)
        subprocess.run(["git", "commit", "-q", "--no-verify", "--allow-empty",
                        "-m", second_message], cwd=self.repo.dir,
                       env={**self.repo.env, **env}, check=True, capture_output=True)
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        base = self.repo.git("rev-parse", "HEAD~1").stdout.strip()
        return head, base

    def test_pre_push_blocks_ai_coauthor(self):
        head, base = self._two_commits(
            f"fix: x\n\nCo-authored-by: {AI_IDENTITIES['coding agent']}\n")
        code, err = self.repo.pre_push("refs/heads/main", head, base)
        self.assertEqual(code, 1, err)
        self.assertIn("co-author is an AI assistant", err)

    def test_pre_push_blocks_ai_author(self):
        head, base = self._two_commits(
            "fix: x\n", GIT_AUTHOR_NAME="Codex", GIT_AUTHOR_EMAIL="codex@openai.com")
        code, err = self.repo.pre_push("refs/heads/main", head, base)
        self.assertEqual(code, 1, err)
        self.assertIn("is an AI assistant", err)

    def test_pre_push_blocks_ai_committer(self):
        head, base = self._two_commits(
            "fix: x\n", GIT_COMMITTER_NAME="Claude", GIT_COMMITTER_EMAIL="noreply@anthropic.com")
        code, err = self.repo.pre_push("refs/heads/main", head, base)
        self.assertEqual(code, 1, err)
        self.assertIn('committer "Claude <noreply@anthropic.com>"', err)

    def test_pre_push_passes_any_branch_name_and_message_text(self):
        head, base = self._two_commits("fix: bump claude-code-action\n\nNamed Claude here.\n")
        for ref in ("refs/heads/claude/issue-12-fix", "refs/heads/fix/anthropic-docs"):
            with self.subTest(ref):
                code, err = self.repo.pre_push(ref, head, base)
                self.assertEqual(code, 0, err)

    def test_pre_push_passes_web_flow_committer(self):
        head, base = self._two_commits(
            "Merge pull request #1\n", GIT_COMMITTER_NAME="GitHub",
            GIT_COMMITTER_EMAIL="noreply@github.com")
        code, err = self.repo.pre_push("refs/heads/main", head, base)
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()

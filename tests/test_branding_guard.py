"""Tests for the co-author allowlist in the commit guard.

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
ALLOWED = "dev@example.org"
OTHER_HUMAN = "teammate@example.org"
ZERO = "0" * 40

UNAPPROVED = {
    "general assistant": "Co-authored-by: Claude <noreply@anthropic.com>",
    "coding agent": "Co-authored-by: Codex <codex@openai.com>",
    "editor agent": "Co-authored-by: Cursor Agent <cursoragent@cursor.com>",
    "terminal agent": "Co-authored-by: aider <aider@aider.chat>",
    "model vendor": "Co-authored-by: Gemini <gemini-code-assist@google.com>",
    "review bot": "Co-authored-by: coderabbitai[bot] "
                  "<136622811+coderabbitai[bot]@users.noreply.github.com>",
    "unlisted human": f"Co-authored-by: Teammate <{OTHER_HUMAN}>",
    "no address": "Co-authored-by: Someone",
    "lower-case key": "co-authored-by: X <x@example.com>",
    "upper-case key": "CO-AUTHORED-BY: X <x@example.com>",
    "indented": "   Co-authored-by: X <x@example.com>",
    "no hyphen": "Coauthored-by: X <x@example.com>",
}


class GuardRepo:
    """A temporary repository with the shipped guard, hooks and an allowlist."""

    def __init__(self, coauthors=None, allowlist=True):
        self.dir = Path(tempfile.mkdtemp(prefix="guard-test-"))
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith("GIT_"):
                del self.env[key]
        self.env.update({
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Dev",
            "GIT_AUTHOR_EMAIL": ALLOWED,
            "GIT_COMMITTER_NAME": "Dev",
            "GIT_COMMITTER_EMAIL": ALLOWED,
        })
        self.git("init", "-q")
        hooks = self.dir / ".githooks"
        hooks.mkdir()
        for name in ("branding-guard.sh", "commit-msg", "pre-push"):
            shutil.copy(HOOKS / name, hooks / name)
            # Git ignores a hook without the executable bit, and the tracked
            # hooks do not carry it (install.sh sets it in each clone).
            (hooks / name).chmod(0o755)
        if allowlist:
            (hooks / "allowed-authors.txt").write_text(
                f"# approved\n{ALLOWED.upper()}\n", encoding="utf-8")
        if coauthors is not None:
            (hooks / "allowed-coauthors.txt").write_text(
                "# approved co-authors\n" + "".join(c + "\n" for c in coauthors),
                encoding="utf-8")
        self.git("config", "core.hooksPath", ".githooks")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.dir, env=self.env,
                              capture_output=True, text=True, check=check)

    def check(self, message):
        """Run coauthor_check on a message; return (exit code, stderr)."""
        proc = subprocess.run(
            ["sh", "-c", '. ./.githooks/branding-guard.sh; coauthor_check "test"'],
            cwd=self.dir, env=self.env, input=message.encode("utf-8"),
            capture_output=True)
        return proc.returncode, proc.stderr.decode("utf-8", "replace")

    def commit(self, message):
        """Make a real commit through the commit-msg hook; return the exit code."""
        (self.dir / "file.txt").write_text(message, encoding="utf-8")
        self.git("add", "file.txt")
        return self.git("commit", "-q", "-m", message, check=False).returncode

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class CoauthorCheckTests(unittest.TestCase):

    def setUp(self):
        self.repo = GuardRepo()

    def tearDown(self):
        self.repo.close()

    def assertPasses(self, message):
        code, err = self.repo.check(message)
        self.assertEqual(code, 0, err)

    def assertBlocks(self, message):
        code, err = self.repo.check(message)
        self.assertEqual(code, 1, f"expected a block for: {message!r}")
        self.assertIn("co-author not approved", err)

    def test_message_without_coauthor_passes(self):
        self.assertPasses("fix: correct a typo\n\nLonger body.\n")

    def test_approved_coauthor_passes_case_insensitively(self):
        self.assertPasses(f"fix: x\n\nCo-authored-by: Dev <{ALLOWED}>\n")

    def test_every_unapproved_coauthor_is_blocked(self):
        for label, line in UNAPPROVED.items():
            with self.subTest(label):
                self.assertBlocks(f"fix: x\n\n{line}\n")

    def test_one_bad_line_among_good_ones_blocks(self):
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <{ALLOWED}>\n"
                          f"{UNAPPROVED['coding agent']}\n")

    def test_crlf_message(self):
        self.assertPasses(f"fix: x\r\n\r\nCo-authored-by: Dev <{ALLOWED}>\r\n")
        self.assertBlocks(f"fix: x\r\n\r\n{UNAPPROVED['coding agent']}\r\n")

    def test_comment_lines_are_ignored(self):
        self.assertPasses(f"fix: x\n\n# {UNAPPROVED['coding agent']}\n")

    def test_address_must_match_exactly(self):
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <x{ALLOWED}>\n")
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <{ALLOWED}.evil>\n")
        # A leading hyphen must not turn the address into a grep option.
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <-e{ALLOWED}>\n")
        self.assertBlocks(f"fix: x\n\nCo-authored-by: Dev <-i>\n")


class AllowlistFileTests(unittest.TestCase):

    def test_missing_allowlist_fails_closed(self):
        repo = GuardRepo(allowlist=False)
        try:
            self.assertEqual(repo.check(f"x\n\nCo-authored-by: D <{ALLOWED}>\n")[0], 1)
            self.assertEqual(repo.check("x\n")[0], 0)
        finally:
            repo.close()

    def test_lists_without_final_newline_stay_separate(self):
        bot = "136622811+coderabbitai[bot]@users.noreply.github.com"
        repo = GuardRepo(coauthors=[bot])
        try:
            hooks = repo.dir / ".githooks"
            (hooks / "allowed-authors.txt").write_text(ALLOWED, encoding="utf-8")
            (hooks / "allowed-coauthors.txt").write_text(bot, encoding="utf-8")
            self.assertEqual(repo.check(f"x\n\nCo-authored-by: D <{ALLOWED}>\n")[0], 0)
            self.assertEqual(repo.check(f"x\n\nCo-authored-by: R <{bot}>\n")[0], 0)
        finally:
            repo.close()

    def test_coauthor_file_extends_the_allowlist(self):
        bot = "136622811+coderabbitai[bot]@users.noreply.github.com"
        repo = GuardRepo(coauthors=[bot])
        try:
            self.assertEqual(repo.check(f"x\n\nCo-authored-by: R <{bot}>\n")[0], 0)
            self.assertEqual(repo.check(f"x\n\n{UNAPPROVED['coding agent']}\n")[0], 1)
        finally:
            repo.close()


class HookTests(unittest.TestCase):

    def setUp(self):
        self.repo = GuardRepo()

    def tearDown(self):
        self.repo.close()

    def test_commit_msg_hook(self):
        self.assertEqual(self.repo.commit(f"fix: x\n\n{UNAPPROVED['coding agent']}\n"), 1)
        self.assertEqual(self.repo.commit(f"fix: x\n\nCo-authored-by: D <{ALLOWED}>\n"), 0)

    def test_pre_push_hook(self):
        self.assertEqual(self.repo.commit("chore: base\n"), 0)
        self.repo.git("commit", "-q", "--no-verify", "--allow-empty",
                      "-m", f"fix: x\n\n{UNAPPROVED['coding agent']}\n")
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        base = self.repo.git("rev-parse", "HEAD~1").stdout.strip()
        proc = subprocess.run(
            ["sh", ".githooks/pre-push", "origin", "https://example.invalid/r.git"],
            cwd=self.repo.dir, env=self.repo.env, capture_output=True,
            # bytes, so Windows text mode cannot turn the newline into CRLF
            input=f"refs/heads/main {head} refs/heads/main {base}\n".encode())
        stderr = proc.stderr.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 1, stderr)
        self.assertIn("co-author not approved", stderr)


if __name__ == "__main__":
    unittest.main()

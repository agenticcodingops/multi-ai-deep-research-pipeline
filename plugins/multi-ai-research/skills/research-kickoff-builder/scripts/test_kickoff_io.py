#!/usr/bin/env python
"""Tests for kickoff_io.py: deterministic rendering, atomic promotion,
config merge, digests, answer-sheet verification, normalization, and the
closed predicate AST.

Race/interruption simulation uses unittest.mock on os.link/os.replace and
pre-created files — never sleeps or threads.
"""

import contextlib
import copy
import errno
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import validate_kickoff as vk  # noqa: E402
import kickoff_io as kio  # noqa: E402
import test_validate_kickoff as tvk  # noqa: E402


def run_cli(args):
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "kickoff_io.py")] + args,
        capture_output=True, text=True)
    report = json.loads(proc.stdout) if proc.stdout.strip() else None
    return proc.returncode, report


# The exact errno set kickoff_io maps to HARDLINK_UNSUPPORTED.
HARDLINK_ERRNOS = (errno.EPERM, errno.EOPNOTSUPP,
                   getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
                   errno.ENOSYS, errno.EACCES, errno.EXDEV)


def run_main_captured(args):
    """In-process kio.main for mocked-FS tests; returns (code, report)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = kio.main(args)
    out = buf.getvalue().strip()
    return code, json.loads(out) if out else None


def write_control(ws, name="pass_uc2_youtube", mutate=None):
    control, _ = tvk.generate_golden(name)
    control = copy.deepcopy(control)
    if mutate:
        mutate(control)
    path = os.path.join(ws, "control.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(control, fh, ensure_ascii=False)
    return control, path


def tree_state(root):
    state = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            state[os.path.relpath(path, root)] = kio.sha256_hex_file(path)
    return state


class RenderTests(unittest.TestCase):
    def test_render_deterministic_and_valid(self):
        with tempfile.TemporaryDirectory() as ws:
            control, cpath = write_control(ws)
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "build"])
            self.assertEqual(code, 0, report)
            self.assertEqual(report["result"], "ok")
            candidate = report["paths"]["candidate"]
            self.assertTrue(candidate.endswith("00-kickoff.draft.md"))
            with open(candidate, "rb") as fh:
                raw = fh.read()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r\n", raw)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            self.assertEqual(
                kio.render_markdown(control, tvk.TEMPLATE).encode("utf-8"),
                raw)

    def test_render_candidate_no_clobber(self):
        with tempfile.TemporaryDirectory() as ws:
            control, cpath = write_control(ws)
            target = os.path.join(ws, "dossiers",
                                  control["project"]["topic_slug"])
            os.makedirs(target)
            candidate = os.path.join(target, "00-kickoff.draft.md")
            with open(candidate, "w", encoding="utf-8") as fh:
                fh.write("stale candidate")
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "build"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "CANDIDATE_EXISTS")
            with open(candidate, "r", encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "stale candidate")

    def test_incomplete_control_writes_nothing(self):
        with tempfile.TemporaryDirectory() as ws:
            def strip(control):
                control["project"]["research_question"] = ""
            _control, cpath = write_control(ws, mutate=strip)
            before = tree_state(ws)
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "build"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "VALIDATION_FAILED")
            self.assertEqual(tree_state(ws), before)

    def test_malformed_control_json_exit2(self):
        with tempfile.TemporaryDirectory() as ws:
            path = os.path.join(ws, "control.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"a": 1,,}')
            code, report = run_cli(["render", path, "--workspace-root",
                                    ws, "--operation", "build"])
            self.assertEqual(code, 2)
            self.assertEqual(report["code"], "MALFORMED_JSON")

    def test_build_rejects_existing_brief_flag(self):
        with tempfile.TemporaryDirectory() as ws:
            _control, cpath = write_control(ws)
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "build",
                                    "--existing-brief",
                                    os.path.join(ws, "00-kickoff.md")])
            self.assertEqual(code, 2)
            self.assertEqual(report["code"], "USAGE")

    def test_refine_requires_existing_brief(self):
        with tempfile.TemporaryDirectory() as ws:
            _control, cpath = write_control(ws)
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "refine"])
            self.assertEqual(code, 2)
            self.assertEqual(report["code"], "USAGE")

    def test_refine_identity_mismatch_is_new_build_request(self):
        with tempfile.TemporaryDirectory() as ws:
            control, cpath = write_control(ws)
            elsewhere = os.path.join(ws, "dossiers", "other-slug")
            os.makedirs(elsewhere)
            existing = os.path.join(elsewhere, "00-kickoff.md")
            with open(existing, "w", encoding="utf-8") as fh:
                fh.write("existing")
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "refine",
                                    "--existing-brief", existing])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "CANDIDATE_NAME")
            self.assertIn("new-build request", report["message"])

    def test_refine_renders_v2_with_before_hash(self):
        with tempfile.TemporaryDirectory() as ws:
            control, cpath = write_control(ws)
            # publish the original first
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "build"])
            self.assertEqual(code, 0, report)
            code, report = run_cli(["finalize",
                                    report["paths"]["candidate"],
                                    "--workspace-root", ws,
                                    "--operation", "build"])
            self.assertEqual(code, 0, report)
            final = report["paths"]["final"]
            original_hash = kio.sha256_hex_file(final)
            def retitle(control):
                control["project"]["title"] = "Refined title"
            _c2, cpath2 = write_control(ws, mutate=retitle)
            os.replace(cpath2, cpath)
            code, report = run_cli(["render", cpath, "--workspace-root",
                                    ws, "--operation", "refine",
                                    "--existing-brief", final])
            self.assertEqual(code, 0, report)
            self.assertTrue(report["paths"]["candidate"]
                            .endswith("00-kickoff.v2.md"))
            self.assertEqual(report["sha256"]["before"], original_hash)

    def test_fence_length_rule_backticks_in_value(self):
        control, _ = tvk.generate_golden("pass_uc2_youtube")
        control = copy.deepcopy(control)
        control["standing_instructions"] = "```json\nnested fence\n```"
        text = kio.render_markdown(control, tvk.TEMPLATE)
        section = text.split("## Standing instructions", 1)[1]
        self.assertIn("````", section)
        report = vk.validate_document(text, tempfile.mkdtemp(), "validate")
        self.assertEqual(report["result"], "pass", report["findings"])

    def test_pretty_json_two_space_non_ascii(self):
        control, _ = tvk.generate_golden("pass_uc2_youtube")
        control = copy.deepcopy(control)
        control["project"]["audience"] = "Ingénieurs sénior — équipe"
        text = kio.render_markdown(control, tvk.TEMPLATE)
        self.assertIn("Ingénieurs sénior — équipe", text)
        self.assertNotIn("\\u00e9", text)


class FinalizeBuildTests(unittest.TestCase):
    def _rendered(self, ws):
        _control, cpath = write_control(ws)
        code, report = run_cli(["render", cpath, "--workspace-root", ws,
                                "--operation", "build"])
        assert code == 0, report
        return report["paths"]["candidate"], report["paths"]["final"]

    def test_publish_links_then_unlinks(self):
        with tempfile.TemporaryDirectory() as ws:
            candidate, final = self._rendered(ws)
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "build"])
            self.assertEqual(code, 0, report)
            self.assertEqual(report["code"], "PUBLISHED")
            self.assertTrue(os.path.isfile(final))
            self.assertFalse(os.path.exists(candidate))
            self.assertEqual(report["sha256"]["after"],
                             kio.sha256_hex_file(final))

    def test_race_final_appears_before_link(self):
        with tempfile.TemporaryDirectory() as ws:
            candidate, final = self._rendered(ws)
            with open(final, "w", encoding="utf-8") as fh:
                fh.write("raced")
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "build"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "COLLISION_FINAL_EXISTS")
            with open(final, "r", encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "raced")
            self.assertTrue(os.path.isfile(candidate))

    def test_context_appears_before_link(self):
        with tempfile.TemporaryDirectory() as ws:
            candidate, final = self._rendered(ws)
            context = os.path.join(os.path.dirname(final),
                                   "00-context.md")
            with open(context, "w", encoding="utf-8") as fh:
                fh.write("context")
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "build"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "COLLISION_FINAL_EXISTS")

    def test_hardlink_unsupported_no_rename_fallback(self):
        for eno in HARDLINK_ERRNOS:
            with self.subTest(errno=errno.errorcode.get(eno, eno)):
                with tempfile.TemporaryDirectory() as ws:
                    candidate, final = self._rendered(ws)
                    calls = {"rename": 0}

                    def deny_link(*_args, **_kwargs):
                        raise OSError(eno, "hard links unsupported")

                    def count_rename(*_args, **_kwargs):
                        calls["rename"] += 1
                        raise AssertionError("rename fallback is forbidden")

                    with mock.patch("os.link", side_effect=deny_link), \
                            mock.patch("os.rename",
                                       side_effect=count_rename), \
                            mock.patch("os.replace",
                                       side_effect=count_rename):
                        code, report = run_main_captured(
                            ["finalize", candidate,
                             "--workspace-root", ws,
                             "--operation", "build"])
                    self.assertEqual(code, 1)
                    self.assertEqual(report["code"], "HARDLINK_UNSUPPORTED")
                    self.assertEqual(calls["rename"], 0)
                    self.assertTrue(os.path.isfile(candidate))
                    self.assertFalse(os.path.exists(final))

    def test_non_pass_candidate_never_finalized(self):
        with tempfile.TemporaryDirectory() as ws:
            candidate, final = self._rendered(ws)
            with open(candidate, "r", encoding="utf-8") as fh:
                text = fh.read()
            with open(candidate, "w", encoding="utf-8") as fh:
                fh.write(text.replace('"topic_slug": "', '"topic_slug": "UPPER-'))
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "build"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "VALIDATION_FAILED")
            self.assertFalse(os.path.exists(final))


class FinalizeRefineTests(unittest.TestCase):
    def _published(self, ws):
        _control, cpath = write_control(ws)
        code, report = run_cli(["render", cpath, "--workspace-root", ws,
                                "--operation", "build"])
        assert code == 0, report
        code, report = run_cli(["finalize", report["paths"]["candidate"],
                                "--workspace-root", ws,
                                "--operation", "build"])
        assert code == 0, report
        final = report["paths"]["final"]

        def retitle(control):
            control["project"]["title"] = "Refined title"
        _c, cpath2 = write_control(ws, mutate=retitle)
        code, report = run_cli(["render", cpath2, "--workspace-root", ws,
                                "--operation", "refine",
                                "--existing-brief", final])
        assert code == 0, report
        return final, report["paths"]["candidate"], \
            kio.sha256_hex_file(final)

    def test_requires_approved(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "refine",
                                    "--expected-final-sha256", before])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "APPROVAL_REQUIRED")

    def test_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "refine", "--approved",
                                    "--expected-final-sha256", "0" * 64])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "HASH_MISMATCH")
            self.assertEqual(kio.sha256_hex_file(final), before)

    def test_replace_success_with_backup(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "refine", "--approved",
                                    "--expected-final-sha256", before])
            self.assertEqual(code, 0, report)
            self.assertEqual(report["code"], "REPLACED")
            backup = report["paths"]["backup"]
            self.assertTrue(os.path.isfile(backup))
            self.assertIn(before[:12], os.path.basename(backup))
            self.assertEqual(kio.sha256_hex_file(backup), before)
            self.assertEqual(report["sha256"]["after"],
                             kio.sha256_hex_file(final))
            self.assertNotEqual(report["sha256"]["after"], before)
            self.assertFalse(os.path.exists(candidate))
            lock = kio._Lock(final)
            self.assertFalse(os.path.exists(lock.path))

    def test_lock_held_blocks_without_mutation(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)
            lock = kio._Lock(final)
            self.assertTrue(lock.acquire("test"))
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "refine", "--approved",
                                    "--expected-final-sha256", before])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "LOCK_HELD")
            self.assertEqual(kio.sha256_hex_file(final), before)
            self.assertTrue(os.path.exists(lock.path))
            lock.release()

    def test_interrupted_replace_leaves_recovery_artifacts(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)

            def boom(*_args, **_kwargs):
                raise OSError(errno.EACCES, "interrupted")

            with mock.patch("os.replace", side_effect=boom):
                with self.assertRaises(OSError):
                    kio.main(["finalize", candidate,
                              "--workspace-root", ws,
                              "--operation", "refine", "--approved",
                              "--expected-final-sha256", before])
            # original intact, backup + candidate recoverable, lock freed
            self.assertEqual(kio.sha256_hex_file(final), before)
            self.assertTrue(os.path.isfile(candidate))
            backups = [p for p in os.listdir(os.path.dirname(final))
                       if p.endswith(".bak")]
            self.assertTrue(backups)
            lock = kio._Lock(final)
            self.assertFalse(os.path.exists(lock.path))

    def test_backup_collision_conflicting_content(self):
        with tempfile.TemporaryDirectory() as ws:
            final, candidate, before = self._published(ws)
            backup = final + "." + before[:12] + ".bak"
            with open(backup, "w", encoding="utf-8") as fh:
                fh.write("conflicting")
            code, report = run_cli(["finalize", candidate,
                                    "--workspace-root", ws,
                                    "--operation", "refine", "--approved",
                                    "--expected-final-sha256", before])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "BACKUP_EXISTS")
            self.assertEqual(kio.sha256_hex_file(final), before)

    def test_backup_hardlink_unsupported_fails_closed(self):
        for eno in HARDLINK_ERRNOS:
            with self.subTest(errno=errno.errorcode.get(eno, eno)):
                with tempfile.TemporaryDirectory() as ws:
                    final, candidate, before = self._published(ws)
                    calls = {"replace": 0}

                    def deny_link(*_args, **_kwargs):
                        raise OSError(eno, "hard links unsupported")

                    def count_replace(*_args, **_kwargs):
                        calls["replace"] += 1
                        raise AssertionError(
                            "os.replace must not run after backup failure")

                    with mock.patch("os.link", side_effect=deny_link), \
                            mock.patch("os.replace",
                                       side_effect=count_replace):
                        code, report = run_main_captured(
                            ["finalize", candidate,
                             "--workspace-root", ws,
                             "--operation", "refine", "--approved",
                             "--expected-final-sha256", before])
                    self.assertEqual(code, 1)
                    self.assertEqual(report["code"], "HARDLINK_UNSUPPORTED")
                    self.assertEqual(calls["replace"], 0)
                    self.assertEqual(kio.sha256_hex_file(final), before)
                    self.assertTrue(os.path.isfile(candidate))
                    backups = [p for p in
                               os.listdir(os.path.dirname(final))
                               if p.endswith(".bak")]
                    self.assertEqual(backups, [])
                    lock = kio._Lock(final)
                    self.assertFalse(os.path.exists(lock.path))


class MergeConfigTests(unittest.TestCase):
    def _updates(self, ws, payload):
        path = os.path.join(ws, "updates.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        return path

    def _config_path(self, ws):
        return os.path.join(ws, "research-config.md")

    def test_missing_config_created_from_template(self):
        with tempfile.TemporaryDirectory() as ws:
            updates = self._updates(ws, {"dossier_root": "dossiers",
                                         "agent_access": {}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 0, report)
            self.assertEqual(report["code"], "CREATED")
            with open(self._config_path(ws), "r", encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("Dossier root: dossiers", text)
            for label in vk.CONFIG_LABELS.values():
                self.assertIn("- %s: " % label, text)
            self.assertIn('"status":"unknown"', text)

    def test_missing_config_requires_root(self):
        with tempfile.TemporaryDirectory() as ws:
            updates = self._updates(ws, {"dossier_root": None,
                                         "agent_access": {}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "REQUIRED_FIELD")

    def test_requires_approved(self):
        with tempfile.TemporaryDirectory() as ws:
            updates = self._updates(ws, {"dossier_root": "dossiers",
                                         "agent_access": {}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "APPROVAL_REQUIRED")

    def test_wrong_path_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            updates = self._updates(ws, {"dossier_root": "dossiers",
                                         "agent_access": {}})
            code, report = run_cli(["merge-config",
                                    os.path.join(ws, "other.md"),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "CONFIG_PATH")

    def _legacy_config(self, ws):
        text = "\n".join([
            "# Research configuration", "",
            "Dossier root: dossiers/", "",
            "## Agent access", "",
            "- Perplexity: Pro",
            "- Gemini: none",
            "- Claude: {\"status\":\"available\",\"tier\":\"Max\","
            "\"routes\":[\"claude_web_extended_thinking\"]}",
            "", "<!-- operator note: keep this comment -->", ""])
        with open(self._config_path(ws), "w", encoding="utf-8") as fh:
            fh.write(text)
        return text

    def test_legacy_lines_preserved_until_replaced(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            updates = self._updates(ws, {
                "dossier_root": None,
                "agent_access": {"perplexity": {
                    "status": "available", "tier": "Pro",
                    "routes": ["web"]}}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 0, report)
            with open(self._config_path(ws), "r", encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn('- Perplexity: {"routes":["web"],'
                          '"status":"available","tier":"Pro"}', text)
            self.assertIn("- Gemini: none", text)  # untouched legacy line
            self.assertIn("<!-- operator note: keep this comment -->",
                          text)
            self.assertIn("Dossier root: dossiers/", text)

    def test_duplicate_known_line_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            with open(self._config_path(ws), "a", encoding="utf-8") as fh:
                fh.write("- Perplexity: Pro again\n")
            updates = self._updates(ws, {"dossier_root": None,
                                         "agent_access": {}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "DUPLICATE_LINE")

    def test_malformed_json_line_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            with open(self._config_path(ws), "w", encoding="utf-8") as fh:
                fh.write("# Research configuration\n\n"
                         "Dossier root: dossiers/\n\n## Agent access\n\n"
                         "- Claude: {\"status\": broken}\n")
            updates = self._updates(ws, {"dossier_root": None,
                                         "agent_access": {}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "MALFORMED_LINE")

    def test_transient_state_rejected(self):
        cases = [
            {"status": "available", "tier": None, "routes": []},
            {"status": "unknown", "tier": "Pro", "routes": []},
        ]
        for entry in cases:
            with self.subTest(entry=entry), \
                    tempfile.TemporaryDirectory() as ws:
                self._legacy_config(ws)
                updates = self._updates(ws, {
                    "dossier_root": None,
                    "agent_access": {"perplexity": entry}})
                code, report = run_cli(
                    ["merge-config", self._config_path(ws),
                     "--updates", updates,
                     "--workspace-root", ws, "--approved"])
                self.assertEqual(code, 1)
                self.assertEqual(report["code"], "TRANSIENT_STATE")

    def test_secret_value_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            updates = self._updates(ws, {
                "dossier_root": None,
                "agent_access": {"perplexity": {
                    "status": "available",
                    "tier": "sk-abcdefghijklmnop1234",
                    "routes": ["web"]}}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "TRANSIENT_STATE")

    def test_unknown_access_id_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            updates = self._updates(ws, {
                "dossier_root": None,
                "agent_access": {"felo": {"status": "unknown",
                                          "tier": None, "routes": []}}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "UNKNOWN_KEY")

    def test_unknown_updates_key_rejected(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            updates = self._updates(ws, {"dossier_root": None,
                                         "agent_access": {},
                                         "extra": 1})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 1)
            self.assertEqual(report["code"], "MALFORMED_JSON")

    def test_idempotent_merge_changed_false(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            updates = self._updates(ws, {
                "dossier_root": None,
                "agent_access": {"claude": {
                    "status": "available", "tier": "Max",
                    "routes": ["claude_web_extended_thinking"]}}})
            code, report = run_cli(["merge-config", self._config_path(ws),
                                    "--updates", updates,
                                    "--workspace-root", ws, "--approved"])
            self.assertEqual(code, 0, report)
            self.assertEqual(report["code"], "UNCHANGED")
            self.assertFalse(report["changed"])

    def test_interrupted_replace_leaves_original(self):
        with tempfile.TemporaryDirectory() as ws:
            self._legacy_config(ws)
            before = kio.sha256_hex_file(self._config_path(ws))
            updates = self._updates(ws, {
                "dossier_root": "elsewhere",
                "agent_access": {}})

            def boom(*_args, **_kwargs):
                raise OSError(errno.EACCES, "interrupted")

            with mock.patch("os.replace", side_effect=boom):
                with self.assertRaises(OSError):
                    kio.main(["merge-config", self._config_path(ws),
                              "--updates", updates,
                              "--workspace-root", ws, "--approved"])
            self.assertEqual(kio.sha256_hex_file(self._config_path(ws)),
                             before)


class IoReportTests(unittest.TestCase):
    def test_report_all_keys_always_present(self):
        with tempfile.TemporaryDirectory() as ws:
            _control, cpath = write_control(ws)
            _code, report = run_cli(["render", cpath, "--workspace-root",
                                     ws, "--operation", "build"])
        self.assertEqual(
            set(report),
            {"io_report_schema_version", "result", "command", "code",
             "changed", "paths", "sha256", "message"})
        self.assertEqual(set(report["paths"]),
                         {"candidate", "final", "config", "backup"})
        self.assertEqual(set(report["sha256"]),
                         {"before", "candidate", "after", "backup"})

    def test_usage_error_exit2(self):
        code, report = run_cli(["render"])
        self.assertEqual(code, 2)
        self.assertEqual(report["code"], "USAGE")


class DigestTests(unittest.TestCase):
    def test_canonical_json_exact_form(self):
        self.assertEqual(kio.canonical_json({"b": 1, "a": "é"}),
                         '{"a":"é","b":1}')

    def test_catalog_digest_deterministic(self):
        catalog = kio.load_question_catalog()
        self.assertEqual(kio.question_catalog_digest(catalog),
                         kio.question_catalog_digest(
                             json.loads(json.dumps(catalog))))

    def test_sheet_instance_digest_composition(self):
        digest = kio.question_catalog_digest([])
        framings = [{"framing_id": "F1", "label": "x", "consequence": "y",
                     "value": {"use_case_id": 1, "decision_shaped": False,
                               "suggested_additional_renders": []}}]
        self.assertEqual(
            kio.sheet_instance_digest(digest, framings),
            kio.sha256_hex_text(kio.canonical_json(
                {"question_catalog_digest": digest,
                 "generated_framings": framings})))

    def _sheet(self, mutate=None):
        catalog = kio.load_question_catalog()
        digest = kio.question_catalog_digest(catalog)
        framings = [
            {"framing_id": "F%d" % i, "label": "Framing %d" % i,
             "consequence": "consequence %d" % i,
             "value": {"use_case_id": i, "decision_shaped": i == 3,
                       "suggested_additional_renders": []}}
            for i in (1, 2, 3)]
        sheet = {
            "answer_sheet_schema_version": 1,
            "question_catalog_digest": digest,
            "generated_framings": framings,
            "framing_selection": {"selected_ids": ["F1"],
                                  "primary_id": "F1"},
            "sheet_instance_digest": kio.sheet_instance_digest(digest,
                                                               framings),
            "answers": {r["question_id"]: None for r in catalog},
        }
        if mutate:
            mutate(sheet)
        return "prefix prose (ignored)\n%s\n```json\n%s\n```\n%s\n" % (
            kio.ANSWER_SHEET_BEGIN,
            json.dumps(sheet, indent=2, ensure_ascii=False),
            kio.ANSWER_SHEET_END)

    def test_verify_answer_sheet_ok(self):
        result = kio.verify_answer_sheet(self._sheet())
        self.assertTrue(result["ok"], result["findings"])

    def test_verify_rejects_stale_catalog_digest(self):
        def stale(sheet):
            sheet["question_catalog_digest"] = "0" * 64
            sheet["sheet_instance_digest"] = kio.sheet_instance_digest(
                "0" * 64, sheet["generated_framings"])
        result = kio.verify_answer_sheet(self._sheet(stale))
        self.assertFalse(result["ok"])
        self.assertTrue(any("stale" in f for f in result["findings"]))

    def test_verify_rejects_tampered_framings(self):
        def tamper(sheet):
            sheet["generated_framings"][0]["value"]["use_case_id"] = 5
        result = kio.verify_answer_sheet(self._sheet(tamper))
        self.assertFalse(result["ok"])
        self.assertTrue(any("sheet_instance_digest" in f
                            for f in result["findings"]))

    def test_verify_rejects_bad_framing_ids(self):
        def bad(sheet):
            sheet["generated_framings"][0]["framing_id"] = "F9"
            digest = sheet["question_catalog_digest"]
            sheet["sheet_instance_digest"] = kio.sheet_instance_digest(
                digest, sheet["generated_framings"])
        result = kio.verify_answer_sheet(self._sheet(bad))
        self.assertFalse(result["ok"])

    def test_verify_rejects_unknown_question_ids(self):
        def extra(sheet):
            sheet["answers"]["Q_FAKE"] = "x"
        result = kio.verify_answer_sheet(self._sheet(extra))
        self.assertFalse(result["ok"])

    def test_verify_rejects_missing_question_ids(self):
        def missing(sheet):
            sheet["answers"].pop("Q_CORE_RESEARCH_QUESTION")
        result = kio.verify_answer_sheet(self._sheet(missing))
        self.assertFalse(result["ok"])

    def test_verify_rejects_duplicate_blocks(self):
        text = self._sheet()
        result = kio.verify_answer_sheet(text + text)
        self.assertFalse(result["ok"])

    def test_verify_rejects_primary_not_selected(self):
        def bad(sheet):
            sheet["framing_selection"] = {"selected_ids": ["F1"],
                                          "primary_id": "F2"}
        result = kio.verify_answer_sheet(self._sheet(bad))
        self.assertFalse(result["ok"])

    def test_shipped_sheet_template_digest_current(self):
        path = os.path.join(kio.SKILL_DIR, "templates",
                            "headless-answer-sheet.md")
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        result = kio.verify_answer_sheet(text)
        # the template is structurally digest-consistent (framings are
        # empty, which is its only expected finding class)
        self.assertIn("question_catalog_digest: %s"
                      % kio.question_catalog_digest(
                          kio.load_question_catalog()),
                      "question_catalog_digest: %s"
                      % result["sheet"]["question_catalog_digest"])
        self.assertEqual(
            result["sheet"]["question_catalog_digest"],
            kio.question_catalog_digest(kio.load_question_catalog()))


class NormalizationTests(unittest.TestCase):
    def test_menu_letter_case_insensitive(self):
        record = tvk.RECORDS["Q_CORE_STAKES"]
        self.assertEqual(kio.normalize_menu_answer(record, "A"), "medium")
        self.assertEqual(kio.normalize_menu_answer(record, "b"), "high")

    def test_menu_exact_label(self):
        record = tvk.RECORDS["Q_CORE_STAKES"]
        self.assertEqual(kio.normalize_menu_answer(record, "High"),
                         "high")

    def test_menu_typed_value(self):
        record = tvk.RECORDS["Q_CORE_STAKES"]
        self.assertEqual(kio.normalize_menu_answer(record, "low"), "low")

    def test_menu_other_validated_against_field_schema(self):
        record = tvk.RECORDS["Q_P02_DURATION"]
        self.assertEqual(kio.normalize_menu_answer(record, 15), 15)
        with self.assertRaises(ValueError):
            kio.normalize_menu_answer(record, 0)

    def test_multiselect_dedupe_catalog_order(self):
        record = tvk.RECORDS["Q_CORE_MODES"]
        self.assertEqual(
            kio.normalize_menu_answer(
                record, ["red-team", "debate", "red-team"]),
            ["debate", "red-team"])

    def test_none_plus_atomic_rejected(self):
        record = tvk.RECORDS["Q_CORE_ADDL_RENDERS_UC6"]
        with self.assertRaises(ValueError):
            kio.normalize_menu_answer(record, [[], "youtube_script"])

    def test_nfc_normalization(self):
        record = tvk.RECORDS["Q_CORE_AUDIENCE"]
        decomposed = "Ingénieurs"
        self.assertEqual(kio.normalize_text_answer(record, decomposed),
                         "Ingénieurs")

    def test_text_trim_preserves_internal(self):
        record = tvk.RECORDS["Q_CORE_STANDING_INSTRUCTIONS"]
        self.assertEqual(
            kio.normalize_text_answer(record, "  a\n\n b\n"), "a\n\n b")

    def test_path_rejects_control_chars(self):
        record = tvk.RECORDS["Q_CORE_DOSSIER_ROOT"]
        with self.assertRaises(ValueError):
            kio.normalize_text_answer(record, "bad\npath")
        self.assertEqual(
            kio.normalize_text_answer(record, "dossiers & files — 'ok'"),
            "dossiers & files — 'ok'")

    def test_structured_strict_json(self):
        record = tvk.RECORDS["Q_CORE_SEED_AREAS"]
        self.assertEqual(
            kio.normalize_structured_answer(record, '["a", "b"]'),
            ["a", "b"])
        with self.assertRaises(ValueError):
            kio.normalize_structured_answer(record, '["a",]')
        with self.assertRaises(ValueError):
            kio.normalize_structured_answer(record, '[1]')

    def test_structured_duplicate_key_rejected(self):
        record = tvk.RECORDS["Q_CORE_DECORRELATED_EXCEPTION"]
        with self.assertRaises(ValueError):
            kio.normalize_structured_answer(
                record, '{"active":true,"active":true,'
                        '"reason":"r","risk_accepted":true}')


class PredicateTests(unittest.TestCase):
    STATE = {"use_case_id": 5, "overlay_13_active": False,
             "control": {"use_case_profile": {
                 "keyword_brief": {"status": "pending"}}}}

    def test_each_predicate_kind(self):
        cases = [
            ({"predicate": "always"}, True),
            ({"predicate": "use_case_in", "ids": [5]}, True),
            ({"predicate": "use_case_in", "ids": [2]}, False),
            ({"predicate": "overlay_13_active", "value": False}, True),
            ({"predicate": "field_equals",
              "path": "/use_case_profile/keyword_brief/status",
              "value": "pending"}, True),
            ({"predicate": "field_state",
              "path": "/project/classified_inputs",
              "state": "empty"}, True),
            ({"predicate": "not", "item": {"predicate": "always"}}, False),
            ({"predicate": "all", "items": [
                {"predicate": "always"},
                {"predicate": "use_case_in", "ids": [5]}]}, True),
            ({"predicate": "any", "items": [
                {"predicate": "use_case_in", "ids": [2]},
                {"predicate": "always"}]}, True),
        ]
        for node, expected in cases:
            with self.subTest(node=node):
                self.assertEqual(
                    kio.evaluate_predicate(node, self.STATE), expected)

    def test_rejections(self):
        bad = [
            {"predicate": "exec", "code": "x"},
            {"predicate": "always", "extra": 1},
            {"predicate": "use_case_in", "ids": []},
            {"predicate": "use_case_in", "ids": [0]},
            {"predicate": "use_case_in", "ids": [True]},
            {"predicate": "overlay_13_active", "value": "yes"},
            {"predicate": "field_equals", "path": "/etc/passwd",
             "value": 1},
            {"predicate": "field_equals",
             "path": "/use_case_profile/keyword_brief/status",
             "value": {"a": 1}},
            {"predicate": "field_state",
             "path": "/use_case_profile/keyword_brief/status",
             "state": "weird"},
            {"predicate": "all", "items": []},
            {"predicate": "not"},
            "not a node",
        ]
        for node in bad:
            with self.subTest(node=node):
                with self.assertRaises(ValueError):
                    kio.evaluate_predicate(node, self.STATE)

    def test_depth_limit(self):
        node = {"predicate": "always"}
        for _ in range(5):
            node = {"predicate": "not", "item": node}
        with self.assertRaises(ValueError):
            kio.evaluate_predicate(node, self.STATE)

    def test_bool_int_disambiguation(self):
        state = {"use_case_id": 3, "overlay_13_active": False,
                 "control": {"use_case_profile": {"client_pitch": True}}}
        self.assertTrue(kio.evaluate_predicate(
            {"predicate": "field_equals",
             "path": "/use_case_profile/client_pitch", "value": True},
            state))
        self.assertFalse(kio.evaluate_predicate(
            {"predicate": "field_equals",
             "path": "/use_case_profile/client_pitch", "value": 1},
            state))


class DerivationTests(unittest.TestCase):
    def test_default_lane_plan_standard(self):
        lanes = kio.derive_expected_lanes(tvk.rich_access(), 2, False)
        self.assertEqual([l["agent"] for l in lanes],
                         ["perplexity", "gemini", "grok", "claude",
                          "deepseek"])
        by_agent = {l["agent"]: l for l in lanes}
        self.assertEqual(by_agent["deepseek"]["role"], "decorrelated")
        self.assertEqual(by_agent["deepseek"]["route"], "consumer_web")
        self.assertEqual(by_agent["grok"]["role"], "sentiment")
        self.assertEqual(by_agent["claude"]["role"], "synthesis")

    def test_confidential_route_precedence(self):
        lanes = kio.derive_expected_lanes(tvk.rich_access(), 1, True)
        by_agent = {l["agent"]: l for l in lanes}
        self.assertEqual(by_agent["deepseek"]["route"], "self_hosted")

    def test_health_adds_mandatory_tools(self):
        lanes = kio.derive_expected_lanes(tvk.rich_access(), 6, False)
        agents = [l["agent"] for l in lanes]
        for agent in ("notebooklm", "elicit", "consensus"):
            self.assertIn(agent, agents)
        self.assertNotIn("scite", agents)

    def test_evidence_floor_fallback_order(self):
        access = tvk.rich_access()
        # only grok + claude + deepseek-unavailable: promote grok
        for agent in ("perplexity", "gemini", "chatgpt", "notebooklm",
                      "elicit", "consensus", "deepseek"):
            access[agent] = {"status": "unavailable", "tier": None,
                             "routes": []}
        lanes = kio.derive_expected_lanes(access, 2, False)
        by_agent = {l["agent"]: l for l in lanes}
        self.assertEqual(by_agent["grok"]["role"], "evidence")

    def test_mode_rules_union_and_order(self):
        self.assertEqual(kio.derive_modes(set()), [])
        self.assertEqual(kio.derive_modes({"novel_problem"}),
                         ["first-principles"])
        self.assertEqual(
            kio.derive_modes({"high_stakes_signoff", "novel_problem"}),
            ["first-principles", "debate", "red-team"])
        self.assertEqual(kio.derive_modes({"prelaunch"}), ["red-team"])

    def test_conduct_constants(self):
        conduct = kio.derive_conduct(6)
        self.assertEqual(conduct["non_cancellable_phases"], [4])
        self.assertTrue(conduct["run_all_phases"])
        self.assertEqual(kio.derive_conduct(2)["non_cancellable_phases"],
                         [])

    def test_layered_overlay_derivation(self):
        self.assertEqual(kio.derive_layered_overlays(3, True),
                         [vk.OVERLAY_13])
        self.assertEqual(kio.derive_layered_overlays(4, True), [])
        self.assertEqual(kio.derive_layered_overlays(8, True), [])
        self.assertEqual(kio.derive_layered_overlays(3, False), [])


class RenderingRoundTripTests(unittest.TestCase):
    def test_plain_text_menu_rendering_shape(self):
        record = tvk.RECORDS["Q_CORE_STAKES"]
        text = kio.render_plain_text_question(record, 3)
        lines = text.split("\n")
        self.assertEqual(lines[0], "3. %s" % record["question"])
        self.assertTrue(lines[1].startswith("   a) Medium (Recommended)"))
        self.assertIn("—", lines[1])
        self.assertEqual(lines[-1], "   or type your own")

    def test_multiselect_marker_rendered(self):
        record = tvk.RECORDS["Q_CORE_MODES"]
        self.assertIn("[multi-select allowed]",
                      kio.render_plain_text_question(record, 1))

    def test_three_surfaces_round_trip_same_typed_value(self):
        # tool-surface value, plain-text letter, and headless typed value
        # must all normalize identically
        record = tvk.RECORDS["Q_CORE_CONFIDENTIALITY"]
        by_tool = kio.normalize_menu_answer(record, "non_confidential")
        by_letter = kio.normalize_menu_answer(record, "a")
        by_label = kio.normalize_menu_answer(
            record, "Non-confidential (Recommended)")
        self.assertEqual(by_tool, by_letter)
        self.assertEqual(by_tool, by_label)


if __name__ == "__main__":
    unittest.main()

"""Tests for validate_config.py against the fixtures in fixtures/config/."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import validate_config as vc

FIXTURES = os.path.join(HERE, "fixtures", "config")
TEMPLATE = os.path.join(HERE, "..", "templates", "research-config.example.md")


def run_cli(name_or_path, extra=None):
    path = name_or_path if os.path.isabs(name_or_path) \
        else os.path.join(FIXTURES, name_or_path)
    argv = [path, "--json"] + list(extra or [])
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), \
            contextlib.redirect_stderr(io.StringIO()):
        code = vc.main(argv)
    output = buffer.getvalue()
    report = json.loads(output) if output.strip() else None
    return code, report


def failure_codes(report):
    return {f["code"] for f in report["failures"]}


def warning_codes(report):
    return {w["code"] for w in report["warnings"]}


class ValidateConfigTests(unittest.TestCase):

    def write_config(self, text, newline="\n"):
        handle, path = tempfile.mkstemp(suffix=".md")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(text)
        return path

    # ---------------------------------------------------------------- passing
    def test_shipped_template_validates_clean(self):
        # The template documents its own reading rules inside an HTML comment,
        # and several of those lines parse as "- Label: value". Without comment
        # masking the template fails its own validator.
        code, report = run_cli(os.path.abspath(TEMPLATE))
        self.assertEqual(code, 0)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["dossier_root"], "dossiers/")
        self.assertEqual(report["summary"],
                         {"v1": 10, "legacy": 0, "invalid": 0, "missing": 0})

    def test_pass_v1_full(self):
        code, report = run_cli("pass_v1_full.md")
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["v1"], 10)
        self.assertEqual(report["warnings"], [])

    def test_legacy_is_loud_but_never_fatal(self):
        # The whole point: an operator who wrote "none" meaning "I don't have
        # this" is read as unknown and re-asked three sessions later. Step 0.3
        # OFFERS to normalize; a red gate here would coerce acceptance.
        code, report = run_cli("pass_legacy_mixed.md")
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "pass")
        classes = {e["label"]: e["class"] for e in report["entries"]}
        self.assertEqual(classes["Perplexity"], "legacy")
        self.assertEqual(classes["NotebookLM"], "legacy")
        self.assertEqual(classes["Elicit"], "legacy")
        self.assertEqual(classes["Gemini"], "v1")
        self.assertEqual(classes["Scite"], "missing")
        for entry in report["entries"]:
            if entry["class"] == "legacy":
                self.assertEqual(entry["read_as"], "unknown")
        text = " ".join(w["message"] for w in report["warnings"])
        self.assertIn("read as UNKNOWN, not as confirmed unavailable", text)
        self.assertIn("legacy_empty", warning_codes(report))

    def test_minimal_root_only_passes(self):
        # Step 0.0 item 2 may write a config with a root and nothing else; a
        # validator that failed that would fail the file the skill just wrote.
        code, report = run_cli("pass_minimal_root_only.md")
        self.assertEqual(code, 0)
        self.assertFalse(report["agent_access_section"])
        self.assertEqual(report["summary"]["missing"], 10)
        self.assertIn("agent_access_section_absent", warning_codes(report))

    def test_prose_bullet_ignored(self):
        # The template promises "everything else in this file is ignored".
        code, report = run_cli("pass_prose_ignored.md")
        self.assertEqual(code, 0)
        self.assertIn("ignored_line", warning_codes(report))

    def test_comment_bullets_masked(self):
        # pass_comment_bullets.md deliberately carries an EXACT known-label
        # bullet (`- Grok: {...unavailable...}`) inside the closed comment —
        # if comment masking were disabled, Grok would parse as an active v1
        # entry instead of missing, so this test observes the masking itself
        # (the earlier fixture held only prose bullets, and the test stayed
        # green with masking off).
        for name in ("pass_comment_bullets.md", "pass_unterminated_comment.md"):
            with self.subTest(fixture=name):
                code, report = run_cli(name)
                self.assertEqual(code, 0)
                classes = {e["label"]: e["class"] for e in report["entries"]}
                self.assertEqual(classes["Perplexity"], "v1")
                self.assertEqual(classes["Grok"], "missing")
                grok = [e for e in report["entries"]
                        if e["label"] == "Grok"][0]
                self.assertEqual(grok["read_as"], "unknown")

    # ---------------------------------------------------------------- failing
    def test_structural_defects_fail(self):
        cases = {
            "fail_no_dossier_root.md": "dossier_root_missing",
            "fail_blank_dossier_root.md": "dossier_root_blank",
            "fail_two_roots.md": "dossier_root_conflict",
            "fail_malformed_json.md": "entry_json_malformed",
            "fail_not_object.md": "entry_shape",
            "fail_bad_status.md": "entry_shape",
            "fail_available_no_routes.md": "entry_shape",
            "fail_unknown_with_tier.md": "entry_shape",
            "fail_unavailable_with_routes.md": "entry_shape",
            "fail_route_not_in_enum.md": "entry_shape",
            "fail_duplicate_routes.md": "entry_shape",
            "fail_extra_key.md": "entry_shape",
            "fail_missing_key.md": "entry_shape",
            "fail_blank_tier.md": "entry_shape",
            "fail_secret_in_tier.md": "secret_like",
            "fail_duplicate_label.md": "duplicate_label",
            "fail_unknown_label_alias.md": "unknown_label_alias",
            "fail_unknown_label_v1_shaped.md": "unknown_label_v1_shaped",
        }
        for name, code_expected in sorted(cases.items()):
            with self.subTest(fixture=name):
                code, report = run_cli(name)
                self.assertEqual(code, 1)
                self.assertIn(code_expected, failure_codes(report))

    def test_invalid_entry_is_classed_invalid(self):
        code, report = run_cli("fail_bad_status.md")
        classes = {e["label"]: e["class"] for e in report["entries"]}
        self.assertEqual(classes["Grok"], "invalid")

    def test_secret_message_names_the_exposure_path(self):
        code, report = run_cli("fail_secret_in_tier.md")
        text = " ".join(f["message"] for f in report["failures"])
        self.assertIn("00-context.md", text)

    def test_secret_anywhere_is_fatal_and_never_echoed(self):
        # Review finding 4: a legacy value carrying `sk-...` exited 0 and the
        # report printed the secret back. The scan now runs over the RAW file
        # — comments and fences included, since a committed secret is a
        # secret wherever markdown hides it — and every surface is redacted.
        sentinel = "sk-ABCDEFGHIJKLMNOP"
        shapes = {
            "legacy value": "- Perplexity: {0}\n".format(sentinel),
            "comment": "<!--\n- Grok: {0}\n-->\n".format(sentinel),
            "fence": "```text\ntoken: {0}\n```\n".format(sentinel),
            "prose": "Remember {0} for later.\n".format(sentinel),
        }
        for label, body in shapes.items():
            with self.subTest(where=label):
                path = self.write_config(
                    "# Research configuration\n\nDossier root: dossiers/\n\n"
                    "## Agent access\n\n" + body)
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer), \
                        contextlib.redirect_stderr(io.StringIO()):
                    code = vc.main([path, "--json"])
                self.assertEqual(code, 1)
                out = buffer.getvalue()
                self.assertNotIn(sentinel, out)
                self.assertIn("secret_like", out)
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    vc.main([path])
                self.assertNotIn(sentinel, buffer.getvalue())

    def test_fenced_config_is_not_active(self):
        # Review finding 8: a fenced `Dossier root: decoy/` example was ACTIVE
        # configuration, and a fenced fake `## Agent access` heading before
        # the real section hid every real entry from validation.
        path = self.write_config("```text\nDossier root: decoy/\n```\n")
        code, report = run_cli(path)
        self.assertEqual(code, 1)
        self.assertIn("dossier_root_missing", failure_codes(report))
        path = self.write_config(
            "# Research configuration\n\nDossier root: dossiers/\n\n"
            "```text\n## Agent access\n\n- Grok: nonsense\n```\n\n"
            "## Agent access\n\n"
            '- Grok: {"status":"maybe","tier":null,"routes":[]}\n')
        code, report = run_cli(path)
        self.assertEqual(code, 1)
        self.assertIn("entry_shape", failure_codes(report))

    def test_markers_inside_hidden_regions_are_inert(self):
        # PR review: comment spans and fence spans were computed independently
        # over the raw text, so an unmatched ``` INSIDE a comment opened a
        # fence that masked the real configuration through EOF — and a `<!--`
        # inside a fence did the same in the other direction. The mask now
        # scans left to right: the first opener claims text through its own
        # closer, and markers inside a claimed region are inert.
        for name in ("pass_fence_marker_in_comment.md",
                     "pass_comment_opener_in_fence.md"):
            with self.subTest(fixture=name):
                code, report = run_cli(name)
                self.assertEqual(code, 0, report)
                self.assertEqual(report["failures"], [])
                self.assertEqual(report["dossier_root"], "dossiers/")
                classes = {e["label"]: e["class"] for e in report["entries"]}
                self.assertEqual(classes["Perplexity"], "v1")

    def test_multiple_active_sections_are_ambiguous(self):
        path = self.write_config(
            "# Research configuration\n\nDossier root: dossiers/\n\n"
            "## Agent access\n\n"
            '- Grok: {"status":"unknown","tier":null,"routes":[]}\n\n'
            "## Agent access\n\n"
            '- Grok: {"status":"unavailable","tier":null,"routes":[]}\n')
        code, report = run_cli(path)
        self.assertEqual(code, 1)
        self.assertIn("agent_access_ambiguous", failure_codes(report))

    def test_duplicate_json_keys_rejected(self):
        # The approved writer (kickoff_io merge-config) rejects duplicate
        # keys; a last-key-wins parse here would pass a line it later refuses.
        path = self.write_config(
            "# Research configuration\n\nDossier root: dossiers/\n\n"
            "## Agent access\n\n"
            '- Grok: {"status":"available","status":"unknown","tier":null,'
            '"routes":[]}\n')
        code, report = run_cli(path)
        self.assertEqual(code, 1)
        self.assertIn("entry_json_malformed", failure_codes(report))

    def test_traversal_root_is_outside_workspace(self):
        # Review finding 9: `../outside` was labelled workspace_relative on
        # the strength of its spelling while resolving outside the workspace.
        workdir = tempfile.mkdtemp(prefix="cfg-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        path = self.write_config("Dossier root: ../outside\n")
        report = vc.run(path, workspace_root=workdir)
        self.assertEqual(report["dossier_root_scope"], "outside_workspace")
        path = self.write_config("Dossier root: nested/../dossiers\n")
        report = vc.run(path, workspace_root=workdir)
        self.assertEqual(report["dossier_root_scope"], "workspace_relative")

    def test_symlink_escape_is_outside_workspace(self):
        workdir = tempfile.mkdtemp(prefix="cfg-")
        outside = tempfile.mkdtemp(prefix="cfg-out-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        link = os.path.join(workdir, "escape")
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("platform does not permit creating symlinks "
                          "(Windows requires developer mode or privilege)")
        path = self.write_config("Dossier root: escape/dossiers\n")
        report = vc.run(path, workspace_root=workdir)
        self.assertEqual(report["dossier_root_scope"], "outside_workspace")

    def test_near_miss_label_is_not_silently_ignored(self):
        # "- DeepSeek:" without " route" would otherwise read as
        # "DeepSeek route missing => unknown" — the same silent-opposite trap.
        code, report = run_cli("fail_unknown_label_alias.md")
        text = " ".join(f["message"] for f in report["failures"])
        self.assertIn("DeepSeek route", text)

    # ------------------------------------------------------- per-agent routes
    def test_route_enums_are_enforced_per_agent(self):
        for agent, routes in sorted(vc.ROUTES_BY_AGENT.items()):
            other = next(r for a, rs in sorted(vc.ROUTES_BY_AGENT.items())
                         for r in rs if r not in routes)
            for route in routes:
                with self.subTest(agent=agent, route=route):
                    self.assertEqual(vc.validate_entry(agent, {
                        "status": "available", "tier": None,
                        "routes": [route]}), [])
            with self.subTest(agent=agent, route=other):
                self.assertTrue(vc.validate_entry(agent, {
                    "status": "available", "tier": None, "routes": [other]}))

    def test_every_label_can_be_legacy_on_its_own(self):
        for agent, label in sorted(vc.CONFIG_LABELS.items()):
            with self.subTest(label=label):
                path = self.write_config(
                    "# Research configuration\n\nDossier root: dossiers/\n\n"
                    "## Agent access\n\n- {0}: none\n".format(label))
                code, report = run_cli(path)
                self.assertEqual(code, 0)
                legacy = [w for w in report["warnings"]
                          if w["code"] == "legacy_entry"]
                self.assertEqual(len(legacy), 1)
                self.assertEqual(legacy[0]["label"], label)

    # ------------------------------------------------------------------- I/O
    def test_missing_file_exits_2(self):
        code, report = run_cli(os.path.join(FIXTURES, "does-not-exist.md"))
        self.assertEqual(code, 2)
        self.assertIsNone(report)

    def test_directory_exits_2(self):
        code, report = run_cli(os.path.abspath(FIXTURES))
        self.assertEqual(code, 2)

    def test_crlf_and_bom_read_identically(self):
        body = ("# Research configuration\n\nDossier root: dossiers/\n\n"
                "## Agent access\n\n"
                '- Grok: {"status":"unknown","tier":null,"routes":[]}\n')
        lf = self.write_config(body)
        crlf = self.write_config(body, newline="\r\n")
        bom = self.write_config(u"﻿" + body)
        reports = [vc.run(p) for p in (lf, crlf, bom)]
        for report in reports:
            self.assertEqual(report["result"], "pass")
            self.assertEqual(report["dossier_root"], "dossiers/")
            self.assertEqual(report["summary"]["v1"], 1)

    def test_never_writes(self):
        # "Offer, never automatic rewrite", locked at the script level.
        source = os.path.join(FIXTURES, "pass_legacy_mixed.md")
        workdir = tempfile.mkdtemp(prefix="cfg-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        path = os.path.join(workdir, "research-config.md")
        shutil.copyfile(source, path)
        def snapshot():
            with open(path, "rb") as fh:
                return fh.read(), os.stat(path).st_mtime_ns

        before = snapshot()
        vc.run(path, workspace_root=workdir)
        after = snapshot()
        self.assertEqual(before, after)
        self.assertEqual(sorted(os.listdir(workdir)), ["research-config.md"])

    # ------------------------------------------------------- workspace root
    def test_workspace_root_is_advisory(self):
        workdir = tempfile.mkdtemp(prefix="cfg-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        code, report = run_cli("pass_v1_full.md", ["--workspace-root", workdir])
        self.assertEqual(code, 0)
        self.assertEqual(report["dossier_root_scope"], "workspace_relative")
        self.assertFalse(report["dossier_root_exists"])
        self.assertFalse(os.listdir(workdir))  # never creates it

    def test_absolute_root_scope(self):
        # Built with os.path.join rather than a fixture: a literal "/srv/..."
        # is NOT absolute under ntpath on Python 3.13, so a fixture would make
        # this assertion platform-dependent and CI runs both OSes.
        workdir = tempfile.mkdtemp(prefix="cfg-")
        outside = tempfile.mkdtemp(prefix="cfg-out-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        inside = self.write_config(
            "Dossier root: {0}\n".format(os.path.join(workdir, "d")))
        self.assertEqual(vc.run(inside, workspace_root=workdir)
                         ["dossier_root_scope"], "absolute_inside_workspace")
        beyond = self.write_config(
            "Dossier root: {0}\n".format(os.path.join(outside, "d")))
        self.assertEqual(vc.run(beyond, workspace_root=workdir)
                         ["dossier_root_scope"], "outside_workspace")

    # ------------------------------------------------------------------- CLI
    def test_human_render_and_exit_codes(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = vc.main([os.path.join(FIXTURES, "pass_legacy_mixed.md")])
        self.assertEqual(code, 0)
        self.assertIn("RESULT: PASS", buffer.getvalue())
        self.assertIn("legacy", buffer.getvalue())
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = vc.main([os.path.join(FIXTURES, "fail_bad_status.md")])
        self.assertEqual(code, 1)
        self.assertIn("RESULT: FAIL", buffer.getvalue())

    def test_help_and_bad_flag(self):
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(vc.main(["--help"]), 0)
            self.assertEqual(vc.main(["--nope"]), 2)

    def test_entries_are_all_ten_in_declaration_order(self):
        code, report = run_cli("pass_minimal_root_only.md")
        self.assertEqual([e["agent"] for e in report["entries"]],
                         list(vc.AGENT_IDS))


if __name__ == "__main__":
    unittest.main()

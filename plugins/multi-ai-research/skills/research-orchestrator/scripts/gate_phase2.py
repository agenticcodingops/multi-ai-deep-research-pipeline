#!/usr/bin/env python3
"""Gate checker for Phase 2 lane outputs (checks C1-C7).

Gates each 02-<lane>.md / 02b-debate-<lane>.md file: echo/answer split, the
six required sections, confidence tags, citations, hidden-span concealment,
claims-vs-delivery, and echo share.

Exit codes: 0 = all lanes pass, 1 = gate failures, 2 = usage/IO error.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

CHECKS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
SENTINEL_RE = re.compile(r"(?m)^\s*===BEGIN LANE OUTPUT===\s*$")
HIDDEN_RE = re.compile(
    r"(?is)<(span|div)\b[^>]*(?:display\s*:\s*none|hidden)[^>]*>(.*?)</\1>")
URL_RE = re.compile(r"https?://[^\s<>\)\]\"']+")
HTTPS_RE = re.compile(r"https://[^\s<>\)\]\"']+")
MARKER_RES = [
    re.compile(r"(?<!\^)\[(\d{1,3})\](?!\()"),
    re.compile(r"\[\^(\d{1,3})\]"),
    re.compile(u"【\\d{1,3}(?:†[^】]{0,80})?】"),
]
TAG_RE = re.compile(r"\[(HIGH|MEDIUM|LOW)\]")
ITEM_RE = re.compile(r"(?m)^\s*\d+[.)]\s")
BULLET_RE = re.compile(u"(?m)^\\s*[-*•]\\s+")
CLAIM_RE = re.compile(
    r"(?i)(all\s+(?:six|6)\s+sections|full\s+(?:six|6)[- ]section"
    r"|sections?\s+(?:above|delivered|as\s+requested|complete))")
HEADING_PREFIX = r"^(?:#{1,6}\s*)?(?:\*\*)?(?:\d+[.)]\s*)?"
SECTIONS = [
    ("tldr", "TL;DR", r"TL;?DR\b"),
    ("findings", "Findings", r"Findings\b"),
    ("conflicts", "Conflicts and uncertainties", r"Conflicts?\b(?:\s+and\s+uncertainties)?"),
    ("wwc", "What would change your recommendation", r"What\s+would\s+change\b"),
    ("sources", "Sources consulted", r"Sources\b(?:\s+consulted)?"),
    ("gaps", "Coverage gaps", r"Coverage\s+gaps?\b"),
]
SECTION_RES = [(key, label, re.compile("(?im)" + HEADING_PREFIX + "(?:" + pattern + ")"))
               for key, label, pattern in SECTIONS]
SECTION_PHRASES = {"tldr": "tl;dr", "findings": "findings section",
                   "conflicts": "conflicts and uncertainties",
                   "wwc": "what would change", "sources": "sources consulted",
                   "gaps": "coverage gap"}
OUT_NAME_RES = [("initial", re.compile(r"^02-([a-z0-9_-]+)\.md$")),
                ("debate", re.compile(r"^02b-debate-([a-z0-9_-]+)\.md$"))]
_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!>~|-])")


class GateUsageError(Exception):
    """Bad CLI usage or unusable input paths; maps to exit code 2."""


def normalize(text):
    """NFC-normalize, drop markdown escapes, strip bold pairs and backticks."""
    text = unicodedata.normalize("NFC", text)
    text = _MD_ESCAPE_RE.sub(r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]*)`", r"\1", text)
    return text


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _distinct_urls(matches):
    return {m.rstrip(".,;:!?") for m in matches}


def _classify(name):
    for kind, rx in OUT_NAME_RES:
        match = rx.match(name)
        if match:
            return kind, match.group(1)
    return None, None


def _prompt_name(kind, lane):
    if kind == "debate":
        return "02b-prompts-debate-{0}.md".format(lane)
    return "02a-prompts-{0}.md".format(lane)


def collect_targets(paths, prompts_dir=None, prompt_file=None):
    targets = []
    for path in paths:
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                kind, lane = _classify(name)
                if kind is not None:
                    targets.append((os.path.join(path, name), kind, lane))
        elif os.path.isfile(path):
            kind, lane = _classify(os.path.basename(path))
            if kind is None:
                kind = "initial"
                lane = os.path.splitext(os.path.basename(path))[0]
            targets.append((path, kind, lane))
        else:
            raise GateUsageError("path not found: {0}".format(path))
    if not targets:
        raise GateUsageError(
            "no lane output files (02-<lane>.md / 02b-debate-<lane>.md) found")
    if prompt_file is not None and len(targets) != 1:
        raise GateUsageError("--prompt is only valid with a single output file")
    resolved = []
    for out_path, kind, lane in targets:
        if prompt_file is not None:
            candidate = prompt_file
        else:
            base = prompts_dir if prompts_dir else os.path.dirname(os.path.abspath(out_path))
            candidate = os.path.join(base, _prompt_name(kind, lane))
        resolved.append((out_path, kind, lane,
                         candidate if os.path.isfile(candidate) else None))
    return resolved


def _head_check(url):
    import http.client
    import ssl
    import urllib.parse
    parts = urllib.parse.urlparse(url)
    scheme = parts.scheme.lower()
    factories = {"https": http.client.HTTPSConnection,
                 "http": http.client.HTTPConnection}
    factory = factories.get(scheme)
    if factory is None:
        return "unsupported scheme '{0}'".format(scheme)
    kwargs = {"timeout": 5}
    if scheme == "https":
        # Certificate verification is explicit (and the default on Python 3.9+).
        kwargs["context"] = ssl.create_default_context()
    connection = factory(parts.netloc, **kwargs)
    try:
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query
        connection.request("HEAD", target)
        response = connection.getresponse()
        if response.status >= 400:
            return "status {0}".format(response.status)
        return None
    except Exception as exc:
        return exc.__class__.__name__
    finally:
        connection.close()


def gate_file(out_path, kind, lane, prompt_path, opts):
    norm = normalize(_read(out_path))
    spans = [m.group(2) for m in HIDDEN_RE.finditer(norm)]
    visible = HIDDEN_RE.sub("", norm)
    notes = []
    prompt_norm = None
    if prompt_path is None:
        notes.append("prompt file not found; prompt-tail fallback unavailable")
    else:
        prompt_norm = normalize(_read(prompt_path))

    checks = {c: {"status": "PASS", "details": []} for c in CHECKS}

    def fail(check, message):
        checks[check]["status"] = "FAIL"
        checks[check]["details"].append(message)

    def warn(check, message):
        if checks[check]["status"] != "FAIL":
            checks[check]["status"] = "WARN"
        checks[check]["details"].append(message)

    # C1: echo/answer split
    sentinel = None
    for match in SENTINEL_RE.finditer(visible):
        sentinel = match
    method = "whole-file"
    answer = visible
    offset = 0
    if sentinel is not None:
        method = "sentinel"
        offset = sentinel.end()
        answer = visible[offset:]
    else:
        tail = None
        if prompt_norm:
            tail_lines = [ln.strip() for ln in prompt_norm.splitlines() if ln.strip()]
            tail = tail_lines[-1] if tail_lines else None
        index = visible.rfind(tail) if tail else -1
        if index >= 0:
            method = "prompt-tail"
            offset = index + len(tail)
            answer = visible[offset:]
        elif prompt_norm:
            probes = [ln.strip() for ln in prompt_norm.splitlines()
                      if len(ln.strip()) >= 20]
            echoed = sum(1 for ln in probes if ln in visible)
            fraction = float(echoed) / len(probes) if probes else 0.0
            if fraction >= 0.30:
                method = "echo-backstop"
                fail("C1", "echo present, boundary indeterminate — re-export with "
                           "the sentinel ({0:.0%} of prompt lines echoed)".format(fraction))
    answer_chars = len(answer.strip())
    if answer_chars < opts["min_answer_chars"]:
        fail("C1", "answer region {0} chars, below the minimum {1}".format(
            answer_chars, opts["min_answer_chars"]))
    checks["C1"]["details"].insert(
        0, "split={0}; answer={1:,} chars".format(method, answer_chars))

    # C2: six required sections
    occurrences = []
    for key, _label, rx in SECTION_RES:
        for match in rx.finditer(answer):
            occurrences.append((match.start(), match.end(), key))
    occurrences.sort()
    starts = [o[0] for o in occurrences]
    sections = {}
    for start, end, key in occurrences:
        if key in sections:
            continue
        line_end = answer.find("\n", end)
        if line_end == -1:
            line_end = len(answer)
        nxt = len(answer)
        for s in starts:
            if s > start:
                nxt = s
                break
        sections[key] = (start, answer[line_end:nxt])
    order = [sections[key][0] for key, _l, _r in SECTIONS if key in sections]
    if order != sorted(order):
        warn("C2", "sections out of canonical order")
    failed_sections = set()
    findings_content = None
    findings_count = 0
    for key, label, _rx in SECTIONS:
        if key not in sections:
            failed_sections.add(key)
            fail("C2", "missing section '{0}'".format(label))
            continue
        content = sections[key][1]
        chars = len(content.strip())
        ok, why = True, ""
        if key == "tldr":
            bullets = len(BULLET_RE.findall(content))
            ok = chars >= 80 or bullets >= 2
            why = "TL;DR too thin ({0} chars, {1} bullet lines)".format(chars, bullets)
        elif key == "findings":
            findings_content = content
            findings_count = len(ITEM_RE.findall(content))
            ok = findings_count >= opts["min_findings"] and chars >= 600
            why = "Findings too thin ({0} numbered items, {1} chars)".format(
                findings_count, chars)
        elif key == "conflicts":
            ok = chars >= 120
            why = "Conflicts section under 120 chars ({0})".format(chars)
        elif key == "wwc":
            ok = chars >= 120
            why = "What-would-change section under 120 chars ({0})".format(chars)
        elif key == "sources":
            section_urls = _distinct_urls(HTTPS_RE.findall(content))
            ok = len(section_urls) >= 3
            why = "Sources section lists {0} distinct https URLs (<3)".format(
                len(section_urls))
        elif key == "gaps":
            ok = chars >= 60
            why = "Coverage-gaps section under 60 chars ({0})".format(chars)
        if not ok:
            failed_sections.add(key)
            fail("C2", "section '{0}' below threshold: {1}".format(label, why))

    # C3: confidence tags on every findings item
    if findings_content is None:
        checks["C3"]["status"] = "-"
        checks["C3"]["details"].append("no Findings section to check")
    else:
        item_starts = [m.start() for m in ITEM_RE.finditer(findings_content)]
        untagged = []
        for i, s in enumerate(item_starts):
            e = item_starts[i + 1] if i + 1 < len(item_starts) else len(findings_content)
            if not TAG_RE.search(findings_content[s:e]):
                untagged.append(i + 1)
        if untagged:
            fail("C3", "findings items missing [HIGH]/[MEDIUM]/[LOW] tags: {0}".format(
                ", ".join(str(i) for i in untagged)))

    # C4: citations
    urls = _distinct_urls(URL_RE.findall(answer))
    dead = sum(len(rx.findall(answer)) for rx in MARKER_RES)
    ratio = float(len(urls)) / max(1, findings_count)
    if len(urls) < 3:
        fail("C4", "only {0} distinct URLs in the answer (<3)".format(len(urls)))
    if ratio < opts["url_ratio"]:
        fail("C4", "URL-per-finding ratio {0:.2f} below {1:.2f}".format(
            ratio, opts["url_ratio"]))
    if dead > len(urls):
        fail("C4", "{0} dead citation markers exceed {1} URLs".format(dead, len(urls)))
    if opts["check_urls"] and urls:
        for url in sorted(urls):
            error = _head_check(url)
            if error:
                warn("C4", "URL check failed for {0}: {1}".format(url, error))

    # C5: concealment in hidden spans
    for i, span in enumerate(spans):
        has_marker = any(rx.search(span) for rx in MARKER_RES) or URL_RE.search(span)
        if has_marker or len(span.strip()) >= 50:
            fail("C5", "references concealed in hidden span — the export is "
                       "damaged (span {0}: {1} chars)".format(i + 1, len(span.strip())))
    if not spans:
        checks["C5"]["details"].append("no hidden spans")

    # C6: claims-vs-delivery
    claim_lines = [line for line in answer.splitlines()
                   if not any(rx.match(line) for _k, _l, rx in SECTION_RES)]
    claim_text = "\n".join(claim_lines)
    claim_low = claim_text.lower()
    generic = CLAIM_RE.search(claim_text) is not None
    named = {key for key, phrase in SECTION_PHRASES.items() if phrase in claim_low}
    broken_named = sorted(named & failed_sections)
    if (generic and failed_sections) or broken_named:
        which = set(broken_named) if broken_named else failed_sections
        labels = [label for key, label, _rx in SECTIONS if key in which]
        fail("C6", "claims delivery of sections the structural check cannot find: "
                   "{0}".format(", ".join(labels)))

    # C7: echo share
    if offset > 0 and len(visible) > 0:
        share = float(offset) / len(visible)
        checks["C7"]["details"].append("echo share {0:.0%}".format(share))
        if share > 0.60:
            warn("C7", "echoed prompt is {0:.0%} of the file".format(share))

    failed = any(checks[c]["status"] == "FAIL" for c in CHECKS)
    return {
        "path": out_path,
        "kind": kind,
        "lane": lane,
        "prompt_path": prompt_path,
        "split_method": method,
        "answer_chars": answer_chars,
        "notes": notes,
        "checks": checks,
        "result": "fail" if failed else "pass",
    }


def run(paths, prompts_dir=None, prompt_file=None, min_findings=3,
        min_answer_chars=1500, url_ratio=0.5, check_urls=False):
    """Gate the given lane outputs and return the report dict."""
    opts = {"min_findings": min_findings, "min_answer_chars": min_answer_chars,
            "url_ratio": url_ratio, "check_urls": check_urls}
    targets = collect_targets(paths, prompts_dir, prompt_file)
    files = [gate_file(out, kind, lane, prompt, opts)
             for out, kind, lane, prompt in targets]
    failed_lanes = sum(1 for f in files if f["result"] == "fail")
    return {
        "result": "fail" if failed_lanes else "pass",
        "failed_lanes": failed_lanes,
        "files": files,
    }


def render_human(report):
    lines = []
    for entry in report["files"]:
        lines.append("File: {0}".format(entry["path"]))
        lines.append("Lane: {0}  split={1}  answer={2:,} chars".format(
            entry["lane"], entry["split_method"], entry["answer_chars"]))
        for note in entry["notes"]:
            lines.append("  note: {0}".format(note))
        for check in CHECKS:
            state = entry["checks"][check]
            detail = "; ".join(state["details"])
            lines.append("  {0} {1}{2}".format(
                check, state["status"], "  " + detail if detail else ""))
        lines.append("")
    if len(report["files"]) > 1:
        names = [entry["lane"] for entry in report["files"]]
        width = max([len(n) for n in names] + [6]) + 2
        lines.append(("Check " + "".join(n.ljust(width) for n in names)).rstrip())
        for check in CHECKS:
            row = "".join(entry["checks"][check]["status"].ljust(width)
                          for entry in report["files"])
            lines.append((check.ljust(6) + row).rstrip())
        lines.append("")
    if report["result"] == "pass":
        lines.append("RESULT: PASS")
    else:
        lines.append("RESULT: FAIL — do not proceed to Phase 3 "
                     "({0} lane failures)".format(report["failed_lanes"]))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(
        prog="gate_phase2",
        description="Gate Phase 2 lane outputs (checks C1-C7).")
    parser.add_argument("paths", nargs="+",
                        help="lane output files or directories to gate")
    parser.add_argument("--prompts-dir", dest="prompts_dir", default=None,
                        help="directory holding the staged prompt files")
    parser.add_argument("--prompt", dest="prompt", default=None,
                        help="explicit prompt file (single output file only)")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit a machine-readable JSON report")
    parser.add_argument("--min-findings", type=int, default=3)
    parser.add_argument("--min-answer-chars", type=int, default=1500)
    parser.add_argument("--url-ratio", type=float, default=0.5)
    parser.add_argument("--check-urls", action="store_true",
                        help="HEAD-request each URL; failures are warnings only")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 2
    try:
        report = run(args.paths, args.prompts_dir, args.prompt, args.min_findings,
                     args.min_answer_chars, args.url_ratio, args.check_urls)
    except (GateUsageError, OSError) as exc:
        sys.stderr.write("error: {0}\n".format(exc))
        return 2
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

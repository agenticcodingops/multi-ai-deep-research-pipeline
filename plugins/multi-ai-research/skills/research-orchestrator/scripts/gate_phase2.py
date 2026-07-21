#!/usr/bin/env python3
"""Gate checker for Phase 2 lane outputs (checks C1-C7).

Gates each 02-<lane>.md / 02b-debate-<lane>.md file: echo/answer split, the
six required sections (or six debate elements), confidence tags, citations,
hidden-markup concealment, claims-vs-delivery, and echo share.

Pipeline per file: normalize -> mask code fences and autolinks for parsing ->
one HTML scan collecting hidden regions, comments, and tag markup -> "scan"
text with concealed/markup spans blanked (fences restored) -> boundary split
on scan -> all positive credit computed from the answer region of scan only.

Exit codes: 0 = all lanes pass, 1 = gate failures, 2 = usage/IO error.
"""

import argparse
import json
import math
import os
import re
import sys
import unicodedata
from html.parser import HTMLParser

CHECKS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
MIN_DEBATE_URLS = 2
SENTINEL_RE = re.compile(r"(?m)^\s*===BEGIN LANE OUTPUT===\s*$")
URL_RE = re.compile(r"https?://[^\s<>\)\]\"']+")
HTTPS_RE = re.compile(r"https://[^\s<>\)\]\"']+")
AUTOLINK_RE = re.compile(r"<https?://[^<>\s]*>")
MARKER_RES = [
    re.compile(r"(?<!\^)\[(\d{1,3})\](?!\()"),
    re.compile(u"\\[\\d{1,3}(?:\\s*[,\\-–]\\s*\\d{1,3})+\\](?!\\()"),
    re.compile(r"\[\^(\d{1,3})\]"),
    re.compile(r"\[\^[A-Za-z][\w-]{0,30}\]"),
    re.compile(u"【\\d{1,3}(?:†[^】]{0,80})?】"),
]
MARKER_WORD_RE = re.compile(
    r"^\^?\s*(HIGH|MEDIUM|LOW|UNVERIFIED|REASONED|SENTIMENT-CONCUR"
    r"|CONTRADICTS-GROUND-TRUTH|GROUND-TRUTH-[A-Z-]+)\s*$")
TAG_RE = re.compile(r"\[(HIGH|MEDIUM|LOW)\]")
REASONED_RE = re.compile(r"\[REASONED\]")
ITEM_RE = re.compile(r"(?m)^\s*\d+[.)]\s")
BULLET_RE = re.compile(u"(?m)^\\s*[-*•]\\s+")
CLAIM_RE = re.compile(
    r"(?i)(all\s+(?:six|6)\s+sections|full\s+(?:six|6)[- ]section"
    r"|sections?\s+(?:above|delivered|as\s+requested|complete))")
_H_PRE = r"^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:\*\*[ \t]*)?(?:\d{1,2}[.)][ \t]*)?"
_H_SUF = r"[ \t]*:?[ \t]*(?:\*\*)?[ \t]*$"
SECTIONS = [
    ("tldr", "TL;DR", r"TL;?DR"),
    ("findings", "Findings", r"(?:Key[ \t]+)?Findings"),
    ("conflicts", "Conflicts and uncertainties",
     r"Conflicts(?:[ \t]+(?:and|&)[ \t]+uncertainties)?"),
    ("wwc", "What would change my mind",
     r"What[ \t]+would[ \t]+change(?:[ \t]+[A-Za-z' ]{1,40})?"),
    ("sources", "Sources consulted", r"Sources(?:[ \t]+consulted)?"),
    ("gaps", "Coverage gaps", r"Coverage[ \t]+gaps?"),
]
SECTION_RES = [(key, label, re.compile("(?im)" + _H_PRE + "(?:" + pattern + ")" + _H_SUF))
               for key, label, pattern in SECTIONS]
SECTION_PHRASES = {"tldr": "tl;dr", "findings": "findings section",
                   "conflicts": "conflicts and uncertainties",
                   "wwc": "what would change", "sources": "sources consulted",
                   "gaps": "coverage gap"}
DEBATE_ELEMENTS = [
    ("position", re.compile(r"(?im)^[^\n]{0,30}\bposition\b[^\n]{0,60}$|\bposition[ \t]*:")),
    ("evidence/reasoning", re.compile(r"(?i)\bevidence\b|\breasoning\b")),
    ("rebuttal", re.compile(r"(?i)\brebutt(?:al|ing)\b|\bcounter[- ]argument\b")),
    ("flip-fact", re.compile(
        r"(?i)\bflip(?:s|ped)?\b|\bwould[ \t]+(?:change|reverse)[ \t]+my[ \t]+position\b")),
    ("key tension", re.compile(r"(?i)\bkey[ \t]+tension\b")),
    ("common ground", re.compile(r"(?i)\bcommon[ \t]+ground\b")),
]
OUT_NAME_RES = [("initial", re.compile(r"^02-([a-z0-9_-]+)\.md$")),
                ("debate", re.compile(r"^02b-debate-([a-z0-9_-]+)\.md$"))]
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
HIDDEN_NAME_SET = {"hidden", "sr-only", "visually-hidden", "screen-reader"}
STYLE_HIDDEN_RE = re.compile(r"(?i)display\s*:\s*none|visibility\s*:\s*hidden")
_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!>~|-])")


class GateUsageError(Exception):
    """Bad CLI usage or unusable input paths; maps to exit code 2."""


def normalize(text):
    """NFC-normalize, drop markdown escapes, strip bold pairs and backticks."""
    text = unicodedata.normalize("NFC", text)
    text = _MD_ESCAPE_RE.sub(r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    return text


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _content_len(text):
    """Length of the whitespace-collapsed text."""
    return len(" ".join(text.split()))


def _distinct_urls(matches):
    return {m.rstrip(".,;:!?") for m in matches}


def _dead_marker_count(text):
    """Count dead citation markers, excluding confidence/verdict tag forms."""
    spans = {}
    for rx in MARKER_RES:
        for match in rx.finditer(text):
            spans[(match.start(), match.end())] = match.group(0)
    count = 0
    for token in spans.values():
        inner = token.strip(u"[]【】")
        if MARKER_WORD_RE.match(inner.upper()):
            continue
        count += 1
    return count


def _fence_intervals(text):
    """Character intervals covering fenced code blocks (``` or ~~~ lines)."""
    intervals = []
    open_start = None
    position = 0
    for line in text.splitlines(True):
        stripped = line.lstrip(" \t")
        indent = len(line) - len(stripped)
        if indent <= 3 and (stripped.startswith("```") or stripped.startswith("~~~")):
            if open_start is None:
                open_start = position
            else:
                intervals.append((open_start, position + len(line)))
                open_start = None
        position += len(line)
    if open_start is not None:
        intervals.append((open_start, len(text)))
    return intervals


def _mask_spans(text, spans):
    """Blank the given (start, end) spans to spaces, preserving newlines."""
    if not spans:
        return text
    chars = list(text)
    for start, end in spans:
        for i in range(max(0, start), min(len(chars), end)):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def _is_concealing(attrs):
    for name, value in attrs:
        lowered = (name or "").lower()
        if lowered == "hidden":
            return True
        if lowered == "style" and value and STYLE_HIDDEN_RE.search(value):
            return True
        if lowered == "class" and value and \
                set(value.lower().split()) & HIDDEN_NAME_SET:
            return True
        if lowered == "id" and value and value.lower() in HIDDEN_NAME_SET:
            return True
    return False


class _HiddenScan(HTMLParser):
    """Single-pass scan collecting hidden regions, comments, and tag markup.

    Offsets index into the fed text. Nested hidden elements merge into one
    region; void tags do not push the stack; stray end tags are ignored; a
    region still open at EOF is finalized with closed=False.
    """

    def __init__(self, text):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.text = text
        starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                starts.append(i + 1)
        self.line_starts = starts
        self.stack = []          # (tag, concealing)
        self.hidden_depth = 0
        self.region_start = 0
        self.region_tag = ""
        self.region_text = []
        self.hidden = []         # (start, end, text, closed, tag)
        self.comments = []       # (start, end, text)
        self.markup = []         # (start, end) of tags outside hidden regions

    def _pos(self):
        lineno, col = self.getpos()
        return self.line_starts[lineno - 1] + col

    def _tag_end(self, start):
        end = self.text.find(">", start)
        return end + 1 if end != -1 else len(self.text)

    def handle_starttag(self, tag, attrs):
        start = self._pos()
        raw = self.get_starttag_text() or ""
        end = start + len(raw)
        concealing = _is_concealing(attrs)
        was_hidden = self.hidden_depth > 0
        if tag in VOID_TAGS:
            if not was_hidden:
                if concealing:
                    self.hidden.append((start, end, "", True, tag))
                else:
                    self.markup.append((start, end))
            return
        self.stack.append((tag, concealing))
        if concealing:
            self.hidden_depth += 1
            if not was_hidden:
                self.region_start = start
                self.region_tag = tag
                self.region_text = []
        elif not was_hidden:
            self.markup.append((start, end))

    def handle_startendtag(self, tag, attrs):
        start = self._pos()
        raw = self.get_starttag_text() or ""
        end = start + len(raw)
        if self.hidden_depth == 0:
            if _is_concealing(attrs):
                self.hidden.append((start, end, "", True, tag))
            else:
                self.markup.append((start, end))

    def handle_endtag(self, tag):
        start = self._pos()
        end = self._tag_end(start)
        was_hidden = self.hidden_depth > 0
        if tag in [t for t, _c in self.stack]:
            while self.stack:
                popped_tag, popped_conceal = self.stack.pop()
                if popped_conceal:
                    self.hidden_depth -= 1
                    if self.hidden_depth == 0:
                        self.hidden.append((self.region_start, end,
                                            "".join(self.region_text), True,
                                            self.region_tag))
                if popped_tag == tag:
                    break
        if not was_hidden and self.hidden_depth == 0:
            self.markup.append((start, end))

    def handle_data(self, data):
        if self.hidden_depth > 0:
            self.region_text.append(data)

    def handle_comment(self, data):
        start = self._pos()
        end = min(start + len(data) + 7, len(self.text))
        if self.hidden_depth > 0:
            self.region_text.append(data)
        else:
            self.comments.append((start, end, data))

    def _swallow_markup(self):
        start = self._pos()
        end = self._tag_end(start)
        if self.hidden_depth == 0:
            self.markup.append((start, end))

    def handle_decl(self, decl):
        self._swallow_markup()

    def unknown_decl(self, data):
        self._swallow_markup()

    def handle_pi(self, data):
        self._swallow_markup()

    def finalize(self):
        self.close()
        if self.hidden_depth > 0:
            self.hidden.append((self.region_start, len(self.text),
                                "".join(self.region_text), False,
                                self.region_tag))
            self.hidden_depth = 0
            del self.stack[:]


def _scan_html(parse_input):
    scanner = _HiddenScan(parse_input)
    scanner.feed(parse_input)
    scanner.finalize()
    return scanner


def _split_boundary(scan, prompt_norm, prompt_exists):
    """Return (method, answer_offset, failure_message_or_None). Fails closed."""
    sentinel = None
    for match in SENTINEL_RE.finditer(scan):
        sentinel = match
    if sentinel is not None:
        return "sentinel", sentinel.end(), None
    usable = prompt_exists and bool(prompt_norm and prompt_norm.strip())
    if not usable:
        return "whole-file", 0, None
    tail_lines = [ln.strip() for ln in prompt_norm.splitlines() if ln.strip()]
    tail = tail_lines[-1] if tail_lines else ""
    if len(tail) >= 12 and scan.count(tail) == 1:
        index = scan.find(tail)
        return "prompt-tail", index + len(tail), None
    probes = [ln.strip() for ln in prompt_norm.splitlines() if len(ln.strip()) >= 20]
    echoed = sum(1 for probe in probes if probe in scan)
    prompt_line_set = set(tail_lines)
    prefix = 0
    for line in scan.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in prompt_line_set:
            prefix += 1
        else:
            break
    if echoed or prefix:
        return ("echo-backstop", 0,
                "echo present, boundary indeterminate — re-export with the "
                "sentinel ({0} prompt line(s) echoed, {1} leading line(s) match "
                "the prompt)".format(echoed, prefix))
    return ("unsplit", 0,
            "no sentinel and the staged prompt's final line not found; boundary "
            "unverifiable — re-export with the sentinel")


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
    if prompts_dir is not None and not os.path.isdir(prompts_dir):
        raise GateUsageError("--prompts-dir is not a directory: {0}".format(prompts_dir))
    if prompt_file is not None and not os.path.isfile(prompt_file):
        raise GateUsageError("--prompt file not found: {0}".format(prompt_file))
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


def _vet_url(url):
    """Vet a URL before any connection is attempted. (host, port, error)."""
    import ipaddress
    import socket
    import urllib.parse
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() != "https":
        return None, None, "non-https URL rejected"
    if parts.username or parts.password:
        return None, None, "credentials in URL rejected"
    host = parts.hostname
    if not host:
        return None, None, "URL without hostname rejected"
    lowered = host.lower().rstrip(".")
    if lowered == "localhost" or lowered.endswith(".localhost") or \
            lowered.endswith(".local"):
        return None, None, "non-public hostname rejected"
    try:
        port = parts.port or 443
    except ValueError:
        return None, None, "invalid port rejected"
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return None, None, "DNS resolution failed"
    except OSError:
        return None, None, "address lookup failed"
    for info in infos:
        ip_text = str(info[4][0]).split("%")[0]
        try:
            addr = ipaddress.ip_address(ip_text)
        except ValueError:
            return None, None, "unparseable resolved address rejected"
        mapped = getattr(addr, "ipv4_mapped", None)
        if mapped is not None:
            addr = mapped
        if (not addr.is_global) or addr.is_multicast or \
                str(addr) == "169.254.169.254":
            return None, None, "non-public address rejected"
    return host, port, None


def _head_check(url):
    import http.client
    import ssl
    import urllib.parse
    host, port, error = _vet_url(url)
    if error:
        return error
    parts = urllib.parse.urlsplit(url)
    target = parts.path or "/"
    if parts.query:
        target += "?" + parts.query
    connection = None
    try:
        factory = http.client.HTTPSConnection
        # Certificate verification is explicit (and the default on Python 3.9+).
        connection = factory(host, port, timeout=5,
                             context=ssl.create_default_context())
        connection.request("HEAD", target)
        response = connection.getresponse()
        if response.status >= 400:
            return "status {0}".format(response.status)
        return None
    except Exception as exc:
        return exc.__class__.__name__
    finally:
        if connection is not None:
            connection.close()


def gate_file(out_path, kind, lane, prompt_path, opts):
    norm = normalize(_read(out_path))
    fences = _fence_intervals(norm)
    parse_input = _mask_spans(norm, fences)
    parse_input = AUTOLINK_RE.sub(lambda m: " " * len(m.group(0)), parse_input)
    scanner = _scan_html(parse_input)
    concealed = [(r[0], r[1]) for r in scanner.hidden] + \
                [(c[0], c[1]) for c in scanner.comments] + list(scanner.markup)
    scan = _mask_spans(norm, concealed)
    heading_full = _mask_spans(scan, fences)

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

    # C1: echo/answer split (fails closed on an unverifiable boundary)
    method, offset, boundary_error = _split_boundary(
        scan, prompt_norm, prompt_path is not None)
    if boundary_error:
        fail("C1", boundary_error)
    answer_scan = scan[offset:]
    heading_answer = heading_full[offset:]
    answer_chars = _content_len(answer_scan)
    if answer_chars < opts["min_answer_chars"]:
        fail("C1", "answer region {0} content chars, below the minimum {1}".format(
            answer_chars, opts["min_answer_chars"]))
    checks["C1"]["details"].insert(
        0, "split={0}; answer={1:,} chars".format(method, answer_chars))

    failed_sections = set()
    findings_content = None
    findings_count = 0

    if kind == "debate":
        # C2 slot: the six debate elements
        for name, rx in DEBATE_ELEMENTS:
            if not rx.search(heading_answer):
                fail("C2", "missing debate element '{0}'".format(name))
        # C3 slot: at least one [REASONED] tag
        if not REASONED_RE.search(answer_scan):
            fail("C3", "missing [REASONED] tag in the debate answer")
        checks["C6"]["status"] = "-"
        checks["C6"]["details"].append("not applicable to debate outputs")
    else:
        # C2: six required sections; headings located on heading_answer,
        # content credit taken from answer_scan at the same offsets.
        occurrences = []
        for key, _label, rx in SECTION_RES:
            for match in rx.finditer(heading_answer):
                occurrences.append((match.start(), match.end(), key))
        occurrences.sort()
        starts = [o[0] for o in occurrences]
        sections = {}
        for start, end, key in occurrences:
            if key in sections:
                continue
            line_end = heading_answer.find("\n", end)
            if line_end == -1:
                line_end = len(heading_answer)
            nxt = len(heading_answer)
            for s in starts:
                if s > start:
                    nxt = s
                    break
            sections[key] = (start, answer_scan[line_end:nxt])
        order = [sections[key][0] for key, _l, _r in SECTIONS if key in sections]
        if order != sorted(order):
            warn("C2", "sections out of canonical order")
        for key, label, _rx in SECTIONS:
            if key not in sections:
                failed_sections.add(key)
                fail("C2", "missing section '{0}'".format(label))
                continue
            content = sections[key][1]
            chars = _content_len(content)
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

    # C4: citations (only https URLs earn credit)
    https_urls = _distinct_urls(HTTPS_RE.findall(answer_scan))
    dead = _dead_marker_count(answer_scan)
    floor = MIN_DEBATE_URLS if kind == "debate" else 3
    if len(https_urls) < floor:
        fail("C4", "only {0} distinct https URLs in the answer (<{1})".format(
            len(https_urls), floor))
    if kind != "debate":
        ratio = float(len(https_urls)) / max(1, findings_count)
        if ratio < opts["url_ratio"]:
            fail("C4", "URL-per-finding ratio {0:.2f} below {1:.2f}".format(
                ratio, opts["url_ratio"]))
    if dead > 0 and dead >= len(https_urls):
        fail("C4", "{0} dead citation markers meet or exceed {1} https URLs".format(
            dead, len(https_urls)))
    if opts["check_urls"] and https_urls:
        ordered = sorted(https_urls)
        if len(ordered) > 20:
            notes.append("URL check truncated to 20 of {0} URLs".format(len(ordered)))
            ordered = ordered[:20]
        for url in ordered:
            error = _head_check(url)
            if error:
                warn("C4", "URL check failed for {0}: {1}".format(url, error))

    # C5: concealment in hidden regions and comments (pre-answer echo exempt)
    for index, region in enumerate(scanner.hidden):
        start, end, text, closed, tag = region
        if end <= offset:
            continue
        if not closed:
            fail("C5", "malformed hidden markup — unclosed <{0}>".format(tag))
            continue
        if _dead_marker_count(text) > 0 or URL_RE.search(text) or \
                _content_len(text) >= 50:
            fail("C5", "references concealed in hidden span — the export is "
                       "damaged (span {0}: {1} content chars)".format(
                           index + 1, _content_len(text)))
    for index, comment in enumerate(scanner.comments):
        start, end, text = comment
        if end <= offset:
            continue
        if _dead_marker_count(text) > 0 or URL_RE.search(text) or \
                _content_len(text) >= 50:
            fail("C5", "references concealed in hidden comment — the export is "
                       "damaged (comment {0}: {1} content chars)".format(
                           index + 1, _content_len(text)))
    if not scanner.hidden and not scanner.comments:
        checks["C5"]["details"].append("no hidden spans or comments")

    # C6: claims-vs-delivery (initial outputs only; "-" for debate above)
    if kind != "debate":
        claim_lines = [line for line in answer_scan.splitlines()
                       if not any(rx.match(line) for _k, _l, rx in SECTION_RES)]
        claim_text = "\n".join(claim_lines)
        claim_low = claim_text.lower()
        generic = CLAIM_RE.search(claim_text) is not None
        named = {key for key, phrase in SECTION_PHRASES.items() if phrase in claim_low}
        broken_named = sorted(named & failed_sections)
        if (generic and failed_sections) or broken_named:
            which = set(broken_named) if broken_named else failed_sections
            labels = [label for key, label, _rx in SECTIONS if key in which]
            fail("C6", "claims delivery of sections the structural check cannot "
                       "find: {0}".format(", ".join(labels)))

    # C7: echo share
    if offset > 0 and len(scan) > 0:
        share = float(offset) / len(scan)
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
    files = []
    for out_path, kind, lane, prompt in targets:
        try:
            files.append(gate_file(out_path, kind, lane, prompt, opts))
        except Exception as exc:
            checks = {c: {"status": "PASS", "details": []} for c in CHECKS}
            checks["C1"] = {"status": "FAIL",
                            "details": ["internal error: {0}: {1}".format(
                                exc.__class__.__name__, exc)]}
            files.append({"path": out_path, "kind": kind, "lane": lane,
                          "prompt_path": prompt, "split_method": "error",
                          "answer_chars": 0, "notes": [], "checks": checks,
                          "result": "fail"})
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


def _nonneg_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            "expected a non-negative integer, got {0!r}".format(value))
    if number < 0:
        raise argparse.ArgumentTypeError(
            "expected a non-negative integer, got {0!r}".format(value))
    return number


def _pos_ratio(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            "expected a positive ratio, got {0!r}".format(value))
    if not (math.isfinite(number) and 0 < number <= 10):
        raise argparse.ArgumentTypeError(
            "expected a finite ratio in (0, 10], got {0!r}".format(value))
    return number


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
    parser.add_argument("--min-findings", type=_nonneg_int, default=3)
    parser.add_argument("--min-answer-chars", type=_nonneg_int, default=1500)
    parser.add_argument("--url-ratio", type=_pos_ratio, default=0.5)
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

#!/bin/sh
# Shared authorship guard.
# Sourced by .githooks/commit-msg and .githooks/pre-push, and invoked by CI.
# Single source of truth for the patterns.
#
# Scope (see AGENTS.md):
#   - No AI assistant may be a commit author, committer or Co-authored-by
#     co-author. This is a deny list: every other identity passes, humans and
#     code-quality, dependency, release and workflow bots included.
#   - PR text may not carry an AI attribution line: a Co-authored-by line
#     naming an AI assistant, or a "Generated with/by <AI assistant>" byline.
# Nothing else is scanned. Tool names in commit subjects and bodies, branch
# names, tags, PR titles, prose and files are fine. A Signed-off-by line is
# not contributor credit and is never checked.

# AI-assistant identities, matched as whole tokens (case-insensitive) in an
# author, committer or co-author identity "Name <email>", or in a byline.
# Ambiguous given names are matched only in their bot forms (devin-ai...,
# google-labs-jules, kiro...[bot]) so a human called Devin, Jules or Kiro passes.
AI_ERE='(^|[^a-z0-9])(claude|anthropic|openai|chatgpt|codex|copilot|gemini|cursor|cursoragent|aider|grok|x\.ai|xai|antigravity|devin-ai[a-z0-9-]*|google-labs-jules|kiro[a-z0-9-]*\[bot\]|kiro\.dev|opus|sonnet|haiku|fable|gpt[- ]?[0-9][a-z0-9.]*)([^a-z0-9]|$)'

# A co-author trailer key. Commits: at the start of a line.
COAUTHOR_ERE='^[[:space:]]*co-?authored-?by[[:space:]]*:'

# PR text: a co-author line or a "Generated with/by" byline, allowing a
# leading emoji, quote or list marker.
PR_COAUTHOR_ERE='^[^[:alnum:]]*co-?authored-?by[[:space:]]*:'
PR_BYLINE_ERE='^[^[:alnum:]]*generated[[:space:]]+(with|by)[[:space:]]'

# Returns 0 if $1 names an AI assistant.
is_ai_identity() {
    printf '%s\n' "$1" | grep -q -i -E "$AI_ERE" 2>/dev/null
}

# No co-author may be an AI assistant. GitHub lists each co-author of a
# default-branch commit as a contributor.
# Message on stdin; $1 = human-readable label. Returns 1 if any co-author fails.
coauthor_check() {
    _label="$1"
    _lines=$(tr -d '\r' | sed '/^[[:space:]]*#/d' \
             | grep -i -E "$COAUTHOR_ERE" 2>/dev/null)
    [ -n "$_lines" ] || return 0
    _cfail=0
    while IFS= read -r _line; do
        _who=$(printf '%s\n' "$_line" | sed 's/^[^:]*:[[:space:]]*//')
        if is_ai_identity "$_who"; then
            printf 'BLOCKED: co-author is an AI assistant in %s:\n    %s\n' "$_label" \
                   "$(printf '%s' "$_line" | sed 's/^[[:space:]]*//')" >&2
            _cfail=1
        fi
    done <<EOF
$_lines
EOF
    return "$_cfail"
}

# An author or committer must not be an AI assistant.
# $1 = identity "Name <email>", $2 = role label, $3 = commit ref (optional)
identity_check() {
    _ident="$1"; _role="$2"; _ref="$3"
    if is_ai_identity "$_ident"; then
        printf 'BLOCKED: %s "%s" of %s is an AI assistant.\n' \
               "$_role" "$_ident" "${_ref:-commit}" >&2
        return 1
    fi
    return 0
}

# PR or issue text on stdin; $1 = label. Blocks only AI attribution lines:
# a Co-authored-by line or a "Generated with/by" byline that names an AI
# assistant. Other text, tool names included, is not checked.
attribution_scan() {
    _label="$1"
    _hits=$(tr -d '\r' | grep -n -i -E "$PR_COAUTHOR_ERE|$PR_BYLINE_ERE" 2>/dev/null \
            | grep -i -E "$AI_ERE" 2>/dev/null)
    if [ -n "$_hits" ]; then
        printf 'BLOCKED: %s carries an AI attribution line:\n' "$_label" >&2
        printf '%s\n' "$_hits" | sed 's/^/    /' >&2
        return 1
    fi
    return 0
}

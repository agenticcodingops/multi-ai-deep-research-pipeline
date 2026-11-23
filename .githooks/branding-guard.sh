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
# leading emoji, quote or list marker, and Markdown emphasis or code marks
# around the words ("**Generated with** Claude", "**Co-authored-by**: Codex").
PR_COAUTHOR_ERE='^[^[:alnum:]]*co-?authored-?by[^[:alnum:]]*:'
PR_BYLINE_ERE='^[^[:alnum:]]*generated[^[:alnum:]]+(with|by)([^[:alnum:]]|$)'

# A byline credits a product, not a person, so it also matches the agent
# names that AI_ERE takes only in their bot forms (so that humans called
# Devin, Jules or Kiro pass as contributors).
BYLINE_AI_ERE='(^|[^a-z0-9])(jules|devin|kiro)([^a-z0-9]|$)'

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
    _text=$(tr -d '\r')
    _hits=$( { printf '%s\n' "$_text" | grep -n -i -E "$PR_COAUTHOR_ERE" 2>/dev/null \
                   | grep -i -E "$AI_ERE" 2>/dev/null
               printf '%s\n' "$_text" | grep -n -i -E "$PR_BYLINE_ERE" 2>/dev/null \
                   | grep -i -E "$AI_ERE|$BYLINE_AI_ERE" 2>/dev/null
             } | sort -t: -k1,1n -u)
    if [ -n "$_hits" ]; then
        printf 'BLOCKED: %s carries an AI attribution line:\n' "$_label" >&2
        printf '%s\n' "$_hits" | sed 's/^/    /' >&2
        return 1
    fi
    return 0
}

# Prints the commits a push or PR adds, one per line, for the checks above.
# $1 = old tip (empty or all zeros for a new ref), $2 = new tip,
# $3 = default-branch ref (for example origin/main).
# When the old tip is a commit in this clone, the range is old..new. When it
# is empty, zero or not in this clone (a force push can leave the previous
# tip unreachable), the range is every commit the new tip adds to the default
# branch; and when that is empty because the new tip is already on the default
# branch (the default branch itself was created or force-pushed), the new
# tip's whole ancestry. Returns 1, printing nothing, if git cannot list them.
commit_range() {
    _base="$1"; _head="$2"; _default="$3"
    if [ -n "$_base" ] && [ "$_base" != "0000000000000000000000000000000000000000" ] \
       && git cat-file -e "$_base^{commit}" 2>/dev/null; then
        git rev-list "$_base..$_head" || return 1
        return 0
    fi
    if [ -n "$_default" ] && git rev-parse -q --verify "$_default^{commit}" >/dev/null 2>&1; then
        _added=$(git rev-list "$_head" --not "$_default") || return 1
        if [ -n "$_added" ]; then
            printf '%s\n' "$_added"
            return 0
        fi
    fi
    git rev-list "$_head" || return 1
}

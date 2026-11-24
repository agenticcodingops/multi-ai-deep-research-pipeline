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

# AI-assistant names that are not also common human names. In an identity
# "Name <email>" they are matched as whole tokens (case-insensitive) in the
# name and in the address's local part, never in its domain, so a person with
# an address at an AI vendor passes. Ambiguous given names are matched only
# in bot forms (devin-ai..., google-labs-jules, kiro...[bot]) or, for Claude,
# as a bare assistant name (CLAUDE_ERE), so people called Devin, Jules, Kiro
# or Claude pass.
AI_NAMES='anthropic|openai|chatgpt|codex|copilot|gemini|cursor|cursoragent|aider|grok|x\.ai|xai|antigravity|devin-ai[a-z0-9-]*|google-labs-jules|kiro[a-z0-9-]*\[bot\]|kiro\.dev|opus|sonnet|haiku|fable|gpt[- ]?[0-9][a-z0-9.]*'
AI_ERE="(^|[^a-z0-9])($AI_NAMES)([^a-z0-9]|\$)"

# "Claude" alone or with assistant words ("Claude Code", "claude[bot]",
# "claude-code-action[bot]", "Claude 4"), but not "Claude Martin".
CLAUDE_ERE='^[^a-z0-9]*claude([^a-z0-9]+(code|ai|agent|bot|assistant|app|action|cli|github|[0-9][0-9.]*))*[^a-z0-9]*$'
# In an address's local part, "claude" counts only with an assistant word
# ("claude[bot]", "claude-code-action[bot]"), so a person called Claude with
# the mailbox claude@example.org passes. A bare "claude" mailbox counts only
# at an AI vendor's domain (VENDOR_LOCAL_ERE).
CLAUDE_LOCAL_ERE='^[^a-z0-9]*claude([^a-z0-9]+(code|ai|agent|bot|assistant|app|action|cli|github|[0-9][0-9.]*))+[^a-z0-9]*$'

# An AI vendor's domain counts only for a noreply, bot or bare "claude"
# mailbox there.
VENDOR_DOMAIN_ERE='(^|\.)(anthropic\.com|openai\.com|x\.ai|cursor\.com|kiro\.dev|aider\.chat)$'
VENDOR_LOCAL_ERE='^(no-?reply|notifications?|bot|agent|assistant)([^a-z0-9].*)?$|^claude$'

# A byline credits a product, not a person, so every agent name counts there.
BYLINE_NAMES="$AI_NAMES|claude|jules|devin|kiro"

# A co-author trailer key. Commits: at the start of a line.
COAUTHOR_ERE='^[[:space:]]*co-?authored-?by[[:space:]]*:'

# PR text: a co-author line or a "Generated with/by" byline, allowing a
# leading emoji, quote or list marker, and Markdown emphasis or code marks
# around the words ("**Generated with** Claude", "**Co-authored-by**: Codex").
# Inline HTML tags (<sub>, <p align=...>) are removed before matching.
PR_COAUTHOR_ERE='^[^[:alnum:]]*co-?authored-?by[^[:alnum:]]*:'
PR_BYLINE_ERE='^[^[:alnum:]]*generated[^[:alnum:]]+(with|by)([^[:alnum:]]|$)'

# The credited product must come first after "Generated with/by", after
# Markdown marks and a few filler words ("the help of"); a tool named later
# in the sentence does not count.
BYLINE_PRODUCT_ERE="^[^a-z0-9]*((the|an?|help|assistance|from|of|using)[^a-z0-9]+)*($BYLINE_NAMES)([^a-z0-9]|\$)"

# Returns 0 if the identity $1 ("Name <email>", or a bare name) is an AI
# assistant.
is_ai_identity() {
    _ai_id=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
    case "$_ai_id" in
        *"<"*) _ai_name=${_ai_id%%<*}; _ai_mail=${_ai_id#*<}; _ai_mail=${_ai_mail%%>*} ;;
        *)     _ai_name=$_ai_id; _ai_mail="" ;;
    esac
    _ai_local=${_ai_mail%@*}
    _ai_domain=""
    case "$_ai_mail" in *@*) _ai_domain=${_ai_mail##*@} ;; esac
    # GitHub noreply addresses carry an "<id>+" prefix.
    _ai_local=$(printf '%s' "$_ai_local" | sed 's/^[0-9]*+//')
    printf '%s\n%s\n' "$_ai_name" "$_ai_local" | grep -q -E "$AI_ERE" 2>/dev/null && return 0
    printf '%s\n' "$_ai_name" | grep -q -E "$CLAUDE_ERE" 2>/dev/null && return 0
    printf '%s\n' "$_ai_local" | grep -q -E "$CLAUDE_LOCAL_ERE" 2>/dev/null && return 0
    if [ -n "$_ai_domain" ] \
       && printf '%s\n' "$_ai_domain" | grep -q -E "$VENDOR_DOMAIN_ERE" 2>/dev/null \
       && printf '%s\n' "$_ai_local" | grep -q -E "$VENDOR_LOCAL_ERE" 2>/dev/null; then
        return 0
    fi
    return 1
}

# No co-author may be an AI assistant. GitHub lists each co-author of a
# default-branch commit as a contributor.
# Message on stdin; $1 = human-readable label. Returns 1 if any co-author fails.
# A trailer folded onto indented continuation lines ("Co-authored-by:" then
# "  Claude <...>") is unfolded first, as git reads it.
coauthor_check() {
    _label="$1"
    _lines=$(tr -d '\r' | sed '/^[[:space:]]*#/d' \
             | awk '{
                   key = (tolower($0) ~ /^[ \t]*co-?authored-?by[ \t]*:/)
                   if (have && !key && $0 ~ /^[ \t]/) { sub(/^[ \t]+/, ""); buf = buf " " $0 }
                   else { if (have) print buf; buf = $0; have = 1 }
               } END { if (have) print buf }' \
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

# Returns 0 if the attribution of kind $1 ("c" co-author, "b" byline) with
# value $2 (the text after the key) names an AI assistant.
_attribution_is_ai() {
    if [ "$1" = c ]; then
        # Drop Markdown marks around the identity ("`Claude`", "*Codex*").
        _at_who=$(printf '%s' "$2" | sed 's/^[[:space:]*_`]*//; s/[[:space:]*_`]*$//')
        is_ai_identity "$_at_who"
    else
        printf '%s\n' "$2" | tr '[:upper:]' '[:lower:]' \
            | grep -q -E "$BYLINE_PRODUCT_ERE" 2>/dev/null
    fi
}

# PR or issue text on stdin; $1 = label. Blocks only AI attribution lines:
# a Co-authored-by line or a "Generated with/by" byline that names an AI
# assistant. Other text, tool names included, is not checked. When the key
# ends its line ("Generated with" then "Claude Code"), the next line is the
# value, since Markdown joins the two into one paragraph.
attribution_scan() {
    _label="$1"
    _text=$(tr -d '\r' \
            | sed -E 's#</?[A-Za-z][A-Za-z0-9]*([[:space:]][^>]*)?/?>##g')
    _hits=""; _n=0; _pend=""; _pend_line=""
    while IFS= read -r _l; do
        _n=$((_n + 1))
        if [ -n "$_pend" ]; then
            if printf '%s' "$_l" | grep -q '[[:alnum:]]' \
               && _attribution_is_ai "$_pend" "$_l"; then
                _hits="$_hits$_pend_line
"
            fi
            _pend=""
        fi
        _low=$(printf '%s\n' "$_l" | tr '[:upper:]' '[:lower:]')
        if printf '%s\n' "$_low" | grep -q -E "$PR_COAUTHOR_ERE" 2>/dev/null; then
            _kind=c
            _val=$(printf '%s\n' "$_l" | sed 's/^[^:]*://')
        elif printf '%s\n' "$_low" | grep -q -E "$PR_BYLINE_ERE" 2>/dev/null; then
            _kind=b
            _val=$(printf '%s\n' "$_low" \
                   | sed -E 's/^[^[:alnum:]]*generated[^[:alnum:]]+(with|by)//')
        else
            continue
        fi
        if printf '%s' "$_val" | grep -q '[[:alnum:]]'; then
            if _attribution_is_ai "$_kind" "$_val"; then
                _hits="$_hits$_n:$_l
"
            fi
        else
            _pend=$_kind; _pend_line="$_n:$_l"
        fi
    done <<EOF
$_text
EOF
    if [ -n "$_hits" ]; then
        printf 'BLOCKED: %s carries an AI attribution line:\n' "$_label" >&2
        printf '%s' "$_hits" | sed 's/^/    /' >&2
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

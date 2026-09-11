#!/bin/sh
# Enable this repository's versioned hooks. Run once per clone:
#     sh .githooks/install.sh
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg .githooks/pre-push .githooks/branding-guard.sh 2>/dev/null || true
printf 'Hooks enabled: core.hooksPath -> .githooks\n'
printf 'Approved identities: .githooks/allowed-authors.txt\n'

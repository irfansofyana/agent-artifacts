#!/usr/bin/env bash
# Publish one verified patch: commit exactly the files the CLI reported, push a
# branch named after the finding, open a draft MR.
#
# This is the only process in the pipeline that holds a repository write
# credential, and it never hands that credential to the agent. It uses its own
# HOME ($CS_PUB_HOME) so the glab config and git credential helper live somewhere
# the agent's sandbox does not read.
#
# Usage: publish_patch.sh <finding-id> <comma,separated,files> <statement>
# Prints the merge request URL on stdout.
set -euo pipefail

id="$1"
files="$2"
statement="${3:-}"

: "${CS_WORK:?}"
: "${CS_BASE_SHA:?}"
: "${CS_PUB_HOME:?publisher HOME, holds the glab config}"
: "${GITLAB_WRITE_TOKEN:?repository write token is required to publish}"

prefix="${CS_BRANCH_PREFIX:-codex-security}"
branch="$prefix/$id"
target="${CS_TARGET_BRANCH:-main}"

export HOME="$CS_PUB_HOME"
git config --global --get user.email >/dev/null 2>&1 || {
  git config --global user.name "${CS_BOT_NAME:-codex-security-bot}"
  git config --global user.email "${CS_BOT_EMAIL:-codex-security-bot@example.invalid}"
}

IFS=',' read -r -a filelist <<<"$files"
[ "${#filelist[@]}" -gt 0 ] || { echo "no files reported for $id" >&2; exit 1; }

cd "$CS_WORK"
git checkout -q -B "$branch" "$CS_BASE_SHA"

# Stage only what the agent reported changing. A stray edit outside that list is
# a signal something went wrong, not something to commit.
git add -- "${filelist[@]}"
if git diff --cached --quiet; then
  echo "nothing staged for $id; refusing to open an empty MR" >&2
  exit 1
fi

git commit -q -m "fix(security): ${id} ${statement:0:80}" \
  -m "Verified by Codex Security. Review the diff before merging."

# -f makes the branch state match the verified patch on a re-run instead of
# fighting a stale branch from an earlier attempt.
git push -q -f origin "HEAD:refs/heads/$branch"

desc="${CS_OUT:-/tmp}/mr-$id.md"
{
  echo "Finding: \`$id\`"
  echo
  echo "\`\`\`"
  echo "$statement"
  echo "\`\`\`"
  echo
  echo "Files changed: \`${files}\`"
  echo
  echo "Draft on purpose. Nothing in this pipeline merges."
} > "$desc"

glab mr create --draft --yes \
  --source-branch "$branch" --target-branch "$target" \
  --title "fix(security): $id" \
  --description "$(cat "$desc")" 2>/dev/null | tail -n1

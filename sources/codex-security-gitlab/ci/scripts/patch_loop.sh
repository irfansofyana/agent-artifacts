#!/usr/bin/env bash
# Time-budgeted patch loop.
#
# Works through as many confirmed findings as fit inside a budget this script
# owns, resets the clone before each one, and hands every verified patch to
# publish_patch.sh. It stops cleanly when the budget runs out instead of letting
# GitLab kill the job mid-push, and it writes progress after every finding so a
# killed run loses at most one iteration.
#
# The agent never sees a repository write credential: it is launched with `env -i`
# and a HOME that holds no glab or git credentials. Only publish_patch.sh does.
#
# Required env: CS_CONFIRMED CS_BUDGET_SECONDS CS_PER_FINDING_P90 CS_CALL_TIMEOUT
#               CS_WORK CS_BASE_SHA CS_OUT CS_BIN
#               CS_CODEX_HOME CS_STATE_DIR CS_AGENT_HOME
#               LITELLM_API_KEY, and GITLAB_WRITE_TOKEN when CS_PUBLISH=1
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HERE/state.py"

: "${CS_CONFIRMED:?path to confirmed.json}"
: "${CS_OUT:?result directory}"
: "${CS_BIN:?codex-security binary}"
: "${CS_WORK:?clean clone of the base commit}"
: "${CS_BASE_SHA:?base commit to reset to before every finding}"
CS_BUDGET_SECONDS="${CS_BUDGET_SECONDS:-2700}"
CS_PER_FINDING_P90="${CS_PER_FINDING_P90:-300}"
CS_CALL_TIMEOUT="${CS_CALL_TIMEOUT:-1800}"
CS_MAX_ATTEMPTS="${CS_MAX_ATTEMPTS:-2}"
CS_PUBLISH="${CS_PUBLISH:-0}"
CS_AGENT_HOME="${CS_AGENT_HOME:-/tmp/cs-agent-home}"
CS_CODEX_HOME="${CS_CODEX_HOME:-/tmp/cs-codex-home}"
CS_STATE_DIR="${CS_STATE_DIR:-/tmp/cs-state}"

mkdir -p "$CS_OUT" "$CS_AGENT_HOME" "$CS_CODEX_HOME" "$CS_STATE_DIR"
PROGRESS="$CS_OUT/progress.json"
LOG="$CS_OUT/loop.log"

WORKLIST="$CS_OUT/patch-worklist.tsv"
python3 - "$CS_CONFIRMED" "$WORKLIST" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
with open(sys.argv[2], "w") as fh:
    for r in rows:
        stmt = " ".join(str(r.get("statement") or "").split())
        if stmt:
            fh.write(f"{r.get('finding_id') or r.get('id')}\t{stmt}\n")
print(f"patch worklist: {len(rows)} findings", file=sys.stderr)
PY

key="${LITELLM_API_KEY:-}"
write_token="${GITLAB_WRITE_TOKEN:-}"
unset LITELLM_API_KEY GITLAB_WRITE_TOKEN

started=$(date +%s)
remaining() { echo $(( CS_BUDGET_SECONDS - ( $(date +%s) - started ) )); }
stopped="complete"

# A cancelled or timed-out job still gets this far: leave a breadcrumb in the
# progress file rather than dying silently.
trap 'printf "interrupted %s remaining=%ss\n" "$(date -u +%FT%TZ)" "$(remaining)" >> "$LOG"; exit 0' TERM INT

while IFS=$'\t' read -r id statement; do
  [ -n "${id:-}" ] || continue

  rem=$(remaining)
  if [ "$rem" -lt "$CS_PER_FINDING_P90" ]; then
    stopped="budget"
    printf 'budget stop: %ss left, below the %ss p90\n' "$rem" "$CS_PER_FINDING_P90" | tee -a "$LOG"
    break
  fi

  # Idempotency has two sources: a terminal status already recorded, and a branch
  # that already exists for this finding (a previous run published it).
  branch="no"
  if [ "$CS_PUBLISH" = "1" ]; then
    # Ask the remote, with the publisher HOME so git can use glab's credential
    # helper. A branch for this finding means an earlier run already published it.
    if HOME="$CS_PUB_HOME" git -C "$CS_WORK" ls-remote --exit-code --heads origin \
        "${CS_BRANCH_PREFIX:-codex-security}/$id" >/dev/null 2>&1; then
      branch="yes"
    fi
  fi
  decision_line=$(python3 "$STATE" should-skip --progress "$PROGRESS" --id "$id" \
    --max-attempts "$CS_MAX_ATTEMPTS" --branch-exists "$branch")
  decision="${decision_line%%$'\t'*}"
  reason="${decision_line#*$'\t'}"
  if [ "$decision" = "skip" ]; then
    printf 'skip %s (%s)\n' "$id" "$reason" >> "$LOG"
    continue
  fi

  # patch refuses to run against a dirty tree, so every iteration starts clean.
  git -C "$CS_WORK" checkout -f -q "$CS_BASE_SHA" 2>/dev/null
  git -C "$CS_WORK" reset --hard -q "$CS_BASE_SHA"
  git -C "$CS_WORK" clean -qfd

  t0=$(date +%s)
  # Run the agent inside the clone: it works on the repository in its cwd. A
  # subshell keeps this from moving the loop's own working directory.
  ( cd "$CS_WORK" && env -i PATH="$PATH" HOME="$CS_AGENT_HOME" LANG=C.UTF-8 CI=true \
      CODEX_HOME="$CS_CODEX_HOME" CODEX_SECURITY_STATE_DIR="$CS_STATE_DIR" \
      LITELLM_API_KEY="$key" \
      timeout "$CS_CALL_TIMEOUT" "$CS_BIN" patch "$statement" \
      --assess-patch-risk --json \
      > "$CS_OUT/patch-$id.json" 2> "$CS_OUT/patch-$id.err" )
  rc=$?
  duration=$(( $(date +%s) - t0 ))

  parsed=$(python3 "$STATE" classify --json "$CS_OUT/patch-$id.json" --stderr "$CS_OUT/patch-$id.err" --rc "$rc")
  status=$(printf '%s' "$parsed" | tr '\t' '\n' | sed -n 's/^status=//p')
  retryable=$(printf '%s' "$parsed" | tr '\t' '\n' | sed -n 's/^retryable=//p')
  files=$(printf '%s' "$parsed" | tr '\t' '\n' | sed -n 's/^files=//p')

  mr=""
  note="rc=$rc retryable=$retryable"
  if [ "$status" = "verified" ]; then
    if [ "$CS_PUBLISH" = "1" ] && [ -n "$files" ]; then
      if mr=$(GITLAB_WRITE_TOKEN="$write_token" bash "$HERE/publish_patch.sh" "$id" "$files" "$statement" 2>>"$LOG"); then
        status="published"
      else
        note="$note publish_failed"
      fi
    else
      note="$note patch_only"
    fi
  fi

  python3 "$STATE" record --progress "$PROGRESS" --id "$id" --status "$status" \
    --duration "$duration" --mr "$mr" --note "$note" --files "$files" >> "$LOG"
  printf 'finding %s -> %s in %ss (remaining %ss)\n' "$id" "$status" "$duration" "$(remaining)" | tee -a "$LOG"
done < "$WORKLIST"

echo "loop finished: $stopped, $(( $(date +%s) - started ))s of ${CS_BUDGET_SECONDS}s"
python3 "$STATE" summary --progress "$PROGRESS" --markdown --verify-mrs
exit 0

#!/usr/bin/env bash
# Validate every statement from the work list, one call at a time.
#
# This stage changes nothing and spends model calls only, so it is the cheap
# gate: only findings with verdict "confirmed" reach the patch stage. Each call
# gets its own ceiling, so one pathological finding cannot eat the whole job.
#
# Required env: CS_STATEMENTS CS_OUT CS_BIN CS_CALL_TIMEOUT CS_CODEX_HOME
#               CS_STATE_DIR CS_AGENT_HOME
#               LITELLM_API_KEY (unset before the agent is launched)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HERE/state.py"

: "${CS_STATEMENTS:?path to statements.json}"
: "${CS_OUT:?result directory}"
: "${CS_BIN:?codex-security binary}"
CS_CALL_TIMEOUT="${CS_CALL_TIMEOUT:-600}"
CS_AGENT_HOME="${CS_AGENT_HOME:-/tmp/cs-agent-home}"
CS_CODEX_HOME="${CS_CODEX_HOME:-/tmp/cs-codex-home}"
CS_STATE_DIR="${CS_STATE_DIR:-/tmp/cs-state}"
CS_EFFORT="${CS_EFFORT:-low}"
# Same budget pattern as the patch loop: this script owns a wall-clock budget
# that is shorter than the GitLab job timeout, and it stops cleanly rather than
# letting the runner kill it mid-call.
CS_BUDGET_SECONDS="${CS_BUDGET_SECONDS:-900}"
CS_PER_FINDING_P90="${CS_PER_FINDING_P90:-60}"

mkdir -p "$CS_OUT/assessments" "$CS_AGENT_HOME" "$CS_CODEX_HOME" "$CS_STATE_DIR"
WORKLIST="$CS_OUT/validate-worklist.tsv"
python3 - "$CS_STATEMENTS" "$WORKLIST" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
with open(sys.argv[2], "w") as fh:
    for r in rows:
        stmt = " ".join(str(r["statement"]).split())
        fh.write(f"{r['id']}\t{stmt}\n")
print(f"validate worklist: {len(rows)} findings", file=sys.stderr)
PY

key="${LITELLM_API_KEY:-}"
unset LITELLM_API_KEY
started=$(date +%s)
done_count=0
stopped="complete"

while IFS=$'\t' read -r id statement; do
  [ -n "${id:-}" ] || continue
  rem=$(( CS_BUDGET_SECONDS - ( $(date +%s) - started ) ))
  if [ "$rem" -lt "$CS_PER_FINDING_P90" ]; then
    stopped="budget"
    printf 'budget stop: %ss left, below the %ss p90\n' "$rem" "$CS_PER_FINDING_P90" | tee -a "$CS_OUT/loop.log"
    break
  fi
  t0=$(date +%s)
  env -i PATH="$PATH" HOME="$CS_AGENT_HOME" LANG=C.UTF-8 CI=true \
    CODEX_HOME="$CS_CODEX_HOME" CODEX_SECURITY_STATE_DIR="$CS_STATE_DIR" \
    LITELLM_API_KEY="$key" \
    timeout "$CS_CALL_TIMEOUT" "$CS_BIN" validate "$statement" \
    --output-schema "$HERE/assessment.schema.json" --effort "$CS_EFFORT" \
    > "$CS_OUT/assessments/$id.json" 2> "$CS_OUT/assessments/$id.err"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    # No verdict came back. Record it as inconclusive so the confirm gate stays
    # closed; never invent a confirmation from a failed call.
    printf '{"finding_id":"%s","verdict":"inconclusive","confidence":"low","reasoning":"no verdict: exit %s after %ss"}\n' \
      "$id" "$rc" "$(( $(date +%s) - t0 ))" > "$CS_OUT/assessments/$id.json"
  fi
  done_count=$((done_count + 1))
  printf 'validate %s rc=%s %ss\n' "$id" "$rc" "$(( $(date +%s) - t0 ))" >> "$CS_OUT/loop.log"
done < "$WORKLIST"

echo "validated $done_count findings in $(( $(date +%s) - started ))s ($stopped)"
python3 "$STATE" select-confirmed --assessments "$CS_OUT/assessments" \
  --statements "$CS_STATEMENTS" --out "$CS_OUT/confirmed.json"

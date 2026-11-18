#!/usr/bin/env bash
# End-to-end harness for the time-budgeted Codex Security loop.
#
# Exercises the real scripts against stub binaries and a real local git remote,
# so the parts that actually decide behaviour (budget accounting, per-call
# timeouts, classification, idempotency, credential isolation) are tested rather
# than described. What it cannot test is the agent itself: the stub returns
# outcomes from a scenario file instead of calling a model.
#
# Usage: bash ci/tests/harness.sh
set -uo pipefail

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$CI_DIR/tests/bin"
SCRIPTS="$CI_DIR/scripts"
FIX="$CI_DIR/tests/fixtures"
STUBS="$CI_DIR/tests/.stub-state"

pass=0
fail=0
check() {
  if [ "$2" = "$3" ]; then
    echo "PASS  $1"
    pass=$((pass + 1))
  else
    echo "FAIL  $1 -> got '$2', want '$3'"
    fail=$((fail + 1))
  fi
}
check_contains() {
  case "$2" in
    *"$3"*) echo "PASS  $1"; pass=$((pass + 1)) ;;
    *) echo "FAIL  $1 -> '$3' not found in '$(printf '%s' "$2" | tr '\n' '|')'"; fail=$((fail + 1)) ;;
  esac
}
pval() {
  python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
print(d.get(sys.argv[2],{}).get(sys.argv[3],""))' "$1" "$2" "$3"
}
set_scenario() {
  python3 - "$1" "$STUBS/scenario.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
data["_sleep"] = 30
json.dump(data, open(sys.argv[2], "w"))
PY
}

TMP="$(mktemp -d)"
TMPR="$(cd "$TMP" && pwd -P)"
echo "workdir: $TMP"

# ---------------------------------------------------------------- fixtures
git init -q --bare "$TMP/origin.git"
git init -q "$TMP/seed"
cd "$TMP/seed"
git config user.email seed@example.invalid
git config user.name seed
mkdir -p src/util src/http src/reports config
for f in src/util/crypto.py src/http/handlers.py src/reports/query.py config/settings.py; do
  echo "# $f" > "$f"
done
git add -A
git commit -qm "seed"
git branch -M main
git remote add origin "$TMP/origin.git"
git push -q origin main
cd - >/dev/null

git clone -q "$TMP/origin.git" "$TMP/work"
BASE_SHA="$(git -C "$TMP/work" rev-parse HEAD)"
echo "base: $BASE_SHA"

OUT="$TMP/out"
mkdir -p "$OUT"
export PATH="$BIN:$PATH"
export LITELLM_API_KEY="model-key-placeholder"
export GITLAB_WRITE_TOKEN="write-token-placeholder"
export CS_BIN="$BIN/codex-security"
export CS_OUT="$OUT"
export CS_WORK="$TMP/work"
export CS_BASE_SHA="$BASE_SHA"
export CS_AGENT_HOME="$TMP/agent-home"
export CS_PUB_HOME="$TMP/pub-home"
export CS_CODEX_HOME="$TMP/codex-home"
export CS_STATE_DIR="$TMP/state"
export CS_TARGET_BRANCH=main
mkdir -p "$CS_AGENT_HOME" "$CS_PUB_HOME" "$CS_CODEX_HOME" "$CS_STATE_DIR"

# The stubs keep their state next to themselves, because the pipeline launches
# the agent and the publisher with scrubbed environments on purpose.
rm -rf "$STUBS"
mkdir -p "$STUBS"
printf '%s' "$TMP/work" > "$STUBS/repo.path"

# ---------------------------------------------------------------- work list
python3 "$SCRIPTS/collect_findings.py" --input "$FIX/findings.json" \
  --statements "$OUT/statements.json" --needs-triage "$OUT/needs-triage.json" \
  --limit 5 > "$TMP/collect.log" 2>&1
echo "--- collect ---"
cat "$TMP/collect.log"
count=$(python3 -c 'import json;print(len(json.load(open("'"$OUT"'/statements.json"))))')
check "work list keeps only findings with a source location" "$count" "5"

# ---------------------------------------------------------------- validate
set_scenario "$FIX/scenario-validate.json"
export CS_STATEMENTS="$OUT/statements.json"
export CS_CALL_TIMEOUT=10
echo "--- validate ---"
bash "$SCRIPTS/validate_loop.sh" 2>&1 | tail -3
confirmed=$(python3 -c 'import json;print(len(json.load(open("'"$OUT"'/confirmed.json"))))')
check "only confirmed verdicts become patch work" "$confirmed" "4"
with_statement=$(python3 -c 'import json;print(sum(1 for r in json.load(open("'"$OUT"'/confirmed.json")) if r.get("statement")))')
check "confirmed findings carry their statement forward" "$with_statement" "4"
rejected=$(python3 -c 'import json;print(sum(1 for r in json.load(open("'"$OUT"'/confirmed.json")) if r.get("finding_id") == "101"))')
check "a rejected finding never becomes patch work" "$rejected" "0"
triaged=$(python3 -c 'import json;print(len(json.load(open("'"$OUT"'/needs-triage.json"))))')
check "findings without a location are triaged, not guessed" "$triaged" "3"

# ---------------------------------------------------------------- patch run 1
rm -f "$STUBS/agent-env.txt" "$STUBS/agent-calls.jsonl" "$STUBS/glab-calls.jsonl"
set_scenario "$FIX/scenario-patch.json"
export CS_CONFIRMED="$OUT/confirmed.json"
export CS_BUDGET_SECONDS=600
export CS_PER_FINDING_P90=5
export CS_CALL_TIMEOUT=3
export CS_MAX_ATTEMPTS=2
export CS_PUBLISH=1
echo "--- patch run 1 ---"
run1="$(bash "$SCRIPTS/patch_loop.sh" 2>&1)"
rc1=$?
printf '%s\n' "$run1" | tail -14
PROGRESS="$OUT/progress.json"

check "run finished on its own, not on the budget" "$rc1" "0"
check_contains "run reports complete" "$run1" "loop finished: complete"
check "verified finding published" "$(pval "$PROGRESS" 103 status)" "published"
check "second verified finding published" "$(pval "$PROGRESS" 106 status)" "published"
check "no_change recorded as terminal" "$(pval "$PROGRESS" 108 status)" "no_change"
check "killed call classified as timeout" "$(pval "$PROGRESS" 105 status)" "timeout"
check "timeout consumed one attempt" "$(pval "$PROGRESS" 105 attempts)" "1"
check "MR url recorded for 103" "$(pval "$PROGRESS" 103 mr)" "https://gitlab.example.invalid/pilot/-/merge_requests/1"
check "MR url recorded for 106" "$(pval "$PROGRESS" 106 mr)" "https://gitlab.example.invalid/pilot/-/merge_requests/2"
agentcwd=$(python3 -c 'import json,sys;print(json.loads(open(sys.argv[1]).readline())["cwd"])' "$STUBS/agent-calls.jsonl")
check "agent ran inside the clone, not the project dir" "$agentcwd" "$TMPR/work"

remotes="$(git -C "$TMP/work" ls-remote --heads "$TMP/origin.git" 2>/dev/null | sed 's#.*refs/heads/##' | sort | tr '\n' ' ')"
check_contains "branch pushed for 103" "$remotes" "codex-security/103"
check_contains "branch pushed for 106" "$remotes" "codex-security/106"
case "$remotes" in
  *codex-security/105*|*codex-security/108*)
    echo "FAIL  no branch for an unpublished finding"; fail=$((fail + 1)) ;;
  *) echo "PASS  no branch for an unpublished finding"; pass=$((pass + 1)) ;;
esac

mrs=$(grep -c 'mr.*create' "$STUBS/glab-calls.jsonl" 2>/dev/null || echo 0)
check "one MR call per published finding" "$mrs" "2"
[ -f "$OUT/mr-103.md" ] && { echo "PASS  MR description written"; pass=$((pass + 1)); } || { echo "FAIL  MR description missing"; fail=$((fail + 1)); }
committed="$(git -C "$TMP/work" show --stat --oneline "codex-security/103" | head -3 | tr '\n' '|')"
check_contains "branch carries a commit with the agent's file" "$committed" "src/util/crypto.py"

# Credential isolation: the agent's environment must never carry the write token.
if grep -q 'GITLAB_WRITE_TOKEN' "$STUBS/agent-env.txt"; then
  echo "FAIL  write token leaked into the agent environment"; fail=$((fail + 1))
else
  echo "PASS  write token absent from the agent environment"; pass=$((pass + 1))
fi
if grep -q 'write-token-placeholder' "$STUBS/agent-env.txt"; then
  echo "FAIL  write token value visible to the agent"; fail=$((fail + 1))
else
  echo "PASS  write token value invisible to the agent"; pass=$((pass + 1))
fi
if grep -q 'LITELLM_API_KEY=model-key-placeholder' "$STUBS/agent-env.txt"; then
  echo "PASS  agent still receives its model key"; pass=$((pass + 1))
else
  echo "FAIL  agent did not receive the model key it needs"; fail=$((fail + 1))
fi

# ---------------------------------------------------------------- patch run 2
calls_before=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
set_scenario "$FIX/scenario-rerun.json"
echo "--- patch run 2 (rerun) ---"
run2="$(bash "$SCRIPTS/patch_loop.sh" 2>&1)"
printf '%s\n' "$run2" | tail -10
calls_after=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
check "rerun retried only the retryable finding" "$((calls_after - calls_before))" "1"
skip_log="$(grep 'skip 103' "$OUT/loop.log" | tail -1)"
check_contains "rerun skipped an already-published finding" "$skip_log" "skip 103"
check_contains "skip is explained, not silent" "$skip_log" "status=published"
check "retry recorded a second attempt" "$(pval "$PROGRESS" 105 attempts)" "2"
check "retry outcome replaces the earlier status" "$(pval "$PROGRESS" 105 status)" "no_change"
mrs=$(grep -c 'mr.*create' "$STUBS/glab-calls.jsonl" 2>/dev/null || echo 0)
check "rerun published nothing new" "$mrs" "2"

# ---------------------------------------------------------------- run 2b
# The progress file does not survive every boundary: artifacts expire, runners
# change, and a new pipeline may start with nothing. So the branch on the remote
# has to be the second source of truth, and this run proves it is.
calls_before=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
export CS_OUT="$TMP/out-fresh"
mkdir -p "$CS_OUT"
echo "--- patch run 2b (fresh progress, same remote) ---"
run2b="$(bash "$SCRIPTS/patch_loop.sh" 2>&1)"
printf '%s\n' "$run2b" | tail -6
calls_after=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
check "without a progress file only unpublished findings run" "$((calls_after - calls_before))" "2"
fresh_skips=$(grep -c 'branch_exists' "$CS_OUT/loop.log" 2>/dev/null || echo 0)
check "a lost progress file still refuses to republish" "$fresh_skips" "2"
mrs=$(grep -c 'mr.*create' "$STUBS/glab-calls.jsonl" 2>/dev/null || echo 0)
check "no duplicate MR after losing the progress file" "$mrs" "2"
export CS_OUT="$OUT"

# ---------------------------------------------------------------- run 3
calls_before=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
export CS_BUDGET_SECONDS=2
export CS_PER_FINDING_P90=30
echo "--- patch run 3 (budget smaller than one finding) ---"
out3="$(bash "$SCRIPTS/patch_loop.sh" 2>&1)"
rc3=$?
printf '%s\n' "$out3" | tail -4
check_contains "loop stops on budget instead of being killed" "$out3" "budget stop"
calls_after=$(wc -l < "$STUBS/agent-calls.jsonl" | tr -d ' ')
check "budget stop spent no model call" "$((calls_after - calls_before))" "0"
check "budget stop exits 0" "$rc3" "0"

# ---------------------------------------------------------------- summary
echo
echo "--- progress summary ---"
python3 "$SCRIPTS/state.py" summary --progress "$PROGRESS" --markdown --verify-mrs
echo
echo "passed: $pass  failed: $fail"
[ "$fail" -eq 0 ] || exit 1
echo "harness clean; artifacts left in $TMP"

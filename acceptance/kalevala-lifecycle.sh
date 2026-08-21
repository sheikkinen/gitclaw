#!/usr/bin/env bash
set -uo pipefail

# End-to-end GitClaw lifecycle witness. The required positional parameter names
# the repository to test using the operator's existing gh keyring session.

REPO="${1:-}"
WORKFLOW="intake.yml"
POLL_LIMIT="${GITCLAW_ACCEPTANCE_POLL_LIMIT:-60}"
POLL_SECONDS="${GITCLAW_ACCEPTANCE_POLL_SECONDS:-5}"
FAILURES=0
FR_PATH=""
IMPLEMENTATION_PR=""
BLOCKED=0

usage() {
  echo "usage: $0 owner/repo" >&2
  exit 64
}

fail() {
  echo "acceptance: $*" >&2
  exit 1
}

record_failure() {
  echo "acceptance: FAIL: $*" >&2
  FAILURES=$((FAILURES + 1))
}

[[ "$REPO" =~ ^[^/[:space:]]+/[^/[:space:]]+$ ]] || usage
for token_name in GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN; do
  [[ -z "${!token_name:-}" ]] || fail "refusing inherited token variable: $token_name"
done
command -v gh >/dev/null || fail "gh CLI is required"
command -v git >/dev/null || fail "git is required"
gh auth status >/dev/null 2>&1 || fail "existing gh keyring authentication is required"
gh repo view "$REPO" --json nameWithOwner >/dev/null \
  || fail "repository is unavailable: $REPO"

RUN_DIR="${TMPDIR:-/tmp}/gitclaw-kalevala-acceptance-$(date +%Y%m%dT%H%M%S)-$$"
mkdir -p "$RUN_DIR"
echo "acceptance: evidence=$RUN_DIR"

phase_summary() {
  local label="$1"
  local phase_status="$2"
  local reason="$3"
  local issue_url="${4:-}"
  local run_url="${5:-}"
  local conclusion="${6:-}"
  local pr_url="${7:-}"
  local changed_file="${8:-$RUN_DIR/$label-changed-files.txt}"
  {
    printf 'field\tvalue\n'
    printf 'phase\t%s\n' "$label"
    printf 'status\t%s\n' "$phase_status"
    printf 'reason\t%s\n' "$reason"
    printf 'issue_url\t%s\n' "$issue_url"
    printf 'run_url\t%s\n' "$run_url"
    printf 'conclusion\t%s\n' "$conclusion"
    printf 'pr_url\t%s\n' "$pr_url"
    printf 'changed_files\t%s\n' "$changed_file"
  } >"$RUN_DIR/$label-summary.tsv"
}

skip_phase() {
  local label="$1"
  local reason="$2"
  : >"$RUN_DIR/$label-changed-files.txt"
  phase_summary "$label" skipped "$reason"
  echo "acceptance: SKIP: $label: $reason" >&2
}

find_run() {
  local title="$1"
  local baseline="$2"
  gh run list -R "$REPO" --workflow "$WORKFLOW" --event issues --limit 50 \
    --json databaseId,displayTitle \
    --jq ".[] | select(.displayTitle == \"$title\") | .databaseId" \
    | grep -vxFf "$baseline" | head -n 1
}

wait_for_run() {
  local title="$1"
  local baseline="$2"
  local run_id=""
  local attempt
  for ((attempt = 1; attempt <= POLL_LIMIT; attempt++)); do
    run_id="$(find_run "$title" "$baseline")"
    [[ -n "$run_id" ]] && break
    sleep "$POLL_SECONDS"
  done
  [[ -n "$run_id" ]] || return 1
  printf '%s' "$run_id"
}

wait_for_completion() {
  local run_id="$1"
  local run_status=""
  local attempt
  for ((attempt = 1; attempt <= POLL_LIMIT; attempt++)); do
    run_status="$(gh run view "$run_id" -R "$REPO" --json status --jq .status)"
    [[ "$run_status" == "completed" ]] && return 0
    sleep "$POLL_SECONDS"
  done
  return 1
}

issue_pr() {
  local issue="$1"
  gh issue view "$issue" -R "$REPO" --json comments \
    --jq '[.comments[].body | capture("PR: (?<url>https://github.com/[^ ]+/pull/[0-9]+)").url] | last // ""'
}

observe_issue() {
  local label="$1"
  local title="$2"
  local body="$3"
  local issue_url issue run_id conclusion pr_url run_url baseline

  echo
  echo "acceptance: ISSUE $label: $title"
  baseline="$RUN_DIR/$label-baseline-runs.txt"
  gh run list -R "$REPO" --workflow "$WORKFLOW" --event issues --limit 100 \
    --json databaseId --jq '.[].databaseId' >"$baseline"
  issue_url="$(gh issue create -R "$REPO" --title "$title" --body "$body")" || {
    record_failure "$label issue creation"
    phase_summary "$label" failed "issue creation failed"
    return 1
  }
  issue="${issue_url##*/}"
  echo "acceptance: issue=$issue_url"

  run_id="$(wait_for_run "$title" "$baseline")" || {
    record_failure "$label workflow was not observed"
    phase_summary "$label" failed "workflow was not observed" "$issue_url"
    return 1
  }
  run_url="https://github.com/$REPO/actions/runs/$run_id"
  echo "acceptance: run=$run_url"
  wait_for_completion "$run_id" || {
    record_failure "$label workflow did not complete before polling limit"
    phase_summary "$label" failed "workflow completion timed out" \
      "$issue_url" "$run_url"
    return 1
  }
  gh run view "$run_id" -R "$REPO" --log >"$RUN_DIR/$label-run.log" 2>&1 || true
  conclusion="$(gh run view "$run_id" -R "$REPO" --json conclusion --jq .conclusion)"
  echo "acceptance: conclusion=$conclusion"

  pr_url="$(issue_pr "$issue")"
  if [[ -n "$pr_url" ]]; then
    echo "acceptance: pr=$pr_url"
    gh pr diff "$pr_url" -R "$REPO" --name-only | tee "$RUN_DIR/$label-changed-files.txt"
  else
    : >"$RUN_DIR/$label-changed-files.txt"
  fi

  if [[ "$conclusion" != "success" ]]; then
    record_failure "$label workflow conclusion: $conclusion"
    phase_summary "$label" failed "workflow conclusion was not success" \
      "$issue_url" "$run_url" "$conclusion" "$pr_url"
    return 1
  fi
  phase_summary "$label" passed "workflow and phase observation succeeded" \
    "$issue_url" "$run_url" "$conclusion" "$pr_url"
  printf '%s\n%s\n' "$issue" "$pr_url" >"$RUN_DIR/$label-result.txt"
}

require_single_path() {
  local label="$1"
  local expected="$2"
  local changed_file="$RUN_DIR/$label-changed-files.txt"
  [[ "$(wc -l <"$changed_file" | tr -d ' ')" == "1" ]] \
    && [[ "$(cat "$changed_file")" == "$expected" ]]
}

merge_authority_pr() {
  local label="$1"
  local pr_url="$2"
  [[ -n "$pr_url" ]] || {
    record_failure "$label produced no authority PR"
    return 1
  }
  gh pr merge "$pr_url" -R "$REPO" --squash --delete-branch || {
    record_failure "$label authority PR merge"
    return 1
  }
}

PLAN_TITLE="Plan conversion of haiku based example to Kalevala runic format as a Feature Request"
PLAN_BODY="Convert the existing haiku-based example to Finnish Kalevala runic format. Preserve the self-sufficient date tool and optional city configuration. Plan only; judgement is a separate issue."
if observe_issue plan "$PLAN_TITLE" "$PLAN_BODY"; then
  PLAN_PR="$(tail -n 1 "$RUN_DIR/plan-result.txt")"
  if [[ -n "$PLAN_PR" ]]; then
    FR_PATH="$(gh pr diff "$PLAN_PR" -R "$REPO" --name-only | grep -E '^feature-requests/FR-[^/]+\.md$' | grep -v '\.judgement\.md$' | head -n 1)"
  fi
  if [[ -z "$FR_PATH" ]] || ! require_single_path plan "$FR_PATH"; then
    record_failure "plan must produce exactly one FR and no other path"
    phase_summary plan failed "Plan was not FR-only" \
      "$(awk -F '\t' '$1 == "issue_url" {print $2}' "$RUN_DIR/plan-summary.tsv")" \
      "$(awk -F '\t' '$1 == "run_url" {print $2}' "$RUN_DIR/plan-summary.tsv")" \
      success "$PLAN_PR"
    BLOCKED=1
  elif ! merge_authority_pr plan "$PLAN_PR"; then
    BLOCKED=1
  fi
else
  record_failure "plan command did not execute successfully"
  BLOCKED=1
fi

if ((BLOCKED == 0)) && [[ -n "$FR_PATH" ]]; then
  JUDGE_TITLE="Judge $FR_PATH"
  if observe_issue judge "$JUDGE_TITLE" "Judge the committed feature request. Produce only its sibling judgement artifact."; then
    JUDGE_PR="$(tail -n 1 "$RUN_DIR/judge-result.txt")"
    JUDGEMENT_PATH="${FR_PATH%.md}.judgement.md"
    if ! require_single_path judge "$JUDGEMENT_PATH"; then
      record_failure "judge must produce exactly the sibling judgement"
      phase_summary judge failed "Judge was not judgement-only" \
        "$(awk -F '\t' '$1 == "issue_url" {print $2}' "$RUN_DIR/judge-summary.tsv")" \
        "$(awk -F '\t' '$1 == "run_url" {print $2}' "$RUN_DIR/judge-summary.tsv")" \
        success "$JUDGE_PR"
      BLOCKED=1
    elif ! merge_authority_pr judge "$JUDGE_PR"; then
      BLOCKED=1
    fi
  else
    record_failure "judge command did not execute successfully"
    BLOCKED=1
  fi
else
  skip_phase judge "blocked by Plan RED"
fi

if ((BLOCKED == 0)) && [[ -n "$FR_PATH" ]]; then
  ENFORCE_TITLE="Enforce $FR_PATH"
  if observe_issue enforce "$ENFORCE_TITLE" "Implement exactly the committed judged plan using TDD and the graph-authoring route where required."; then
    IMPLEMENTATION_PR="$(tail -n 1 "$RUN_DIR/enforce-result.txt")"
    if [[ -z "$IMPLEMENTATION_PR" ]]; then
      record_failure "enforce produced no implementation PR"
      BLOCKED=1
    fi
  else
    record_failure "enforce command did not execute successfully"
    BLOCKED=1
  fi
else
  skip_phase enforce "blocked by authority RED"
fi

if ((BLOCKED == 0)) && [[ -n "$FR_PATH" && -n "$IMPLEMENTATION_PR" ]]; then
  PR_NUMBER="${IMPLEMENTATION_PR##*/}"
  observe_issue review "Review $PR_NUMBER against $FR_PATH" \
    "Review the implementation PR against the committed FR and judgement." \
    || record_failure "review command did not execute successfully"

  observe_issue test "Test PR $PR_NUMBER" \
    "Run the repository test suite against the implementation PR head. Do not modify files." \
    || record_failure "test command did not execute successfully"

  observe_issue run-yamlgraph "Run YAMLGraph PR $PR_NUMBER expecting graph failure" \
    "At the implementation PR head, run yamlgraph graph lint features/haiku/graph.yaml and record lint_exit=0 plus output. Then run yamlgraph graph run features/haiku/graph.yaml --full and record graph_exit as nonzero plus output. Do not modify files." \
    || record_failure "YAMLGraph command did not execute successfully"
  RUN_LOG="$RUN_DIR/run-yamlgraph-run.log"
  RUN_CHANGED="$RUN_DIR/run-yamlgraph-changed-files.txt"
  if ! grep -Fq 'lint_exit=0' "$RUN_LOG" \
    || ! grep -Eq 'graph_exit=[1-9][0-9]*' "$RUN_LOG" \
    || ! grep -Fq 'yamlgraph graph lint features/haiku/graph.yaml' "$RUN_LOG" \
    || ! grep -Fq 'yamlgraph graph run features/haiku/graph.yaml --full' "$RUN_LOG" \
    || [[ -s "$RUN_CHANGED" ]]; then
    record_failure "Run YAMLGraph lacks lint-zero/run-nonzero/no-diff evidence"
    phase_summary run-yamlgraph failed "missing expected-failure semantic evidence" \
      "$(awk -F '\t' '$1 == "issue_url" {print $2}' "$RUN_DIR/run-yamlgraph-summary.tsv")" \
      "$(awk -F '\t' '$1 == "run_url" {print $2}' "$RUN_DIR/run-yamlgraph-summary.tsv")" \
      success ""
  fi
  [[ "$(gh pr view "$IMPLEMENTATION_PR" -R "$REPO" --json state --jq .state)" == "OPEN" ]] \
    || record_failure "implementation PR was merged or closed"
else
  skip_phase review "blocked by authority or enforcement RED"
  skip_phase test "blocked by authority or enforcement RED"
  skip_phase run-yamlgraph "blocked by authority or enforcement RED"
fi

if ((FAILURES > 0)); then
  echo "acceptance: RED ($FAILURES failed expectations); evidence=$RUN_DIR" >&2
  exit 1
fi

echo "acceptance: GREEN; all six issue commands succeeded; evidence=$RUN_DIR"
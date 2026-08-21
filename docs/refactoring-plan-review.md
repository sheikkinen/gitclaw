# Critical Review: GitClaw Architecture Refactoring Overview

**Date:** 2026-08-21
**Reviewed:** `docs/refactoring-plan.md` against `docs/architecture.md` and the
current GitClaw implementation
**Verdict:** REQUEST CHANGES

The ownership model is strong, but the plan does not yet define a migration in
which every merged subtask leaves one coherent, functioning path. Several
subtasks retire a current dependency before its replacement is consumable, and
some target architecture rules lack mechanical witnesses.

## Findings

### 1. Critical: The issue #4 branch is not a valid GitOps publication input

Subtask 1 uses `gitclaw/issue-4-plan` as the required branch-without-PR RED and
requires rerun to create its missing PR/comment. That branch contains three
paths relative to `main`:

- intake request bookkeeping;
- a feature request; and
- a judgement produced by the currently coupled Plan operation.

The target architecture requires Plan-only output and forbids intake
bookkeeping in product PRs. Reconciling this exact branch into a PR would
publish a known-invalid result and make GitOps appear correct by preserving the
old composition defect.

**Required correction:** Use issue #4 as historical causal evidence, not as a
publication fixture. Build a synthetic branch-only fixture from a valid
mechanical task result, or first define and produce the minimum valid task
result. GitOps reconciliation tests must prove branch-without-PR behavior
without legitimizing invalid semantic output.

### 2. Critical: Classifier and issue-request subtasks cannot retire their old paths independently

Subtask 2 removes `parse_command()` and workflow output parsing. Subtask 3 then
removes committed request files and hash verification. Named operation tasks do
not arrive until Subtask 5. The current generic executor consumes both the
Python command result and request artifact contract.

As written, Subtask 2 or 3 can leave `main` with a classifier/output shape that
the generic executor does not consume, or without the request path/hash it still
requires. The plan forbids permanent dual paths but does not define a temporary
coherent handoff.

**Required correction:** Define one atomic migration slice that introduces the
classifier result, issue-snapshot input, dispatcher, and at least the first
consuming named task before retiring regex/request contracts. Alternatively,
keep old code explicitly until Subtask 5 and move retirement there. Every
intermediate merge must run one complete lifecycle path.

### 3. Critical: The runner cannot report a final commit identity before GitOps commits

The architecture says the worktree runner reports starting and final commit
identity to GitOps, while GitOps owns commit creation after task completion.
Those contracts are temporally inconsistent. Before GitOps commits, the task
worktree has a starting commit plus uncommitted changes, not a new final commit.

**Required correction:** The runner result should contain starting commit,
worktree path, process result, changed paths/hashes, and evidence paths. GitOps
creates the commit and returns final commit/branch/PR identity. Reserve “final
commit” for GitOps output.

### 4. High: The no-Git task boundary is advisory, not enforceable

Subtask 4 removes GitHub write credentials and passes a no-Git instruction.
That prevents many remote writes but does not prevent local `git add`, `git
commit`, branch changes, hooks, or other mutations. A normal Git worktree still
contains a usable `.git` link and Git executable.

The required witness says a task attempting commit/push must fail, but the plan
does not define the mechanism that makes local commit fail.

**Required correction:** Choose and test a mechanical enforcement mechanism,
for example a task PATH with a restricted Git wrapper permitting only declared
read operations, plus no `gh`/write token. The runner may use real Git outside
the task environment. Prompt text remains defense in depth, not enforcement.

### 5. High: Issue edit and retry semantics are undefined

The architecture declares the issue to be the lifecycle record and each edit a
new event, but the plan does not decide what happens when an issue is edited
while classification/task/publication is active.

Without an explicit rule, a stale run may publish after a newer edit, two runs
may prepare competing worktrees, or a retry may duplicate publication.

**Required correction:** Define event identity and supersession before removing
the request contract. At minimum, each run consumes one issue event/version;
publication checks that no newer event supersedes it, or records an explicit
conflict. Concurrency and retry behavior must be part of Subtasks 2-4 and GitOps
idempotency tests.

### 6. High: `Other` recreates the generic executor escape hatch

The architecture permits `Other` to produce either evidence or arbitrary
working-tree results. That weakens named-task ownership and can become the path
for every operation not yet modeled, preserving the generic executor under a
new label.

**Required correction:** Make `Other` read-only and diagnostic, or classify it
as unsupported and report that result on the issue. Any file-producing behavior
must have a named task with explicit inputs, outputs, and semantic owner.

### 7. Medium: User-facing documentation is deferred too long

The plan waits until Subtask 9 to align README and tests. Earlier subtasks change
classification, request handling, worktree behavior, operation availability,
and publication. Leaving README on the old model throughout the migration makes
the public contract knowingly false.

**Required correction:** Every behavior-changing subtask updates the affected
README/current-behavior section and tests in the same change. Subtask 9 performs
the final whole-repository reconciliation and purge, not all documentation
alignment.

## Missing Program Rule

Add this constraint to the overview:

> Every merged subtask leaves exactly one functioning end-to-end path for the
> behavior it touches. A replacement and the retirement of its final consumer
> occur in the same atomic migration slice. Temporary adapters require explicit
> judged scope and deletion in the immediately following dependent subtask;
> permanent dual paths are forbidden.

Each subtask FR should identify:

1. the complete path that works before the change;
2. the complete path that works after the change;
3. the cutover point;
4. the old components retired at cutover; and
5. an end-to-end witness proving `main` remains coherent.

## Recommended Plan Revision

1. Keep Subtask 0 as the architecture freeze.
2. Revise Subtask 1 to define/test GitOps using synthetic valid task results;
   retain issue #4 only as incident evidence.
3. Combine classifier, issue-as-request, dispatcher, and one consuming task into
   the first atomic semantic cutover, or defer parser/request retirement until
   the named-task subtask.
4. Define runner result without final commit identity and select a mechanical
   no-Git enforcement mechanism.
5. Define issue event supersession/retry semantics before the request artifact
   is removed.
6. Restrict `Other` to read-only unsupported/diagnostic reporting.
7. Require README and test alignment in every behavior-changing subtask.
8. Keep acceptance simplification after the product lifecycle owns transitions;
   acceptance must not bridge temporary migration gaps.

## Review Summary

The plan should not be enforced in its current sequence. The architecture is a
credible target, but the migration needs atomic cutovers and explicit temporal
contracts. The next revision should optimize for coherent intermediate states,
not merely correct final ownership.
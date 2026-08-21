# GitClaw and YAMLGraph

GitClaw is a consumer, integration example, and project template built on
[YAMLGraph](https://github.com/sheikkinen/yamlgraph). YAMLGraph is the framework;
GitClaw must compose it rather than implement a second orchestration framework.

## Repository Ownership

**YAMLGraph owns:**

- graph and prompt schemas;
- node execution, routing, state, and CLI behavior;
- reusable Plan, Judge, Enforce, Review, and graph-authoring skills/adapters;
- framework doctrine and generic hooks; and
- fixes or capabilities useful beyond GitClaw.

**GitClaw owns:**

- trusted GitHub issue intake;
- the issue-classification graph and named GitClaw tasks;
- GitHub/Git publication and partial-side-effect reconciliation;
- repository permissions and credential separation;
- scheduled invocation of one configured YAMLGraph task;
- GitClaw acceptance observation; and
- the retained example task.

If GitClaw needs a missing framework capability, plan it in YAMLGraph rather
than hiding an approximation in GitClaw workflow/Python code. GitClaw-specific
GitHub behavior remains in GitClaw.

## Executable Control Bundle

GitClaw mirrors a pinned subset of YAMLGraph instructions, skills, adapters,
wrappers, and hooks. `control-bundle.json` records the source commit, paths,
hashes, modes, and local adaptations.

- Treat `mirror` files as upstream-owned copies.
- Document unavoidable GitClaw changes as `adapt-local`.
- Do not casually edit mirrored doctrine to solve a GitClaw product problem.
- Verify the bundle with `python -m tools.control_bundle`.
- Use GitClaw's local `scripts/author.sh`, `scripts/judge.sh`, and
  `scripts/review.sh`; they execute the mirrored YAMLGraph routes.

See `control-bundle-trace.md` and `docs/control-bundle-adaptations.md` for the
exact provenance boundary.

## Current Direction

`docs/architecture.md` is GitClaw's target architecture. The implementation
still diverges from it. `docs/refactoring-plan.md` sequences independently
judged subtasks that establish each owner and retire the shadow implementation.

Read in this order:

1. `docs/context.md` - repository relationship;
2. `docs/architecture.md` - responsibilities and allowed dependencies;
3. `docs/refactoring-plan.md` - migration sequence and retirement;
4. `README.md` - current user-facing behavior; and
5. `control-bundle-trace.md` - mirrored runtime provenance.

When architecture and current behavior differ, do not infer the target from
tests or existing code. Follow the architecture, then implement only through a
researched and judged subtask.
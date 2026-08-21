# gitclaw

**A trusted GitHub issue becomes governed working-tree artifacts.**

gitclaw is a public YAMLGraph integration demo and project template. A trusted
issue starts one generic Copilot executor. Repository instructions and mirrored
YAMLGraph skills decide the intellectual workflow; deterministic scripts verify
artifacts and own every Git/GitHub side effect. A separate cron workflow keeps
running one configured YAMLGraph task.

## Setup

1. Use this repository as a template and enable Actions.
2. Add `COPILOT_CLI_TOKEN`: a dedicated Copilot credential/account with **no
   repository-write access**. The executor receives this token, so a normal
   write-capable `gh auth token` is not an acceptable unattended credential.
3. Add `ANTHROPIC_API_KEY` for the scheduled starter task.
4. Set the repository variable `YAMLGRAPH_TASK` to the starter value
  `features/haiku/graph.yaml`.
5. File a trusted issue using one exact command title. The body is optional
   supporting detail.

```text
Plan a daily greeting as a Feature Request
Enforce feature-requests/FR-001-daily-greeting.md
Review 12 against feature-requests/FR-001-daily-greeting.md
Revise PR 12: handle source timeouts explicitly
```

Unknown or ambiguous titles fail before Copilot runs.

## Execution Model

```text
trusted issue
  -> immutable request.json + hash
  -> exact command classification
  -> one generic Copilot/YAMLGraph node
  -> applicable mirrored skills/adapters
  -> uncommitted working-tree artifacts
  -> deterministic artifact/containment checks
  -> explicit-path commit, branch, PR, and factual issue comment
```

The generic node has no `GH_TOKEN` and checkout credentials are not persisted.
Only the post-agent publisher receives the repository-scoped Actions token.
Copilot may not commit, push, merge, comment, close, or use GitHub APIs.
`executor_contract` also rejects any local commit made during execution.

The four commands produce different governed artifacts:

- **Plan** writes exactly one FR and sibling judgement through `judge.sh`.
- **Enforce** consumes committed FR/judgement authority, follows TDD, and uses
  `author.sh` for graph or prompt work.
- **Review** uses `review.sh` against the real PR head and writes one head-linked
  review artifact. Review is optional; humans remain merge authority.
- **Revise** produces either new FR/judgement authority or implementation-only
  changes on the existing PR. Mixed authority and implementation changes fail.

## Trust Boundary

The job-level event gate admits:

- opened/edited issues authored by `OWNER`, `MEMBER`, or `COLLABORATOR`; or
- the owner applying the `gitclaw` label.

Issue title/body enter shell only through environment variables and are written
to a canonical bounded request artifact before model execution. Request and
optional owner reference hashes are verified after execution.

The Copilot credential is still visible to the agent process. Security therefore
requires that credential to have Copilot entitlement but no repository-write
capability. Prompt instructions and diff containment are not a sandbox against a
malicious model.

## Executable Control Bundle

The agent control plane is mirrored from YAMLGraph commit
`15f134d8ddf8e16266170ed57fdebfd3d67e11de`:

- repository instructions;
- feature-request, judge, graph-authoring, and review skills;
- canonical judge/author/review adapters and wrappers; and
- command, authoring-sentinel, Python, YAML, and Markdown hooks.

`control-bundle.json` closes and hashes the runtime set;
`control-bundle-trace.md` records dependencies and dispositions. Verify with:

```bash
python -m tools.control_bundle
```

Adapters are advisory artifact producers and perform no Git/GitHub side effect.
Local hook adaptations are documented in `docs/control-bundle-adaptations.md`.

## References

An owner may select one committed bounded reference set by adding exactly:

```text
Reference-set: <name>
```

The workflow stages and hashes it under the request directory. Reference files
are data with provenance: agents may inspect/adapt them but never execute or
modify them.

## Scheduled YAMLGraph Runtime

Cron schedules one YAMLGraph task. `cron.yml` remains independent from issue
execution and invokes the configured task at 06:00 UTC or by manual dispatch.
The workflow validates that `YAMLGRAPH_TASK` names a tracked regular YAML file,
then runs exactly:

```bash
YAMLGRAPH_TASK=features/haiku/graph.yaml
yamlgraph graph run "$YAMLGRAPH_TASK" --full
```

The same command runs from a normal checkout. The task owns its inputs, outputs,
effects, and failure semantics; cron does not discover graphs, inject dates,
interpret state, write files, or publish commits. The starter task resolves its
own date, defaults the city to Oulu, Finland, and accepts an optional city
override when run manually.

## Development

```bash
python -m pytest tests/ -q
python -m tools.control_bundle
yamlgraph graph lint gitclaw.yaml
```

The current control bundle expects Python 3.12, Node 22, Git, POSIX shell tools,
`@github/copilot`, and `yamlgraph`. Agent-facing controls are enforcement
infrastructure and require human review before push.

## Security and Operational Limits

- The system assumes a single trusted operator and trusted model/vendor.
- Generated code is not runtime-sandboxed.
- Provider and action versions are not yet fully pinned.
- GitHub scheduled workflows may run late.
- Upstream APIs and schemas drift; task failures propagate through the
  YAMLGraph command and fail the scheduled job.
- No automatic merge occurs.

The license disclaims warranty; the repository owner remains accountable for
task effects and published artifacts.

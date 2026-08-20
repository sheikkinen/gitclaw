# gitclaw 🐾

**Issue in, feature out, output every morning.**

gitclaw is a forkable template repo: file a GitHub issue describing a
small daily LLM feature ("daily haiku about the weather in Oulu"), and
a plan → judge → enforce → review pipeline — run entirely by GitHub
Copilot CLI inside GitHub Actions — writes the feature request, judges
it, implements it as a [YAMLGraph](https://github.com/sheikkinen/yamlgraph)
graph, reviews the diff, and commits it. A daily cron then runs every
accepted feature and commits its output.

## Use it

1. **Use this template** (green button) to create your own copy.
2. Enable Actions on your copy (template instantiation disables workflows).
3. Set two repository secrets:
   | Secret | Value |
   |---|---|
   | `COPILOT_CLI_TOKEN` | a GitHub token with Copilot access (e.g. `gh auth token`) — consumed as `COPILOT_GITHUB_TOKEN` by Copilot CLI |
   | `ANTHROPIC_API_KEY` | provider key for running the generated graphs |

   No PAT is needed for git/issue operations — the built-in
   `GITHUB_TOKEN` with `contents: write` / `issues: write` suffices.
4. File an issue with a one-line feature wish. Watch the pipeline.
5. Every morning (06:00 UTC), `cron.yml` runs all accepted features and
   commits their outputs to `outputs/`.

## Trust model

The intake workflow triggers on all issues but the **job-level `if` is
the sole barrier** before LLM execution with secrets:

- `opened`: issue author must be `OWNER`, `MEMBER`, or `COLLABORATOR`.
  `CONTRIBUTOR` is deliberately excluded — a merged typo fix must not
  grant LLM invocation rights.
- `labeled`: label must be `gitclaw` **and the sender applying it must
  be the repo owner** — label presence alone is insufficient (issue
  forms can auto-apply labels; no template in this repo may auto-apply
  `gitclaw`).

Anonymous/other issues never reach the LLM. Issue text enters shell
steps only via `env:` blocks, never inline `${{ }}` interpolation.

## Pipeline

```
issue → ledger(seen) → plan → judge ──REJECTED──→ comment + close
                                │
                     APPROVED / WITH REVISIONS
                                ▼
                      enforce (resumes plan session)
                                ▼
                             review ──REJECTED──→ one remediation lap,
                                │                 then final reject
                            APPROVED
                                ▼
              containment gate → commit → comment → close
```

- **Verdicts are read from artifacts** (`judgement.md` / `review.md`),
  never from LLM stdout tokens. Unparseable verdict = fail closed.
- **Ledger** (`state/issues.jsonl`): append-only frozen state machine
  (`tools/ledger.py`); every transition commits immediately. Illegal
  transitions raise.
- **Containment** (`tools/contain.py`): fail-closed allowlist — a
  pipeline run may only touch `features/<name>/**` and the ledger.
  Anything else aborts before push.
- **Idempotency**: re-delivered events skip terminal issues (exit 78);
  interrupted non-terminal issues demand human recovery (exit 65).

## Layout

```
gitclaw.yaml            orchestrator graph (YAMLGraph)
prompts/                plan / judge / enforce / review contracts
features/<name>/        FR.md, judgement.md, review.md,
                        authoring-report.md, graph.yaml, prompts/
tools/                  ledger, containment, slug, cron runner
scripts/author-report.sh  mechanical artifact verifier
state/issues.jsonl      append-only ledger
outputs/                daily cron outputs
.github/skills/         vendored authoring/judging doctrine snapshot
```

## Limitations

- Copilot CLI must authenticate via `COPILOT_GITHUB_TOKEN`; there is no
  API fallback. If your token lacks Copilot access, intake fails.
- Cron cadence is best-effort (GitHub scheduled workflows may delay or
  skip under load).
- A failed cron feature is recorded (`outputs/<date>-<name>.failed.json`)
  and does not block other features; the job exits 1 as an operator
  signal.
- One remediation lap on review rejection, then final reject — no
  infinite enforce loops.

Governed by yamlgraph FR-827.

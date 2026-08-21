# Judgement: FR-001 Convert haiku example to Finnish Kalevala runic format

**Verdict:** APPROVED WITH REVISIONS — the requested conversion is narrow and feasible, but authority activates only after the FR removes its plan-only/judgement acceptance item and resolves the state-key contradiction.

**Reviewed against:** `feature-requests/FR-001-kalevala-runic-haiku-conversion.md`; cited evidence `features/issue-4-32443301071/request.json`, `features/haiku/graph.yaml`, `features/haiku/prompts/haiku.yaml`; doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `.github/skills/graph-authoring/doctrine.md`, `feature-requests/TEMPLATE.md`.

## What is sound

The source request is real and specific: convert the existing haiku example to Finnish Kalevala runic format while preserving the self-sufficient date tool and optional city configuration (`features/issue-4-32443301071/request.json:1`). The existing graph has exactly the surfaces the FR names: `features/haiku/graph.yaml` defines `current_date` as `date +%Y-%m-%d`, default `city: Oulu, Finland`, and the linear `START -> date -> generate -> END` path (`features/haiku/graph.yaml:11-41`). The existing prompt is a direct haiku prompt with a `haiku` schema field and 5-7-5 requirements, so the conversion can be localized to graph description/state output and prompt/schema text (`features/haiku/prompts/haiku.yaml:1-20`).

Strategic classification: **Contrib/example**. This is one concrete example conversion using existing graph and prompt abstractions; it does not justify a framework primitive. The FR correctly routes material graph/prompt edits through graph-authoring doctrine (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:70-72`; `.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:86-102`) and preserves the existing graph topology rather than inventing new runtime machinery (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:65-69`).

## Required revisions

### R-1: Remove judgement execution from enforcement acceptance

Delete the acceptance criterion that says the FR must be reviewed and judged via `scripts/judge.sh` (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:79-80`). Judgement is the gate producing this artifact, not a deliverable for the enforcer. Replace it with an enforcement-facing criterion that the revised FR has a judgement artifact and that implementation proceeds only after the revisions are folded.

### R-2: Resolve the output state-key contradiction

Choose one output key and state it consistently. The FR currently says there will be "no new nodes, tools, or state keys" (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:48`, `feature-requests/FR-001-kalevala-runic-haiku-conversion.md:70`) while also requiring `state_key` to change from `haiku` to a renamed schema field (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:57-66`). Fold this as: "the generated output state key may be renamed from `haiku` to `verse`; no additional output key beyond that rename is authorized."

### R-3: Freeze the prompt-file strategy

Replace "Rename/adapt `features/haiku/prompts/haiku.yaml` (or add a sibling prompt)" (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:54-55`) with one exact strategy. Authorized default: modify the existing `features/haiku/prompts/haiku.yaml` in place and update `features/haiku/graph.yaml` to reference the resulting prompt name if the prompt schema name changes. A sibling prompt is not authorized unless the FR is revised to explain why the old prompt must remain.

### R-4: Make form validation mechanically checkable

Rewrite the poetic-form acceptance criterion (`feature-requests/FR-001-kalevala-runic-haiku-conversion.md:81-82`) into file-content assertions plus smoke validation. The enforcer can check that prompt/schema text no longer requires "haiku" or "5-7-5" and does require "Kalevala", "trochaic tetrameter", "alliteration", and "parallel" language. The smoke run can prove the graph executes, but it cannot reliably prove metrical correctness of an LLM output.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `features/haiku/graph.yaml` description and generated output `state_key` only |
| D-2 | `features/haiku/prompts/haiku.yaml` schema field/name/description and system/user instructions |
| D-3 | The narrowest documentation/example description that names Kalevala runic verse, only if such a description exists adjacent to the example |
| D-4 | `tmp/draft-authoring-report.md` from the graph-authoring adapter during enforcement |

Not authorized: new graph nodes, new tools, changed `current_date` command, changed date node, changed city variable/default/optionality, changed edge list, new runtime primitives, framework code changes, judge/review/doctrine/hook/CI changes, metric tooling, broad example restructuring, or a second coexisting haiku/Kalevala example without a new FR.

## Revised acceptance criteria

- [ ] AC-01: The folded FR no longer lists judge execution as an enforcement deliverable and states that authority begins only after this judgement's required revisions are incorporated.
- [ ] AC-02: `features/haiku/graph.yaml` still contains `current_date` with command `date +%Y-%m-%d`, `city: Oulu, Finland`, and exactly the existing linear edge sequence `START -> date -> generate -> END`.
- [ ] AC-03: The generated output key is consistently named in both `features/haiku/graph.yaml` and `features/haiku/prompts/haiku.yaml`; if renamed, the only authorized rename is `haiku` to `verse`.
- [ ] AC-04: `features/haiku/prompts/haiku.yaml` no longer instructs 5-7-5 haiku output and includes explicit Kalevala runic-verse requirements: trochaic tetrameter, alliteration, and parallelism/repetition.
- [ ] AC-05: The graph-authoring adapter is used for enforcement and its `tmp/draft-authoring-report.md` lists modified artifacts, precedent, exact lint command, exact smoke command, repairs, and any blocked validation.
- [ ] AC-06: `yamlgraph graph lint features/haiku/graph.yaml` passes.
- [ ] AC-07: A narrow smoke run of `features/haiku/graph.yaml` with a city variable executes successfully, or the exact blocked command and reason are recorded in the authoring report.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the FR before any graph or prompt artifact is changed. | GATE |
| C-2 | Use the graph-authoring adapter route for the material `graph.yaml` and `prompts/*.yaml` edits; unsentineled manual authoring is not authorized. | GATE |
| C-3 | Preserve the date tool, city configuration, and edge topology exactly; only the poetic form and single generated output key rename are in scope. | GATE |
| C-4 | Do not claim metrical correctness from a smoke run alone; validate prompt instructions by file assertions and execution by lint/smoke. | GATE |

Authority granted: after the required revisions are folded, enforcement may convert the existing `features/haiku` example from haiku to Kalevala-style runic verse by changing only the prompt/schema text, graph description, and one generated output key rename.

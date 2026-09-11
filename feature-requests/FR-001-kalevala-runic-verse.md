# Feature Request: Convert the weather haiku to Kalevala runic verse

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-21
**First consumer / first event:** the daily cron invokes
`features/haiku/graph.yaml` with its default or operator-supplied city after a
separate judgement and enforcement change.

## Summary

Plan an in-place conversion of the existing weather haiku task to Finnish
Kalevala-style runic verse. Preserve its self-sufficient date command, optional
city override, graph path, node sequence, and cron integration.

This issue produces the plan only. Judgement and implementation remain separate
events.

## Value Statement

GitClaw's Finnish weather example uses a Finnish poetic form while retaining the
small, independently runnable YAMLGraph task already used by cron.

## Problem

The current task asks for a Japanese 5-7-5 haiku even though its subject, default
city, and dry voice are Finnish. Issue #4 requests Kalevala runic form without
changing the date tool or city configuration.

The committed task currently has two nodes (`date`, `generate`), three edges,
the command `date +%Y-%m-%d`, and the default `city: Oulu, Finland`. Its prompt
schema, instructions, output field, graph name, and description all still name
haiku.

## Research

- `acceptance/kalevala-lifecycle.sh` sends this exact plan request and requires
  the Plan phase to change exactly one `feature-requests/FR-*.md` path. Later
  Judge and Enforce phases are distinct.
- The same acceptance witness later invokes
  `features/haiku/graph.yaml`, making that graph path part of the current
  lifecycle contract.
- Repository search found live haiku-path or behavior references in the cron
  contract tests, repository-hygiene tests, README, authoring report, acceptance
  witness, graph, and prompt. A path-wide rename is therefore larger than the
  requested form conversion.
- Remote branch `origin/gitclaw/issue-4-plan` contains commit `a4076a9`, which
  adds two files and 164 lines but has no pull request. It combines the FR with a
  judgement despite the plan-only request, so it is prior evidence rather than
  a submission candidate.

## Ideal Result

The existing cron task generates one short Finnish Kalevala-style weather verse
for the configured city and current date. The task remains runnable at the same
graph path, uses the same date command and city contract, and adds no framework
capability, tool, node, edge, or second example.

## Proposed Solution

1. Keep `features/haiku/graph.yaml` and its `START -> date -> generate -> END`
   topology. Preserve the date node, command, city variable, and default exactly.
2. Update the graph name and description to describe Kalevala runic verse.
   Rename the generated state key from `haiku` to `verse`; do not add another
   output key.
3. Adapt `features/haiku/prompts/haiku.yaml` in place. Rename its schema and field
   to weather verse terms and replace 5-7-5 instructions with concise Finnish
   runic-form guidance: trochaic tetrameter, alliteration, and parallelism or
   repetition. Keep the dry Finnish tone and output-only contract.
4. Update existing tests and nearby README wording only where they assert or
   advertise haiku behavior. Do not add a new example, weather provider, runtime
   primitive, configuration flag, or process mechanism.
5. During the later Enforce phase, route the material graph and prompt edits
   through GitClaw's graph-authoring adapter, then run the target's lint, focused
   tests, and smoke command.

## Acceptance Criteria

- [ ] This Plan change adds only this feature-request file; it does not create a
      judgement or modify implementation files.
- [ ] A separate enforcement keeps the graph at
      `features/haiku/graph.yaml` with the existing date command, city variable
      and default, two nodes, and three-edge sequence.
- [ ] The graph and prompt consistently use `verse` as the only generated output
      key and no longer request 5-7-5 haiku behavior.
- [ ] The prompt explicitly requests Kalevala-style trochaic tetrameter,
      alliteration, and parallelism or repetition while retaining the dry
      Finnish tone and output-only response.
- [ ] Existing tests cover the preserved date/city/topology contract and the new
      poetic-form instructions; stale README claims are updated.
- [ ] The later graph-authoring report records the exact lint and smoke commands,
      their outcomes, repairs, and any blocked validation.
- [ ] `yamlgraph graph lint features/haiku/graph.yaml` and the focused target
      tests pass during enforcement.
- [ ] No YAMLGraph framework code, new example, weather provider, node, tool,
      edge, or configuration option is added.

## Alternatives Considered

| Alternative | Probe | Disposition |
|---|---|---|
| Submit `origin/gitclaw/issue-4-plan` | `git show --stat a4076a9` reports two files and 164 lines, including a judgement; target PR query returns none. | Rejected. It crosses the issue's plan-only boundary. Its repository observations remain useful prior evidence. |
| Add a second Kalevala example | Issue #4 says convert the existing example; `test_haiku_is_the_only_example` currently asserts one feature directory. | Rejected. It grows the example surface and contradicts the request. |
| Rename the `features/haiku` directory | The acceptance witness later runs the exact path `features/haiku/graph.yaml`; repository search finds additional path references in tests, README, and reports. | Rejected for this change. Keep the lifecycle path stable and convert behavior in place. |
| Keep the output field named `haiku` | The graph and prompt currently use that field specifically for 5-7-5 output. | Rejected. A single `haiku` to `verse` rename removes a false contract without adding state. |

## Related

- [GitHub issue #4](https://github.com/sheikkinen/gitclaw/issues/4)
- Prior unsubmitted commit: `a4076a9`
- `acceptance/kalevala-lifecycle.sh`
- `features/haiku/graph.yaml`
- `features/haiku/prompts/haiku.yaml`
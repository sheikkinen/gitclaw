# Feature Request: Convert haiku example to Finnish Kalevala runic format

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-21
**First consumer / first event:** the daily cron fixture at
`features/haiku/graph.yaml` (renamed target), at the moment `generate`
node calls the prompt with `{state.city}` and `{state.date}` — the
existing self-sufficient `current_date` tool node fires unchanged, only
the prompt's poetic form and schema field name change.
**Source:** features/issue-4-32443301071/request.json (SHA-256
bb3cd63b08046cbb50d81818fdaec3a03953f99ec1b024043e7eec3490a1f805)

## Summary

Convert the existing haiku-based weather example
(`features/haiku/graph.yaml` + `features/haiku/prompts/haiku.yaml`) from
5-7-5 Japanese haiku form to Finnish Kalevala trochaic tetrameter (runic
verse / "Kalevala-mitta"), while preserving the graph's structure: the
self-sufficient `current_date` tool node and the optional `city`
variable (defaulted, overridable) stay exactly as they are today.

## Value Statement

Gives gitclaw a locale-fitting example — Finnish weather reported in the
nation's own epic verse form instead of a borrowed Japanese one —
without touching the tool/date/city plumbing that other examples may
copy from this fixture.

## Problem

The current example generates a 5-7-5 haiku about the weather in a
configurable city. This is a plan-only issue asking to replace the
haiku poetic form with Kalevala runic meter (trochaic tetrameter,
alliteration, parallelism/repetition — the "Kalevala-mitta" used in the
Finnish national epic), keeping everything else (date tool, city
config) unchanged. Judgement of this plan is explicitly deferred to a
separate issue; this FR only records the plan.

## Ideal Result

A single example graph produces a short Kalevala-style runic verse
(trochaic tetrameter with alliteration and parallel repetition) about
today's weather in a configurable Finnish city, generated via the same
`current_date` tool node and `city` variable default that the existing
haiku example already uses — no new nodes, tools, or state keys.

## Proposed Solution

Minimal path back from the ideal result:

1. Rename/adapt `features/haiku/prompts/haiku.yaml` (or add a sibling
   prompt) so the schema field and prompt instructions request Kalevala
   runic verse instead of a 5-7-5 haiku:
   - Schema field renamed from `haiku` to a form-accurate name (e.g.
     `verse` or `runo`), with a description referencing Kalevala metre
     (trochaic tetrameter, alliteration, parallelism).
   - System/user prompt text swapped from "laconic Finnish poet who
     writes haiku" to "Finnish runo-singer who composes in Kalevala
     metre", with style requirements listing trochaic tetrameter,
     alliteration, and parallel couplets instead of 5-7-5 syllable
     counting.
2. Update `features/haiku/graph.yaml`'s `state_key` (from `haiku` to
   match the renamed schema field) and description string to reflect
   the new form; leave `tools.current_date`, the `date` node, the
   `city` variable/default, and the edge list (`START -> date ->
   generate -> END`) untouched.
3. No new tools, nodes, or state keys are introduced — this is a
   prompt/schema content change only, authored via `scripts/author.sh`
   per the graph-authoring doctrine when enforcement proceeds.
4. This FR records the plan only. Judgement (`scripts/judge.sh`) and
   any implementation/enforcement happen in separate, later steps per
   the issue's explicit request.

## Acceptance Criteria

- [ ] FR reviewed and judged via `scripts/judge.sh` (separate issue, out
      of scope for this plan-only FR)
- [ ] On enforcement: prompt content changed from 5-7-5 haiku to
      Kalevala trochaic-tetrameter runic verse
- [ ] On enforcement: `current_date` tool node and `city`
      variable/default preserved unchanged (same tool command, same
      default value, same optionality)
- [ ] On enforcement: `yamlgraph graph lint` and a smoke run of the
      converted graph both pass
- [ ] Documentation/example description updated to name the new form

## Alternatives Considered

- Add a brand-new second example instead of converting the existing
  one — rejected because the issue explicitly asks to convert/replace
  the existing haiku example while preserving its tool/city plumbing.
- Rewrite the whole graph from scratch — rejected as scope creep; only
  the poetic form (prompt + schema field name) needs to change.

## Related

- Source request: `features/issue-4-32443301071/request.json`
- Existing example: `features/haiku/graph.yaml`,
  `features/haiku/prompts/haiku.yaml`
- Issue #4 (sheikkinen/gitclaw)

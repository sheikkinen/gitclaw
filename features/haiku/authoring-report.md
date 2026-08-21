# Authoring Report: FR-847 Self-Sufficient Haiku

## Artifacts

- `features/haiku/graph.yaml`
- `features/haiku/prompts/haiku.yaml`

The canonical `scripts/author.sh tmp/fr-847-haiku-authoring-brief.md` route
authored both material changes. Its verified draft report was reviewed before
this durable report was updated.

## Precedent

- Preserved the committed haiku LLM prompt/state pattern.
- Used YAMLGraph's deterministic named shell-tool node contract for current
  date resolution.
- Top-level graph variables provide a default city while CLI variables retain
  override precedence.

## Validation

- `yamlgraph graph lint features/haiku/graph.yaml` passed with no issues.
- The no-variable run reached the LLM node with `date: 2026-08-21` and
  `city: Oulu, Finland`.
- The city-override run reached the LLM node with `date: 2026-08-21` and
  `city: Rovaniemi, Finland`.

## Repairs

No lint repair was required.

## Blocked validation

Both full smokes were blocked at provider authentication because the authoring
process had no API credential. The deterministic date tool and default/override
city state completed before that boundary. No successful LLM output is claimed.

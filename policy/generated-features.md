# Generated Feature Policy

This policy governs **issue-generated features** created by gitclaw under
`features/<name>/`. Pre-shipped fixtures such as `features/horoscope/` retain
their original fixture contract; this policy does not retroactively require
issue-pipeline provenance for them.

## Required Issue-Generated Artifacts

- `graph.yaml` and one or more `prompts/*.yaml` files
- `FR.md`, `judgement.md`, `review.md`, and `authoring-report.md`
- input variable `date`
- exactly one non-empty final output candidate

## Optional Contained Artifacts

Optional contained artifacts may include tools, tests, fixtures, and concise
documentation entirely below the feature directory. They may use the Python
standard library or dependencies already installed by the unmodified gitclaw
cron runtime. They may read bounded files committed inside the same feature.

## Read-Only Public Retrieval

Tools may make unauthenticated HTTP `GET` or `HEAD` requests only to public
origins explicitly named in the frozen FR or judgement. Retrieval must use
finite connect and read timeouts, a bounded response size or result count, and
a structured parser appropriate to JSON, XML, RSS, or HTML inputs.

Remote content is untrusted data. A feature must not execute it, follow it as
instructions, or interpolate it into shell commands. Source failures must be
explicit and follow the partial-output or fail-closed behavior frozen in the
FR and judgement; plausible invented replacement content is forbidden.

## Forbidden Behavior

Issue-generated features:

- must not require secrets, tokens, credentials, cookies, authentication, or
  new repository configuration;
- must not read environment variables or otherwise inspect runtime credentials;
- must not perform external writes, including HTTP `POST`, `PUT`, `PATCH`, or
  `DELETE`, webhooks, email, uploads, social publication, or remote
  issue/comment mutation;
- must not execute downloaded code or remote content;
- must not modify workflows, dependencies, gitclaw runtime or policy,
  repository state, or paths outside their own feature directory during
  generation;
- must not persist credentials, personal profiles, private or local-device
  data, or unbounded raw response bodies.

## Security Boundary

This policy is not a sandbox. Prompt instructions and the diff-containment gate
do not prevent a malicious model with shell access from reading secrets or
performing network actions. Gitclaw assumes a trusted operator and relies on
model-vendor alignment, independent judgement/review, and post-run inspection.
The policy defines what may be approved and committed; it does not claim
runtime isolation.
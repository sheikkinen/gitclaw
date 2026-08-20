# Control Bundle Trace

Source: `https://github.com/sheikkinen/yamlgraph` at
`15f134d8ddf8e16266170ed57fdebfd3d67e11de`.

This trace closes the runtime file set in `control-bundle.json`. The manifest
contains only `mirror` and `adapt-local` entries; excluded references are
recorded here as `not-runtime`.

## Wrappers

| Referencer | Referenced path | Disposition | Rationale |
|---|---|---|---|
| `scripts/judge.sh` | `.github/skills/judge-fr/adapters/graph.yaml` | mirror | Sole judge route |
| `scripts/author.sh` | `.github/skills/graph-authoring/adapters/graph.yaml` | mirror | Sole authoring route |
| `scripts/author.sh` | `scripts/author_preflight.py` | mirror | Mechanical brief preflight |
| `scripts/review.sh` | `.github/skills/review-pr/adapters/graph.yaml` | mirror | Sole review route |
| wrapper diagnostics | `scripts/worktree.sh` | not-runtime | Mentioned only as operator advice; wrappers never execute it |

## Skills and Adapters

Every regular file below these source roots is mirrored and manifest-listed:

- `.github/skills/feature-request/`
- `.github/skills/judge-fr/`
- `.github/skills/graph-authoring/`
- `.github/skills/review-pr/`

Adapter graphs reference only prompts and doctrine/templates inside their own
mirrored roots. Markdown references ending in punctuation are documentation,
not additional runtime paths.

## Hooks

| Referenced source | Disposition | Rationale |
|---|---|---|
| `.github/hooks/pre-command-guard.json` | mirror | Copilot PreToolUse registration |
| `.github/hooks/post-edit-checks.json` | adapt-local | Removes YAMLGraph-only FR checker; retains Python/YAML/Markdown checks |
| `.github/hooks/scripts/pre-command-guard.sh` | adapt-local | Maps governed graph paths and runtime audit state to GitClaw |
| `.github/hooks/scripts/checks/common.sh` | mirror | Shared hook payload parsing and result emission |
| `.github/hooks/scripts/checks/python-checks.sh` | mirror | Applicable Python feedback |
| `.github/hooks/scripts/checks/yaml-checks.sh` | mirror | YAML parsing and YAMLGraph graph lint |
| `.github/hooks/scripts/checks/markdown-checks.sh` | mirror | Markdown whitespace feedback |
| `.github/hooks/scripts/checks/fr-checks.sh` and prior-art helpers | not-runtime | YAMLGraph FR-board/registry policy is not present in GitClaw |
| reasoning-pattern hook/config/data | not-runtime | Session-reasoning policy is outside the six FR-846 guarantees |
| classify/session probe hooks and helpers | not-runtime | YAMLGraph observability and briefing infrastructure, not adapter execution |
| `.github/hooks/logs/**` | not-runtime | Runtime audit state moves to `tmp/hook-logs/` outside bundle closure |
| `.github/hooks/cmd` | not-runtime | Guard recognizes a command-channel string; no tracked source file exists |
| hook tests from YAMLGraph | not-runtime | GitClaw has focused bundle/hook witnesses instead of importing source tests |

## Instructions and Bundle Tooling

| Source | Target | Disposition | Rationale |
|---|---|---|---|
| `.github/copilot-instructions.md` | same | mirror | Canonical agent doctrine |
| `scripts/check_authoring_proof.py` | `scripts/control-bundle/verify.py` | adapt-local | Retains artifact-verification intent as the GitClaw bundle CLI |
| `tools/control_bundle.py` | local only | outside bundle | FR-846 verifier implementation, not mirrored authority |

## Closure

`python -m tools.control_bundle` walks every declared bundle root and rejects
unlisted regular files. Explicit instruction/wrapper targets are hash-checked
from manifest entries. Temporary witness artifacts remain under
`tmp/fr-846-witness/` and cannot enter the bundle closure.
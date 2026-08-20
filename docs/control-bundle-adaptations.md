# Control Bundle Local Adaptations

Source pin: `15f134d8ddf8e16266170ed57fdebfd3d67e11de`.

## `.github/hooks/post-edit-checks.json`

**Changed lines:** removed the `fr-checks.sh` PostToolUse command.

**GitClaw assumption:** GitClaw does not carry YAMLGraph's FR board, capability
registry, or prior-art hook dependencies.

**Original guarantee:** edited Python, YAML, Markdown, and FR files receive
immediate post-edit feedback.

**Preserved guarantee:** Python, YAML, and Markdown checks remain registered and
tested. FR process guarantees come from the mirrored skill/adapters, not a
non-portable YAMLGraph registry checker.

## `.github/hooks/scripts/pre-command-guard.sh`

**Changed lines:** default audit path and graph-authoring governed-path matcher,
copy-tree matcher, quick command filter, and denial text.

**GitClaw assumption:** generated graph artifacts live under
`features/<slug>/` today and `feature/` in the planned single-feature template.
Runtime logs must not appear under a manifest-closed bundle root.

**Original guarantee:** command bypasses are denied; hook parse ambiguity fails
closed; governed graph/prompt writes require the per-run authoring sentinel;
audit/lockdown state is available.

**Preserved guarantee:** the command checks are unchanged. The sentinel token
and file validation are unchanged. Only governed path classes map from
YAMLGraph examples/graphs to GitClaw feature paths. Audit/lockdown state moves
to `tmp/hook-logs/` and is exercised by focused witnesses.

## `.github/hooks/scripts/checks/yaml-checks.sh`

**Changed lines:** added an explicit PyYAML availability check before parsing.

**GitClaw assumption:** bootstrap test CI intentionally installs pytest only,
while real adapter runs install YAMLGraph (and therefore PyYAML).

**Original guarantee:** malformed graph/prompt YAML surfaces immediate feedback.

**Preserved guarantee:** when PyYAML exists, parsing/lint behavior is unchanged;
when absent, validation reports the missing parser instead of silently approving
the edit.

## `scripts/control-bundle/verify.py`

**Changed lines:** complete local CLI implementation derived from the artifact-
verification role of `scripts/check_authoring_proof.py`.

**GitClaw assumption:** bundle verification is a repository-local concern and
delegates to `tools.control_bundle`.

**Original guarantee:** required governance artifacts are verified by content,
not trusted from process exit status.

**Preserved guarantee:** the CLI exits non-zero unless manifest closure, paths,
hashes, modes, and regular-file constraints all verify.
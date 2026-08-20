"""FR-846 executable control bundle contract."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "control-bundle.json"
EXPECTED_ROOTS = [
    ".github/hooks",
    ".github/skills/feature-request",
    ".github/skills/graph-authoring",
    ".github/skills/judge-fr",
    ".github/skills/review-pr",
    "scripts/control-bundle",
]
EXPECTED_ADAPTERS = [
    ".github/skills/graph-authoring/adapters/graph.yaml",
    ".github/skills/judge-fr/adapters/graph.yaml",
    ".github/skills/review-pr/adapters/graph.yaml",
    "scripts/author.sh",
    "scripts/judge.sh",
    "scripts/review.sh",
    "feature-requests/TEMPLATE.md",
]


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_manifest_closes_pinned_bundle():
    manifest = load_manifest()
    assert set(manifest) == {"version", "source", "source_sha", "bundle_roots", "files"}
    assert manifest["version"] == 1
    assert manifest["source"] == "https://github.com/sheikkinen/yamlgraph"
    assert len(manifest["source_sha"]) == 40
    assert manifest["bundle_roots"] == EXPECTED_ROOTS
    targets = [entry["target"] for entry in manifest["files"]]
    assert targets == sorted(targets)
    assert len(targets) == len(set(targets))


def test_canonical_adapters_and_wrappers_exist():
    for relative in EXPECTED_ADAPTERS:
        assert (ROOT / relative).is_file(), relative


def test_hook_guarantees_are_configured():
    guard = (ROOT / ".github/hooks/scripts/pre-command-guard.sh").read_text()
    assert "--no-verify" in guard
    assert "Co-authored-by" in guard
    assert "YAMLGRAPH_AUTHORING_SENTINEL" in guard
    assert "scripts/author.sh" in guard
    assert "features/" in guard
    assert "prompts/" in guard


def run_guard(payload: dict, env: dict | None = None) -> dict:
    result = subprocess.run(
        [".github/hooks/scripts/pre-command-guard.sh"],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "HOOK_LOG_DIR": str(ROOT / "tmp/test-hook-logs"), **(env or {})},
        check=True,
    )
    return json.loads(result.stdout)


def test_guard_fails_closed_on_unparseable_payload():
    result = subprocess.run(
        [".github/hooks/scripts/pre-command-guard.sh"],
        cwd=ROOT,
        input="not-json",
        capture_output=True,
        text=True,
        env={**os.environ, "HOOK_LOG_DIR": str(ROOT / "tmp/test-hook-logs")},
        check=True,
    )
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "git commit --no-verify -m x",
        "git commit -m 'x\nCo-authored-by: Agent <agent@example.test>'",
    ],
)
def test_guard_denies_commit_bypasses(command):
    output = run_guard({"toolName": "run_in_terminal", "toolInput": {"command": command}})
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_guard_denies_unsentineled_feature_graph_write():
    output = run_guard(
        {
            "toolName": "apply_patch",
            "toolInput": {
                "input": "*** Begin Patch\n*** Add File: features/demo/graph.yaml\n+x\n*** End Patch"
            },
        }
    )
    detail = output["hookSpecificOutput"]
    assert detail["permissionDecision"] == "deny"
    assert "scripts/author.sh" in detail["permissionDecisionReason"]


def test_guard_allows_sentineled_feature_graph_write(tmp_path):
    token = "abc123"
    sentinel = tmp_path / "sentinel.json"
    sentinel.write_text(json.dumps({"token": token}))
    output = run_guard(
        {
            "toolName": "apply_patch",
            "toolInput": {
                "input": "*** Begin Patch\n*** Add File: features/demo/graph.yaml\n+x\n*** End Patch"
            },
        },
        {
            "YAMLGRAPH_AUTHORING_TOKEN": token,
            "YAMLGRAPH_AUTHORING_SENTINEL": str(sentinel),
        },
    )
    assert output.get("decision") == "approve"


def test_guard_lockdown_round_trip(tmp_path):
    env = {"HOOK_LOG_DIR": str(tmp_path)}
    locked = run_guard(
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": ".github/hooks/cmd lockdown"},
        },
        env,
    )
    assert locked["hookSpecificOutput"]["permissionDecision"] == "deny"
    denied = run_guard(
        {"toolName": "read_file", "toolInput": {"filePath": "README.md"}}, env
    )
    assert "LOCKDOWN ACTIVE" in denied["hookSpecificOutput"]["permissionDecisionReason"]
    unlocked = run_guard(
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": ".github/hooks/cmd unlock"},
        },
        env,
    )
    assert "Lockdown lifted" in unlocked["hookSpecificOutput"]["permissionDecisionReason"]
    assert (tmp_path / "audit.jsonl").is_file()


def test_yaml_post_edit_failure_surfaces(tmp_path):
    prompt = tmp_path / "prompts" / "bad.yaml"
    prompt.parent.mkdir()
    prompt.write_text("system: [unterminated\n")
    payload = {
        "toolName": "apply_patch",
        "toolInput": {
            "input": f"*** Begin Patch\n*** Update File: {prompt}\n*** End Patch"
        },
    }
    result = subprocess.run(
        [".github/hooks/scripts/checks/yaml-checks.sh"],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "HOOK_LOG_DIR": str(tmp_path / "logs")},
        check=True,
    )
    output = json.loads(result.stdout)
    assert "Prompt file error" in output["systemMessage"]


def test_verifier_accepts_committed_bundle():
    from tools import control_bundle

    control_bundle.verify(ROOT, MANIFEST)


def copy_bundle(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    manifest = load_manifest()
    for entry in manifest["files"]:
        target = root / entry["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / entry["target"], target)
    path = root / "control-bundle.json"
    path.write_text(json.dumps(manifest))
    return root, path


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown-key",
        "hash",
        "traversal",
        "duplicate-target",
        "duplicate-source",
        "mode",
        "missing",
        "unlisted",
        "symlink",
        "dirty",
    ],
)
def test_verifier_fails_closed(tmp_path, mutation):
    from tools import control_bundle

    root, path = copy_bundle(tmp_path)
    manifest = json.loads(path.read_text())
    if mutation == "unknown-key":
        manifest["unexpected"] = True
    elif mutation == "hash":
        manifest["files"][0]["sha256"] = "0" * 64
    elif mutation == "traversal":
        manifest["files"][0]["target"] = "../escape"
    elif mutation == "duplicate-target":
        manifest["files"].append(dict(manifest["files"][0]))
    elif mutation == "duplicate-source":
        manifest["files"][1]["source"] = manifest["files"][0]["source"]
    elif mutation == "mode":
        manifest["files"][0]["mode"] = (
            "100755" if manifest["files"][0]["mode"] == "100644" else "100644"
        )
    elif mutation == "missing":
        (root / manifest["files"][0]["target"]).unlink()
    elif mutation == "unlisted":
        (root / manifest["bundle_roots"][0] / "unlisted.txt").write_text("x")
    elif mutation == "symlink":
        target = root / manifest["files"][0]["target"]
        target.unlink()
        target.symlink_to(root / manifest["files"][1]["target"])
    else:
        with (root / manifest["files"][0]["target"]).open("a") as handle:
            handle.write("dirty")
    path.write_text(json.dumps(manifest))
    with pytest.raises(control_bundle.ControlBundleError):
        control_bundle.verify(root, path)
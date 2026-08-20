"""FR-846 executable control bundle contract."""

import json
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


def test_verifier_accepts_committed_bundle():
    from tools import control_bundle

    control_bundle.verify(ROOT, MANIFEST)


@pytest.mark.parametrize("mutation", ["hash", "traversal", "duplicate"])
def test_verifier_fails_closed(tmp_path, mutation):
    from tools import control_bundle

    manifest = load_manifest()
    if mutation == "hash":
        manifest["files"][0]["sha256"] = "0" * 64
    elif mutation == "traversal":
        manifest["files"][0]["target"] = "../escape"
    else:
        manifest["files"].append(dict(manifest["files"][0]))
    path = tmp_path / "control-bundle.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(control_bundle.ControlBundleError):
        control_bundle.verify(ROOT, path)
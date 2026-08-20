"""Operation-aware generic executor containment."""

from tools import contain


def test_plan_and_review_allow_exact_artifacts_only():
    expected = {"feature-requests/FR-001.md", "feature-requests/FR-001.judgement.md"}
    assert contain.violations(sorted(expected), "plan", expected) == []
    assert contain.violations(["src/app.py"], "plan", expected) == ["src/app.py"]


def test_enforce_blocks_authority_and_platform_but_allows_project_code():
    paths = [
        "src/app.py",
        "tests/test_app.py",
        "feature-requests/FR-001.md",
        "features/x/request.json",
        ".github/workflows/evil.yml",
        "tools/evil.py",
        "gitclaw.yaml",
    ]
    assert contain.violations(paths, "enforce") == paths[2:]


def test_traversal_and_absolute_paths_fail():
    assert contain.violations(["../outside", "/tmp/x"], "enforce") == [
        "../outside",
        "/tmp/x",
    ]

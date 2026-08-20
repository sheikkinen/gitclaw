"""FR-845 generic skill executor contract."""

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
CRON_HASHES = {
    ".github/workflows/cron.yml": "c242d8008ba351b37ee9a28b2f31d0e7de757cef52b0efa5795a4952aa028779",
    "tools/cron_run.py": "aedafd7e735ee178cf39415ab55c413e53ceea1d792ce07208461bb0b7891e80",
}


def test_exact_command_parser():
    from tools.executor_contract import parse_command

    assert parse_command("Plan a greeting as a Feature Request").operation == "plan"
    assert parse_command("Enforce feature-requests/FR-001-greeting.md").operation == "enforce"
    review = parse_command("Review 12 against feature-requests/FR-001-greeting.md")
    assert review.operation == "review" and review.pr == 12
    revise = parse_command("Revise PR 12: fix timeout handling")
    assert revise.operation == "revise" and revise.pr == 12


@pytest.mark.parametrize(
    "command",
    [
        "make a greeting",
        "Plan x as a Feature Request; Enforce feature-requests/FR-1.md",
        "Enforce ../secret.md",
        "Review nope against feature-requests/FR-001.md",
        "Revise feature-requests/FR-001.md:",
    ],
)
def test_command_parser_fails_closed(command):
    from tools.executor_contract import ExecutorContractError, parse_command

    with pytest.raises(ExecutorContractError):
        parse_command(command)


def test_generic_graph_has_one_copilot_node_and_no_resume():
    graph = (ROOT / "gitclaw.yaml").read_text()
    assert graph.count("type: copilot") == 1
    assert "prompt: generic" in graph
    for forbidden in ("resume:", "prompt: plan", "prompt: judge", "prompt: enforce", "prompt: review"):
        assert forbidden not in graph


def test_generic_prompt_is_thin_and_stage_neutral():
    prompt = (ROOT / "prompts/generic.yaml").read_text()
    for marker in (
        "request_path",
        "request_sha256",
        "operation",
        "current_head",
        "Do not commit",
        "Do not push",
        "Do not use GitHub APIs",
    ):
        assert marker in prompt
    assert "{issue_body}" not in prompt


def test_old_semantic_harness_is_absent():
    for name in ("plan.yaml", "judge.yaml", "enforce.yaml", "review.yaml"):
        assert not (ROOT / "prompts" / name).exists()
    assert not (ROOT / "policy/generated-features.md").exists()


def test_workflow_isolates_agent_credentials_and_publishes_after_verify():
    workflow = (ROOT / ".github/workflows/intake.yml").read_text()
    assert "persist-credentials: false" in workflow
    agent = workflow.split("- name: Run generic agent", 1)[1].split("- name:", 1)[0]
    assert "GH_TOKEN" not in agent
    assert "github.token" not in agent
    assert "COPILOT_GITHUB_TOKEN" in agent
    assert workflow.index("executor_contract verify") < workflow.index("executor_publish")


def test_revision_classification_is_exclusive():
    from tools.executor_contract import ExecutorContractError, classify_revision

    assert classify_revision(["feature-requests/FR-002.md", "feature-requests/FR-002.judgement.md"]) == "replan"
    assert classify_revision(["src/app.py", "tests/test_app.py"]) == "implementation"
    with pytest.raises(ExecutorContractError):
        classify_revision(["feature-requests/FR-002.md", "src/app.py"])
    with pytest.raises(ExecutorContractError):
        classify_revision([])


def test_plan_gate_requires_one_hash_linked_fr_and_judgement(tmp_path, monkeypatch):
    from tools.executor_contract import ExecutorContractError, _plan

    monkeypatch.chdir(tmp_path)
    digest = "a" * 64
    fr = tmp_path / "feature-requests" / "FR-001-greeting.md"
    fr.parent.mkdir()
    fr.write_text(
        "# Feature Request: Greeting\n\n"
        + "\n\n".join(
            (
                "## Summary\nGreeting",
                "## Value Statement\nValue",
                "## Problem\nMissing",
                "## Ideal Result\nWorks",
                "## Proposed Solution\nGraph",
                "## Acceptance Criteria\n- [ ] Green",
                "## Alternatives Considered\nNone",
            )
        )
        + f"\n\nRequest SHA-256: `{digest}`\n"
    )
    judgement = tmp_path / "feature-requests" / "FR-001-greeting.judgement.md"
    judgement.write_text("# Judgement\n\n**Verdict:** APPROVED\n")
    assert _plan(
        [fr.relative_to(tmp_path).as_posix(), judgement.relative_to(tmp_path).as_posix()],
        digest,
    ) == ["feature-requests/FR-001-greeting.md", "feature-requests/FR-001-greeting.judgement.md"]
    judgement.unlink()
    with pytest.raises(ExecutorContractError):
        _plan(["feature-requests/FR-001-greeting.md"], digest)


def test_enforce_gate_keeps_authority_immutable_and_requires_report(tmp_path, monkeypatch):
    from tools.executor_contract import ExecutorContractError, _enforce

    monkeypatch.chdir(tmp_path)
    graph = tmp_path / "features" / "greeting" / "graph.yaml"
    graph.parent.mkdir(parents=True)
    graph.write_text("version: '1.0'\n")
    with pytest.raises(ExecutorContractError):
        _enforce(["features/greeting/graph.yaml"], "feature-requests/FR-001.md")
    report = tmp_path / "tmp" / "draft-authoring-report.md"
    report.parent.mkdir()
    report.write_text("Artifacts Precedent Validation Repairs Blocked validation")
    assert _enforce(["features/greeting/graph.yaml"], "feature-requests/FR-001.md")
    with pytest.raises(ExecutorContractError):
        _enforce(["feature-requests/FR-001.md"], "feature-requests/FR-001.md")


def test_review_gate_is_head_linked_and_single_artifact(tmp_path, monkeypatch):
    from tools.executor_contract import _review

    monkeypatch.chdir(tmp_path)
    head = "b" * 40
    review = tmp_path / "reviews" / f"pr-12-{head}.md"
    review.parent.mkdir()
    review.write_text("**Merge verdict:** Not approved\n")
    assert _review([review.relative_to(tmp_path).as_posix()], 12, head)


def test_publisher_rechecks_report_hashes_before_side_effects(tmp_path, monkeypatch):
    from tools.executor_publish import PublishError, publish

    monkeypatch.chdir(tmp_path)
    artifact = tmp_path / "artifact.md"
    artifact.write_text("ok")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "operation": "plan",
                "paths": [{"path": "artifact.md", "sha256": "0" * 64}],
            }
        )
    )
    monkeypatch.setenv("GH_TOKEN", "canary")
    with pytest.raises(PublishError, match="changed"):
        publish(report, "owner/repo", 1)


def test_changed_paths_expands_untracked_directories(tmp_path, monkeypatch):
    from tools.executor_contract import changed_paths

    monkeypatch.chdir(tmp_path)
    subprocess = __import__("subprocess")
    subprocess.run(["git", "init"], check=True, capture_output=True)
    directory = tmp_path / "features" / "greeting"
    directory.mkdir(parents=True)
    (directory / "graph.yaml").write_text("version: 1\n")
    (directory / "prompts").mkdir()
    (directory / "prompts" / "greeting.yaml").write_text("system: hi\n")
    assert changed_paths() == [
        "features/greeting/graph.yaml",
        "features/greeting/prompts/greeting.yaml",
    ]


def test_cron_runtime_is_byte_unchanged():
    for relative, expected in CRON_HASHES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
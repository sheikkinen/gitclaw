"""FR-845 generic skill executor contract."""

import hashlib
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


def test_cron_runtime_is_byte_unchanged():
    for relative, expected in CRON_HASHES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
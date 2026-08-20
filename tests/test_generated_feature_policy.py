"""Generated-feature policy must stay aligned across all pipeline stages."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
POLICY_PATH = "policy/generated-features.md"
PROMPTS = {
    "plan": "prompts/plan.yaml",
    "judge": "prompts/judge.yaml",
    "enforce": "prompts/enforce.yaml",
    "review": "prompts/review.yaml",
}
BANNED_TOOL_EXCLUSIONS = (
    "YAMLGraph-only artifacts",
    "graph.yaml plus prompts/",
    "YAML-only implementation",
    "graph + prompts only",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_policy_defines_read_only_public_tool_boundary():
    policy = " ".join(read(POLICY_PATH).lower().split())
    required = (
        "issue-generated features",
        "pre-shipped fixtures",
        "optional contained artifacts",
        "get",
        "head",
        "public origins explicitly named",
        "finite connect and read timeouts",
        "bounded response",
        "must not read environment variables",
        "post",
        "delete",
        "external writes",
        "not a sandbox",
    )
    assert all(marker in policy for marker in required)


def test_all_stages_reference_shared_policy():
    for prompt in PROMPTS.values():
        assert POLICY_PATH in read(prompt)


def test_stages_state_distinct_policy_responsibilities():
    expected = {
        "plan": ("public origins", "failure semantics", "contained tools"),
        "judge": ("Permit", "read-only public tools", "Reject"),
        "enforce": ("optional contained tools", "frozen"),
        "review": ("every generated feature path", "tools and tests"),
    }
    for stage, markers in expected.items():
        prompt = read(PROMPTS[stage])
        assert all(marker in prompt for marker in markers)


def test_judge_and_enforce_do_not_exclude_tools():
    text = read(PROMPTS["judge"]) + read(PROMPTS["enforce"])
    assert not any(banned in text for banned in BANNED_TOOL_EXCLUSIONS)
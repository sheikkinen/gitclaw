"""FR-847: cron schedules one independently runnable YAMLGraph task."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "cron.yml"
README = ROOT / "README.md"
HAIKU_GRAPH = ROOT / "features" / "haiku" / "graph.yaml"
HAIKU_PROMPT = ROOT / "features" / "haiku" / "prompts" / "haiku.yaml"
RUN_COMMAND = 'yamlgraph graph run "$YAMLGRAPH_TASK" --full'


def _workflow() -> str:
    return WORKFLOW.read_text()


def _step_script(workflow: str, name: str) -> str:
    match = re.search(
        rf"      - name: {re.escape(name)}\n(?:        [^\n]+\n)*?        run: \|\n"
        r"(?P<script>(?:          .*\n)+)",
        workflow,
    )
    assert match, f"workflow step not found: {name}"
    return "\n".join(line[10:] for line in match.group("script").splitlines())


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _validation_result(root: Path, task: str) -> subprocess.CompletedProcess[str]:
    script = _step_script(_workflow(), "Validate task")
    env = {**os.environ, "YAMLGRAPH_TASK": task}
    return subprocess.run(
        ["bash", "-eu", "-o", "pipefail", "-c", script],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )


def test_cron_is_read_only_one_task_invocation() -> None:
    workflow = _workflow()
    assert 'cron: "0 6 * * *"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "YAMLGRAPH_TASK: ${{ vars.YAMLGRAPH_TASK }}" in workflow
    assert workflow.count(RUN_COMMAND) == 1
    assert workflow.index("Validate task") < workflow.index(RUN_COMMAND)
    assert "ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}" in workflow

    forbidden = (
        "contents: write",
        "python -m tools.cron_run",
        "--json",
        "--var date=",
        "--var city=",
        "source_snapshots",
        "git config",
        "git add",
        "git commit",
        "git push",
        "GH_TOKEN",
    )
    for value in forbidden:
        assert value not in workflow


@pytest.mark.parametrize(
    "task",
    ["", "/graph.yaml", "../graph.yaml", "missing.yaml", "graph.yml", "tasks"],
)
def test_task_validation_rejects_invalid_paths(tmp_path: Path, task: str) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "tasks").mkdir()
    assert _validation_result(tmp_path, task).returncode != 0


def test_task_validation_rejects_untracked_and_symlinked_yaml(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "untracked.yaml").write_text("version: '1.0'\n")
    assert _validation_result(tmp_path, "untracked.yaml").returncode != 0

    (tmp_path / "tracked.yaml").write_text("version: '1.0'\n")
    _git(tmp_path, "add", "tracked.yaml")
    (tmp_path / "linked.yaml").symlink_to("tracked.yaml")
    _git(tmp_path, "add", "linked.yaml")
    assert _validation_result(tmp_path, "linked.yaml").returncode != 0


def test_task_validation_accepts_tracked_regular_yaml(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "task.yaml").write_text("version: '1.0'\n")
    _git(tmp_path, "add", "task.yaml")
    assert _validation_result(tmp_path, "task.yaml").returncode == 0


def test_readme_documents_starter_and_exact_command() -> None:
    readme = README.read_text()
    assert "YAMLGRAPH_TASK=features/haiku/graph.yaml" in readme
    assert RUN_COMMAND in readme
    assert "Cron schedules one YAMLGraph task" in readme
    assert "task owns" in readme.lower()


def test_haiku_is_the_only_example_and_owns_date() -> None:
    feature_dirs = sorted(path.name for path in (ROOT / "features").iterdir())
    assert feature_dirs == ["haiku"]

    graph = HAIKU_GRAPH.read_text()
    prompt = HAIKU_PROMPT.read_text()
    assert 'city: "Oulu, Finland"' in graph
    assert "command: date +%Y-%m-%d" in graph
    assert "type: tool" in graph
    assert "type: python" not in graph
    assert 'city: "{state.city}"' in graph
    assert 'date: "{state.date}"' in graph
    assert "{city}" in prompt
    assert "{date}" in prompt
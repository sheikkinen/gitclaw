"""Cron runner: execute every feature graph, commit outputs, continue
past failures (FR-827 R-5 cron machine: running -> succeeded |
failed_recorded, never starve the rest).

CLI: python -m tools.cron_run [date]
Exit 1 if any feature failed (all features still attempted).
"""

import json
import subprocess
import sys
import time
from pathlib import Path


def _coerce(value, key: str) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, dict):
        inner = value.get(key)
        if isinstance(inner, str) and inner.strip():
            return inner
        if len(value) == 1:
            only = next(iter(value.values()))
            if isinstance(only, str) and only.strip():
                return only
    return None


def extract_output(state: dict, feature: str) -> str | None:
    text = _coerce(state.get(feature), feature)
    if text is not None:
        return text
    # generated graphs pick their own state_key; accept a lone
    # self-named candidate, fail closed on zero or many
    candidates = [
        _coerce(v, k)
        for k, v in state.items()
        if isinstance(v, dict) and k in v
    ]
    candidates = [c for c in candidates if c is not None]
    return candidates[0] if len(candidates) == 1 else None


def static_gate(graph: Path) -> str | None:
    """Feature graphs are LLM-only: a `tools:` section means shell or
    python execution with secrets in env, every day — refuse."""
    import yaml

    config = yaml.safe_load(graph.read_text())
    if isinstance(config, dict) and "tools" in config:
        return "feature graph declares tools: — LLM-only graphs permitted in cron"
    return None


def run_feature(graph: Path, date: str) -> tuple[bool, str]:
    """Returns (ok, text): output text on success, reason on failure."""
    refusal = static_gate(graph)
    if refusal is not None:
        return False, refusal
    proc = subprocess.run(
        ["yamlgraph", "graph", "run", str(graph), "--var", f"date={date}", "--json"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        return False, f"exit {proc.returncode}: {proc.stderr[-500:]}"
    try:
        state = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, f"non-JSON stdout: {proc.stdout[-500:]}"
    text = extract_output(state, graph.parent.name)
    if text is None:
        # failed LLM nodes exit 0 with the error only in state
        return False, f"no output in state: {list(state.keys())}"
    return True, text


def main(date: str | None = None) -> int:
    date = date or time.strftime("%Y-%m-%d", time.gmtime())
    Path("outputs").mkdir(exist_ok=True)
    failures = 0
    for graph in sorted(Path("features").glob("*/graph.yaml")):
        name = graph.parent.name
        ok, text = run_feature(graph, date)
        if ok:
            Path(f"outputs/{date}-{name}.md").write_text(text + "\n")
            print(f"succeeded: {name}")
        else:
            record = {"feature": name, "date": date, "reason": text}
            Path(f"outputs/{date}-{name}.failed.json").write_text(json.dumps(record) + "\n")
            print(f"failed_recorded: {name}: {text}", file=sys.stderr)
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))

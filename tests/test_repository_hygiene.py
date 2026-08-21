"""FR-848: the live template excludes superseded repository artifacts."""

from pathlib import Path


ROOT = Path(__file__).parents[1]

OBSOLETE_PATHS = (
    ".github/workflows/spike-copilot-cli.yml",
    "outputs/2026-08-20-daily-aphorism-about-software-craft.md",
    "outputs/2026-08-20-haiku.md",
    "outputs/2026-08-20-horoscope.md",
    "logs/red.log",
    "logs/green.log",
    "docs/authoring-report-2026-08-20-bootstrap.md",
    "docs/authoring-report-2026-08-20-push-race.md",
    "docs/authoring-report-2026-08-20-toolnodes.md",
    "docs/authoring-report-2026-08-20-verdict-gates.md",
    "features/haiku/FR.md",
    "features/haiku/judgement.md",
    "features/haiku/review.md",
)

PROTECTED_PATHS = (
    ".github/workflows/cron.yml",
    ".github/workflows/intake.yml",
    ".github/copilot-instructions.md",
    "README.md",
    "control-bundle.json",
    "control-bundle-trace.md",
    "gitclaw.yaml",
    "features/haiku/graph.yaml",
    "features/haiku/prompts/haiku.yaml",
    "features/haiku/authoring-report.md",
    "tools/__init__.py",
)


def test_obsolete_paths_are_absent() -> None:
    assert len(OBSOLETE_PATHS) == 13
    assert [path for path in OBSOLETE_PATHS if (ROOT / path).exists()] == []


def test_only_current_haiku_artifacts_remain() -> None:
    files = sorted(
        path.relative_to(ROOT / "features" / "haiku").as_posix()
        for path in (ROOT / "features" / "haiku").rglob("*")
        if path.is_file()
    )
    assert files == ["authoring-report.md", "graph.yaml", "prompts/haiku.yaml"]


def test_local_evidence_is_ignored_without_broad_output_ignore() -> None:
    entries = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "tmp/" in entries
    assert "logs/*.log" in entries
    assert "outputs/routes/" in entries
    assert "outputs/" not in entries


def test_protected_runtime_and_control_surfaces_remain() -> None:
    assert [path for path in PROTECTED_PATHS if not (ROOT / path).exists()] == []
    assert (ROOT / ".github" / "skills" / "graph-authoring" / "SKILL.md").is_file()
    assert (ROOT / ".github" / "skills" / "judge-fr" / "SKILL.md").is_file()
    assert (ROOT / ".github" / "skills" / "review-pr" / "SKILL.md").is_file()
    assert (ROOT / ".github" / "hooks" / "scripts" / "pre-command-guard.sh").is_file()


def test_live_consumers_do_not_reference_obsolete_paths() -> None:
    live_roots = (
        ROOT / ".github" / "workflows",
        ROOT / "features" / "haiku",
        ROOT / "scripts",
        ROOT / "tools",
        ROOT / "tests",
    )
    live_files = [ROOT / "README.md", ROOT / "control-bundle.json", ROOT / "control-bundle-trace.md"]
    for live_root in live_roots:
        live_files.extend(path for path in live_root.rglob("*") if path.is_file())

    this_test = Path(__file__).resolve()
    for live_file in live_files:
        if live_file.resolve() == this_test or "__pycache__" in live_file.parts:
            continue
        try:
            text = live_file.read_text()
        except UnicodeDecodeError:
            continue
        for obsolete_path in OBSOLETE_PATHS:
            assert obsolete_path not in text, f"{live_file}: {obsolete_path}"
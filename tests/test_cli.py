"""End-to-end tests for the mise-pr CLI entrypoint."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from mise_pr.cli import should_fail

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(*extra_args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["mise-pr", *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


# ── Test 1: basic markdown report generation ──────────────────────────


def test_analyze_produces_markdown_report(tmp_path: Path) -> None:
    md_path = tmp_path / "report.md"
    result = _run_cli(
        "--base",
        "HEAD~3",
        "--head",
        "HEAD",
        "--output",
        str(md_path),
    )
    assert result.returncode in (0, 1), f"unexpected exit: {result.stderr}"
    assert md_path.exists(), "Markdown report was not created"
    content = md_path.read_text(encoding="utf-8")
    assert "## Mise PR Review Packet" in content


# ── Test 2: --json-output creates a valid JSON file ───────────────────


def test_json_output_flag(tmp_path: Path) -> None:
    md_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    result = _run_cli(
        "--base",
        "HEAD~3",
        "--head",
        "HEAD",
        "--output",
        str(md_path),
        "--json-output",
        str(json_path),
    )
    assert result.returncode in (0, 1), f"unexpected exit: {result.stderr}"
    assert json_path.exists(), "JSON report was not created"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "risk_score" in data
    assert "risk_level" in data
    assert "files" in data


# ── Test 3: --fail-on never always exits 0 ────────────────────────────


def test_fail_on_never_exits_zero(tmp_path: Path) -> None:
    md_path = tmp_path / "report.md"
    result = _run_cli(
        "--base",
        "HEAD~3",
        "--head",
        "HEAD",
        "--output",
        str(md_path),
        "--fail-on",
        "never",
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with --fail-on never, got {result.returncode}: {result.stderr}"
    )


# ── Test 4: --fail-on green exits 1 for any non-trivial diff ──────────


def test_fail_on_green_exits_nonzero(tmp_path: Path) -> None:
    md_path = tmp_path / "report.md"
    result = _run_cli(
        "--base",
        "HEAD~3",
        "--head",
        "HEAD",
        "--output",
        str(md_path),
        "--fail-on",
        "green",
    )
    assert result.returncode == 1, (
        f"Expected exit 1 with --fail-on green for a non-trivial diff, got {result.returncode}"
    )


# ── Test 5: should_fail unit tests with all combos ────────────────────

_LEVELS = ("green", "yellow", "amber", "red")
_THRESHOLDS = ("green", "yellow", "amber", "red", "never")


class TestShouldFail:
    def test_never_always_false(self) -> None:
        for level in _LEVELS:
            assert should_fail(level, "never") is False

    @pytest.mark.parametrize(
        "risk_level,fail_on,expected",
        [
            # green threshold: everything >= green fails
            ("green", "green", True),
            ("yellow", "green", True),
            ("amber", "green", True),
            ("red", "green", True),
            # yellow threshold
            ("green", "yellow", False),
            ("yellow", "yellow", True),
            ("amber", "yellow", True),
            ("red", "yellow", True),
            # amber threshold
            ("green", "amber", False),
            ("yellow", "amber", False),
            ("amber", "amber", True),
            ("red", "amber", True),
            # red threshold
            ("green", "red", False),
            ("yellow", "red", False),
            ("amber", "red", False),
            ("red", "red", True),
        ],
    )
    def test_level_threshold_matrix(self, risk_level: str, fail_on: str, expected: bool) -> None:
        assert should_fail(risk_level, fail_on) is expected


# ── Test 6: --help shows all expected options ──────────────────────────


def test_help_output() -> None:
    result = subprocess.run(
        ["mise-pr", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    out = result.stdout
    expected_flags = (
        "--base",
        "--head",
        "--title",
        "--repository",
        "--author",
        "--output",
        "--json-output",
        "--fail-on",
    )
    for flag in expected_flags:
        assert flag in out, f"Expected {flag} in --help output"


# ── Test 7: report contains expected risk level text ───────────────────


def test_report_contains_risk_level(tmp_path: Path) -> None:
    md_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    result = _run_cli(
        "--base",
        "HEAD~3",
        "--head",
        "HEAD",
        "--output",
        str(md_path),
        "--json-output",
        str(json_path),
        "--fail-on",
        "never",
    )
    assert result.returncode == 0, f"unexpected exit: {result.stderr}"

    md_content = md_path.read_text(encoding="utf-8")
    json_data = json.loads(json_path.read_text(encoding="utf-8"))

    risk_level = json_data["risk_level"]
    assert risk_level in ("green", "yellow", "amber", "red"), f"Unexpected risk level: {risk_level}"
    assert risk_level.upper() in md_content, (
        f"Markdown report should contain risk level '{risk_level.upper()}'"
    )
    assert f"**Risk:** `{risk_level.upper()}`" in md_content

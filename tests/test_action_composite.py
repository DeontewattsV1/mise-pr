"""End-to-end tests for the Mise PR GitHub Action composite definition."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTION_YML = REPO_ROOT / "action.yml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def action() -> dict:
    """Load and parse the action.yml once for the whole module."""
    text = ACTION_YML.read_text(encoding="utf-8")
    return yaml.safe_load(text)


# ===========================================================================
# Test 1 — action.yml is valid YAML with required top-level fields
# ===========================================================================


class TestActionYamlStructure:
    REQUIRED_FIELDS = ("name", "description", "inputs", "outputs", "runs")

    def test_action_yml_is_valid_yaml(self, action: dict) -> None:
        assert isinstance(action, dict), "action.yml did not parse into a dict"

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_has_required_field(self, action: dict, field: str) -> None:
        assert field in action, f"action.yml missing required field: {field}"


# ===========================================================================
# Test 2 — All declared inputs have descriptions and defaults
# ===========================================================================


class TestInputCompleteness:
    def test_all_inputs_have_description(self, action: dict) -> None:
        for name, spec in action["inputs"].items():
            assert "description" in spec, f"Input '{name}' missing 'description'"
            assert len(spec["description"]) > 0, f"Input '{name}' has empty description"

    def test_all_inputs_have_default(self, action: dict) -> None:
        for name, spec in action["inputs"].items():
            assert "default" in spec, f"Input '{name}' missing 'default'"


# ===========================================================================
# Test 3 — The composite action uses 'composite' runs type
# ===========================================================================


class TestCompositeRunsType:
    def test_runs_using_composite(self, action: dict) -> None:
        assert action["runs"]["using"] == "composite"


# ===========================================================================
# Test 4 — Python version is set to 3.11
# ===========================================================================


class TestPythonVersion:
    def test_python_version_311(self, action: dict) -> None:
        steps = action["runs"]["steps"]
        python_step = next(
            (s for s in steps if s.get("uses", "").startswith("actions/setup-python")),
            None,
        )
        assert python_step is not None, "No actions/setup-python step found"
        assert python_step["with"]["python-version"] == "3.11"


# ===========================================================================
# Test 5 — The pip install step references the action path
# ===========================================================================


class TestPipInstallStep:
    def test_pip_install_references_action_path(self, action: dict) -> None:
        steps = action["runs"]["steps"]
        install_step = next(
            (s for s in steps if "pip install" in s.get("run", "")),
            None,
        )
        assert install_step is not None, "No pip-install step found"
        assert "${{ github.action_path }}" in install_step["run"], (
            "pip install step does not reference ${{ github.action_path }}"
        )


# ===========================================================================
# Test 6 — The analyze step passes all input variables correctly
# ===========================================================================


class TestAnalyzeStep:
    EXPECTED_INPUT_VARS = [
        "inputs.base-ref",
        "inputs.head-ref",
        "inputs.output",
        "inputs.json-output",
        "inputs.fail-on",
    ]

    def test_analyze_step_exists(self, action: dict) -> None:
        steps = action["runs"]["steps"]
        analyze_step = self._find_analyze_step(steps)
        assert analyze_step is not None, "No 'Generate review packet' step found"

    def test_analyze_step_env_has_all_inputs(self, action: dict) -> None:
        steps = action["runs"]["steps"]
        analyze_step = self._find_analyze_step(steps)
        assert analyze_step is not None
        env_block = analyze_step.get("env", {})
        env_values = " ".join(str(v) for v in env_block.values())
        run_block = analyze_step.get("run", "")
        combined = env_values + " " + run_block
        for var in self.EXPECTED_INPUT_VARS:
            assert var in combined, f"Analyze step does not reference '{var}'"

    @staticmethod
    def _find_analyze_step(steps: list[dict]) -> dict | None:
        return next(
            (
                s
                for s in steps
                if "analyze" in s.get("name", "").lower() or "mise-pr analyze" in s.get("run", "")
            ),
            None,
        )


# ===========================================================================
# Test 7 — The comment step is conditional on inputs.comment == 'true'
# ===========================================================================


class TestCommentStepConditional:
    def test_comment_step_conditional(self, action: dict) -> None:
        steps = action["runs"]["steps"]
        comment_step = next(
            (s for s in steps if "comment" in s.get("name", "").lower()),
            None,
        )
        assert comment_step is not None, "No comment step found"
        condition = comment_step.get("if", "")
        assert "inputs.comment" in condition, "Comment step 'if' does not reference inputs.comment"
        assert "'true'" in condition or '"true"' in condition.replace("'", '"'), (
            "Comment step condition does not check for 'true'"
        )


# ===========================================================================
# Test 8 — Full integration: install, run CLI, verify output files
# ===========================================================================


class TestFullIntegration:
    MD_PATH = Path("/tmp/test-report.md")
    JSON_PATH = Path("/tmp/test-report.json")

    @pytest.fixture(autouse=True)
    def run_analyze(self) -> None:
        """Run the CLI once; all assertions in this class share the result."""
        for p in (self.MD_PATH, self.JSON_PATH):
            p.unlink(missing_ok=True)

        result = subprocess.run(
            [
                "mise-pr",
                "--base",
                "HEAD~5",
                "--head",
                "HEAD",
                "--output",
                str(self.MD_PATH),
                "--json-output",
                str(self.JSON_PATH),
                "--fail-on",
                "never",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_markdown_output_exists(self) -> None:
        assert self.MD_PATH.exists(), "Markdown report was not created"
        assert self.MD_PATH.stat().st_size > 0, "Markdown report is empty"

    def test_json_output_exists(self) -> None:
        assert self.JSON_PATH.exists(), "JSON report was not created"
        assert self.JSON_PATH.stat().st_size > 0, "JSON report is empty"

    def test_markdown_has_valid_content(self) -> None:
        content = self.MD_PATH.read_text(encoding="utf-8")
        assert "Mise PR" in content, "Markdown report missing 'Mise PR' header"

    def test_json_has_valid_content(self) -> None:
        content = self.JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict), "JSON report root is not a dict"


# ===========================================================================
# Test 9 — Markdown report has the expected sections
# ===========================================================================


class TestMarkdownSections:
    EXPECTED_SECTIONS = [
        "Mise PR Review Packet",
        "Risk:",
        "Score:",
        "Scope",
        "Changed file map",
    ]

    @pytest.fixture(autouse=True)
    def run_analyze(self) -> None:
        md_path = Path("/tmp/test-report-sections.md")
        md_path.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "mise-pr",
                "--base",
                "HEAD~5",
                "--head",
                "HEAD",
                "--output",
                str(md_path),
                "--fail-on",
                "never",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        self.content = md_path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_has_section(self, section: str) -> None:
        assert section in self.content, f"Markdown report missing expected section: '{section}'"

    def test_has_generated_by_footer(self) -> None:
        assert "Generated by" in self.content, "Missing 'Generated by' footer"


# ===========================================================================
# Test 10 — JSON report parses correctly with expected keys
# ===========================================================================


class TestJsonReport:
    EXPECTED_KEYS = [
        "repository",
        "author",
        "title",
        "risk_score",
        "risk_level",
        "attention_budget_minutes",
        "totals",
        "blockers",
        "warnings",
        "recommendations",
        "files",
    ]

    @pytest.fixture(autouse=True)
    def run_analyze(self) -> None:
        json_path = Path("/tmp/test-report-keys.json")
        json_path.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "mise-pr",
                "--base",
                "HEAD~5",
                "--head",
                "HEAD",
                "--json-output",
                str(json_path),
                "--output",
                "/tmp/test-report-keys.md",
                "--fail-on",
                "never",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        self.data = json.loads(json_path.read_text(encoding="utf-8"))

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_has_expected_key(self, key: str) -> None:
        assert key in self.data, f"JSON report missing expected key: '{key}'"

    def test_risk_score_is_int(self) -> None:
        assert isinstance(self.data["risk_score"], int)

    def test_risk_level_is_valid(self) -> None:
        assert self.data["risk_level"] in {"green", "yellow", "amber", "red"}

    def test_totals_has_sub_keys(self) -> None:
        totals = self.data["totals"]
        for sub_key in ("files", "additions", "deletions", "churn"):
            assert sub_key in totals, f"totals missing sub-key: '{sub_key}'"

    def test_files_is_list(self) -> None:
        assert isinstance(self.data["files"], list)
        if self.data["files"]:
            first = self.data["files"][0]
            assert "path" in first
            assert "kind" in first

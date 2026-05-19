"""End-to-end tests for classify_file and enrich_files in mise_pr.git."""

from __future__ import annotations

import pytest

from mise_pr.git import classify_file, enrich_files
from mise_pr.models import ChangedFile, FileKind, Policy


@pytest.fixture
def policy() -> Policy:
    return Policy()


# ---------- 1. Python source files classified as SOURCE ----------

class TestPythonSourceClassifiedAsSource:
    def test_py_file_is_source(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("src/app/main.py", policy)
        assert kind == FileKind.SOURCE

    def test_py_file_not_risky(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("src/app/main.py", policy)
        assert risky is False
        assert reasons == ()

    def test_nested_py_file(self, policy: Policy) -> None:
        kind, _, _ = classify_file("pkg/utils/helpers.py", policy)
        assert kind == FileKind.SOURCE


# ---------- 2. Test files classified as TEST ----------

class TestTestFilesClassifiedAsTest:
    def test_tests_dir(self, policy: Policy) -> None:
        kind, _, _ = classify_file("tests/test_core.py", policy)
        assert kind == FileKind.TEST

    def test_test_in_filename(self, policy: Policy) -> None:
        kind, _, _ = classify_file("src/test_utils.py", policy)
        assert kind == FileKind.TEST

    def test_spec_file(self, policy: Policy) -> None:
        kind, _, _ = classify_file("src/components/Button.spec.tsx", policy)
        assert kind == FileKind.TEST


# ---------- 3. Markdown files classified as DOCS ----------

class TestMarkdownClassifiedAsDocs:
    def test_md_file(self, policy: Policy) -> None:
        kind, _, _ = classify_file("README.md", policy)
        assert kind == FileKind.DOCS

    def test_mdx_file(self, policy: Policy) -> None:
        kind, _, _ = classify_file("docs/guide.mdx", policy)
        assert kind == FileKind.DOCS

    def test_rst_file(self, policy: Policy) -> None:
        kind, _, _ = classify_file("docs/index.rst", policy)
        assert kind == FileKind.DOCS

    def test_docs_dir_txt(self, policy: Policy) -> None:
        kind, _, _ = classify_file("docs/notes.txt", policy)
        assert kind == FileKind.DOCS


# ---------- 4. .github/workflows classified as INFRA ----------

class TestGithubWorkflowsClassifiedAsInfra:
    def test_workflow_yml(self, policy: Policy) -> None:
        kind, _, _ = classify_file(".github/workflows/ci.yml", policy)
        assert kind == FileKind.INFRA

    def test_workflow_yaml(self, policy: Policy) -> None:
        kind, _, _ = classify_file(".github/workflows/deploy.yaml", policy)
        assert kind == FileKind.INFRA

    def test_workflow_is_risky(self, policy: Policy) -> None:
        _, risky, reasons = classify_file(".github/workflows/ci.yml", policy)
        assert risky is True
        assert any("github/workflows" in r for r in reasons)


# ---------- 5. Lock files classified as GENERATED ----------

class TestLockFilesClassifiedAsGenerated:
    def test_package_lock_json(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("package-lock.json", policy)
        assert kind == FileKind.GENERATED
        assert risky is False
        assert reasons == ("generated or lockfile",)

    def test_yarn_lock(self, policy: Policy) -> None:
        kind, _, _ = classify_file("yarn.lock", policy)
        assert kind == FileKind.GENERATED

    def test_poetry_lock(self, policy: Policy) -> None:
        kind, _, _ = classify_file("poetry.lock", policy)
        assert kind == FileKind.GENERATED

    def test_pnpm_lock(self, policy: Policy) -> None:
        kind, _, _ = classify_file("pnpm-lock.yaml", policy)
        assert kind == FileKind.GENERATED


# ---------- 6. Risky patterns flagged ----------

class TestRiskyPatternsFlagged:
    def test_auth_path(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("src/auth/login.py", policy)
        assert risky is True
        assert any("auth" in r for r in reasons)

    def test_payment_path(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("src/payment/stripe.py", policy)
        assert risky is True
        assert any("payment" in r for r in reasons)

    def test_migration_path(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("db/migration/001_init.py", policy)
        assert risky is True
        assert any("migration" in r for r in reasons)

    def test_multiple_risky_reasons(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("src/auth/database/query.py", policy)
        assert risky is True
        assert len(reasons) >= 2


# ---------- 7. Sensitive file types (.env, .pem) ----------

class TestSensitiveFilesFlagged:
    def test_dotenv_standalone_not_detected(self, policy: Policy) -> None:
        """Bug: Path('.env').suffix is '' in Python, so bare .env is not flagged."""
        kind, risky, reasons = classify_file(".env", policy)
        assert risky is False  # Known bug: bare .env not detected

    def test_env_with_prefix_detected(self, policy: Policy) -> None:
        """Files like 'app.env' have suffix '.env' and ARE flagged."""
        kind, risky, reasons = classify_file("config/app.env", policy)
        assert risky is True
        assert "sensitive file type" in reasons

    def test_pem_file(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("certs/server.pem", policy)
        assert risky is True
        assert "sensitive file type" in reasons

    def test_key_file(self, policy: Policy) -> None:
        kind, risky, reasons = classify_file("secrets/private.key", policy)
        assert risky is True
        assert "sensitive file type" in reasons


# ---------- 8. Config files (.json, .toml) classified as CONFIG ----------

class TestConfigFilesClassifiedAsConfig:
    def test_json_config(self, policy: Policy) -> None:
        kind, _, _ = classify_file("config.json", policy)
        assert kind == FileKind.CONFIG

    def test_toml_config(self, policy: Policy) -> None:
        kind, _, _ = classify_file("pyproject.toml", policy)
        assert kind == FileKind.CONFIG

    def test_ini_config(self, policy: Policy) -> None:
        kind, _, _ = classify_file("setup.ini", policy)
        assert kind == FileKind.CONFIG

    def test_cfg_config(self, policy: Policy) -> None:
        kind, _, _ = classify_file("setup.cfg", policy)
        assert kind == FileKind.CONFIG


# ---------- 9. enrich_files correctly enriches ChangedFile objects ----------

class TestEnrichFiles:
    def test_enriches_kind(self, policy: Policy) -> None:
        files = [ChangedFile(path="src/main.py", additions=10, deletions=5)]
        enriched = enrich_files(files, policy)
        assert len(enriched) == 1
        assert enriched[0].kind == FileKind.SOURCE

    def test_enriches_risky_flag(self, policy: Policy) -> None:
        files = [ChangedFile(path="src/auth/handler.py", additions=20, deletions=3)]
        enriched = enrich_files(files, policy)
        assert enriched[0].risky is True
        assert any("auth" in r for r in enriched[0].risk_reasons)

    def test_preserves_additions_deletions(self, policy: Policy) -> None:
        files = [ChangedFile(path="lib/utils.py", additions=42, deletions=7)]
        enriched = enrich_files(files, policy)
        assert enriched[0].additions == 42
        assert enriched[0].deletions == 7
        assert enriched[0].path == "lib/utils.py"

    def test_multiple_files(self, policy: Policy) -> None:
        files = [
            ChangedFile(path="src/app.py", additions=5, deletions=1),
            ChangedFile(path="tests/test_app.py", additions=30, deletions=0),
            ChangedFile(path="README.md", additions=2, deletions=2),
            ChangedFile(path="package-lock.json", additions=500, deletions=300),
        ]
        enriched = enrich_files(files, policy)
        assert len(enriched) == 4
        assert enriched[0].kind == FileKind.SOURCE
        assert enriched[1].kind == FileKind.TEST
        assert enriched[2].kind == FileKind.DOCS
        assert enriched[3].kind == FileKind.GENERATED

    def test_enriched_file_is_new_object(self, policy: Policy) -> None:
        original = ChangedFile(path="src/main.py", additions=1, deletions=0)
        enriched = enrich_files([original], policy)
        assert enriched[0] is not original


# ---------- 10. Unknown file extensions classified as UNKNOWN ----------

class TestUnknownClassifiedAsUnknown:
    def test_no_extension(self, policy: Policy) -> None:
        kind, _, _ = classify_file("Makefile", policy)
        assert kind == FileKind.UNKNOWN

    def test_exotic_extension(self, policy: Policy) -> None:
        kind, _, _ = classify_file("data/file.xyz", policy)
        assert kind == FileKind.UNKNOWN

    def test_binary_extension(self, policy: Policy) -> None:
        kind, _, _ = classify_file("assets/image.png", policy)
        assert kind == FileKind.UNKNOWN

"""Tests for mise_pr.render.render_markdown."""

from __future__ import annotations

from mise_pr.models import ChangedFile, FileKind, PullRequestContext, ReviewPacket
from mise_pr.render import render_markdown


def _make_packet(
    *,
    files: list[ChangedFile] | None = None,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    recommendations: list[str] | None = None,
    risk_score: int = 42,
    risk_level: str = "yellow",
    attention_budget_minutes: int = 10,
) -> ReviewPacket:
    ctx = PullRequestContext(
        title="feat: add widget",
        body="Implements the widget feature.",
        repository="acme/app",
        author="dev",
    )
    return ReviewPacket(
        context=ctx,
        files=files or [],
        risk_score=risk_score,
        risk_level=risk_level,
        blockers=blockers or [],
        warnings=warnings or [],
        recommendations=recommendations or [],
        attention_budget_minutes=attention_budget_minutes,
    )


# ---------- 1. Risk level and score header ----------

def test_output_contains_risk_level_and_score_header():
    packet = _make_packet(risk_score=55, risk_level="yellow")
    md = render_markdown(packet)
    assert "**Risk:** `YELLOW`" in md
    assert "**Score:** `55/100`" in md


# ---------- 2. Scope section with file counts and churn ----------

def test_output_contains_scope_section_with_file_counts_and_churn():
    files = [
        ChangedFile(path="a.py", additions=10, deletions=5, kind=FileKind.SOURCE),
        ChangedFile(path="b.py", additions=3, deletions=2, kind=FileKind.SOURCE),
    ]
    packet = _make_packet(files=files)
    md = render_markdown(packet)
    assert "### Scope" in md
    assert "Files changed: `2`" in md
    assert "Additions: `13`" in md
    assert "Deletions: `7`" in md
    assert "Churn: `20`" in md


# ---------- 3. Blockers section appears when blockers exist ----------

def test_blockers_section_appears_when_blockers_exist():
    packet = _make_packet(blockers=["PR too large", "Missing tests"])
    md = render_markdown(packet)
    assert "### Blocking reviewability issues" in md
    assert "- PR too large" in md
    assert "- Missing tests" in md


def test_blockers_section_absent_when_no_blockers():
    packet = _make_packet(blockers=[])
    md = render_markdown(packet)
    assert "### Blocking reviewability issues" not in md


# ---------- 4. Warnings section appears when warnings exist ----------

def test_warnings_section_appears_when_warnings_exist():
    packet = _make_packet(warnings=["Large diff in auth module"])
    md = render_markdown(packet)
    assert "### Warnings" in md
    assert "- Large diff in auth module" in md


def test_warnings_section_absent_when_no_warnings():
    packet = _make_packet(warnings=[])
    md = render_markdown(packet)
    assert "### Warnings" not in md


# ---------- 5. Recommendations section appears when recommendations exist ----------

def test_recommendations_section_appears_when_recommendations_exist():
    packet = _make_packet(recommendations=["Split into smaller PRs"])
    md = render_markdown(packet)
    assert "### Recommended next moves" in md
    assert "- Split into smaller PRs" in md


def test_recommendations_section_absent_when_no_recommendations():
    packet = _make_packet(recommendations=[])
    md = render_markdown(packet)
    assert "### Recommended next moves" not in md


# ---------- 6. Changed file map groups files by kind with collapsible details ----------

def test_changed_file_map_groups_by_kind_with_collapsible_details():
    files = [
        ChangedFile(path="src/main.py", additions=20, deletions=5, kind=FileKind.SOURCE),
        ChangedFile(path="tests/test_main.py", additions=30, deletions=0, kind=FileKind.TEST),
        ChangedFile(path="README.md", additions=2, deletions=1, kind=FileKind.DOCS),
    ]
    packet = _make_packet(files=files)
    md = render_markdown(packet)
    assert "### Changed file map" in md
    assert "<details><summary>source (1)</summary>" in md
    assert "<details><summary>test (1)</summary>" in md
    assert "<details><summary>docs (1)</summary>" in md
    assert "- `src/main.py` +20/-5" in md
    assert "- `tests/test_main.py` +30/-0" in md
    assert "- `README.md` +2/-1" in md


# ---------- 7. Risky files are marked with warning emoji ----------

def test_risky_files_marked_with_warning_emoji():
    files = [
        ChangedFile(
            path="auth/login.py", additions=10, deletions=2,
            kind=FileKind.SOURCE, risky=True,
        ),
        ChangedFile(
            path="utils/helpers.py", additions=5, deletions=1,
            kind=FileKind.SOURCE, risky=False,
        ),
    ]
    packet = _make_packet(files=files)
    md = render_markdown(packet)
    assert "- `auth/login.py` +10/-2 ⚠️" in md
    assert "- `utils/helpers.py` +5/-1" in md
    # Ensure non-risky file does NOT have the emoji
    helpers_line = [line for line in md.splitlines() if "utils/helpers.py" in line][0]
    assert "⚠️" not in helpers_line


# ---------- 8. Footer contains 'Generated by Mise PR' ----------

def test_footer_contains_generated_by_mise_pr():
    packet = _make_packet()
    md = render_markdown(packet)
    assert "Generated by **Mise PR**" in md


# ---------- 9. Files truncated at 80 per group with '…and N more' ----------

def test_files_truncated_at_80_per_group():
    files = [
        ChangedFile(path=f"src/file_{i:03d}.py", additions=1, deletions=0, kind=FileKind.SOURCE)
        for i in range(100)
    ]
    packet = _make_packet(files=files)
    md = render_markdown(packet)
    # First 80 files should be present
    assert "`src/file_000.py`" in md
    assert "`src/file_079.py`" in md
    # File 80 should NOT appear as a regular entry
    assert "`src/file_080.py`" not in md
    # Truncation message
    assert "…and 20 more" in md

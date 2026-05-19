"""End-to-end tests for mise_pr.analyzer.analyze_pull_request."""

from __future__ import annotations

from mise_pr.analyzer import analyze_pull_request
from mise_pr.models import ChangedFile, FileKind, Policy, PullRequestContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _source_file(path: str = "src/app.py", additions: int = 20, deletions: int = 5) -> ChangedFile:
    return ChangedFile(path=path, additions=additions, deletions=deletions, kind=FileKind.SOURCE)


def _test_file(
    path: str = "tests/test_app.py",
    additions: int = 15,
    deletions: int = 2,
) -> ChangedFile:
    return ChangedFile(path=path, additions=additions, deletions=deletions, kind=FileKind.TEST)


def _risky_file(
    path: str = "src/auth/login.py",
    additions: int = 10,
    deletions: int = 5,
    reasons: tuple[str, ...] = ("auth",),
) -> ChangedFile:
    return ChangedFile(
        path=path,
        additions=additions,
        deletions=deletions,
        kind=FileKind.SOURCE,
        risky=True,
        risk_reasons=reasons,
    )


def _good_context() -> PullRequestContext:
    return PullRequestContext(
        title="Add user validation endpoint",
        body=(
            "## What changed\n"
            "Added POST /api/validate endpoint with request schema validation.\n\n"
            "## Why\n"
            "Fixes #42 — users were able to submit malformed payloads.\n\n"
            "## Testing\n"
            "Unit tests added. Manual QA against staging."
        ),
    )


def _default_policy() -> Policy:
    return Policy()


# ---------------------------------------------------------------------------
# 1. Small clean PR → green
# ---------------------------------------------------------------------------


class TestSmallCleanPR:
    def test_green_score(self) -> None:
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=_default_policy(),
        )
        assert packet.risk_level == "green", (
            f"Expected green, got {packet.risk_level} (score={packet.risk_score})"
        )
        assert packet.risk_score < 20
        assert not packet.blockers
        assert not packet.warnings


# ---------------------------------------------------------------------------
# 2. Exceeding max_files → blocker
# ---------------------------------------------------------------------------


class TestMaxFilesBlocker:
    def test_too_many_files_produces_blocker(self) -> None:
        policy = Policy(max_files=3)
        files = [_source_file(f"src/mod{i}.py", additions=5, deletions=2) for i in range(5)] + [
            _test_file()
        ]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=policy,
        )
        assert len(packet.blockers) >= 1
        assert any("files" in b.lower() for b in packet.blockers)


# ---------------------------------------------------------------------------
# 3. Exceeding max_churn → blocker
# ---------------------------------------------------------------------------


class TestMaxChurnBlocker:
    def test_high_churn_produces_blocker(self) -> None:
        policy = Policy(max_churn=100)
        files = [
            _source_file("src/big.py", additions=200, deletions=50),
            _test_file("tests/test_big.py", additions=50, deletions=10),
        ]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=policy,
        )
        assert len(packet.blockers) >= 1
        assert any("churn" in b.lower() for b in packet.blockers)


# ---------------------------------------------------------------------------
# 4. Source files without test files → warning
# ---------------------------------------------------------------------------


class TestMissingTestWarning:
    def test_source_without_tests_warns(self) -> None:
        files = [_source_file()]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=_default_policy(),
        )
        assert any("test" in w.lower() for w in packet.warnings)


# ---------------------------------------------------------------------------
# 5. Short PR description → warning
# ---------------------------------------------------------------------------


class TestShortDescriptionWarning:
    def test_short_body_warns(self) -> None:
        context = PullRequestContext(
            title="Quick fix",
            body="Fixed a bug. Fixes #10",
        )
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=context,
            policy=_default_policy(),
        )
        assert any("description" in w.lower() for w in packet.warnings)


# ---------------------------------------------------------------------------
# 6. Missing issue link → warning
# ---------------------------------------------------------------------------


class TestMissingIssueLinkWarning:
    def test_no_link_warns(self) -> None:
        context = PullRequestContext(
            title="Refactor logging module",
            body=(
                "Refactored the logging module to use structured output. "
                "This improves observability across all services and makes "
                "debugging production incidents faster and more reliable."
            ),
        )
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=context,
            policy=_default_policy(),
        )
        assert any("issue" in w.lower() or "link" in w.lower() for w in packet.warnings)

    def test_closing_ref_satisfies_link(self) -> None:
        context = PullRequestContext(
            title="Fix login flow",
            body=(
                "Refactored the login handler to validate tokens before session creation. "
                "This prevents expired tokens from creating zombie sessions. "
                "Fixes #99"
            ),
        )
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=context,
            policy=_default_policy(),
        )
        issue_warnings = [w for w in packet.warnings if "issue" in w.lower() or "link" in w.lower()]
        assert not issue_warnings, f"Unexpected issue-link warning: {issue_warnings}"

    def test_url_satisfies_link(self) -> None:
        context = PullRequestContext(
            title="Fix login flow",
            body=(
                "Refactored the login handler to validate tokens before session creation. "
                "See https://example.com/ticket/123 for details and motivation."
            ),
        )
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=context,
            policy=_default_policy(),
        )
        issue_warnings = [w for w in packet.warnings if "issue" in w.lower() or "link" in w.lower()]
        assert not issue_warnings

    def test_ticket_id_satisfies_link(self) -> None:
        context = PullRequestContext(
            title="Fix login flow",
            body=(
                "Refactored the login handler to validate tokens before session creation. "
                "Addresses JIRA-456 from the current sprint backlog and ensures compliance."
            ),
        )
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=context,
            policy=_default_policy(),
        )
        issue_warnings = [w for w in packet.warnings if "issue" in w.lower() or "link" in w.lower()]
        assert not issue_warnings


# ---------------------------------------------------------------------------
# 7. Risky files → recommendations
# ---------------------------------------------------------------------------


class TestRiskyFileRecommendations:
    def test_risky_files_generate_recommendation(self) -> None:
        files = [
            _risky_file("src/auth/handler.py", reasons=("auth",)),
            _risky_file("src/payments/charge.py", reasons=("payment",)),
            _test_file(),
        ]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=_default_policy(),
        )
        risky_recs = [
            r for r in packet.recommendations if "risky" in r.lower() or "human review" in r.lower()
        ]
        assert risky_recs


# ---------------------------------------------------------------------------
# 8. Score clamping between 0 and 100
# ---------------------------------------------------------------------------


class TestScoreClamping:
    def test_score_does_not_exceed_100(self) -> None:
        policy = Policy(max_files=1, max_churn=10)
        files = [_source_file(f"src/mod{i}.py", additions=300, deletions=200) for i in range(30)]
        packet = analyze_pull_request(
            files=files,
            context=PullRequestContext(title="x", body=""),
            policy=policy,
        )
        assert packet.risk_score <= 100

    def test_score_does_not_go_below_0(self) -> None:
        files = [_test_file("tests/test_only.py", additions=1, deletions=0)]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=_default_policy(),
        )
        assert packet.risk_score >= 0


# ---------------------------------------------------------------------------
# 9. Clean PR with no issues → 'review-ready' recommendation
# ---------------------------------------------------------------------------


class TestReviewReadyRecommendation:
    def test_clean_pr_gets_review_ready(self) -> None:
        files = [_source_file(), _test_file()]
        packet = analyze_pull_request(
            files=files,
            context=_good_context(),
            policy=_default_policy(),
        )
        assert any("review-ready" in r.lower() for r in packet.recommendations)

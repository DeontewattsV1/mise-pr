"""End-to-end tests for risk scoring and attention budget calculations."""

from __future__ import annotations

import pytest

from mise_pr.analyzer import _attention_budget, _risk_level, analyze_pull_request
from mise_pr.models import ChangedFile, FileKind, Policy, PullRequestContext

# ---------------------------------------------------------------------------
# 1-4: _risk_level boundary tests
# ---------------------------------------------------------------------------

class TestRiskLevel:
    @pytest.mark.parametrize("score", [0, 1, 10, 19])
    def test_green_for_score_0_to_19(self, score: int) -> None:
        assert _risk_level(score) == "green"

    @pytest.mark.parametrize("score", [20, 30, 44])
    def test_yellow_for_score_20_to_44(self, score: int) -> None:
        assert _risk_level(score) == "yellow"

    @pytest.mark.parametrize("score", [45, 60, 74])
    def test_amber_for_score_45_to_74(self, score: int) -> None:
        assert _risk_level(score) == "amber"

    @pytest.mark.parametrize("score", [75, 90, 100])
    def test_red_for_score_75_to_100(self, score: int) -> None:
        assert _risk_level(score) == "red"

    def test_exact_boundary_19_is_green(self) -> None:
        assert _risk_level(19) == "green"

    def test_exact_boundary_20_is_yellow(self) -> None:
        assert _risk_level(20) == "yellow"

    def test_exact_boundary_44_is_yellow(self) -> None:
        assert _risk_level(44) == "yellow"

    def test_exact_boundary_45_is_amber(self) -> None:
        assert _risk_level(45) == "amber"

    def test_exact_boundary_74_is_amber(self) -> None:
        assert _risk_level(74) == "amber"

    def test_exact_boundary_75_is_red(self) -> None:
        assert _risk_level(75) == "red"


# ---------------------------------------------------------------------------
# 5-9: _attention_budget tests
# ---------------------------------------------------------------------------

class TestAttentionBudget:
    def test_minimum_is_5_minutes(self) -> None:
        result = _attention_budget(files_count=0, churn=0, score=0)
        assert result >= 5

    def test_maximum_is_120_minutes(self) -> None:
        result = _attention_budget(files_count=500, churn=100_000, score=100)
        assert result <= 120
        assert result == 120

    def test_high_risk_adds_25_minutes(self) -> None:
        base_low = _attention_budget(files_count=5, churn=100, score=10)
        base_high = _attention_budget(files_count=5, churn=100, score=75)
        assert base_high - base_low == 25

    def test_amber_risk_adds_15_minutes(self) -> None:
        base_low = _attention_budget(files_count=5, churn=100, score=10)
        base_amber = _attention_budget(files_count=5, churn=100, score=45)
        assert base_amber - base_low == 15

    def test_yellow_risk_adds_5_minutes(self) -> None:
        base_low = _attention_budget(files_count=5, churn=100, score=10)
        base_yellow = _attention_budget(files_count=5, churn=100, score=20)
        assert base_yellow - base_low == 5

    def test_green_adds_no_bonus(self) -> None:
        result = _attention_budget(files_count=0, churn=0, score=0)
        # base = 5 + 0*2 + ceil(0/120)*5 = 5, no bonus for green
        assert result == 5

    def test_clamp_to_5_even_with_zero_inputs(self) -> None:
        assert _attention_budget(files_count=0, churn=0, score=0) == 5

    def test_clamp_to_120_with_huge_inputs(self) -> None:
        assert _attention_budget(files_count=1000, churn=1_000_000, score=100) == 120


# ---------------------------------------------------------------------------
# 10: Score component contributions via analyze_pull_request
# ---------------------------------------------------------------------------

def _make_file(
    path: str = "src/app.py",
    additions: int = 10,
    deletions: int = 5,
    kind: FileKind = FileKind.SOURCE,
    risky: bool = False,
    risk_reasons: tuple[str, ...] = (),
) -> ChangedFile:
    return ChangedFile(
        path=path,
        additions=additions,
        deletions=deletions,
        kind=kind,
        risky=risky,
        risk_reasons=risk_reasons,
    )


def _minimal_context() -> PullRequestContext:
    return PullRequestContext(
        title="fix: handle edge case",
        body="Fixes #123. " + "x" * 80,
        base_ref="origin/main",
        head_ref="HEAD",
    )


def _permissive_policy() -> Policy:
    return Policy(
        max_files=999,
        max_churn=999_999,
        max_single_file_churn=999_999,
        require_issue_link=False,
        require_tests_for_source=False,
        require_description=False,
    )


class TestScoreComponents:
    def test_file_count_contributes_up_to_25(self) -> None:
        """file_count component: min(25, max(0, N-4) * 3)
        With 4 files => max(0, 4-4)*3 = 0
        With 13 files => max(0, 13-4)*3 = 27 → capped at 25
        """
        ctx = _minimal_context()
        policy = _permissive_policy()

        # 4 non-generated files: component = 0
        files_4 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(4)]
        pkt_4 = analyze_pull_request(files=files_4, context=ctx, policy=policy)

        # 13 non-generated files: component = min(25, 9*3) = 25
        files_13 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(13)]
        pkt_13 = analyze_pull_request(files=files_13, context=ctx, policy=policy)

        assert pkt_13.risk_score - pkt_4.risk_score == 25

    def test_file_count_cap_at_25(self) -> None:
        ctx = _minimal_context()
        policy = _permissive_policy()

        # 50 files → max(0, 50-4)*3 = 138, capped at 25
        files_50 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(50)]
        pkt = analyze_pull_request(files=files_50, context=ctx, policy=policy)

        # 100 files → still capped at 25
        files_100 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(100)]
        pkt2 = analyze_pull_request(files=files_100, context=ctx, policy=policy)

        assert pkt.risk_score == pkt2.risk_score

    def test_churn_contributes_up_to_25(self) -> None:
        """churn component: min(25, total_churn // 35)
        churn=875 → 875//35 = 25 (exact cap)
        churn=0 → 0
        """
        ctx = _minimal_context()
        policy = _permissive_policy()

        # 4 files with 0 churn (stay at file threshold)
        files_zero = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(4)]
        pkt_zero = analyze_pull_request(files=files_zero, context=ctx, policy=policy)

        # 4 files with total churn = 875 (875//35 = 25)
        files_churn = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(3)]
        files_churn.append(_make_file(path="src/big.py", additions=500, deletions=375))
        pkt_churn = analyze_pull_request(files=files_churn, context=ctx, policy=policy)

        assert pkt_churn.risk_score - pkt_zero.risk_score == 25

    def test_churn_cap_at_25(self) -> None:
        ctx = _minimal_context()
        policy = _permissive_policy()

        files_a = [_make_file(path="src/a.py", additions=500, deletions=375)]
        files_a += [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(3)]

        files_b = [_make_file(path="src/a.py", additions=5000, deletions=5000)]
        files_b += [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(3)]

        pkt_a = analyze_pull_request(files=files_a, context=ctx, policy=policy)
        pkt_b = analyze_pull_request(files=files_b, context=ctx, policy=policy)

        assert pkt_a.risk_score == pkt_b.risk_score

    def test_risky_files_contribute_up_to_18(self) -> None:
        """risky component: min(18, len(risky) * 6)
        3 risky files → 3*6 = 18 (exact cap)
        """
        ctx = _minimal_context()
        policy = _permissive_policy()

        files_no_risk = [
            _make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(4)
        ]
        pkt_no_risk = analyze_pull_request(files=files_no_risk, context=ctx, policy=policy)

        files_risky = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(1)]
        files_risky += [
            _make_file(
                path=f"src/auth{i}.py", additions=0, deletions=0,
                risky=True, risk_reasons=("auth",),
            )
            for i in range(3)
        ]
        pkt_risky = analyze_pull_request(files=files_risky, context=ctx, policy=policy)

        assert pkt_risky.risk_score - pkt_no_risk.risk_score == 18

    def test_risky_files_cap_at_18(self) -> None:
        ctx = _minimal_context()
        policy = _permissive_policy()

        # Both lists have 11 total non-generated files so the file_count
        # component is identical and only the risky component varies.
        files_3 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(8)]
        files_3 += [
            _make_file(
                path=f"src/auth{i}.py", additions=0, deletions=0,
                risky=True, risk_reasons=("auth",),
            )
            for i in range(3)
        ]

        files_10 = [_make_file(path=f"src/f{i}.py", additions=0, deletions=0) for i in range(1)]
        files_10 += [
            _make_file(
                path=f"src/auth{i}.py", additions=0, deletions=0,
                risky=True, risk_reasons=("auth",),
            )
            for i in range(10)
        ]

        pkt_3 = analyze_pull_request(files=files_3, context=ctx, policy=policy)
        pkt_10 = analyze_pull_request(files=files_10, context=ctx, policy=policy)

        assert pkt_3.risk_score == pkt_10.risk_score


class TestAnalyzePullRequestIntegration:
    def test_clean_pr_is_green(self) -> None:
        ctx = _minimal_context()
        policy = _permissive_policy()
        files = [
            _make_file(path="src/app.py", additions=5, deletions=2, kind=FileKind.SOURCE),
            _make_file(path="tests/test_app.py", additions=10, deletions=0, kind=FileKind.TEST),
        ]
        pkt = analyze_pull_request(files=files, context=ctx, policy=policy)
        assert pkt.risk_level == "green"
        assert pkt.risk_score < 20

    def test_large_risky_pr_scores_high(self) -> None:
        ctx = PullRequestContext(title="big change", body="x" * 100)
        policy = Policy(
            max_files=5,
            max_churn=100,
            max_single_file_churn=50,
            require_issue_link=True,
            require_tests_for_source=True,
            require_description=True,
        )
        files = [
            _make_file(
                path=f"src/auth{i}.py", additions=100, deletions=80,
                risky=True, risk_reasons=("auth",),
            )
            for i in range(10)
        ]
        pkt = analyze_pull_request(files=files, context=ctx, policy=policy)
        assert pkt.risk_level == "red"
        assert pkt.risk_score >= 75

    def test_score_is_clamped_0_to_100(self) -> None:
        ctx = PullRequestContext(title="huge", body="")
        policy = Policy(
            max_files=1,
            max_churn=1,
            max_single_file_churn=1,
            require_issue_link=True,
            require_tests_for_source=True,
            require_description=True,
        )
        files = [
            _make_file(
                path=f"src/auth{i}.py", additions=5000, deletions=5000,
                risky=True, risk_reasons=("auth",),
            )
            for i in range(50)
        ]
        pkt = analyze_pull_request(files=files, context=ctx, policy=policy)
        assert 0 <= pkt.risk_score <= 100

    def test_attention_budget_in_packet_matches_standalone(self) -> None:
        ctx = _minimal_context()
        policy = _permissive_policy()
        files = [
            _make_file(path=f"src/f{i}.py", additions=50, deletions=30) for i in range(8)
        ]
        files.append(_make_file(
            path="generated/schema.py", additions=200,
            deletions=0, kind=FileKind.GENERATED,
        ))
        pkt = analyze_pull_request(files=files, context=ctx, policy=policy)
        non_generated = [f for f in files if f.kind != FileKind.GENERATED]
        expected = _attention_budget(
            files_count=len(non_generated),
            churn=sum(f.churn for f in files),
            score=pkt.risk_score,
        )
        assert pkt.attention_budget_minutes == expected

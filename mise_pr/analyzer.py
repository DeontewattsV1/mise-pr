from __future__ import annotations

import math
import re

from .models import FileKind, Policy, PullRequestContext, ReviewPacket

_CLOSING_REF_RE = re.compile(r"(?i)(?:fixe?s|close?s|resolve?s)\s+#\d+")
_TICKET_ID_RE = re.compile(r"[A-Z]{2,}-\d+")
_URL_RE = re.compile(r"https?://")


def analyze_pull_request(*, files: list, context: PullRequestContext, policy: Policy) -> ReviewPacket:
    blockers: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    total_churn = sum(file.churn for file in files)
    source_files = [file for file in files if file.kind == FileKind.SOURCE]
    test_files = [file for file in files if file.kind == FileKind.TEST]
    risky_files = [file for file in files if file.risky]
    non_generated_files = [file for file in files if file.kind != FileKind.GENERATED]

    score = 0
    score += min(25, max(0, len(non_generated_files) - 4) * 3)
    score += min(25, total_churn // 35)
    score += min(18, len(risky_files) * 6)

    if len(non_generated_files) > policy.max_files:
        blockers.append(f"PR changes {len(non_generated_files)} reviewable files; policy target is <= {policy.max_files}.")
        score += 16

    if total_churn > policy.max_churn:
        blockers.append(f"PR churn is {total_churn} lines; policy target is <= {policy.max_churn}.")
        score += 16

    large_files = [file for file in files if file.churn > policy.max_single_file_churn]
    if large_files:
        warnings.append("Large single-file changes: " + ", ".join(f"{file.path} ({file.churn})" for file in large_files[:5]))
        score += min(12, len(large_files) * 4)

    if policy.require_tests_for_source and source_files and not test_files:
        warnings.append("Source changed without test files in the same PR.")
        recommendations.append("Add tests, link existing coverage, or explain why tests are not required.")
        score += 14

    description_text = f"{context.title}\n{context.body}".strip()
    if policy.require_description and len(context.body.strip()) < 80:
        warnings.append("PR description is short; reviewers may lack intent, risk, and validation context.")
        recommendations.append("Add: what changed, why it changed, how it was tested, and rollback notes.")
        score += 8

    if policy.require_issue_link and not _has_issue_link(description_text):
        warnings.append("No linked issue, ticket, URL, or closing reference found.")
        recommendations.append("Link the issue/spec so reviewers can inspect original intent.")
        score += 7

    if risky_files:
        recommendations.append("Require explicit human review for risky paths: " + ", ".join(sorted({reason for file in risky_files for reason in file.risk_reasons})[:6]))

    if not blockers and not warnings:
        recommendations.append("PR appears review-ready. Keep the description, tests, and scope intact.")

    score = max(0, min(100, score))
    risk_level = _risk_level(score)
    attention_budget_minutes = _attention_budget(files_count=len(non_generated_files), churn=total_churn, score=score)

    return ReviewPacket(context=context, files=files, risk_score=score, risk_level=risk_level, blockers=blockers, warnings=warnings, recommendations=recommendations, attention_budget_minutes=attention_budget_minutes)


def _has_issue_link(text: str) -> bool:
    return bool(_CLOSING_REF_RE.search(text) or _TICKET_ID_RE.search(text) or _URL_RE.search(text))


def _risk_level(score: int) -> str:
    if score >= 75:
        return "red"
    if score >= 45:
        return "amber"
    if score >= 20:
        return "yellow"
    return "green"


def _attention_budget(*, files_count: int, churn: int, score: int) -> int:
    base = 5 + files_count * 2 + math.ceil(churn / 120) * 5
    if score >= 75:
        base += 25
    elif score >= 45:
        base += 15
    elif score >= 20:
        base += 5
    return min(120, max(5, base))

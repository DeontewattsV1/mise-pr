from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileKind(str, Enum):
    SOURCE = "source"
    TEST = "test"
    DOCS = "docs"
    CONFIG = "config"
    INFRA = "infra"
    DATA = "data"
    GENERATED = "generated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChangedFile:
    path: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"
    kind: FileKind = FileKind.UNKNOWN
    risky: bool = False
    risk_reasons: tuple[str, ...] = ()

    @property
    def churn(self) -> int:
        return self.additions + self.deletions

    @property
    def suffix(self) -> str:
        return Path(self.path).suffix.lower()


@dataclass(frozen=True)
class Policy:
    max_files: int = 12
    max_churn: int = 450
    max_single_file_churn: int = 180
    require_issue_link: bool = True
    require_tests_for_source: bool = True
    require_description: bool = True
    risky_path_patterns: tuple[str, ...] = (
        "auth", "security", "payment", "billing", "permission", "migration", "infra",
        "terraform", "k8s", "docker", "github/workflows", "secrets", "crypto", "sql", "database",
    )
    generated_path_patterns: tuple[str, ...] = (
        "dist/", "build/", "coverage/", "node_modules/", "vendor/", ".next/",
        "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
    )


@dataclass(frozen=True)
class PullRequestContext:
    title: str = ""
    body: str = ""
    base_ref: str = "origin/main"
    head_ref: str = "HEAD"
    repository: str = "local"
    author: str = "unknown"


@dataclass
class ReviewPacket:
    context: PullRequestContext
    files: list[ChangedFile]
    risk_score: int
    risk_level: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    attention_budget_minutes: int = 5

    @property
    def total_additions(self) -> int:
        return sum(f.additions for f in self.files)

    @property
    def total_deletions(self) -> int:
        return sum(f.deletions for f in self.files)

    @property
    def total_churn(self) -> int:
        return self.total_additions + self.total_deletions

    @property
    def source_files(self) -> list[ChangedFile]:
        return [f for f in self.files if f.kind == FileKind.SOURCE]

    @property
    def test_files(self) -> list[ChangedFile]:
        return [f for f in self.files if f.kind == FileKind.TEST]

    @property
    def risky_files(self) -> list[ChangedFile]:
        return [f for f in self.files if f.risky]

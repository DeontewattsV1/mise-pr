from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import ChangedFile, FileKind, Policy

_NUMSTAT_RE = re.compile(r"^(?P<additions>\d+|-)\s+(?P<deletions>\d+|-)\s+(?P<path>.+)$")


def run_git(args: list[str], cwd: str | Path = '.') -> str:
    result = subprocess.run(['git', *args], cwd=cwd, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def collect_changed_files(base_ref: str, head_ref: str = 'HEAD', cwd: str | Path = '.') -> list[ChangedFile]:
    output = run_git(['diff', '--numstat', f'{base_ref}...{head_ref}'], cwd=cwd)
    files: list[ChangedFile] = []
    for line in output.splitlines():
        match = _NUMSTAT_RE.match(line.strip())
        if not match:
            continue
        files.append(ChangedFile(path=match.group('path'), additions=_parse_int(match.group('additions')), deletions=_parse_int(match.group('deletions'))))
    return files


def classify_file(path: str, policy: Policy) -> tuple[FileKind, bool, tuple[str, ...]]:
    normalized = path.lower().replace('\\', '/')
    suffix = Path(normalized).suffix
    reasons: list[str] = []
    if any(pattern in normalized for pattern in policy.generated_path_patterns):
        return FileKind.GENERATED, False, ('generated or lockfile',)
    if normalized.startswith(('docs/', 'doc/')) or suffix in {'.md', '.mdx', '.rst', '.txt'}:
        kind = FileKind.DOCS
    elif 'test' in normalized or 'spec' in normalized or normalized.startswith('__tests__/'):
        kind = FileKind.TEST
    elif normalized.startswith(('.github/', 'infra/', 'ops/', 'k8s/')) or suffix in {'.tf', '.yaml', '.yml', '.dockerfile'}:
        kind = FileKind.INFRA if any(x in normalized for x in ('terraform', 'k8s', 'docker', '.github/workflows')) else FileKind.CONFIG
    elif suffix in {'.json', '.toml', '.ini', '.cfg', '.env', '.lock'}:
        kind = FileKind.CONFIG
    elif suffix in {'.csv', '.parquet', '.sqlite', '.db'}:
        kind = FileKind.DATA
    elif suffix in {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java', '.kt', '.swift', '.rb', '.php', '.cs', '.c', '.cpp', '.h'}:
        kind = FileKind.SOURCE
    else:
        kind = FileKind.UNKNOWN
    for pattern in policy.risky_path_patterns:
        if pattern.lower() in normalized:
            reasons.append(f'touches {pattern}')
    if suffix in {'.env', '.pem', '.key'}:
        reasons.append('sensitive file type')
    return kind, bool(reasons), tuple(reasons)


def enrich_files(files: list[ChangedFile], policy: Policy) -> list[ChangedFile]:
    enriched: list[ChangedFile] = []
    for file in files:
        kind, risky, reasons = classify_file(file.path, policy)
        enriched.append(ChangedFile(path=file.path, additions=file.additions, deletions=file.deletions, status=file.status, kind=kind, risky=risky, risk_reasons=reasons))
    return enriched


def _parse_int(value: str) -> int:
    return 0 if value == '-' else int(value)

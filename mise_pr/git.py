from __future__ import annotations

import subprocess
from pathlib import Path

from .models import ChangedFile, FileKind, Policy


def run_git(args: list[str], cwd: str | Path = '.') -> str:
    result = subprocess.run(['git', *args], cwd=cwd, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def collect_changed_files(base_ref: str, head_ref: str = 'HEAD', cwd: str | Path = '.') -> list[ChangedFile]:
    output = run_git(['diff', '--numstat', f'{base_ref}...{head_ref}'], cwd=cwd)
    files: list[ChangedFile] = []
    for line in output.splitlines():
        parsed = _parse_numstat_line(line)
        if parsed is None:
            continue
        additions_str, deletions_str, path = parsed
        files.append(ChangedFile(path=path, additions=_parse_int(additions_str), deletions=_parse_int(deletions_str)))
    return files


def _classify_kind(normalized: str, suffix: str, policy: Policy) -> FileKind:
    if any(pattern in normalized for pattern in policy.generated_path_patterns):
        return FileKind.GENERATED
    if normalized.startswith(('docs/', 'doc/')) or suffix in {'.md', '.mdx', '.rst', '.txt'}:
        return FileKind.DOCS
    if 'test' in normalized or 'spec' in normalized or normalized.startswith('__tests__/'):
        return FileKind.TEST
    if normalized.startswith(('.github/', 'infra/', 'ops/', 'k8s/')) or suffix in {'.tf', '.yaml', '.yml', '.dockerfile'}:
        if any(x in normalized for x in ('terraform', 'k8s', 'docker', '.github/workflows')):
            return FileKind.INFRA
        return FileKind.CONFIG
    if suffix in {'.json', '.toml', '.ini', '.cfg', '.env', '.lock'}:
        return FileKind.CONFIG
    if suffix in {'.csv', '.parquet', '.sqlite', '.db'}:
        return FileKind.DATA
    if suffix in {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java', '.kt', '.swift', '.rb', '.php', '.cs', '.c', '.cpp', '.h'}:
        return FileKind.SOURCE
    return FileKind.UNKNOWN


def classify_file(path: str, policy: Policy) -> tuple[FileKind, bool, tuple[str, ...]]:
    normalized = path.lower().replace('\\', '/')
    suffix = Path(normalized).suffix
    kind = _classify_kind(normalized, suffix, policy)
    if kind == FileKind.GENERATED:
        return FileKind.GENERATED, False, ('generated or lockfile',)
    reasons: list[str] = []
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


def _parse_numstat_line(line: str) -> tuple[str, str, str] | None:
    parts = line.strip().split('\t', 2)
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def _parse_int(value: str) -> int:
    return 0 if value == '-' else int(value)

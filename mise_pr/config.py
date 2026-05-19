from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Policy


def load_policy(path: str | Path | None = None) -> Policy:
    candidate = Path('.mise-pr.yml') if path is None else Path(path)
    if not candidate.exists():
        return Policy()
    data = yaml.safe_load(candidate.read_text(encoding='utf-8')) or {}
    if not isinstance(data, dict):
        raise ValueError(f'Policy file must contain a mapping: {candidate}')
    allowed = set(Policy.__dataclass_fields__.keys())
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        raise ValueError(f"Unknown policy keys in {candidate}: {', '.join(unknown)}")
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if key.endswith('patterns') and isinstance(value, list):
            normalized[key] = tuple(str(v) for v in value)
        else:
            normalized[key] = value
    return Policy(**normalized)

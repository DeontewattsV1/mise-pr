from __future__ import annotations

import json
import os
from pathlib import Path


def write_pr_body_from_event(output_path: str = '.mise-pr-body.md') -> Path:
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    output = Path(output_path)
    if not event_path or not Path(event_path).exists():
        output.write_text('', encoding='utf-8')
        return output
    data = json.loads(Path(event_path).read_text(encoding='utf-8'))
    body = (data.get('pull_request') or {}).get('body') or ''
    output.write_text(body, encoding='utf-8')
    return output


if __name__ == '__main__':
    write_pr_body_from_event()

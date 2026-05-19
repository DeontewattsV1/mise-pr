from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .analyzer import analyze_pull_request
from .config import load_policy
from .git import collect_changed_files, enrich_files
from .models import PullRequestContext
from .render import render_json, render_markdown

app = typer.Typer(add_completion=False, help="Turn chaotic pull requests into review-ready packets.")
console = Console()


@app.command()
def analyze(
    base: str = typer.Option("origin/main", help="Base git ref for comparison."),
    head: str = typer.Option("HEAD", help="Head git ref for comparison."),
    title: str = typer.Option("", help="Pull request title."),
    repository: str = typer.Option("local", help="Repository name."),
    author: str = typer.Option("unknown", help="PR author."),
    output: Path = typer.Option(Path("mise-pr-report.md"), help="Markdown report output path."),
    json_output: Path | None = typer.Option(None, help="Optional JSON output path."),
    fail_on: str = typer.Option("red", help="green, yellow, amber, red, never"),
) -> None:
    policy = load_policy(None)
    context = PullRequestContext(title=title, body="", base_ref=base, head_ref=head, repository=repository, author=author)
    files = enrich_files(collect_changed_files(base, head), policy)
    packet = analyze_pull_request(files=files, context=context, policy=policy)
    output.write_text(render_markdown(packet), encoding="utf-8")
    if json_output is not None:
        json_output.write_text(render_json(packet), encoding="utf-8")
    console.print(f"Mise PR: {packet.risk_level.upper()} risk, score {packet.risk_score}/100")
    if should_fail(packet.risk_level, fail_on):
        raise typer.Exit(code=1)


def should_fail(risk_level: str, fail_on: str) -> bool:
    if fail_on == "never":
        return False
    order = {"green": 0, "yellow": 1, "amber": 2, "red": 3}
    return order[risk_level] >= order.get(fail_on, 3)


if __name__ == "__main__":
    app()

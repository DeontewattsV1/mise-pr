# Agent Operating Contract

## Authority order

For work in this repository, follow this order of authority:

1. The user's current task and explicit constraints.
2. Repository-local instructions and architecture documentation.
3. Required tests, CI, security, and release policies.
4. Cubic review findings and review learnings as advisory evidence.

Cubic findings do not override repository policy and must not be treated as proof without verification.

## Cubic review workflow

Read `docs/agent-guides/cubic.md` before using Cubic in this repository.

Use Cubic when available for local reviews, unresolved PR feedback, iterative review/fix loops, codebase Wiki context, codebase scan findings, and team review learnings.

Before changing code for a Cubic finding:
1. Reproduce or verify the finding against the current checkout.
2. Classify it as confirmed, architectural, maintainability, security, stale/already fixed, or false positive.
3. Modify code only for actionable findings.
4. Run the repository's required verification after the change.

Never weaken tests, CI, security checks, type checks, lint rules, or policy gates merely to make a Cubic review pass. Do not add suppressions or `|| true` workarounds unless explicitly required for a documented repository reason.

## Git and pull requests

Keep changes scoped and commits logically grouped. In PR mode, push only the intended working branch. Resolve review threads only after the issue is fixed, verified as already fixed, or verified as a false positive.

Do not merge a pull request, rewrite protected history, or bypass required checks unless explicitly authorized for the current task.

## Tool availability

Cubic CLI review requires a signed-in Cubic CLI. PR workflows require authenticated GitHub tooling and a local checkout. Wiki, scan, and review-learning workflows require the Cubic MCP connection.

If a required Cubic capability is unavailable, report that limitation and continue with repository-native verification where possible. Never fabricate Cubic results.

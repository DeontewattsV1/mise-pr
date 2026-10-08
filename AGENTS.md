# Agent Operating Contract

## Authority order

For work in this repository, follow this order of authority:

1. The user's current task and explicit constraints.
2. Repository-local instructions and architecture documentation.
3. Required tests, CI, security, and release policies.


## Review verification

Verify findings against current evidence before changing code. Never weaken tests, security controls, lint, type checks, or required review gates. Resolve review threads only when their findings are fixed, already fixed, or verified false positive.

## Git and pull requests

Keep changes scoped and commits logically grouped. In PR mode, push only the intended working branch. Resolve review threads only after the issue is fixed, verified as already fixed, or verified as a false positive.

Do not merge a pull request, rewrite protected history, or bypass required checks unless explicitly authorized for the current task.

## Tool availability

PR workflows require authenticated GitHub tooling and a local checkout. Report unavailable verification capabilities; never fabricate results.

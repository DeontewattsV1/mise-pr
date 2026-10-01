# Cubic Agent Review Guide

This repository treats Cubic as a review-intelligence layer beneath repository policy, tests, CI, and human approval.

## Prerequisites

Use the capabilities appropriate to the workflow:

- Local review: install/sign in to the Cubic CLI.
- Pull-request comments and review loops: install/sign in to GitHub CLI and work from a local checkout.
- Wiki, codebase scans, and review learnings: connect Cubic's MCP server with OAuth for an account that can access this repository.
- Agent skills: install Cubic's skills for the coding agent, for example:
  `npx @cubic-plugin/cubic-plugin install --to codex --skills-only`

The skills-only installer intentionally leaves MCP configuration unchanged.

## Preferred workflows

### Local review

Ask the coding agent:

`Use cubic's run-review skill to review my changes.`

If the working tree is clean, review the current branch against its base.

### Pull-request findings

Ask:

`Use cubic's check-pr-comments skill to inspect unresolved review feedback. Verify every finding before changing code, fix actionable issues, run repository verification, commit and push the current PR branch, and resolve only handled threads. Do not merge.`

For read-only inspection:

`Use cubic's get_pr_issues MCP tool to summarize open findings. Do not change anything.`

### Review loop

Ask:

`Use cubic's cubic-loop skill. Verify each finding, fix actionable P0-P2 issues, run repository-native verification after each batch, commit fixes between iterations, and stop when no actionable P0-P2 findings remain or after five iterations. Do not weaken gates or merge the PR.`

The default loop ceiling is five iterations. P3-only findings may remain when the loop stops.

### Architecture and historical context

Use `codebase-context` for Cubic Wiki context and `review-patterns` for team review learnings. Treat both as context, not authority over current source, tests, or policy.

### Codebase scans

Use `handle-codebase-scan` to inspect or remediate scan findings. Re-check every reported issue against the current checkout before editing. Listing findings is read-only; commits, pushes, PR creation, and scan triage require explicit task scope.

## Evidence discipline

A review finding is a hypothesis until verified against current evidence.

For each finding, preserve:
- source or review thread;
- affected file/line when available;
- classification;
- reproduction or reasoning;
- change made, if any;
- verification command and result;
- disposition: fixed, already fixed, false positive, accepted risk, or unresolved.

Do not collapse “reported”, “confirmed”, “fixed”, and “verified” into a single state.

## Security and confidentiality

Use least-privilege access for Cubic CLI, GitHub, and MCP. Do not copy secrets, credentials, private keys, tokens, or unnecessary proprietary content into review prompts or comments. Keep sensitive repository context inside approved tooling and scopes.

## Completion criteria

A Cubic-assisted remediation is complete only when:
- actionable findings in scope are handled or explicitly documented;
- required repository tests/checks pass, or failures are clearly reported;
- commits are scoped and traceable;
- PR threads are resolved only when their disposition is justified;
- no security or quality gate was weakened to produce a clean review.

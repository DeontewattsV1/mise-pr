# GitHub Marketplace Listing — Mise PR

## Marketplace name
Mise PR Review Packets

## Short description
Pull requests prepped before review.

## Longer description
Mise PR is a lightweight GitHub Action and CLI that turns chaotic pull requests into review-ready packets before humans or AI agents review them.

It checks pull request size, churn, risky paths, missing tests, weak descriptions, and missing issue/spec links. It then produces one Markdown packet for reviewers and one JSON packet for agents and automation.

Mise PR is not another AI code reviewer. It is the review-readiness layer before review starts.

## Primary category
Code quality

## Secondary category
Utilities

## Recommended repository topics
- github-action
- pull-requests
- code-review
- developer-tools
- productivity
- ai-agents
- ci
- review-readiness

## Why install it?

- Reduce noisy review loops before they start.
- Protect senior reviewer attention.
- Give AI coding agents cleaner handoff context.
- Create a consistent review-readiness standard across repos.
- Keep analysis local and deterministic by default.

## Permissions needed in consuming repos

```yaml
permissions:
  contents: read
  pull-requests: read
  issues: write
```

`issues: write` is only needed when `comment: true` is enabled so the action can post or update a PR comment.

## Publish checklist

1. Confirm the repository is public.
2. Confirm the root contains `action.yml`.
3. Create a release tag such as `v0.1.0`.
4. In the GitHub release UI, select **Publish this Action to the GitHub Marketplace**.
5. Choose primary category `Code quality` and secondary category `Utilities`.
6. Publish the release.

## First release title
Mise PR v0.1.0 — Review packets for pull requests

## First release summary
Initial public release of Mise PR, a GitHub Action and CLI that generates deterministic review-readiness packets for pull requests.

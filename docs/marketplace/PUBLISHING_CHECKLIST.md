# Marketplace Publishing Checklist

## Requirements

- Public repository
- One root `action.yml`
- Unique Action metadata name: `Mise PR Review Packets`
- No files under `.github/workflows/`
- Marketplace-ready README
- Release notes prepared
- License included

## Publish flow

1. Open this repository on GitHub.
2. Open `action.yml`.
3. Use the Marketplace banner to draft a release.
4. Select **Publish this Action to the GitHub Marketplace**.
5. Primary category: **Code Quality**.
6. Secondary category: **Continuous Integration** or **Utilities**.
7. Tag: `v0.1.0`.
8. Release title: `Mise PR v0.1.0 — Review Packets for Pull Requests`.
9. Paste the body from `docs/releases/v0.1.0.md`.
10. Publish the release.

## Owner-only step

The Marketplace checkbox may require the repository owner to accept the GitHub Marketplace Developer Agreement and complete two-factor authentication in GitHub's UI.

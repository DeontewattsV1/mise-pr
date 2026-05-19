# Publish Mise PR to GitHub Marketplace

Mise PR is structured as a single GitHub Action repository.

## Manual marketplace steps

1. Open the repository on GitHub.
2. Open `action.yml`.
3. Use the GitHub banner to draft a release for Marketplace.
4. Select **Publish this Action to the GitHub Marketplace**.
5. Accept the GitHub Marketplace Developer Agreement if prompted.
6. Use tag `v0.1.0`.
7. Use title `Mise PR v0.1.0 — Review packets for pull requests`.
8. Paste release notes from `docs/releases/v0.1.0.md`.
9. Select category `Code quality` and secondary category `Utilities`.
10. Publish the release.

## After publishing

Pin the release, add topics, and use this install snippet in posts:

```yaml
- uses: DeontewattsV1/mise-pr@v0.1.0
  with:
    base-ref: origin/${{ github.base_ref }}
    head-ref: HEAD
    comment: true
```

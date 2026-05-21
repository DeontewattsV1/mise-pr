<p align="center">
  <img src="https://img.shields.io/badge/Security-Policy-critical?style=for-the-badge&logo=shield&logoColor=white" alt="Security Policy" />
  <img src="https://img.shields.io/badge/CodeQL-Enabled-2A5699?style=for-the-badge&logo=github&logoColor=white" alt="CodeQL" />
  <img src="https://img.shields.io/badge/License-Apache_2.0-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">Security Policy</h1>

<p align="center"><strong>Mise PR &mdash; Vulnerability Reporting &amp; Security Standards</strong></p>

<p align="center">
  <a href="#-reporting-a-vulnerability">Report a Vulnerability</a> &bull;
  <a href="#-supported-versions">Supported Versions</a> &bull;
  <a href="#-security-model">Security Model</a> &bull;
  <a href="#-hardening-guide">Hardening Guide</a>
</p>

---

## Supported Versions

> Mise PR follows [Semantic Versioning](https://semver.org/). Security patches are back-ported to the latest minor release.

| Version | Status | Security Updates |
|---------|--------|-----------------|
| **0.1.x** (latest) | :white_check_mark: Active | Receiving all patches |
| < 0.1.0 | :x: End-of-life | No patches &mdash; please upgrade |

---

## Reporting a Vulnerability

> [!IMPORTANT]
> **Do NOT open a public GitHub issue for security vulnerabilities.**

We take security seriously. If you discover a vulnerability in Mise PR, please report it responsibly using one of the methods below.

<details>
<summary><strong>Option 1 &mdash; GitHub Private Vulnerability Reporting (Preferred)</strong></summary>

<br/>

1. Navigate to **[Security &rarr; Advisories &rarr; New Draft Advisory](https://github.com/DeontewattsV1/mise-pr/security/advisories/new)**
2. Fill in the advisory form:
   - **Summary**: A concise title describing the vulnerability
   - **Severity**: Your assessment (Critical / High / Medium / Low)
   - **Description**: Steps to reproduce, impact analysis, and any proof-of-concept
   - **Affected versions**: Which versions are affected
3. Submit the draft &mdash; the maintainers will be notified privately
4. You will receive a response within **72 hours**

> GitHub's private reporting keeps the conversation confidential until a fix is published.

</details>

<details>
<summary><strong>Option 2 &mdash; Encrypted Email</strong></summary>

<br/>

Send an encrypted report to: **`deonte.wattss@gmail.com`**

Include the following in your report:

```text
Subject: [SECURITY] mise-pr — <Brief Description>

1. Vulnerability type (e.g., command injection, path traversal)
2. Affected component (e.g., mise_pr/git.py, action.yml)
3. Steps to reproduce
4. Impact assessment
5. Suggested fix (if any)
6. Your preferred attribution name (for the advisory credits)
```

We aim to acknowledge receipt within **48 hours** and provide a resolution timeline within **7 business days**.

</details>

<details>
<summary><strong>What Happens After You Report?</strong></summary>

<br/>

```
 You report ──▶ Triage (48h) ──▶ Confirm & Assign ──▶ Develop Fix ──▶ Release & Disclose
      │                                                       │                │
      │              Private collaboration ◀──────────────────┘                │
      │                                                                        │
      └──────────────── Credit in advisory & CHANGELOG ◀──────────────────────┘
```

| Phase | Timeframe | What Happens |
|-------|-----------|--------------|
| **Triage** | 48 hours | We acknowledge receipt and begin analysis |
| **Assessment** | 7 days | Severity confirmed, CVE requested if applicable |
| **Remediation** | 14–30 days | Patch developed and tested in a private branch |
| **Disclosure** | Coordinated | Advisory published with credit to the reporter |

</details>

---

## Security Model

> Mise PR is a **read-only analysis tool**. It examines Git metadata and PR context to produce review packets. It does not modify source code, merge PRs, or execute user-supplied code.

<details>
<summary><strong>Threat Model &amp; Trust Boundaries</strong></summary>

<br/>

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Runner                     │
│                                                             │
│   ┌──────────┐    ┌────────────┐    ┌───────────────────┐  │
│   │  Git CLI  │───▶│  mise-pr   │───▶│  Review Packet    │  │
│   │ (read)    │    │  analyzer  │    │  (Markdown/JSON)  │  │
│   └──────────┘    └────────────┘    └───────────────────┘  │
│        │                │                     │             │
│   Reads only:      Processes:           Outputs:            │
│   - diff stats     - file counts        - Risk score        │
│   - file paths     - churn metrics      - Blockers          │
│   - numstat        - path patterns      - Warnings          │
│                    - PR metadata         - Recommendations   │
└─────────────────────────────────────────────────────────────┘
```

### Trust Boundaries

| Boundary | Trust Level | Notes |
|----------|-------------|-------|
| Git CLI subprocess calls | **Medium** | Mise PR shells out to `git diff --numstat`. Inputs (base-ref, head-ref) come from workflow configuration |
| PR metadata (title, body) | **Low** | User-supplied text is read for analysis but never executed or interpolated into shell commands |
| Policy configuration (`.mise-pr.yml`) | **Medium** | YAML parsed by PyYAML safe loader; only known scalar keys are consumed |
| Output packets (Markdown/JSON) | **Output** | Generated reports are written to files and optionally posted as PR comments |

</details>

<details>
<summary><strong>What Mise PR Does NOT Do</strong></summary>

<br/>

| Action | Status | Details |
|--------|--------|---------|
| Execute user code | :no_entry_sign: Never | Analysis is purely metadata-based |
| Modify the repository | :no_entry_sign: Never | All git operations are read-only |
| Access secrets or tokens | :no_entry_sign: Never | No secrets are required or consumed |
| Make network requests | :no_entry_sign: Never | Fully offline after `pip install` |
| Approve or merge PRs | :no_entry_sign: Never | Only produces advisory reports |

</details>

<details>
<summary><strong>Permissions Required</strong></summary>

<br/>

The GitHub Action requests **minimum viable permissions**:

```yaml
permissions:
  contents: read          # Read repository files and git history
  pull-requests: read     # Read PR metadata (title, body, author)
  issues: write           # Post review packet as a PR comment (optional)
```

> [!NOTE]
> `issues: write` is only needed when `comment: true` is set. If you don't use the comment feature, you can remove this permission entirely.

**No `write` access to code, no admin access, no secret access.**

</details>

---

## Hardening Guide

> Best practices for running Mise PR securely in your CI pipelines.

<details>
<summary><strong>1. Pin Action Versions</strong></summary>

<br/>

Always pin to a specific version tag or commit SHA rather than a branch:

```yaml
# Recommended — pinned to release tag
- uses: DeontewattsV1/mise-pr@v0.1.0

# Most secure — pinned to commit SHA
- uses: DeontewattsV1/mise-pr@<full-commit-sha>

# Not recommended — tracks moving branch
- uses: DeontewattsV1/mise-pr@main
```

</details>

<details>
<summary><strong>2. Apply Least-Privilege Permissions</strong></summary>

<br/>

Set top-level workflow permissions to restrict defaults, then grant only what Mise PR needs:

```yaml
# Lock down the workflow
permissions: {}

jobs:
  review-packet:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: write        # Only if comment: true
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: DeontewattsV1/mise-pr@v0.1.0
        with:
          fail-on: red
          comment: true
```

</details>

<details>
<summary><strong>3. Restrict Fork PR Execution</strong></summary>

<br/>

For public repositories, prevent untrusted fork PRs from executing workflows with write permissions:

```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened]

jobs:
  review-packet:
    # Only run on PRs from the same repo, not forks
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    # ...
```

> [!WARNING]
> Using `pull_request_target` with `actions/checkout` of the PR head can expose secrets. Mise PR's read-only nature mitigates this, but restricting forks is still recommended.

</details>

<details>
<summary><strong>4. Validate Configuration Files</strong></summary>

<br/>

The `.mise-pr.yml` configuration is parsed with PyYAML's safe loader. Only the following keys are recognized:

| Key | Type | Default |
|-----|------|---------|
| `max_files` | `int` | `12` |
| `max_churn` | `int` | `450` |
| `max_single_file_churn` | `int` | `180` |
| `require_issue_link` | `bool` | `true` |
| `require_tests_for_source` | `bool` | `true` |
| `require_description` | `bool` | `true` |
| `risky_path_patterns` | `list[str]` | See defaults in [`models.py`](mise_pr/models.py) |
| `generated_path_patterns` | `list[str]` | See defaults in [`models.py`](mise_pr/models.py) |

Any unrecognized keys are silently ignored. Arbitrary YAML constructs (anchors, custom tags) are rejected by the safe loader.

</details>

<details>
<summary><strong>5. Audit Risky Path Patterns</strong></summary>

<br/>

Customize `risky_path_patterns` in `.mise-pr.yml` to match your project's sensitive areas:

```yaml
risky_path_patterns:
  - auth
  - security
  - payment
  - billing
  - permission
  - migration
  - infra
  - terraform
  - k8s
  - docker
  - github/workflows
  - secrets
  - crypto
  - sql
  - database
```

> Add any project-specific sensitive directories (e.g., `compliance/`, `pii/`, `encryption/`).

</details>

---

## Supply Chain Security

<details>
<summary><strong>Dependency Verification</strong></summary>

<br/>

Mise PR has a minimal dependency footprint:

| Dependency | Purpose | Pinned |
|------------|---------|--------|
| `pyyaml>=6.0.1` | Config parsing (safe loader only) | :white_check_mark: Minimum version |
| `typer>=0.12.3` | CLI framework | :white_check_mark: Minimum version |
| `rich>=13.7.1` | Terminal formatting | :white_check_mark: Minimum version |

**No transitive network dependencies at runtime.** All analysis is performed locally using only the Git CLI and Python standard library for core logic.

</details>

<details>
<summary><strong>Code Scanning</strong></summary>

<br/>

| Tool | Scope | Schedule |
|------|-------|----------|
| **CodeQL** | Python + GitHub Actions | Every push to `main`, every PR, weekly scan |
| **SonarCloud** | Code quality + security hotspots | Per PR and merge |
| **Dependabot** | Dependency vulnerabilities | Continuous |

> CodeQL configuration: [`.github/workflows/codeql.yml`](.github/workflows/codeql.yml)

</details>

---

## Security Checklist for Contributors

<details>
<summary><strong>Before Submitting a PR</strong></summary>

<br/>

- [ ] **No secrets in code**: No API keys, tokens, or passwords in source files
- [ ] **No shell injection**: All subprocess calls use list-form arguments (never string interpolation)
- [ ] **Safe YAML parsing**: Using `yaml.safe_load()` only (never `yaml.load()`)
- [ ] **Input validation**: All external inputs (refs, paths, config values) are validated before use
- [ ] **No arbitrary code execution**: PR metadata is read, never evaluated or executed
- [ ] **Minimal permissions**: Workflow changes don't request more permissions than needed
- [ ] **Pinned actions**: All third-party action references use version tags or SHAs
- [ ] **Tests pass**: `pytest -v` completes without failures
- [ ] **Lint clean**: `ruff check mise_pr/` reports no issues
- [ ] **Type safe**: `mypy mise_pr/` reports no errors

</details>

---

## Known Security Considerations

<details>
<summary><strong>Git Subprocess Calls</strong></summary>

<br/>

Mise PR invokes `git diff --numstat` via `subprocess.run()` with list-form arguments:

```python
# mise_pr/git.py — safe subprocess usage
result = subprocess.run(
    ['git', *args],       # List form prevents shell injection
    cwd=cwd,
    check=False,
    text=True,
    capture_output=True
)
```

**Mitigation**: Arguments are never passed through a shell. The `shell=False` default is maintained. User-controlled inputs (base-ref, head-ref) are passed as list elements, not interpolated into a command string.

</details>

<details>
<summary><strong>YAML Configuration Parsing</strong></summary>

<br/>

The `.mise-pr.yml` file is parsed using PyYAML's safe loader, which prevents arbitrary Python object instantiation:

```python
# Only safe scalar types are loaded
import yaml
with open(path) as f:
    config = yaml.safe_load(f)
```

**Mitigation**: `yaml.safe_load()` rejects custom tags (`!!python/object`, etc.) that could lead to code execution.

</details>

<details>
<summary><strong>PR Comment Injection</strong></summary>

<br/>

Review packets are posted as PR comments via `actions/github-script`. The Markdown output is generated from structured data (scores, file paths, policy values), not from raw user input.

**Mitigation**: PR title and body text appear in the output but are embedded in Markdown context, not in executable positions. No HTML rendering or JavaScript execution occurs in the generated packets.

</details>

---

## Scope

<details>
<summary><strong>What Is In Scope</strong></summary>

<br/>

| Component | Repository Path |
|-----------|-----------------|
| Python analysis engine | `mise_pr/` |
| CLI interface | `mise_pr/cli.py` |
| GitHub Action definition | `action.yml` |
| CI/CD workflows | `.github/workflows/` |
| Configuration schema | `.mise-pr.yml` |
| Dependencies | `pyproject.toml`, `uv.lock` |

</details>

<details>
<summary><strong>What Is Out of Scope</strong></summary>

<br/>

| Item | Reason |
|------|--------|
| Third-party GitHub Actions (e.g., `actions/checkout`) | Report to their respective maintainers |
| GitHub platform vulnerabilities | Report to [GitHub Bug Bounty](https://bounty.github.com/) |
| Social engineering attacks | Not a software vulnerability |
| Denial-of-service via large PRs | By design, Mise PR analyzes and reports on oversized PRs |

</details>

---

## Security Contacts

| Role | Contact |
|------|---------|
| **Primary Maintainer** | [@DeontewattsV1](https://github.com/DeontewattsV1) |
| **Security Reports** | [GitHub Private Advisory](https://github.com/DeontewattsV1/mise-pr/security/advisories/new) |
| **Email (backup)** | `deonte.wattss@gmail.com` |

---

<p align="center">
  <sub>
    This policy is reviewed and updated with each minor release.<br/>
    Last updated: May 2026 &bull; Mise PR v0.1.x &bull; Apache-2.0
  </sub>
</p>

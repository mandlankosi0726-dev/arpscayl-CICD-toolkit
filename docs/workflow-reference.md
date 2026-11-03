# Reusable workflow reference

## Python CI (`.github/workflows/ci-python.yml`)

Runs Python checks for the caller repository using its source and configuration.

| Input | Required | Default | Notes |
| --- | --- | --- | --- |
| `python-version` | No | `3.12` | Version passed to setup-python. |
| `working-directory` | No | `.` | Project directory within the checked-out caller repository. |
| `requirements-file` | No | `requirements.txt` | Requirements file installed before checks; empty string skips it. |
| `run-typecheck` | No | `false` | Runs `python -m mypy .`; caller dependencies must include/configure mypy. |
| `coverage-minimum` | No | `0` | Positive value enables pytest-cov and threshold enforcement; zero disables coverage. |

No secrets are required. The workflow grants `contents: read`. It runs checkout, Python setup, dependency installation, Ruff, pytest, optional mypy, and uploads JUnit XML and coverage XML reports for seven days when present. It returns no workflow outputs. Install, lint, test, coverage, and optional type-check failures fail the job. Requirements are trusted caller-repository code and must be reviewed; pip installs can execute build backend code. Values are passed as action inputs or environment values rather than interpolated into shell source.

Example caller:

```yaml
jobs:
  python-ci:
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/ci-python.yml@v1.0.0
    with:
      python-version: "3.12"
      requirements-file: requirements.txt
      coverage-minimum: 80
```

## Node.js CI (`.github/workflows/ci-node.yml`)

Installs a locked npm dependency graph and runs the consuming package's standard CI scripts.

| Input | Required | Default | Notes |
| --- | --- | --- | --- |
| `node-version` | No | `22` | Version passed to setup-node. |
| `working-directory` | No | `.` | Must contain `package.json` and `package-lock.json`. |
| `run-typecheck` | No | `false` | Runs the package's `typecheck` script when enabled. |

No secrets are required. The workflow grants `contents: read`. It runs `npm ci`, `npm run lint`, `npm test`, and `npm run build`, then optionally `npm run typecheck`. It has no outputs or uploaded artifacts. Missing lockfiles/scripts, install errors, lint/test/build errors, and requested type-check errors fail the job. `npm ci` runs dependency lifecycle scripts; review the caller's lockfile and dependency tree. Do not expose deployment secrets to this CI workflow.

Example caller:

```yaml
jobs:
  node-ci:
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/ci-node.yml@v1.0.0
    with:
      node-version: "22"
```

Replace `your-org` and `v1.0.0` with the actual toolkit repository owner and a published version. A reviewed full commit SHA can be used when stronger immutability is required.

## Security checks (`.github/workflows/security-checks.yml`)

| Input | Required | Default | Notes |
| --- | --- | --- | --- |
| `language` | Yes | — | `python` or `node` for dependency auditing; CodeQL also supports these values. |
| `working-directory` | No | `.` | Directory for package dependency auditing. |
| `requirements-file` | No | `requirements.txt` | Python requirements file; Python audit uses `pip-audit --strict`. |
| `run-secret-scan` | No | `true` | Scans full checked-out Git history with a digest-pinned Gitleaks image. |
| `run-dependency-scan` | No | `true` | Audits Python requirements or npm's lockfile. |
| `run-sast` | No | `false` | Runs CodeQL and uploads SARIF to GitHub code scanning. |

The default workflow permission is `contents: read`; secret and dependency scans need no secrets. Secret scan uses a digest-pinned Gitleaks image and redacts findings in command output. Python audit fails on reported vulnerabilities; npm audit blocks HIGH and CRITICAL findings. If SAST is enabled, the caller must grant `actions: read`, `contents: read`, and `security-events: write` to the call job, and code scanning must be available in repository settings. Failures in any enabled scan fail its job. See `docs/security.md` for exceptions and scanner limitations.

```yaml
jobs:
  security:
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/security-checks.yml@v1.0.0
    with:
      language: python
      requirements-file: requirements.txt
```

## Docker CI (`.github/workflows/ci-docker.yml`)

Inputs are `context` (`.`), `dockerfile` (`Dockerfile`), `require-non-root` (`true`), and `scan-severity` (`HIGH,CRITICAL`). The severity threshold can be tightened to include MEDIUM or LOW, but must include HIGH and CRITICAL. It requires no secrets and grants `contents: read`. It statically checks that each base image uses an explicit tag or digest, rejects a `latest` tag, checks the final stage's user, builds the image, and scans it with Trivy. The job fails on invalid Dockerfile conventions, build errors, or unfixed findings at the selected severities. No artifact or output is produced.

## Docker build and publish (`.github/workflows/docker-build-publish.yml`)

Inputs are `context` (`.`), `dockerfile` (`Dockerfile`), required lowercase `image-name` (such as `ghcr.io/example/service`), `publish` (`true`), and `require-non-root` (`true`). It builds and vulnerability-scans an image on all events, saves the verified image as a short-lived artifact, and publishes that exact image only on a push to `main` or a `v*` tag. Publishing is skipped for pull requests and other events. It requires no stored registry secret; the publisher uses `GITHUB_TOKEN` and requires the caller job to grant `packages: write`. The workflow output `image-digest` contains the registry digest when published and is empty otherwise. Build, scan, artifact, or push failures fail the corresponding job.

```yaml
jobs:
  image:
    permissions:
      contents: read
      packages: write
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/docker-build-publish.yml@v1.0.0
    with:
      image-name: ghcr.io/your-org/your-app
```

## SSH container deployment (`.github/workflows/deploy-container.yml`)

This workflow deploys a previously built and scanned container image to a Linux Docker host. It requires `environment`, `image-reference`, `host`, `user`, `service-name`, `host-port`, and `container-port`. The image must be a registry digest (`registry/name@sha256:...`); mutable tags are rejected. Optional inputs are `health-path` (`/health`) and `ssh-port` (`22`). Required secrets are `ssh-private-key` and `ssh-known-hosts`; the latter must contain the pinned host key obtained through a trusted out-of-band process. No `ssh-keyscan` trust-on-first-use is used.

The workflow assigns the requested GitHub Environment so its configured protection rules apply. It validates all target and image inputs before using credentials. On the host it pulls the immutable image, preserves the current container, starts the replacement, checks the HTTP health path for up to 60 seconds, and restores the prior container if startup or health checks fail. The remote account needs Docker permissions and the host needs registry pull access. Application-specific mounts, environment files, secrets, TLS, and service networking remain host-managed prerequisites; do not pass them as workflow command fragments.

Example caller (configure `production` with required reviewers and save both SSH values as environment secrets):

```yaml
jobs:
  deploy:
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/deploy-container.yml@v1.0.0
    with:
      environment: production
      image-reference: ghcr.io/your-org/your-app@sha256:REPLACE_WITH_VERIFIED_DIGEST
      host: deploy.example.net
      user: deployer
      service-name: your-app
      host-port: 8080
      container-port: 8080
      health-path: /health
    secrets:
      ssh-private-key: ${{ secrets.DEPLOY_SSH_PRIVATE_KEY }}
      ssh-known-hosts: ${{ secrets.DEPLOY_SSH_KNOWN_HOSTS }}
```

The caller should set a concurrency group per service/environment to prevent overlapping replacements, restrict which branches/tags can deploy, and grant only `contents: read`. A production `environment:` declaration alone is not an approval gate; configure required reviewers and deployment branch rules in repository settings.

## Toolkit release (`.github/workflows/release.yml`)

Pushing a `vMAJOR.MINOR.PATCH` tag creates a GitHub Release with generated notes and an attached `release-manifest.json` recording the tag, source commit, and workflow run. The workflow requires `contents: write` only in its release job. Protect release tags with repository rulesets and ensure the tag points to a reviewed commit. Consumer repositories should select the published semver tag for normal upgrades or a reviewed full SHA for maximum immutability; never consume the mutable default branch in production.

## Terraform CI (`.github/workflows/ci-terraform.yml`)

Inputs are `working-directory` (`.`), exact `terraform-version` (`1.14.6`), and `scan-severity` (`HIGH,CRITICAL`). The workflow installs Terraform from HashiCorp's release site, verifies the archive against the published SHA256SUMS entry, runs recursive `terraform fmt -check`, initializes with `-backend=false`, runs `terraform validate`, and scans IaC misconfigurations with Trivy. It requires no credentials and grants `contents: read`. Formatting, initialization, validation, checksum, and qualifying Trivy findings fail the job. It does not access remote backends, plan, or apply infrastructure.

```yaml
jobs:
  terraform:
    uses: your-org/arpscayl-cicd-toolkit/.github/workflows/ci-terraform.yml@v1.0.0
    with:
      working-directory: infrastructure
      terraform-version: "1.14.6"
      scan-severity: HIGH,CRITICAL
```

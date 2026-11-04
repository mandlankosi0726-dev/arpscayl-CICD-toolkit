# Consumer workflow examples

These examples are read-only validation callers grouped by project type under `examples/consumers/`. They run on pull requests and pushes to `main`, require only `contents: read`, and contain no secrets, deployment jobs, AWS credentials, SSH credentials or client inventory values.

## Examples

| Consumer | Reusable workflow | Project-specific checks |
|---|---|---|
| `bun-frontend/` | `ci-bun.yml` | Frozen `bun.lock` install, lint, tests, build and optional typecheck. |
| `python-backend/` | `ci-python.yml` | Requirements install, Ruff/pytest, compileall, pip consistency and pip-audit. |
| `docker-application/` | `ci-docker.yml` | Dockerfile safety, local image build and Trivy scan; no push. |
| `terraform/` | `ci-terraform.yml` | Terraform 1.10.5 formatting, backend-free init, validation and IaC scan; no plan/apply. |
| `ansible/` | `ci-ansible.yml` | Inert example inventory parse, playbook syntax, Ansible/YAML lint and local tests. |
| `security-toolkit/` | `ci-security.yml` | Lint, format, typecheck, tests, local policy validation and dependency audit. |
| `backup-toolkit/` | `ci-backup.yml` | Lint, format, typecheck, tests, local backup-policy validation and dependency audit. |

The example `your-org/arpscayl-CICD-toolkit@v0.1.0` ref is a placeholder for a protected, published release. The current source tree does not itself publish a release. Before use, replace `your-org` with the actual owner and confirm that the protected semver tag exists, or pin the reusable workflow to a reviewed 40-character commit SHA. Do not use a mutable branch ref for a client or production consumer.

## Adopting an example

1. Copy the relevant caller workflow into the consumer repository's `.github/workflows/` directory and adjust the checked-in project path/runtime version.
2. Keep the consumer workflow's `permissions` at `contents: read` unless a separately reviewed job has a concrete need for more. Validation jobs do not need `secrets:` or a GitHub `environment:`.
3. Verify the project has the required lockfile, scripts, policy, inventory fixtures, or Docker/Terraform context before making the check required.
4. Run on a test branch and compare results with the repository's existing checks. Treat Python package installs, Docker builds and tests as execution of caller-controlled code; do not expose deployment secrets to pull-request validation.
5. Record the toolkit source ref and run URL, then configure branch protection to require the reviewed validation job.

## GitHub Environment configuration for separate deployment workflows

Validation examples never deploy. Publishing and SSH deployment remain distinct workflows. If a consumer separately adopts publishing or deployment, an administrator must create the corresponding GitHub Environment in repository settings, configure required reviewers and allowed branches/tags, and store only the needed environment secrets. Protect release tags with a ruleset. The workflow's `environment:` declaration alone does not create approval protection. Follow [the deployment guide](deployment-guide.md) and [versioning and releases](versioning.md).

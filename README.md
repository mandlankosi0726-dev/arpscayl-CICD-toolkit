# ArpScayl CI/CD Toolkit

A reusable, versioned set of GitHub Actions workflows, project conventions, validation utilities, and templates for application and infrastructure repositories.

## What it solves

The toolkit gives teams a consistent starting point for CI, security checks, container delivery, controlled deployment, and release traceability. It does not provision GitHub settings, secrets, servers, registries, or production environment protection; administrators configure those separately. Passing automated checks is useful evidence, not proof that software is secure.

Supported project categories are Python, Node.js, Dockerized applications, and Terraform infrastructure. The toolkit includes reusable Python, Node.js, Docker, Terraform, security, SSH container deployment, and release workflows, with matching templates. Ansible/Kubernetes validation and automated Kubernetes deployment remain future extensions.

## Quick start

Requires Python 3.12+ and Git. Install tooling with `python -m pip install -e '.[dev]'`.

```bash
python scripts/scaffold_project.py --list
python scripts/validate_config.py --config configs/defaults.yml
python scripts/validate_workflows.py
python -m unittest discover -s tests -v
```

Scaffold a starter with `python scripts/scaffold_project.py --template python-api --output ../my-api`; available templates are listed by `--list`. The tool refuses to overwrite existing files unless `--overwrite` is explicitly supplied. Copy `configs/defaults.yml` to `project-ci.yml` for projects that do not start from a template.

## Repository map

`.github/workflows/` contains toolkit CI and reusable workflows; `templates/` contains scaffold sources; `configs/` and `schemas/` define project conventions; `scripts/` contains local validation and scaffolding utilities; `tests/` verifies them; `docs/` explains use and operations; and `examples/` contains sample consumers. The Terraform starter formats, initializes without a backend, validates, and scans for misconfigurations. It does not plan or apply infrastructure.

## Consume a workflow

The templates show reusable workflow calls, for example `your-org/arpscayl-cicd-toolkit/.github/workflows/ci-python.yml@v1.0.0`. Replace `your-org` and select a published toolkit release. Do not use a mutable branch as a production dependency. Use a full reviewed commit SHA when stronger immutability is required. Reusable workflow files live under `.github/workflows/`, which is GitHub's required location.

For production deployments, configure GitHub Environments and required reviewers in repository settings, then store credentials as environment secrets. Declaring `environment:` in workflow YAML does not configure its protection rules.

The SSH deployment workflow only accepts an image pinned by registry digest and requires verified SSH host keys. Production access is governed by the caller's GitHub Environment rules; the workflow does not create reviewers or authorize a live target for you.

See [deployment](docs/deployment-guide.md), [versioning](docs/versioning.md), and [client onboarding](docs/client-onboarding.md) for the operational setup and release process. Use `make validate`, `make test`, and `make lint` for local checks.

## Contributing and failures

Run the validation and unit test commands above before proposing a change. Add tests and update documentation with each workflow. Investigate failures from the failing job's logs and artifact metadata; never include secrets in logs or issue reports. See `docs/` for workflow inputs, security behavior, and operational requirements.

## License

See [LICENSE](LICENSE).

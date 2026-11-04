# Getting started

Install Python 3.12 or newer and run `python -m pip install -e '.[dev]'`. To create a starter, run `python scripts/scaffold_project.py --template python-api --output ../my-api` or select `node-api`, `dockerized-application`, or `infrastructure`. For Bun, Ansible, Security and Backup projects, use the matching reusable workflow and examples under `examples/consumers/`. Replace `your-org` in the caller workflow with the toolkit repository owner and choose a published protected release tag or reviewed full commit SHA. A consumer repository can call Python CI as follows:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [master]
permissions:
  contents: read
jobs:
  python:
    uses: your-org/arpscayl-CICD-toolkit/.github/workflows/ci-python.yml@v0.1.0
    with:
      python-version: "3.12"
      requirements-file: requirements.txt
      coverage-minimum: 80
```

The `v0.1.0` ref above is illustrative until a protected tag is published. Consumers must pin a released toolkit tag or a reviewed full commit SHA, and must not consume a mutable branch. Copy `configs/defaults.yml` to `project-ci.yml`; edit fields and validate with `python scripts/validate_config.py --config project-ci.yml`.

Python CI installs the configured requirements file, then runs Ruff and pytest; coverage is opt-in through a positive threshold. If enabled, mypy must be present in the project's installed dependencies. Node CI requires a checked-in `package-lock.json`, then runs `npm ci`, `npm run lint`, `npm test`, and `npm run build`. An optional type check invokes the package's `typecheck` script.

For a Dockerized application, call `ci-docker.yml` during pull requests and use `docker-build-publish.yml` to publish the scanned image on a trusted push or version tag. Pass its immutable digest to `deploy-container.yml` only from a protected deployment job. Before using SSH deployment, configure a GitHub Environment, required reviewers for production, and the `ssh-private-key` and verified `ssh-known-hosts` secrets. Read the [deployment guide](deployment-guide.md) before targeting a server.

Terraform projects can use the `infrastructure` template and `ci-terraform.yml`. It checks formatting, initializes without a backend, runs `terraform validate`, and scans for misconfigurations; it does not run `plan` or `apply`. The workflow verifies the Terraform archive against HashiCorp's published SHA256SUMS file before extraction. Cloud plans and applies require separate design and approvals.

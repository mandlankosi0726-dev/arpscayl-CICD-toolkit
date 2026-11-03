# Troubleshooting

## Local validation

- `Unable to read YAML`: check indentation and quote values containing YAML punctuation, then rerun `python scripts/validate_config.py --config project-ci.yml`.
- Unknown or missing configuration fields: compare the file with `configs/defaults.yml` and `schemas/pipeline-config.schema.json`.
- Mutable action reference: pin the action to a reviewed full 40-character commit SHA and update its adjacent version comment.
- Direct shell interpolation policy error: place the context value in a step `env:` entry, validate/allowlist it, and read it as an environment variable in the script.
- Workflow permissions error: replace `write-all` with the smallest job-level permission map needed.
- Scaffolding says files exist: choose a new output directory or review the explicit `--overwrite` behavior before using it; scaffolding protects existing files by default.

## CI and security scans

- Python install errors: check the requirements file path and supported Python version. Package installation can execute project dependency build code.
- Node `npm ci` errors: commit the lockfile produced by the chosen npm version and ensure it matches `package.json`.
- Gitleaks findings: inspect the redacted result, rotate any real exposed credential immediately, then document a time-bounded false-positive exception if justified.
- CodeQL permission or upload errors: enable code scanning where supported and grant `actions: read`, `contents: read`, and `security-events: write` to the calling job.
- Trivy findings: identify the affected base image/package, update to a fixed version, rebuild and rescan. Do not lower severity thresholds to hide an unresolved critical finding.

## Docker publishing and deployment

- Publishing skipped: the publish job runs only for trusted pushes to `main` or `v*` tags and only when `publish` is true. Pull requests build and scan without writing to the registry.
- GHCR permission denied: grant `packages: write` only to the caller job that invokes the publishing workflow and confirm repository/package visibility rules.
- SSH host key mismatch: stop deployment and verify the host identity with the administrator before updating the `ssh-known-hosts` secret. Do not bypass strict checking.
- SSH authentication failure: check the environment secret mapping, key format, target account, authorized key, host/port reachability, and that the private key is scoped to the right host.
- Registry pull failure on host: authenticate the host to the registry using an approved least-privilege credential and verify the immutable image digest exists.
- Health check timeout: inspect application logs and port mapping on the host. The workflow restores the prior container on a failed candidate check; confirm the restored service is healthy before retrying.
- Production deployment is waiting: approve it through the configured GitHub Environment reviewer flow. If no protection rules were configured, `environment: production` alone does not require approval.

Never paste SSH keys, registry tokens, raw secret scan findings, or client data into workflow logs or support issues. See [deployment guide](deployment-guide.md) for rollback limits and operational prerequisites.

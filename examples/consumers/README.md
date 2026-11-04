# Consumer examples

Each project subdirectory contains a caller workflow under `.github/workflows/ci.yml`. Copy that file to the same path in the consumer repository, then adjust the toolkit owner/ref and project paths.

The `v0.1.0` workflow refs are illustrative and are not evidence of a published release. Before adoption, confirm a protected release tag exists or substitute a reviewed full commit SHA. These PR/push validation callers have `contents: read`, no secrets, and no deployment environment. Terraform only validates; Docker validation builds/scans locally; Ansible parses the inert development inventory; Security and Backup validate local project files and tests.

Publishing and deployment remain separate workflows. See `docs/deployment-guide.md` for GitHub Environment reviewers, branch/tag restrictions and environment-specific secret configuration. Do not pass client inventories, cloud credentials or production secrets to these validation examples.

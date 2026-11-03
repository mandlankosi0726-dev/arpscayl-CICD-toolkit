# Security model

The config validator parses YAML as data and never executes configured commands. Workflow validation rejects remote actions not pinned to a full 40-character commit SHA, broad `write-all` permissions, direct interpolation of untrusted contexts into shell commands, and pull-request code checkout in `pull_request_target` workflows. Ordinary CI requires only `contents: read`; publishing and deployment grants are scoped to their privileged jobs.

Python CI installs Ruff, pytest, and pytest-cov at pinned versions. A consuming repository controls its requirements file and should pin reviewed dependencies. Node CI runs `npm ci`, which executes lifecycle scripts from the consuming repository's pinned dependencies. Review that dependency tree and its lockfile integrity hashes.

A passing scan cannot prove a project secure. Gitleaks scans the checked-out Git history and fails on findings; its report output is redacted. Gitleaks false positives can be approved through the consuming repository's reviewed ignore configuration, with a reason, accountable owner, and expiry documented alongside the exception. Rotate a credential if a real secret is found; removing it from the latest commit does not revoke it.

Python dependency auditing fails on reported vulnerabilities through `pip-audit --strict`. npm auditing fails at HIGH or CRITICAL severity. These sources can miss vulnerabilities, and Python and npm severity policies differ. Review findings, upgrade affected dependencies, or record a time-bounded exception with a reason and owner. Docker image scans fail on unfixed HIGH and CRITICAL findings by default; Docker CI can accept only thresholds that still include HIGH and CRITICAL.

CodeQL SAST is optional and supports Python and JavaScript/TypeScript. It needs GitHub code scanning enabled and `security-events: write` permission in the caller workflow. Private repository availability depends on the GitHub plan and repository configuration. If these prerequisites are absent, leave SAST disabled or enable it after an administrator confirms availability.

The Docker build-and-publish workflow verifies and scans an image before publishing. The build job has read-only contents permission; only the publish job receives `packages: write`, and it runs only on a push to `main` or a `v*` tag. The caller must grant `packages: write` to the reusable-workflow job. The image tag contains the source commit and the workflow returns the registry digest. No deployment credentials are used.

The reusable SSH deployment requires an immutable image digest, validates host/user/service/port/path inputs before credential use, and authenticates SSH with a caller-supplied known-hosts secret and strict host-key checking. The previous container is retained until the candidate passes its HTTP health check; on failure the workflow restores it. Configure environment reviewers and deployment branch restrictions in GitHub because workflow YAML cannot enforce the settings by itself. Keep the SSH key scoped to the target host and container service.

The local workflow policy checker also rejects `write-all`, unsafe direct shell interpolation of GitHub event/input values, and checkout use with `pull_request_target`. These static rules are targeted safeguards, not a complete workflow security analysis.

Store credentials in GitHub Secrets or approved short-lived identity systems; never commit secrets. Configure repository rules to require reviews on workflow changes and protect production environments.

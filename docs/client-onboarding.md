# Client project onboarding

Use this checklist when introducing the toolkit into a client repository. Record decisions and owners in the client handover; do not commit client credentials or production configuration.

1. **Assess the repository.** Review its current CI, default branch, branch protections, package manifests, lockfiles, Dockerfiles, release process, and known operational constraints. Preserve working checks while migrating.
2. **Identify the stack and target.** Confirm language/runtime, package manager, supported deployment method, registry, environments, health endpoint, data stores, and who can authorize production changes.
3. **Select the workflow for the actual toolchain.** Choose Bun or npm Node CI according to the checked-in lockfile; use Python, Docker, Terraform, Ansible, Security or Backup validation where appropriate. Examples are in `examples/consumers/`. Terraform CI validates configuration and scans misconfigurations but does not create plans or apply infrastructure.
4. **Configure checks.** Copy `configs/defaults.yml` to `project-ci.yml`, accurately describe the project, then run config and workflow validation. Make disabled security checks visible with a reason, owner, and review date.
5. **Configure GitHub controls.** Grant only the workflow permissions needed. Protect workflow and release files, use Dependabot or another reviewed pin update process, configure environments and branch/tag restrictions, and store environment-specific secrets in GitHub. Production must have required reviewers where appropriate.
6. **Test outside production.** Run the toolkit test suite and read-only consumer validation. These workflows do not connect to client infrastructure. If a deployment is separately approved, use its own protected environment and a non-production target; verify known-host fingerprints through a trusted channel and test health-check rollback.
7. **Validate release and deployment behavior.** Confirm the built image digest maps to the expected source commit, verify registry pull access on the target, check deployment history/manifest records, and rehearse rollback. Do not treat a mutable image tag as deployment identity.
8. **Obtain production authorization.** Get explicit client approval of the deployment target, maintenance window, rollback plan, and GitHub Environment reviewers before enabling production release/deployment rules.
9. **Document and hand over.** Record workflow references and versions, repository settings, environment/secret names (never values), service ownership, alerting, recovery steps, and outstanding limitations. Confirm named maintainers can perform a staging release and rollback.

## Current boundary

The toolkit implements Python, npm Node, Bun, Docker, Terraform, Ansible, Security and Backup validation, plus separate GHCR publishing, SSH container deployment and GitHub Release workflows. Validation jobs use read-only repository access and no client credentials. GitHub Environment protection, repository rules, secrets, target hosts, registry credentials, and monitoring must be configured externally. Kubernetes validation and automated Kubernetes deployment are not implemented. Do not claim an end-to-end production verification unless it was completed in the client's authorized environment.

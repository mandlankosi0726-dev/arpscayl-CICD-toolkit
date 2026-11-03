# Client project onboarding

Use this checklist when introducing the toolkit into a client repository. Record decisions and owners in the client handover; do not commit client credentials or production configuration.

1. **Assess the repository.** Review its current CI, default branch, branch protections, package manifests, lockfiles, Dockerfiles, release process, and known operational constraints. Preserve working checks while migrating.
2. **Identify the stack and target.** Confirm language/runtime, package manager, supported deployment method, registry, environments, health endpoint, data stores, and who can authorize production changes.
3. **Select the template and workflows.** Use the Python, Node.js, Dockerized application, or Terraform infrastructure template as a starting point. Terraform CI validates configuration and scans misconfigurations but does not create plans or apply infrastructure.
4. **Configure checks.** Copy `configs/defaults.yml` to `project-ci.yml`, accurately describe the project, then run config and workflow validation. Make disabled security checks visible with a reason, owner, and review date.
5. **Configure GitHub controls.** Grant only the workflow permissions needed. Protect workflow and release files, use Dependabot or another reviewed pin update process, configure environments and branch/tag restrictions, and store environment-specific secrets in GitHub. Production must have required reviewers where appropriate.
6. **Test outside production.** Run the toolkit test suite, consumer CI, image build and scan, and deployment to a non-production host. Verify known-host fingerprints through a trusted channel and test health-check rollback.
7. **Validate release and deployment behavior.** Confirm the built image digest maps to the expected source commit, verify registry pull access on the target, check deployment history/manifest records, and rehearse rollback. Do not treat a mutable image tag as deployment identity.
8. **Obtain production authorization.** Get explicit client approval of the deployment target, maintenance window, rollback plan, and GitHub Environment reviewers before enabling production release/deployment rules.
9. **Document and hand over.** Record workflow references and versions, repository settings, environment/secret names (never values), service ownership, alerting, recovery steps, and outstanding limitations. Confirm named maintainers can perform a staging release and rollback.

## Current boundary

The toolkit implements Python, Node.js, Docker, Terraform validation, security, GHCR image publishing, SSH container deployment, and GitHub Release workflows. GitHub Environment protection, repository rules, secrets, target hosts, registry credentials, and monitoring must be configured externally. Ansible/Kubernetes validation and automated Kubernetes deployment are not implemented. Do not claim an end-to-end production verification unless it was completed in the client's authorized environment.

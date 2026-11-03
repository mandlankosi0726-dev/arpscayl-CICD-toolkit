# Deployment guide

## What the toolkit performs

`.github/workflows/deploy-container.yml` is a reusable GitHub Actions workflow for replacing one Docker container on a Linux host over SSH. It accepts only an immutable registry digest, validates inputs before using SSH credentials, verifies the server against a supplied `known_hosts` secret, checks the new container's HTTP health endpoint, and restores the previous container if the new one fails.

It does not provision a server, configure a firewall, create GitHub Environment protection, manage application secrets or volumes, configure a reverse proxy, or give the host registry access. The server must already run Docker and `curl`; its deployment user must be authorized to manage the target container. Ensure the registry credentials are configured on the server before using a private image.

## Configure an environment

Create `development`, `staging`, and `production` GitHub Environments as appropriate. For production, configure required reviewers, deployment branch/tag restrictions, and any wait timer in repository settings. Store `DEPLOY_SSH_PRIVATE_KEY` and `DEPLOY_SSH_KNOWN_HOSTS` as environment secrets. Obtain the host key through a trusted channel and verify its fingerprint with the server administrator before storing it. Do not use `ssh-keyscan` during deployment to establish trust.

Call the reusable workflow from a consumer repository; see [the workflow reference](workflow-reference.md#ssh-container-deployment-githubworkflowsdeploy-containeryml). Use a concurrency group scoped to the service and environment. Keep the deployment job separate from ordinary pull-request CI, and ensure only protected branches or reviewed release tags can reach production.

## Image and rollback behavior

Deploy the digest output from the successful Docker build-and-publish workflow. A tag such as `:latest` is not accepted. The remote host pulls the digest before changing the running service. It renames and stops the previous container, starts the new one on the configured port, and polls the configured HTTP path for up to 60 seconds. A failed `docker run` or health check removes the candidate and restores the previous container. A successful health check removes the previous container; retain other image digests in the registry according to your recovery policy.

This rollback restores the previous container image and its existing Docker configuration. It does not reverse database migrations, external side effects, or host configuration changes. Run backward-compatible migrations and test rollback behavior in staging before production use. Add monitoring after the initial health check for application-specific readiness and ongoing health.

## Release and traceability

The toolkit's release workflow creates a GitHub Release when a `vMAJOR.MINOR.PATCH` tag is pushed and attaches a manifest containing the tag, source commit, and workflow run URL. Protect `v*` tags with rulesets and review the commit before tagging. The release workflow requires `contents: write` for release creation. It does not publish Python or npm packages.

For each application deployment, retain the image digest, source commit, GitHub run URL, environment, and approver in the deployment record. Use GitHub's deployment history and the build workflow outputs as the audit trail. The Docker publishing workflow publishes `sha-<commit>` and exposes the registry digest; pass the digest explicitly to this workflow.

## Kubernetes integration pattern

A future Kubernetes workflow should accept only an immutable image digest, use a dedicated GitHub Environment per cluster/environment, authenticate with short-lived workload identity where supported, and grant only namespace-scoped deployment permissions. It should run manifest validation and policy checks before applying changes, wait for rollout health, record the deployed digest and source commit, and define an explicit rollback command. Do not reuse SSH credentials or expose a cluster-wide kubeconfig to general CI jobs. The Terraform workflow currently validates configurations only; it does not plan or apply.

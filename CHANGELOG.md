# Changelog

## Unreleased

- Add reusable Bun frontend, Ansible, Security toolkit and Backup toolkit validation workflows.
- Extend Python CI with optional compileall, pip consistency, pinned pip-audit and project-extra installation.
- Align Terraform validation default with Terraform 1.10.5 used by the ArpScayl staging project.
- Extend project configuration validation for Bun, Ansible, Security and Backup toolchain types.
- Require explicit workflow-level permissions in static validation and add read-only consumer examples.
- Keep validation separate from image publishing, SSH deployment and GitHub Release creation.
- Correct the Docker starter's dependency-scan setting for its `none` package manager and exercise tagged versus digest-pinned Docker validation modes explicitly.

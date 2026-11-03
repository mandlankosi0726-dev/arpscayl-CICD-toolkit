# Terraform infrastructure starter

This starter demonstrates a provider-free Terraform module and a caller for the toolkit's reusable Terraform validation workflow. The sample uses Terraform's built-in `terraform_data` resource so `fmt`, `init`, and `validate` run without cloud credentials or external providers. Replace the example module with reviewed infrastructure code and add provider version constraints and the committed `.terraform.lock.hcl` before using providers.

Run local checks with Terraform 1.14.6 or a compatible pinned version:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

The workflow also runs Trivy misconfiguration scanning and fails on HIGH or CRITICAL findings by default. The checksum file is fetched from the same HashiCorp HTTPS release endpoint as the archive; it detects transfer corruption but does not independently verify a detached publisher signature. The workflow does not run `plan` or `apply`, configure a backend, authenticate to a cloud account, validate organizational policy, or provision resources. Add those stages only with environment-specific approvals, least-privilege identity, and an explicit change review.

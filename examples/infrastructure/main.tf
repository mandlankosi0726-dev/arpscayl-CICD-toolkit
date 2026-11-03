terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

variable "environment" {
  description = "Deployment environment represented by this example module."
  type        = string

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "environment must be development, staging, or production."
  }
}

variable "owner" {
  description = "Team responsible for this infrastructure deployment."
  type        = string
  default     = "platform"
}

resource "terraform_data" "deployment_metadata" {
  input = {
    environment = var.environment
    owner       = var.owner
  }
}

output "deployment_metadata" {
  description = "Metadata emitted by the provider-free Terraform starter."
  value       = terraform_data.deployment_metadata.output
}

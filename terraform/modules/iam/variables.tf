variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "app_name" {
  description = "Application name prefix."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)."
  type        = string
}

variable "custom_roles" {
  description = "Additional IAM roles to grant to the backend service account."
  type        = list(string)
  default     = []
}

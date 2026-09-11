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

variable "region" {
  description = "Google Cloud region for the repository."
  type        = string
  default     = "us-central1"
}

variable "labels" {
  description = "Labels to attach to the repository."
  type        = map(string)
  default     = {}
}

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
  description = "Google Cloud region for the bucket."
  type        = string
  default     = "us-central1"
}

variable "service_account_email" {
  description = "Service account email granted object read/write access."
  type        = string
}

variable "enable_versioning" {
  description = "Enable object versioning on the GCS bucket."
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow destroying the bucket even if it contains objects (useful for dev/test)."
  type        = bool
  default     = false
}

variable "labels" {
  description = "Labels to attach to the GCS bucket."
  type        = map(string)
  default     = {}
}

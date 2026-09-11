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

variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service to monitor."
  type        = string
}

variable "enable_alerts" {
  description = "Whether to create Cloud Monitoring alert policies."
  type        = bool
  default     = true
}

variable "error_rate_threshold" {
  description = "5xx error rate threshold (errors/sec) to trigger alerting."
  type        = number
  default     = 5
}

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

variable "gemini_api_key" {
  description = "Gemini API Key to store in Secret Manager (optional; can be populated manually after secret creation)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "service_account_email" {
  description = "Service account email to grant Secret Accessor rights."
  type        = string
}

variable "labels" {
  description = "Labels to attach to the secret."
  type        = map(string)
  default     = {}
}

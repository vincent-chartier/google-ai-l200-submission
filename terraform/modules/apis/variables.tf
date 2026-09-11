variable "project_id" {
  description = "The GCP project ID in which to enable service APIs."
  type        = string
}

variable "services" {
  description = "List of GCP Service APIs required by the Cinema Outings Multi-Agent platform."
  type        = list(string)
  default = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "dlp.googleapis.com",
    "aiplatform.googleapis.com",
    "generativelanguage.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ]
}

variable "disable_services_on_destroy" {
  description = "Whether to disable services when the Terraform configuration is destroyed."
  type        = bool
  default     = false
}

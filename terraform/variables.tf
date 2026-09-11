variable "project_id" {
  description = "The Google Cloud Project ID where resources will be provisioned."
  type        = string
  default     = "vchartier-project"
}

variable "region" {
  description = "The primary Google Cloud region for deploying resources."
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Name prefix applied to all resources."
  type        = string
  default     = "cinema-outings"
}

variable "environment" {
  description = "Deployment environment stage (e.g. dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Optional custom container image URI. If left empty, points to the Artifact Registry repository image."
  type        = string
  default     = ""
}

variable "gemini_api_key" {
  description = "Google Gemini API key stored securely in Google Secret Manager."
  type        = string
  sensitive   = true
  default     = ""
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances to keep warm (set >= 1 for production to avoid cold starts)."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances for Cloud Run autoscaling."
  type        = number
  default     = 5
}

variable "cpu_limit" {
  description = "CPU allocation for the multi-agent container (e.g. 1, 2, 4)."
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory allocation for the multi-agent container (e.g. 1Gi, 2Gi, 4Gi)."
  type        = string
  default     = "2Gi"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated public access to the Cloud Run service."
  type        = bool
  default     = true
}

variable "enable_gcs_volume" {
  description = "Mount GCS bucket directly as a Cloud Storage FUSE volume to /data in Cloud Run."
  type        = bool
  default     = false
}

variable "enable_vpc_connector" {
  description = "Provision a Serverless VPC Access connector for private network egress."
  type        = bool
  default     = false
}

variable "enable_monitoring_alerts" {
  description = "Provision Cloud Monitoring alert policies for error rate monitoring."
  type        = bool
  default     = true
}

variable "model_coordinator" {
  description = "Gemini model tier for the Outing Coordinator agent."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_search_reco_deep" {
  description = "Gemini model tier for deep reasoning recommendations."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "model_search_reco_fast" {
  description = "Gemini model tier for fast screening search & catalog lookup."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_booking" {
  description = "Gemini model tier for booking transactions."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_housekeeping" {
  description = "Gemini model tier for housekeeping agent summaries and calendar generation."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "labels" {
  description = "Common labels applied to all resources."
  type        = map(string)
  default     = {}
}

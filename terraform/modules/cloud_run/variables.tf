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
  description = "Google Cloud region for the Cloud Run service."
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "URI of the container image in Artifact Registry."
  type        = string
}

variable "service_account_email" {
  description = "Email of the IAM service account attached to the Cloud Run revision."
  type        = string
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances to keep warm."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances."
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for container (e.g. 1, 2, 4)."
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for container (e.g. 1Gi, 2Gi, 4Gi)."
  type        = string
  default     = "2Gi"
}

variable "gemini_api_key_secret_id" {
  description = "Secret ID in Secret Manager for GEMINI_API_KEY."
  type        = string
}

variable "gcs_bucket_name" {
  description = "Cloud Storage bucket name for session state and artifact persistence."
  type        = string
  default     = ""
}

variable "enable_gcs_volume" {
  description = "Mount Cloud Storage bucket directly to /data using Cloud Run volume mount."
  type        = bool
  default     = false
}

variable "model_coordinator" {
  description = "Gemini model tier for coordinator agent."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_search_reco_deep" {
  description = "Gemini model tier for deep reasoning search & recommendations."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "model_search_reco_fast" {
  description = "Gemini model tier for fast catalog search & retrieval."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_booking" {
  description = "Gemini model tier for booking agent transactions."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_housekeeping" {
  description = "Gemini model tier for housekeeping & memory summaries."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated public access to the Cloud Run service."
  type        = bool
  default     = true
}

variable "ingress" {
  description = "Ingress traffic policy (INGRESS_TRAFFIC_ALL, INGRESS_TRAFFIC_INTERNAL_ONLY, INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER)."
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}

variable "vpc_connector_id" {
  description = "VPC connector ID for private egress routing (optional)."
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to attach to the Cloud Run service."
  type        = map(string)
  default     = {}
}

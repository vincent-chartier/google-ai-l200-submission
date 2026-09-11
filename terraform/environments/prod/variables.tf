variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "vchartier-project"
}

variable "region" {
  description = "Google Cloud region."
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name."
  type        = string
  default     = "cinema-outings"
}

variable "gemini_api_key" {
  description = "Gemini API key for production."
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_vpc_connector" {
  description = "Enable Serverless VPC Access connector in prod."
  type        = bool
  default     = false
}

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
  description = "Google Cloud region for networking components."
  type        = string
  default     = "us-central1"
}

variable "enable_vpc_connector" {
  description = "Whether to provision a Serverless VPC Access connector."
  type        = bool
  default     = false
}

variable "connector_cidr" {
  description = "CIDR range (/28) for the Serverless VPC Access connector."
  type        = string
  default     = "10.8.0.0/28"
}

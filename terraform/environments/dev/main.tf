terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "cinema_outings" {
  source = "../../"

  project_id               = var.project_id
  region                   = var.region
  app_name                 = var.app_name
  environment              = "dev"
  gemini_api_key           = var.gemini_api_key
  min_instances            = 0
  max_instances            = 2
  cpu_limit                = "1"
  memory_limit             = "1Gi"
  allow_unauthenticated    = true
  enable_gcs_volume        = false
  enable_vpc_connector     = false
  enable_monitoring_alerts = false
  labels = {
    environment = "dev"
    application = "cinema-outings"
    managed_by  = "terraform"
  }
}

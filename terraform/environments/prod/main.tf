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

  # Production remote state storage
  # backend "gcs" {
  #   bucket = "vchartier-project-cinema-outings-tfstate-prod"
  #   prefix = "terraform/state"
  # }
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
  environment              = "prod"
  gemini_api_key           = var.gemini_api_key
  min_instances            = 1
  max_instances            = 10
  cpu_limit                = "2"
  memory_limit             = "2Gi"
  allow_unauthenticated    = true
  enable_gcs_volume        = true
  enable_vpc_connector     = var.enable_vpc_connector
  enable_monitoring_alerts = true
  labels = {
    environment = "prod"
    application = "cinema-outings"
    managed_by  = "terraform"
  }
}

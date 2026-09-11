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

  # Optional backend configuration for remote state storage in GCS
  # backend "gcs" {
  #   bucket = "YOUR_GCS_TERRAFORM_STATE_BUCKET"
  #   prefix = "terraform/state/cinema-outings"
  # }
}

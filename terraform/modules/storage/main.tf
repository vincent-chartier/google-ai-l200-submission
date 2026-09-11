resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "google_storage_bucket" "app_data" {
  project                     = var.project_id
  name                        = "${var.project_id}-${var.app_name}-${var.environment}-data-${random_id.bucket_suffix.hex}"
  location                    = var.region
  force_destroy               = var.force_destroy
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    action {
      type = "AbortIncompleteMultipartUpload"
    }
    condition {
      age = 7
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 3
      with_state         = "ARCHIVED"
    }
  }

  labels = merge(
    {
      environment = var.environment
      app         = var.app_name
      managed_by  = "terraform"
    },
    var.labels
  )
}

resource "google_storage_bucket_iam_member" "backend_access" {
  bucket = google_storage_bucket.app_data.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${var.service_account_email}"
}

locals {
  service_name = "${var.app_name}-${var.environment}"
}

resource "google_cloud_run_v2_service" "backend" {
  project  = var.project_id
  name     = local.service_name
  location = var.region
  ingress  = var.ingress

  labels = merge(
    {
      environment = var.environment
      app         = var.app_name
      managed_by  = "terraform"
    },
    var.labels
  )

  template {
    service_account       = var.service_account_email
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    dynamic "vpc_access" {
      for_each = var.vpc_connector_id != null ? [1] : []
      content {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY"
      }
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "DATA_DIR"
        value = "/data"
      }

      env {
        name  = "DATABASE_PATH"
        value = "/data/cinema_sessions.db"
      }

      env {
        name  = "MODEL_COORDINATOR"
        value = var.model_coordinator
      }

      env {
        name  = "MODEL_SEARCH_RECO_DEEP"
        value = var.model_search_reco_deep
      }

      env {
        name  = "MODEL_SEARCH_RECO_FAST"
        value = var.model_search_reco_fast
      }

      env {
        name  = "MODEL_BOOKING"
        value = var.model_booking
      }

      env {
        name  = "MODEL_HOUSEKEEPING"
        value = var.model_housekeeping
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = var.gcs_bucket_name
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_api_key_secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8080
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 5
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8080
        }
        timeout_seconds   = 3
        period_seconds    = 30
        failure_threshold = 3
      }

      dynamic "volume_mounts" {
        for_each = var.enable_gcs_volume && var.gcs_bucket_name != "" ? [1] : []
        content {
          name       = "cinema-storage"
          mount_path = "/data"
        }
      }
    }

    dynamic "volumes" {
      for_each = var.enable_gcs_volume && var.gcs_bucket_name != "" ? [1] : []
      content {
        name = "cinema-storage"
        gcs {
          bucket    = var.gcs_bucket_name
          read_only = false
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

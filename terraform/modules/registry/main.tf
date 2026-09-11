resource "google_artifact_registry_repository" "backend_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "${var.app_name}-${var.environment}-repo"
  description   = "Docker container repository for ${var.app_name} backend (${var.environment})"
  format        = "DOCKER"

  labels = merge(
    {
      environment = var.environment
      app         = var.app_name
      managed_by  = "terraform"
    },
    var.labels
  )
}

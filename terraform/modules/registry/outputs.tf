output "repository_id" {
  description = "The Artifact Registry repository ID."
  value       = google_artifact_registry_repository.backend_repo.repository_id
}

output "repository_name" {
  description = "The full resource name of the repository."
  value       = google_artifact_registry_repository.backend_repo.name
}

output "repository_url" {
  description = "The base URL for pushing and pulling Docker images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

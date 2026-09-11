output "service_id" {
  description = "The ID of the Cloud Run service."
  value       = google_cloud_run_v2_service.backend.id
}

output "service_name" {
  description = "The name of the Cloud Run service."
  value       = google_cloud_run_v2_service.backend.name
}

output "service_uri" {
  description = "The HTTPS URI of the Cloud Run backend service."
  value       = google_cloud_run_v2_service.backend.uri
}

output "service_location" {
  description = "The location of the Cloud Run backend service."
  value       = google_cloud_run_v2_service.backend.location
}

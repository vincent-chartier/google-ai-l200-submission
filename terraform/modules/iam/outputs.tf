output "service_account_email" {
  description = "The email address of the backend service account."
  value       = google_service_account.backend_sa.email
}

output "service_account_name" {
  description = "The fully-qualified name of the backend service account."
  value       = google_service_account.backend_sa.name
}

output "service_account_id" {
  description = "The unique ID of the backend service account."
  value       = google_service_account.backend_sa.unique_id
}

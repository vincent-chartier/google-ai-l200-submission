output "cloud_run_url" {
  description = "Dev Cloud Run service HTTPS URL."
  value       = module.cinema_outings.cloud_run_url
}

output "artifact_registry_repo" {
  description = "Dev Artifact Registry repository."
  value       = module.cinema_outings.artifact_registry_repo
}

output "storage_bucket_name" {
  description = "Dev Cloud Storage bucket name."
  value       = module.cinema_outings.storage_bucket_name
}

output "service_account_email" {
  description = "Dev IAM service account email."
  value       = module.cinema_outings.service_account_email
}

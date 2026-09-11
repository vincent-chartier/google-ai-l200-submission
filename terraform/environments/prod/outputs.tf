output "cloud_run_url" {
  description = "Production Cloud Run service HTTPS URL."
  value       = module.cinema_outings.cloud_run_url
}

output "artifact_registry_repo" {
  description = "Production Artifact Registry repository."
  value       = module.cinema_outings.artifact_registry_repo
}

output "storage_bucket_name" {
  description = "Production Cloud Storage bucket name."
  value       = module.cinema_outings.storage_bucket_name
}

output "service_account_email" {
  description = "Production IAM service account email."
  value       = module.cinema_outings.service_account_email
}

output "monitoring_dashboard_id" {
  description = "Production Cloud Monitoring dashboard ID."
  value       = module.cinema_outings.monitoring_dashboard_id
}

output "monitoring_alert_id" {
  description = "Production Cloud Monitoring alert policy ID."
  value       = module.cinema_outings.monitoring_alert_id
}

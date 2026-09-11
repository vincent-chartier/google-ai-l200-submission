output "cloud_run_url" {
  description = "The public HTTPS URL of the deployed Cinema Outings Multi-Agent backend."
  value       = module.cloud_run.service_uri
}

output "cloud_run_service_name" {
  description = "The name of the Cloud Run service."
  value       = module.cloud_run.service_name
}

output "service_account_email" {
  description = "The email address of the dedicated least-privilege IAM service account."
  value       = module.iam.service_account_email
}

output "artifact_registry_repo" {
  description = "The Artifact Registry Docker repository URL for building and pushing container images."
  value       = module.registry.repository_url
}

output "storage_bucket_name" {
  description = "The Google Cloud Storage bucket name for session state backups and ticketing assets."
  value       = module.storage.bucket_name
}

output "storage_bucket_url" {
  description = "The gs:// URI of the Cloud Storage bucket."
  value       = module.storage.bucket_url
}

output "secret_id_gemini_key" {
  description = "The Secret Manager secret ID storing the Gemini API key."
  value       = module.secrets.secret_id
}

output "monitoring_dashboard_id" {
  description = "The resource ID of the Google Cloud Monitoring dashboard."
  value       = module.monitoring.dashboard_id
}

output "monitoring_alert_id" {
  description = "The resource ID of the Cloud Monitoring high error rate alert policy."
  value       = module.monitoring.alert_policy_id
}

output "dlp_redactions_metric" {
  description = "The name of the Cloud Logging metric tracking sensitive PII sanitizations."
  value       = module.monitoring.dlp_metric_name
}

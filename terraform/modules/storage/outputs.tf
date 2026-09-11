output "bucket_name" {
  description = "The name of the GCS bucket for data persistence and artifacts."
  value       = google_storage_bucket.app_data.name
}

output "bucket_url" {
  description = "The gs:// URL of the GCS bucket."
  value       = google_storage_bucket.app_data.url
}

output "bucket_self_link" {
  description = "The URI of the created GCS bucket."
  value       = google_storage_bucket.app_data.self_link
}

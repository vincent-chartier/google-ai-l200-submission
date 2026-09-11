output "secret_id" {
  description = "The ID of the Gemini API Key secret."
  value       = google_secret_manager_secret.gemini_api_key.secret_id
}

output "secret_name" {
  description = "The resource name of the Gemini API Key secret."
  value       = google_secret_manager_secret.gemini_api_key.name
}

output "secret_version" {
  description = "The version ID of the Gemini API Key secret if populated."
  value       = length(google_secret_manager_secret_version.gemini_api_key_version) > 0 ? google_secret_manager_secret_version.gemini_api_key_version[0].version : "unversioned"
}

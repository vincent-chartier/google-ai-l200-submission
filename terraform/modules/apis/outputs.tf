output "enabled_apis" {
  description = "List of enabled GCP Service APIs."
  value       = [for s in google_project_service.required_apis : s.service]
}

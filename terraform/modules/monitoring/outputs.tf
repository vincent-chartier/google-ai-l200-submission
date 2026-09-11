output "dashboard_id" {
  description = "The ID of the Cloud Monitoring dashboard."
  value       = google_monitoring_dashboard.multi_agent_dashboard.id
}

output "alert_policy_id" {
  description = "The ID of the high error rate alert policy if enabled."
  value       = length(google_monitoring_alert_policy.high_5xx_errors) > 0 ? google_monitoring_alert_policy.high_5xx_errors[0].id : null
}

output "dlp_metric_name" {
  description = "The name of the log-based metric tracking DLP redactions."
  value       = google_logging_metric.dlp_redactions.name
}

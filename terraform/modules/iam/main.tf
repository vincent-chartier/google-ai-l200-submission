locals {
  sa_id = substr("${var.app_name}-${var.environment}-sa", 0, 30)

  base_roles = [
    "roles/dlp.user",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/storage.objectUser"
  ]

  all_roles = distinct(concat(local.base_roles, var.custom_roles))
}

resource "google_service_account" "backend_sa" {
  project      = var.project_id
  account_id   = local.sa_id
  display_name = "Cinema Outings Multi-Agent SA (${var.environment})"
  description  = "Dedicated least-privilege service account for Cinema Outings Multi-Agent Backend on Cloud Run"
}

resource "google_project_iam_member" "sa_roles" {
  for_each = toset(local.all_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.backend_sa.email}"
}

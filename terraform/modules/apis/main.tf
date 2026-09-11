resource "google_project_service" "required_apis" {
  for_each                   = toset(var.services)
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = var.disable_services_on_destroy
  disable_dependent_services = false
}

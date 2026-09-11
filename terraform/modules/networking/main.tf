resource "google_compute_network" "custom_vpc" {
  count                   = var.enable_vpc_connector ? 1 : 0
  project                 = var.project_id
  name                    = "${var.app_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  description             = "Custom VPC for ${var.app_name} (${var.environment})"
}

resource "google_compute_subnetwork" "custom_subnet" {
  count         = var.enable_vpc_connector ? 1 : 0
  project       = var.project_id
  name          = "${var.app_name}-${var.environment}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.custom_vpc[0].id
  description   = "Primary subnet for ${var.app_name} (${var.environment})"
}

resource "google_vpc_access_connector" "serverless_connector" {
  count         = var.enable_vpc_connector ? 1 : 0
  project       = var.project_id
  name          = substr("${var.app_name}-${var.environment}-conn", 0, 25)
  region        = var.region
  ip_cidr_range = var.connector_cidr
  network       = google_compute_network.custom_vpc[0].name
  min_instances = 2
  max_instances = 3

  depends_on = [google_compute_subnetwork.custom_subnet]
}

output "vpc_network_id" {
  description = "The ID of the custom VPC if created."
  value       = var.enable_vpc_connector ? google_compute_network.custom_vpc[0].id : null
}

output "vpc_connector_id" {
  description = "The ID of the Serverless VPC Access connector if enabled."
  value       = var.enable_vpc_connector ? google_vpc_access_connector.serverless_connector[0].id : null
}

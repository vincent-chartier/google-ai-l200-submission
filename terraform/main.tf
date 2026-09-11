provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required GCP APIs
module "apis" {
  source     = "./modules/apis"
  project_id = var.project_id
}

# 2. Least-Privilege IAM Service Account
module "iam" {
  source      = "./modules/iam"
  project_id  = var.project_id
  app_name    = var.app_name
  environment = var.environment

  depends_on = [module.apis]
}

# 3. Secret Manager for Gemini API Key
module "secrets" {
  source                = "./modules/secrets"
  project_id            = var.project_id
  app_name              = var.app_name
  environment           = var.environment
  gemini_api_key        = var.gemini_api_key
  service_account_email = module.iam.service_account_email
  labels                = var.labels

  depends_on = [module.apis]
}

# 4. Cloud Storage for Session Persistence & Artifacts
module "storage" {
  source                = "./modules/storage"
  project_id            = var.project_id
  app_name              = var.app_name
  environment           = var.environment
  region                = var.region
  service_account_email = module.iam.service_account_email
  labels                = var.labels

  depends_on = [module.apis]
}

# 5. Artifact Registry for Container Images
module "registry" {
  source      = "./modules/registry"
  project_id  = var.project_id
  app_name    = var.app_name
  environment = var.environment
  region      = var.region
  labels      = var.labels

  depends_on = [module.apis]
}

# 6. Networking & Serverless VPC Access (Optional)
module "networking" {
  source               = "./modules/networking"
  project_id           = var.project_id
  app_name             = var.app_name
  environment          = var.environment
  region               = var.region
  enable_vpc_connector = var.enable_vpc_connector

  depends_on = [module.apis]
}

# 7. Cloud Run v2 Multi-Agent Backend Service
locals {
  resolved_image = var.container_image != "" ? var.container_image : "${module.registry.repository_url}/${var.app_name}:latest"
}

module "cloud_run" {
  source                   = "./modules/cloud_run"
  project_id               = var.project_id
  app_name                 = var.app_name
  environment              = var.environment
  region                   = var.region
  container_image          = local.resolved_image
  service_account_email    = module.iam.service_account_email
  min_instances            = var.min_instances
  max_instances            = var.max_instances
  cpu_limit                = var.cpu_limit
  memory_limit             = var.memory_limit
  gemini_api_key_secret_id = module.secrets.secret_id
  gcs_bucket_name          = module.storage.bucket_name
  enable_gcs_volume        = var.enable_gcs_volume
  model_coordinator        = var.model_coordinator
  model_search_reco_deep   = var.model_search_reco_deep
  model_search_reco_fast   = var.model_search_reco_fast
  model_booking            = var.model_booking
  model_housekeeping       = var.model_housekeeping
  allow_unauthenticated    = var.allow_unauthenticated
  vpc_connector_id         = module.networking.vpc_connector_id
  labels                   = var.labels

  depends_on = [module.apis, module.iam, module.secrets, module.storage, module.registry]
}

# 8. Observability: Cloud Monitoring Dashboard & Alerts
module "monitoring" {
  source                 = "./modules/monitoring"
  project_id             = var.project_id
  app_name               = var.app_name
  environment            = var.environment
  cloud_run_service_name = module.cloud_run.service_name
  enable_alerts          = var.enable_monitoring_alerts

  depends_on = [module.apis, module.cloud_run]
}

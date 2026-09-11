# Infrastructure as Code (IaC) - Cinema Outings Multi-Agent Platform

This directory contains production-grade **Terraform** configurations for automated provisioning and lifecycle management of the **Cinema Outings Multi-Agent** system on **Google Cloud Platform (GCP)**.

---

## 🏛️ Infrastructure Architecture

The Terraform configuration follows a modular, least-privilege architecture:

```
                                  ┌───────────────────────────┐
                                  │   Terraform IaC Root      │
                                  │ (environments: dev, prod) │
                                  └─────────────┬─────────────┘
                                                │
         ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
         ▼                  ▼                   ▼                   ▼                  ▼
┌─────────────────┐┌─────────────────┐┌─────────────────┐┌─────────────────┐┌─────────────────┐
│  Service APIs   ││   IAM & Roles   ││ Secret Manager  ││  Cloud Storage  ││Artifact Registry│
│  (14 GCP APIs)  ││ (Least-Priv SA) ││ (Gemini API Key)││ (State & Data)  ││ (Docker Images) │
└─────────────────┘└────────┬────────┘└────────┬────────┘└────────┬────────┘└────────┬────────┘
                            │                  │                  │                  │
                            └──────────────────┼──────────────────┼──────────────────┘
                                               ▼
                                  ┌───────────────────────────┐
                                  │     Cloud Run v2 Engine   │
                                  │ • Multi-Agent FastAPI App │
                                  │ • Health Probes (/health) │
                                  │ • GCS Volume Persistence  │
                                  │ • Tiered Gemini Routing   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │  Monitoring & Telemetry   │
                                  │ • Multi-Agent Dashboard   │
                                  │ • Cloud DLP Log Metric    │
                                  │ • 5xx High Error Alert    │
                                  └───────────────────────────┘
```

---

## 📦 Provisioned Google Cloud Resources

| Module | Resource / Service | Purpose |
|---|---|---|
| **`apis`** | `google_project_service` | Enables 14 GCP APIs (`run`, `dlp`, `aiplatform`, `secretmanager`, `storage`, `cloudtrace`, `logging`, `monitoring`, etc.). |
| **`iam`** | `google_service_account` & `google_project_iam_member` | Creates dedicated `cinema-outings-{env}-sa` with least-privilege roles (`dlp.user`, `secretAccessor`, `aiplatform.user`, `cloudtrace.agent`, `logging.logWriter`, `monitoring.metricWriter`, `storage.objectUser`). |
| **`secrets`** | `google_secret_manager_secret` | Stores Gemini API keys securely with automated IAM accessor bindings. |
| **`storage`** | `google_storage_bucket` | Creates encrypted GCS bucket for persistent database files, ticket exports, and session history with versioning & lifecycle rules. |
| **`registry`**| `google_artifact_registry_repository` | Docker container registry for backend application builds. |
| **`cloud_run`**| `google_cloud_run_v2_service` | Deploys backend multi-agent service with CPU/RAM allocation, auto-scaling, startup/liveness health probes, environment flags, and Secret Manager bindings. |
| **`networking`**| `google_compute_network` & `google_vpc_access_connector` | Optional custom VPC and Serverless VPC Access connector for private network connectivity. |
| **`monitoring`**| `google_monitoring_dashboard` & `alert_policy` | Real-time observability dashboard (latency percentiles, CPU/RAM utilization, request throughput, Cloud DLP PII sanitization counts) and 5xx error alerting. |

---

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Root orchestration of modules
├── variables.tf               # Root input variables with validation
├── outputs.tf                 # Root outputs (service URL, SA, repository, bucket)
├── versions.tf                # Provider versions (google ~> 5.30, random ~> 3.5)
├── terraform.tfvars.example   # Example variable definitions
├── README.md                  # This documentation
├── modules/
│   ├── apis/                  # GCP service API enabler
│   ├── iam/                   # Least-privilege IAM service account & bindings
│   ├── secrets/               # Secret Manager configuration
│   ├── storage/               # GCS persistent bucket with lifecycle
│   ├── registry/              # Artifact Registry Docker repository
│   ├── networking/            # Custom VPC & Serverless VPC Connector
│   ├── cloud_run/             # Cloud Run v2 service definition
│   └── monitoring/            # Cloud Monitoring dashboard, alerts, & DLP metric
└── environments/
    ├── dev/                   # Development stage (0 min instances, 1 CPU, 1Gi RAM)
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── terraform.tfvars
    │   └── outputs.tf
    └── prod/                  # Production stage (warm instances, 2 CPU, 2Gi RAM)
        ├── main.tf
        ├── variables.tf
        ├── terraform.tfvars
        └── outputs.tf
```

---

## 🚀 Quickstart Deployment

### 1. Prerequisites
- **Terraform** >= 1.5.0 installed
- **Google Cloud SDK (`gcloud`)** installed and authenticated
- Target GCP project with Owner or Editor + Security Admin permissions

### 2. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_GCP_PROJECT_ID
```

### 3. Deploy Dev Environment
```bash
cd terraform/environments/dev

# 1. Initialize Terraform
terraform init

# 2. Review the execution plan
terraform plan

# 3. Apply infrastructure
terraform apply
```

### 4. Deploy Production Environment
```bash
cd terraform/environments/prod

# 1. Initialize Terraform
terraform init

# 2. Review the execution plan
terraform plan

# 3. Apply infrastructure
terraform apply
```

---

## ⚙️ Key Configuration Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `project_id` | `string` | `"vchartier-project"` | GCP Project ID |
| `region` | `string` | `"us-central1"` | Target Google Cloud region |
| `app_name` | `string` | `"cinema-outings"` | Resource name prefix |
| `environment` | `string` | `"dev"` | Target environment (`dev`, `staging`, `prod`) |
| `min_instances` | `number` | `0` (dev) / `1` (prod) | Minimum warm container instances |
| `max_instances` | `number` | `2` (dev) / `10` (prod) | Maximum autoscaling limit |
| `cpu_limit` | `string` | `"1"` (dev) / `"2"` (prod) | CPU limit per container |
| `memory_limit` | `string` | `"1Gi"` (dev) / `"2Gi"` (prod) | RAM limit per container |
| `gemini_api_key` | `string` | `""` | Gemini API key (stored in Secret Manager) |
| `allow_unauthenticated` | `bool` | `true` | Public access to Cloud Run service |
| `enable_gcs_volume` | `bool` | `false` (dev) / `true` (prod) | Mount GCS bucket via Cloud Run volume |
| `enable_vpc_connector` | `bool` | `false` | Enable Serverless VPC Access connector |

---

## 🔐 Security & Compliance

- **No Hardcoded Secrets**: Secrets such as `GEMINI_API_KEY` are provisioned directly in Google Secret Manager and injected securely via Cloud Run native secret references.
- **Least Privilege Principle**: The Cloud Run runtime identity does not use the default Compute Engine service account. A dedicated service account is granted granular roles strictly required for DLP, Vertex AI, Tracing, Logging, and Storage.
- **Public Access Prevention**: All storage buckets enforce `public_access_prevention = "enforced"` and `uniform_bucket_level_access = true`.
- **Sensitive Data Protection (DLP)**: The infrastructure configures log-based metrics for audit logging of detected PII redactions.

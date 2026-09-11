# Cinema Outings AI: Multi-Agent Mobile Application

A full-stack, AI-agent powered mobile application designed to manage cinema outings for end users. The frontend is built with **Flutter** using the dynamic **A2UI (Agent-to-UI)** declarative protocol, and the backend consists of a multi-agent system built with **Google ADK (Agent Development Kit)**, **Gemini**, and **FastAPI**.

---

## 🏛️ Architecture Overview

The system is partitioned into two primary components:
1. **Frontend (Flutter)**: A cross-platform mobile client featuring an A2UI dynamic renderer that converts declarative JSON specifications into native widgets (movie discovery cards, interactive seat map selector, digital ticket boarding passes, and calendar invitations).
2. **Backend (Python + Google ADK)**: A multi-agent service hosting 4 specialized agents connected via **Session State / Memory Passing**:
   - **Outing Coordinator Agent (Supervisor)**: Orchestrates conversational dialogue, detects user intent, and packages A2UI responses.
   - **Search & Recommendation Agent**: Leverages **MCP (Model Context Protocol)** for live internet discovery of cinema screenings, filtering against watched movies and boosting taste matches using favorite movies passed via session memory.
   - **Booking Agent**: Uses **custom transaction functions** to inspect auditorium seating grids, temporarily hold seats, execute payment transactions, and issue tickets with QR codes.
   - **Housekeeping Agent**: Maintains user watched movie history and favorite movie preferences in shared session memory, and dispatches **calendar invites** (`.ics` format and Google Calendar deep links).

```
                      ┌─────────────────────────────────────────┐
                      │         Flutter Mobile Client           │
                      │  (A2UI Renderer + Chat Canvas + Theme)  │
                      └────────────────────┬────────────────────┘
                                           │
                                    A2UI Protocol
                                   (REST / JSON)
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          FastAPI Backend Gateway        │
                      │   (/api/v1/agent/chat, /a2ui/action)    │
                      └────────────────────┬────────────────────┘
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
┌─────────────────────────┐                                 ┌─────────────────────────┐
│ Outing Coordinator      │                                 │ Shared Session State    │
│ Agent (Supervisor/Host) │ ◄──────── Memory Passing ─────► │ • favorite_movies       │
└────────────┬────────────┘                                 │ • seen_movies           │
             │                                              │ • active_booking        │
             ├──────────────────────┬───────────────────────┤ • active_reservation    │
             ▼                      ▼                       ▼ └─────────────────────────┘
┌─────────────────────────┐┌─────────────────────────┐┌─────────────────────────┐
│ Search & Reco Agent     ││ Booking Agent           ││ Housekeeping Agent      │
│ • MCP Web Search Tools  ││ • Custom Transactions   ││ • Watched Movie History │
│ • Taste Matching Memory ││ • Seat Hold & Payment   ││ • Favorites Memory      │
│ • Duplicate Avoidance   ││ • QR Ticket Pass        ││ • Calendar Invites      │
└────────────┬────────────┘└────────────┬────────────┘└────────────┬────────────┘
             ▼                          ▼                          ▼
┌─────────────────────────┐┌─────────────────────────┐┌─────────────────────────┐
│ MCP Movie Search Server ││ Cinema Ticketing API    ││ iCalendar (.ics) Engine │
│ (mcp<2 stdio server)    ││ (Custom Functions)      ││ & Google Calendar API   │
└─────────────────────────┘└─────────────────────────┘└─────────────────────────┘
```

---

## 🤖 The 4 Agents & Implementation

| Agent | Technology | Role & Key Features |
|---|---|---|
| **1. Outing Coordinator** | Google ADK (`LlmAgent`) | Top-level host; routes user requests, synchronizes memory passing, and formats outgoing A2UI payloads. |
| **2. Search & Reco** | Google ADK + MCP (`McpToolset`) | Queries live internet movie screenings via FastMCP; cross-references `session.state["favorite_movies"]` and avoids `session.state["seen_movies"]`. |
| **3. Booking** | Google ADK + Custom Functions | Executes ticket transactions: `get_seat_availability`, `hold_seats_reservation`, `process_ticket_payment`, and `cancel_booking`. |
| **4. Housekeeping** | Google ADK + Memory Manager | Tracks watched archive, manages user favorites list passed to Reco, and generates calendar invites (`.ics` / Google Calendar). |

---

## 🧠 Strategic Model Routing & Tiered Selection

The system utilizes semantic routing to assign each agent request to the optimal Gemini model tier based on reasoning complexity, latency requirements, and cost:

| Model Tier | Model | Agents / Roles | Rationale |
|---|---|---|---|
| **Deep Reasoning** | `gemini-2.5-pro` | Search & Reco (Nuanced picks) | Nuanced taste matching, stylistic director comparisons, and complex multi-criteria film reasoning. |
| **Fast / Conversational** | `gemini-2.5-flash` | Coordinator, Search & Reco (Catalog) | Sub-second latency for intent classification, user chat, and real-time screening searches. |
| **Deterministic** | `gemini-2.5-flash` | Booking Agent | Strict schema following and zero-temperature execution for reservation holds and payment transactions. |
| **Lite** | `gemini-2.0-flash-lite` | Housekeeping Agent | Ultra-low cost profile memory updates, watched history checks, and `.ics` calendar invitation generation. |

---

## 🛡️ Security Guardrails & Evaluation Plugins

Integrated via Google ADK's native `BasePlugin` lifecycle hooks:

### 1. Security Guardrails (`backend/plugins/security_guardrails.py`)
- **`InputSecurityGuardrailPlugin`**: Intercepts prompt injections, jailbreak attempts, and system override attacks before agent execution. Redacts credit card numbers and sensitive PII.
- **`BookingSafetyGuardrailPlugin`**: Enforces valid unexpired reservation holds before payment execution, stops replay attacks / double charges, and rate-limits seat hold requests.
- **`A2UIValidationGuardrailPlugin`**: Validates that all emitted dynamic UI components strictly adhere to the A2UI schema contract.

### 2. Evaluation & Telemetry Plugins (`backend/plugins/evaluation_plugins.py`)
- **`RecommendationEvaluationPlugin`**: Automatically verifies negative constraints (**0% duplicate seen movies**) and confirms taste explanations ground themselves in actual user favorites.
- **`ToolSequenceEvaluationPlugin`**: Asserts that multi-agent transaction steps follow the required order (`check_availability` -> `hold_seats` -> `process_payment` -> `calendar_invite`).
- **`LatencyAndCostTelemetryPlugin`**: Tracks duration, token throughput, and estimated API cost per model tier (accessible via `/api/v1/telemetry`).


---

## 📱 A2UI (Agent-to-UI) Protocol

The backend agents communicate with the Flutter frontend using the declarative **A2UI Protocol**:
- **`movie_card`**: Film backdrop, runtime, genre tags, taste-matching badges (*"Directed by Christopher Nolan, who directed your favorite: Interstellar"*), and showtime selection buttons.
- **`seat_map_selector`**: 2D curved screen seating chart with selectable seats, row labels, VIP tiers, and real-time subtotal pricing.
- **`ticket_pass`**: Digital boarding pass featuring cinema venue, hall, seat numbers, total price, and scannable QR token.
- **`calendar_invite_card`**: Event invitation allowing one-click export to Google Calendar or downloading standard `.ics` files.
- **`seen_history_list`**: Interactive list displaying user's cinema history and favorites.

---

## 📂 Project Structure

```
google-ai-l200-submission/
├── backend/
│   ├── app.py                      # FastAPI server with A2UI endpoints
│   ├── config.py                   # Environment & Gemini configuration
│   ├── requirements.txt            # Python dependencies
│   ├── agents/
│   │   ├── coordinator_agent.py   # Supervisor / Host Agent
│   │   ├── search_reco_agent.py   # Search & Recommendation Agent (MCP)
│   │   ├── booking_agent.py       # Booking Agent (Custom Transactions)
│   │   └── housekeeping_agent.py  # Housekeeping Agent (History & Calendar)
│   ├── routers/
│   │   └── semantic_router.py     # Intent classification & Gemini tiered model router
│   ├── plugins/
│   │   ├── security_guardrails.py # Input injection defense, hold validation, A2UI contract
│   │   └── evaluation_plugins.py  # Duplicate avoidance, tool sequence, cost telemetry
│   ├── mcp_servers/
│   │   └── movie_search_server.py # FastMCP Movie Discovery Server
│   ├── tools/
│   │   ├── booking_transactions.py # Custom seat & ticketing functions
│   │   └── calendar_tools.py      # .ics & calendar link generator
│   ├── protocols/
│   │   └── a2ui.py                # A2UI Protocol schemas & builders
│   ├── state/
│   │   └── memory_manager.py      # Session memory & state passing
│   └── tests/
│       ├── test_agents.py         # Multi-agent flow & memory tests
│       ├── test_mcp.py            # MCP server tool tests
│       ├── test_a2ui.py           # A2UI protocol serialization tests
│       ├── test_model_routing.py  # Intent & model tier routing tests
│       ├── test_guardrails.py     # Security & transaction guardrail tests
│       ├── test_evaluations.py    # Negative constraint & telemetry tests
│       └── test_terraform.py      # Terraform IaC & containerization test suite
├── terraform/                     # Infrastructure as Code (IaC)
│   ├── main.tf                    # Root module orchestration
│   ├── variables.tf               # Root input variables
│   ├── outputs.tf                 # Root infrastructure outputs
│   ├── versions.tf                # Provider version constraints
│   ├── terraform.tfvars.example   # Sample configuration variables
│   ├── README.md                  # Comprehensive IaC guide
│   ├── modules/                   # Reusable infrastructure modules
│   │   ├── apis/                  # 14 Google Cloud APIs
│   │   ├── iam/                   # Least-privilege Service Account & IAM
│   │   ├── secrets/               # Secret Manager for Gemini API key
│   │   ├── storage/               # Encrypted GCS persistence bucket
│   │   ├── registry/              # Artifact Registry Docker repository
│   │   ├── networking/            # Custom VPC & Serverless VPC Connector
│   │   ├── cloud_run/             # Cloud Run v2 Multi-Agent service
│   │   └── monitoring/            # Cloud Monitoring dashboard, alerts & DLP metric
│   └── environments/              # Staged deployment configurations
│       ├── dev/                   # Cost-optimized development environment
│       └── prod/                  # High-availability production environment
├── frontend/
│   ├── pubspec.yaml                # Flutter project configuration
│   ├── lib/
│   │   ├── main.dart               # App entry point & bottom navigation
│   │   ├── theme/cinema_theme.dart # Dark cinema outing theme
│   │   ├── models/a2ui_models.dart # Dart A2UI models
│   │   ├── services/agent_client.dart # HTTP client for backend agents
│   │   ├── widgets/
│   │   │   ├── a2ui_renderer.dart  # Dynamic A2UI component engine
│   │   │   ├── movie_card_widget.dart
│   │   │   ├── seat_map_widget.dart
│   │   │   ├── ticket_pass_widget.dart
│   │   │   ├── calendar_invite_widget.dart
│   │   │   └── seen_history_widget.dart
│   │   └── screens/
│   │       ├── outing_chat_screen.dart # AI conversational canvas
│   │       └── seen_history_screen.dart # Watched archive & memory profile
│   └── test/
│       └── a2ui_renderer_test.dart # Flutter widget tests
├── Dockerfile                     # Production container image definition
├── .dockerignore                  # Build context exclusions
├── cloudbuild.yaml                # Cloud Build automated CI/CD pipeline
└── README.md
```

---

## 🏗️ Infrastructure as Code (Terraform) & Cloud Deployment

The application features full **Infrastructure as Code (IaC)** using **Terraform** to provision enterprise GCP resources:

### Provisioned GCP Architecture:
- **Cloud Run v2**: Serverless container runtime hosting the FastAPI multi-agent backend with startup/liveness health probes (`/api/v1/health`) and autoscaling.
- **Artifact Registry**: Private Docker repository (`cinema-outings-{env}-repo`) for container images.
- **Secret Manager**: Secure, encrypted storage and automatic injection of the `GEMINI_API_KEY`.
- **Cloud Storage (GCS)**: Encrypted bucket with object versioning, public access prevention, and lifecycle retention policies for SQLite session database persistence and ticket artifacts.
- **Least-Privilege IAM**: Dedicated Service Account (`cinema-outings-{env}-sa`) restricted strictly to Cloud DLP, Secret Manager, Vertex AI, Cloud Trace, and Cloud Logging.
- **Cloud Monitoring & Observability**: Real-time dashboard tracking agent latency percentiles, container CPU/RAM utilization, request throughput, and a custom log metric for Cloud DLP PII sanitizations.
- **Staged Environments**: Out-of-the-box `dev` (scaled down, zero min instances) and `prod` (warm instances, GCS volume mount, alerting) stages.

### Terraform Quickstart:
```bash
# Navigate to the target environment (e.g. dev)
cd terraform/environments/dev

# Initialize providers and modules
terraform init

# Plan infrastructure changes
terraform plan

# Deploy infrastructure to Google Cloud
terraform apply
```

For complete IaC details and variable documentation, see [terraform/README.md](file:///home/vchartier/google-ai-l200-submission/terraform/README.md).

---

## 🚀 Getting Started

### 1. Backend Setup & Execution
```bash
# Sourcing environment (sets GEMINI_API_KEY from ~/gemini_key.txt)
source /home/vchartier/companion-python/set_env.sh

# Run all backend unit, integration, and IaC validation tests
PYTHONPATH=. /home/vchartier/companion-python/venv/bin/pytest backend/tests/ -v

# Launch backend FastAPI server
PYTHONPATH=. /home/vchartier/companion-python/venv/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

### 2. Frontend (Flutter) Setup & Execution
```bash
cd frontend

# Get Flutter dependencies
flutter pub get

# Run Flutter widget test suite
flutter test

# Run the Flutter mobile app
flutter run
```


---
title: "Cross-Project ELT Pipeline Implementation Walkthrough"
project_id: "coc-elt"
nyutu_uuid: 81a47ae0-074b-4530-b1e6-2a3f78c934d0
artifact_type: "Architectural Decision"
tags:
  - "gcp"
  - "terraform"
  - "elt-pipeline"
  - "clash-of-clans"
  - "walkthrough"
source_uri: "specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md"
---

# Cross-Project ELT Pipeline Implementation Walkthrough

### Execution Context
- **Timestamp**: 2026-07-11T13:12:35-05:00
- **Objective**: Implement a cloud-native, secure, and production-ready cross-project ELT pipeline on Google Cloud Platform to extract Clash of Clans API data, load it to Google BigQuery, and prepare it for Dataform transformation.

---

### Executed Commands
The following critical commands were executed to establish dependencies, run tests, and manage state:
1. `uv sync` - Synchronized Python environment and installed requirements.
2. `uv run pytest` - Ran all unit tests (7/7 passed).
3. Checkbox status updates in `specs/coc-elt_20260711_cross-project-elt-pipeline_implementation_plan.md`.

---

### State Mutations
The following files were created or modified during the feature implementation:

- **Created**:
  - `dataform/dataform.json`
  - `dataform/package.json`
  - `dataform/definitions/sources.js`
  - `terraform/backend.tf`
  - `terraform/variables.tf`
  - `terraform/main.tf`
  - `terraform/network.tf`
  - `terraform/security.tf`
  - `terraform/bigquery.tf`
  - `terraform/compute.tf`
  - `terraform/backend_bucket.tf`
  - `terraform/services.tf`
  - `terraform/cicd.tf`
  - `specs/coc-elt_20260712_enable-gcp-apis_implementation_plan.md`
  - `specs/coc-elt_20260712_provision-remaining-resources_implementation_plan.md`
  - `specs/coc-elt_20260712_provision-remaining-resources_walkthrough.md`
  - `src/coc_elt/config.py`
  - `src/coc_elt/api_client.py`
  - `src/coc_elt/bq_client.py`
  - `src/coc_elt/main.py`
  - `src/coc_elt/logging_config.py`
  - `tests/test_api_client.py`
  - `tests/test_bq_client.py`
  - `tests/test_logging.py`
  - `tests/test_main.py`
  - `Dockerfile`
  - `cloudbuild.yaml`

- **Modified**:
  - `pyproject.toml`
  - `specs/coc-elt_20260711_cross-project-elt-pipeline_implementation_plan.md`

---

### Architectural Decisions (ADR) and SOLID
1. **SOLID Principles**:
   - **Single Responsibility Principle (SRP)**: Separated setting values (`config.py`), structured logging formatters (`logging_config.py`), external api client connections (`api_client.py`), BigQuery insertions (`bq_client.py`), and pipeline execution orchestration (`main.py`).
   - **Interface Segregation Principle (ISP)**: Clients expose only highly cohesive methods (`fetch_clan`, `fetch_members`, etc.).
   - **Dependency Inversion Principle (DIP)**: Used Pydantic settings configuration injection and decoupled Clients using client wrapper instances.
2. **Infrastructure & Observability**:
   - Egress traffic routed through Cloud NAT with a static IP address to support IP-based whitelisting of the Clash of Clans API.
   - Cloud Workflows acts as the coordinator, decoupling Cloud Run extraction from Dataform transformation.
   - Structured JSON logging: Implemented a custom JSON formatter on the root logger, formatting logs as JSON to stdout. This enables GCP Cloud Logging to parse fields (`severity`, `message`, `timestamp`, `logging.googleapis.com/sourceLocation`, and custom `extra_args`) natively for structured search and advanced querying.
3. **Database Schema Strategy**:
   - Implemented a resilient, schema-on-read approach in the BigQuery Bronze layer using a two-column schema: `extracted_at` (TIMESTAMP) and `payload` (JSON).

---

### Validation Artifacts
The unit tests execute successfully within the localized Python 3.13 env:
```text
============================= test session starts ==============================
platform linux -- Python 3.13.9, pytest-9.1.1, pluggy-1.6.0
collected 9 items

tests/test_api_client.py ....                                            [ 44%]
tests/test_bq_client.py ..                                               [ 66%]
tests/test_logging.py ..                                                 [ 88%]
tests/test_main.py .                                                     [100%]

============================== 9 passed in 0.18s ===============================
```

---

### Technical Debt
- **Credentials in Non-Prod**: Clash of Clans API keys are expected to be injected in GCP Secret Manager. For local dev/test, dummy mock values are utilized.
- **Workflow Error Routing**: Workflows will raise execution errors and terminate if the Cloud Run Job fails, but there is no notification system (e.g. Pub/Sub or Slack alerts) integrated yet.

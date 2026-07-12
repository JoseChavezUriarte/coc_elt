---
title: "Provision Dedicated Service Account for Dataform with Eventual Consistency Mitigation Walkthrough"
project_id: "coc_elt"
nyutu_uuid: "20790b99-a316-43b9-bb80-c11df5d4b31a"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_revised_dataform_runner_sa_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T14:10:00-05:00
- **Objective**: Provision a dedicated service account `google_service_account.dataform_runner` for Dataform inside the Data Project (`var.data_project_id`), introduce eventual consistency mitigation via a 60-second `time_sleep`, and decouple developer access bindings from the repository lifecycle.

### Executed Commands
- `terraform init` to download the `hashicorp/time` provider.
- `terraform validate` inside the `terraform/` directory.

### State Mutations
- **Created**:
  - [specs/coc_elt_20260712_revised_dataform_runner_sa_walkthrough.md](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc_elt_20260712_revised_dataform_runner_sa_walkthrough.md)
- **Modified**:
  - [terraform/security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):
    - Added dedicated `google_service_account.dataform_runner` inside the Data Project.
    - Granted `roles/bigquery.dataEditor` (marked as tech debt at project-level) and `roles/bigquery.jobUser` on the Data Project.
    - Granted `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator` to the Dataform service agent.
    - Refactored `google_service_account_iam_member.developer_sa_user` to point to the new service account (with no dependencies or `depends_on`).
    - Added `time_sleep.wait_for_dataform_iam` resource configured for a 60-second wait after IAM bindings creation.
    - Removed old `dataform_sa_user` and `dataform_sa_token_creator` targeting `elt_runner.name`.
  - [terraform/bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf):
    - Updated `google_dataform_repository.coc_elt` to reference the new runner SA email.
    - Updated `depends_on` list to reference only `time_sleep.wait_for_dataform_iam`.
  - [specs/coc_elt_20260712_revised_dataform_runner_sa_implementation_plan.md](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc_elt_20260712_revised_dataform_runner_sa_implementation_plan.md):
    - Checked off tasks T1 to T11.

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Separating the service account roles of ELT ingestion runner (`coc-elt-runner` in compute project) and Dataform workflow engine (`coc-dataform-runner` in data project) ensures each credential possesses only the minimum necessary privileges for its scope.
- **Least Privilege Principle**: Restricting Dataform runner permissions to BigQuery read/write (dataEditor and jobUser) instead of broader project editor/owner privileges.
- **Eventual Consistency Mitigation**: The 60-second delay introduced via `time_sleep` prevents Dataform repository creation from failing due to GCP IAM propagation delays.
- **Decoupling**: Decoupled developer-specific IAM roles (`google_service_account_iam_member.developer_sa_user`) from the repository's direct dependencies list.

### Validation Artifacts
- The configuration was verified by running `terraform validate` in the `terraform/` directory, which successfully returned `Success! The configuration is valid.`.

### Technical Debt
- Project-level assignment of `roles/bigquery.dataEditor` to the Dataform runner is a known technical debt item. It must be refactored to dataset-level IAM assignments once medallion datasets are fully codified.

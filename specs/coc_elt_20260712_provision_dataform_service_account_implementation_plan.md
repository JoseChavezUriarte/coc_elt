---
title: "Provision Dedicated Service Account for Dataform in Data Project"
project_id: "coc_elt"
nyutu_uuid: "31af75d0-0b1c-4112-8ea9-50efb76cf79b"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_provision_dataform_service_account_implementation_plan.md"
---

# Implementation Plan - Provision Dedicated Service Account for Dataform in Data Project

This implementation plan details the steps to provision a dedicated service account `google_service_account.dataform_runner` for Dataform inside the Data Project (`var.data_project_id`), grant it required BigQuery and IAM permissions, refactor existing developer access, and update the Dataform repository configuration.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Dataform Runner Service Account Definition)**: The system MUST declare the dedicated service account `google_service_account.dataform_runner` inside the Data Project (`var.data_project_id`) in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R2 (BigQuery Permissions for Dataform Runner)**: The system MUST grant `roles/bigquery.dataEditor` and `roles/bigquery.jobUser` to `google_service_account.dataform_runner` in the Data Project using `google_project_iam_member` resources in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R3 (Dataform Service Agent Access to Runner)**: The system MUST grant `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator` to the Dataform service agent of the Data project (`service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com`) on the new `dataform_runner` service account using `google_service_account_iam_member` resources in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R4 (Developer IAM Mapping)**: The system MUST refactor `google_service_account_iam_member.developer_sa_user` to grant `roles/iam.serviceAccountUser` on `google_service_account.dataform_runner` (instead of `elt_runner`) for emails in `var.dataform_developer_emails` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R5 (Clean up obsolete permissions)**: The system MUST remove the old `dataform_sa_user` and `dataform_sa_token_creator` resource blocks targeting `elt_runner` from [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R6 (Dataform Repository Configuration)**: The system MUST update `google_dataform_repository.coc_elt` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) to use `google_service_account.dataform_runner.email` for the `service_account` argument. (Ubiquitous)
- **R7 (Dataform Repository Dependencies)**: The system MUST update `depends_on` of `google_dataform_repository.coc_elt` to reference `google_service_account_iam_member.dataform_runner_sa_user`, `google_service_account_iam_member.dataform_runner_sa_token_creator`, and `google_service_account_iam_member.developer_sa_user` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf). (Ubiquitous)
- **R8 (Terraform Validation)**: WHEN the Terraform command `terraform validate` is run in the `terraform` directory, the system MUST return a successful validation status without any syntax or configuration errors. (Event)
- **R9 (Error Handling)**: IF any of the required resource references or arguments are misconfigured, THEN the system MUST fail validation during `terraform validate`. (Unwanted)
- **R10 (Edge Case - Empty Developers List)**: WHILE `var.dataform_developer_emails` is empty, the system MUST successfully plan and apply the configuration without attempting to create any developer service account IAM bindings. (State)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
- [terraform/security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) (Modified to define the new service account, grant permissions, refactor developer access, and remove old resources)
- [terraform/bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) (Modified to update the Dataform repository service account and its dependencies)

### New Signatures
We will declare the new resources in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):

```hcl
resource "google_service_account" "dataform_runner" {
  account_id   = "coc-dataform-runner"
  display_name = "Clash of Clans Dataform Runner SA"
  project      = var.data_project_id
}

resource "google_project_iam_member" "dataform_runner_bq_data_editor" {
  project = var.data_project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dataform_runner.email}"
}

resource "google_project_iam_member" "dataform_runner_bq_job_user" {
  project = var.data_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dataform_runner.email}"
}

resource "google_service_account_iam_member" "dataform_runner_sa_user" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "dataform_runner_sa_token_creator" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}
```

We will refactor the existing `developer_sa_user` resource in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) to target the new service account:

```hcl
resource "google_service_account_iam_member" "developer_sa_user" {
  for_each           = var.dataform_developer_emails
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value}"
}
```

We will delete these resource blocks from [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):
- `google_service_account_iam_member.dataform_sa_user`
- `google_service_account_iam_member.dataform_sa_token_creator`

We will update [google_dataform_repository.coc_elt](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf#L39-L51) in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf):

```hcl
resource "google_dataform_repository" "coc_elt" {
  provider        = google-beta
  project         = var.data_project_id
  region          = var.region
  name            = "coc-elt"
  service_account = google_service_account.dataform_runner.email

  depends_on = [
    google_service_account_iam_member.dataform_runner_sa_user,
    google_service_account_iam_member.dataform_runner_sa_token_creator,
    google_service_account_iam_member.developer_sa_user,
  ]
}
```

### Error Handling
- Relying on Terraform CLI compilation and verification of block types and attributes.
- If references are invalid (e.g. referencing `google_service_account_iam_member.dataform_sa_user` which was removed), `terraform validate` will catch them.

### Discarded Alternatives
- **Alternative 1**: Granting project-level Owner or Editor role to the Dataform runner service account.
  - *Why discarded*: Violates the principle of least privilege. Granting specific roles (`roles/bigquery.dataEditor`, `roles/bigquery.jobUser`) in the Data project is more secure and satisfies the data-access requirements without exposing other project resources.
- **Alternative 2**: Continuing to use the `elt_runner` service account for Dataform repository execution.
  - *Why discarded*: The `elt_runner` service account is hosted in the Compute project and handles ELT execution (e.g. fetching API data, running workflows). Reusing it for Dataform in the Data project couples the privileges of extraction/orchestration with transformation. Separating them into dedicated service accounts improves security boundaries.

## 3. Implementation Tasks (Concrete STEPS)

- [ ] T1 — Declare the dedicated service account `google_service_account.dataform_runner` inside the Data Project in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T2 — Grant `roles/bigquery.dataEditor` and `roles/bigquery.jobUser` to `google_service_account.dataform_runner` via `google_project_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T3 — Grant `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator` to the Dataform service agent of the Data project on the new `dataform_runner` service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T4 — Refactor `google_service_account_iam_member.developer_sa_user` to point to `google_service_account.dataform_runner.name` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T5 — Remove obsolete `google_service_account_iam_member.dataform_sa_user` and `google_service_account_iam_member.dataform_sa_token_creator` resource blocks from [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T6 — Update `google_dataform_repository.coc_elt` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) to use the new service account email and reference the new IAM member resources in `depends_on`.
- [ ] T7 — Run `terraform validate` inside `terraform/` directory to verify the configuration correctness.

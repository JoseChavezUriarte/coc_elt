---
title: "Provision Dedicated Service Account for Dataform with Eventual Consistency Mitigation"
project_id: "coc_elt"
nyutu_uuid: "11ef8915-556f-45ec-a695-038c6b433762"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_dataform_runner_service_account_implementation_plan.md"
---

# Revised Implementation Plan - Provision Dedicated Service Account for Dataform with Eventual Consistency Mitigation

This implementation plan details the architectural and procedural changes to provision a dedicated service account `google_service_account.dataform_runner` for Dataform inside the Data Project (`var.data_project_id`), mitigate GCP eventual consistency issues using a 60-second time sleep, and decouple developer access permissions from the core Dataform DAG deployment.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1**: The system MUST declare the dedicated service account `google_service_account.dataform_runner` inside the Data Project (`var.data_project_id`) in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R2**: The system MUST grant `roles/bigquery.dataEditor` to `google_service_account.dataform_runner` in the Data Project using `google_project_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R3**: The system MUST grant `roles/bigquery.jobUser` to `google_service_account.dataform_runner` in the Data Project using `google_project_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R4**: The system MUST grant `roles/iam.serviceAccountUser` to the Dataform service agent of the Data project on the `google_service_account.dataform_runner` service account using `google_service_account_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R5**: The system MUST grant `roles/iam.serviceAccountTokenCreator` to the Dataform service agent of the Data project on the `google_service_account.dataform_runner` service account using `google_service_account_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R6**: The system MUST declare a `time_sleep.wait_for_dataform_iam` resource with a `create_duration` of "60s" in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R7**: The system MUST configure `time_sleep.wait_for_dataform_iam` to explicitly depend on the IAM bindings for Dataform service agent `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator`.
- **R8**: The system MUST refactor `google_service_account_iam_member.developer_sa_user` to point to the new `dataform_runner` service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R9**: The system MUST configure `google_service_account_iam_member.developer_sa_user` using `for_each = var.dataform_developer_emails` without any `depends_on` or dependencies on the Dataform repository in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R10**: The system MUST remove the old `dataform_sa_user` and `dataform_sa_token_creator` resource blocks that were on `elt_runner` from [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- **R11**: The system MUST configure `google_dataform_repository.coc_elt` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) to use `google_service_account.dataform_runner.email` for its `service_account` argument.
- **R12**: The system MUST configure the `depends_on` block of `google_dataform_repository.coc_elt` to reference ONLY `time_sleep.wait_for_dataform_iam` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
- **R13**: WHEN the Terraform command `terraform validate` is run in the `terraform/` directory, the system MUST return a successful validation status.
- **R14**: IF any resource declaration or reference is invalid THEN the system MUST fail the `terraform validate` check.

## 2. Technical Decisions (HOW it will be built)

### Affected Files
- [terraform/security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf): Declare the new service account, grant permissions, refactor developer access, remove old resources, and add the sleep wait.
- [terraform/bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf): Update Dataform repository to reference the new service account email and set its `depends_on` to only reference `time_sleep.wait_for_dataform_iam`.

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

resource "time_sleep" "wait_for_dataform_iam" {
  create_duration = "60s"

  depends_on = [
    google_service_account_iam_member.dataform_runner_sa_user,
    google_service_account_iam_member.dataform_runner_sa_token_creator
  ]
}
```

We will refactor `google_service_account_iam_member.developer_sa_user` to point to the new service account name in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):

```hcl
resource "google_service_account_iam_member" "developer_sa_user" {
  for_each           = var.dataform_developer_emails
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value}"
}
```

We will remove the obsolete resources in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):
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
    time_sleep.wait_for_dataform_iam
  ]
}
```

### Technical Note: Project-Level BigQuery Data Editor Refactoring
> [!NOTE]
> Currently, `roles/bigquery.dataEditor` is applied to `google_service_account.dataform_runner` at the project level. This is done because the Medallion architecture datasets (bronze, silver, gold) are not fully codified as distinct resources in Terraform. Once the dataset boundaries are codified, this permission MUST be refactored to dataset-level bindings via `google_bigquery_dataset_iam_member` to enforce least privilege.

### Error Handling
- Relying on Terraform compile-time static checks to verify syntax, dependencies, and reference correctness via `terraform validate`.
- Eventual consistency is mitigated by introducing `time_sleep.wait_for_dataform_iam` to wait 60 seconds after creating the required service agent access permissions.

### Discarded Alternatives
- **Alternative 1: Adding developer IAM binding to the repository `depends_on` list.**
  - *Why discarded*: Decoupling developer service account mapping from the repository deployment sequence prevents the repository deployment from depending on changes in developer access list.
- **Alternative 2: Granting project-level Editor or Owner access to the Dataform service account.**
  - *Why discarded*: Violates the principle of least privilege. Specifying `roles/bigquery.dataEditor` and `roles/bigquery.jobUser` is sufficient and matches required scopes.

## 3. Implementation Tasks (Concrete STEPS)

- [ ] T1 — Declare `google_service_account.dataform_runner` inside the Data Project in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T2 — Grant `roles/bigquery.dataEditor` to the new runner service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T3 — Grant `roles/bigquery.jobUser` to the new runner service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T4 — Grant `roles/iam.serviceAccountUser` to the Dataform service agent on the new runner service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T5 — Grant `roles/iam.serviceAccountTokenCreator` to the Dataform service agent on the new runner service account in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T6 — Declare `time_sleep.wait_for_dataform_iam` with a `create_duration` of "60s" depending on the service agent's IAM roles in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T7 — Refactor `google_service_account_iam_member.developer_sa_user` to point to `google_service_account.dataform_runner` using `for_each = var.dataform_developer_emails` without dependencies on the repository in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T8 — Remove old `google_service_account_iam_member.dataform_sa_user` and `google_service_account_iam_member.dataform_sa_token_creator` targeting `elt_runner` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T9 — Update `service_account` in `google_dataform_repository.coc_elt` to reference the new runner SA email in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
- [ ] T10 — Update `depends_on` in `google_dataform_repository.coc_elt` to reference only `time_sleep.wait_for_dataform_iam` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
- [ ] T11 — Run `terraform validate` inside `terraform/` directory to verify syntax and reference correctness.

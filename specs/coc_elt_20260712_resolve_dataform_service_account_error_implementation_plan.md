---
title: "Resolve Dataform workflowInvocation 400 error: Service account must be set when strict act as checks are enabled"
project_id: "coc-elt"
nyutu_uuid: "a391e02c-0c6c-447c-9942-abdbc1d4b1c3"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_dataform_service_account_error_implementation_plan.md"
---

# Implementation Plan - Resolve Dataform Service Account Invocation Error

This implementation plan details the steps to resolve the `400 Bad Request` error when invoking Dataform workflow executions:
`"Service account must be set when strict act as checks are enabled."`

This error occurs because Dataform requires an explicit execution service account when strict security checks are enabled, and the Dataform Service Agent of the Data project must be granted permissions to act as/create tokens for that execution service account.

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Define Dataform Repository Service Account)**: The system MUST set the `service_account` argument in the [google_dataform_repository.coc_elt](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf#L39-L44) resource to `google_service_account.elt_runner.email` in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) to establish a default execution identity. (Ubiquitous)
*   **R2 (Retrieve Data Project Number)**: The system MUST retrieve the data project number using the `google_project.data_project` data source in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) with the project ID set to `var.data_project_id`. (Ubiquitous)
*   **R3 (Authorize Dataform Service Agent as Service Account User)**: The system MUST grant the Dataform Service Agent of the data project (`service-[DATA_PROJECT_NUMBER]@gcp-sa-dataform.iam.gserviceaccount.com`) the role `roles/iam.serviceAccountUser` on the [elt_runner](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf#L1-L7) service account using `google_service_account_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
*   **R4 (Authorize Dataform Service Agent as Service Account Token Creator)**: The system MUST grant the Dataform Service Agent of the data project the role `roles/iam.serviceAccountTokenCreator` on the [elt_runner](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf#L1-L7) service account using `google_service_account_iam_member` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
*   **R5 (Terraform Validation)**: WHEN the Terraform configurations are validated, the system MUST pass all validation checks without syntax or configuration errors. (Event)
*   **R6 (Error Handling)**: IF the service account is not specified in the repository, THEN the system MUST fail workflow invocations with a 400 error stating that the service account must be set when strict act as checks are enabled. (Unwanted)
*   **R7 (Error Handling - IAM)**: IF the Dataform Service Agent lacks the required service account roles, THEN the system MUST fail the workflow invocation with a permission denied error when attempting to act as the execution service account. (Unwanted)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
*   [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) (Modified to declare `service_account` in the [google_dataform_repository.coc_elt](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf#L39-L44) resource)
*   [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) (Modified to declare the data source and grant SA roles)

### New Signatures
A new argument in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf):
```hcl
resource "google_dataform_repository" "coc_elt" {
  # ... existing fields
  service_account = google_service_account.elt_runner.email
}
```

New declarations in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):
```hcl
data "google_project" "data_project" {
  project_id = var.data_project_id
}

resource "google_service_account_iam_member" "dataform_sa_user" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}

resource "google_service_account_iam_member" "dataform_sa_token_creator" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}
```

### Error Handling
- The workflow execution uses the `elt_runner` service account to run queries and tasks.
- If the service agent does not have `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator` on the execution service account, the invocation will fail with a permission error. The roles are bound directly to the `elt_runner` service account to prevent unauthorized escalation.

### Discarded Alternatives
*   **Alternative 1: Using project-level IAM bindings for Dataform Service Agent**
    *   *Why discarded*: Granting service account user roles on the project level would grant the Dataform service agent access to use *all* service accounts in the project, violating the principle of least privilege. Granting resource-level access specifically on `google_service_account.elt_runner` is more secure and satisfies strict IAM requirements.
*   **Alternative 2: Disabling strict act as checks on the project**
    *   *Why discarded*: Strict checks are enabled by default on newer projects and serve as a crucial security boundary. Bypassing them reduces the project's overall security posture.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `service_account` parameter to [google_dataform_repository.coc_elt](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf#L39-L44) in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
- [x] T2 — Declare the `google_project.data_project` data source in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [x] T3 — Declare `google_service_account_iam_member.dataform_sa_user` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [x] T4 — Declare `google_service_account_iam_member.dataform_sa_token_creator` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [x] T5 — Run `terraform validate` inside `terraform/` directory to ensure configuration correctness.


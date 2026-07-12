---
title: "Resolve Dataform repository update 403 permission error during terraform apply"
project_id: "coc-elt"
nyutu_uuid: "f3a185c1-11e0-4a08-9529-ecd79a5b4313"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_dataform_repo_403_error_implementation_plan.md"
---

# Implementation Plan - Resolve Dataform Repository Update 403 Permission Error

This implementation plan details the steps to resolve the `400/403 Forbidden` error when updating the Dataform repository during `terraform apply`:
`Error updating Repository ...: Error 403: The caller does not have permission to act as service account: coc-elt-runner@elt-coc.iam.gserviceaccount.com.`

The root cause is a race condition: Terraform attempts to update the Dataform Repository resource before the IAM policy bindings allowing the Dataform Service Agent to act as the runner service account are fully applied. Declaring an explicit dependency using `depends_on` resolves this issue.

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1**: The system MUST declare a `depends_on` block inside the [google_dataform_repository.coc_elt](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf#L39-L45) resource in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf). (Ubiquitous)
*   **R2**: The `depends_on` block MUST reference [google_service_account_iam_member.dataform_sa_user](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf#L142-L148) and [google_service_account_iam_member.dataform_sa_token_creator](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf#L150-L156) to ensure strict order of operations. (Ubiquitous)
*   **R3**: WHEN the Terraform configuration is validated via `terraform validate`, the system MUST pass with no syntax or configuration errors. (Event)
*   **R4**: IF the Dataform Repository resource is created or updated before the IAM permissions are successfully granted to the Dataform Service Agent, THEN the system MUST prevent this ordering by using Terraform's explicit dependency resolution (`depends_on`). (Unwanted)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
*   [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) (Modify the `google_dataform_repository.coc_elt` resource to add a `depends_on` block)

### New Signatures
Modified resource in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf):
```hcl
resource "google_dataform_repository" "coc_elt" {
  provider        = google-beta
  project         = var.data_project_id
  region          = var.region
  name            = "coc-elt"
  service_account = google_service_account.elt_runner.email

  depends_on = [
    google_service_account_iam_member.dataform_sa_user,
    google_service_account_iam_member.dataform_sa_token_creator,
  ]
}
```

### Error Handling
- The `depends_on` constraints force Terraform to delay creation/modification of the Dataform repository until the IAM member resources `google_service_account_iam_member.dataform_sa_user` and `google_service_account_iam_member.dataform_sa_token_creator` are fully provisioned.
- If there's an IAM API propagation delay, the first terraform apply might still fail on transient GCP IAM propagation times, but Terraform will guarantee the sequential call order.

### Discarded Alternatives
*   **Alternative 1: Target-based apply (`terraform apply -target=...`)**
    *   *Why discarded*: Target-based applies are anti-patterns in CI/CD environments as they require manual intervention and disrupt automation.
*   **Alternative 2: Implicit dependency through local values/references**
    *   *Why discarded*: HCL does not support referencing the IAM policy resources in the arguments of `google_dataform_repository` in a way that creates an implicit dependency (since the repository only needs the runner service account email, not the IAM bindings themselves). Explicit `depends_on` is the correct HCL mechanism.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add the `depends_on` block to the `google_dataform_repository.coc_elt` resource in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
- [x] T2 — Run `terraform validate` in the `terraform/` directory to ensure configuration correctness.

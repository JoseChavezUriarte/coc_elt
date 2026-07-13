---
title: "Resolve 403 Permission Denied in run_dataform GCP Workflow Step"
project_id: "coc-elt"
nyutu_uuid: "932738b0-e806-4dea-abeb-c67d4a0622e2"
artifact_type: "Architectural Decision"
tags:
  - "terraform"
  - "gcp-workflows"
  - "iam"
  - "dataform"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_resolve-workflow-dataform-403_implementation_plan.md"
---

# Implementation Plan: Resolve 403 Permission Denied in `run_dataform` Step

This implementation plan details the Terraform IAM updates required to resolve the 403 Permission Denied error in the `run_dataform` step of the GCP Workflow. The workflow service account (`coc-elt-runner`) needs to act as the Dataform runner service account (`coc-dataform-runner`) to trigger Dataform executions.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following security and deployment orchestration requirements:

*   **R1 (IAM Role Assignment)**: The system MUST grant the `roles/iam.serviceAccountUser` role to the workflow runner service account `coc-elt-runner` (`google_service_account.elt_runner.email`) on the Dataform runner service account `coc-dataform-runner` (`google_service_account.dataform_runner.name`).
*   **R2 (IAM Propagation Delay)**: The system MUST ensure the `time_sleep.wait_for_dataform_iam` resource block blocks execution until `google_service_account_iam_member.elt_runner_dataform_sa_user` is fully provisioned.
*   **R3 (Validation Safety)**: IF the Terraform configuration is syntax-invalid or references missing resources, THEN the system MUST fail the validation checks.
*   **R4 (Orchestration Order)**: WHILE provisioning, the system MUST ensure the new IAM member resource is created only after both `google_service_account.dataform_runner` and `google_service_account.elt_runner` are defined.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified
*   **Modify**: `terraform/security.tf`

### 2.2 Signatures & Code Changes

#### 2.2.1 Add IAM Member Binding
A new `google_service_account_iam_member` resource will be appended to `terraform/security.tf`:
```hcl
resource "google_service_account_iam_member" "elt_runner_dataform_sa_user" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.elt_runner.email}"
}
```

#### 2.2.2 Update Propagation Delay
Update the `time_sleep.wait_for_dataform_iam` block in `terraform/security.tf` to include the new resource:
```hcl
resource "time_sleep" "wait_for_dataform_iam" {
  create_duration = "60s"

  depends_on = [
    google_service_account_iam_member.dataform_runner_sa_user,
    google_service_account_iam_member.dataform_runner_sa_token_creator,
    google_service_account_iam_member.developer_sa_user,
    google_service_account_iam_member.elt_runner_dataform_sa_user
  ]
}
```

### 2.3 Discarded Alternatives
*   **Alternative 1: Project-Level Service Account User**. Discarded because granting `roles/iam.serviceAccountUser` at the project level violates the principle of least privilege. The workflow service account would be able to impersonate any service account within the project.
*   **Alternative 2: Workflow Step Impersonation Modification**. Discarded because executing the Dataform workflows workflow tasks requires authentication as the specific Dataform runner service account that has BQ and Dataform permissions.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `google_service_account_iam_member.elt_runner_dataform_sa_user` resource block in `terraform/security.tf`.
- [x] T2 — Append `google_service_account_iam_member.elt_runner_dataform_sa_user` to the `depends_on` list of `time_sleep.wait_for_dataform_iam` in `terraform/security.tf`.
- [x] T3 — Run `terraform validate` inside the `terraform/` directory to verify syntactical correctness.
- [x] T4 — Run `terraform plan` inside the `terraform/` directory to inspect proposed resource changes.

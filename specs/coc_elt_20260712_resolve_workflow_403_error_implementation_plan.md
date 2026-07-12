---
title: "Resolve Cloud Workflows run_job 403 Permission Error by granting roles/run.viewer"
project_id: "coc-elt"
nyutu_uuid: "ecd70b2c-ac43-4cd8-9603-733b37920973"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "workflows"
  - "cloudrun"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_workflow_403_error_implementation_plan.md"
---

# Implementation Plan - Resolve Cloud Workflows 403 Permission Error on Operation Polling

This implementation plan details the steps to resolve the `403 Permission Denied` error (`run.operations.get` denied) when the Cloud Workflows pipeline invokes a Cloud Run Job and polls the returned execution operation. This is done by granting the `coc-elt-runner` service account the `roles/run.viewer` role at the compute project level.

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Grant Run Viewer Role)**: The system MUST grant the `elt_runner` service account (`google_service_account.elt_runner`) the `roles/run.viewer` role at the compute project level (`var.compute_project_id`) in `terraform/security.tf` to allow the Workflow to successfully call `googleapis.run.v2.projects.locations.operations.get`. (Ubiquitous)
*   **R2 (Least Privilege Principle)**: The system MUST NOT grant project-level write/execute permissions (such as `roles/run.developer` or `roles/run.admin` at the project level) to the `elt_runner` service account. (Ubiquitous)
*   **R3 (Terraform Validation)**: WHEN the Terraform configurations are validated, the system MUST pass all validation checks without syntax or configuration errors. (Event)
*   **R4 (Workflow Execution Polling)**: WHEN the Workflow executes, the system MUST successfully poll the Cloud Run execution operation status. (Event)
*   **R5 (Error Handling)**: IF the `roles/run.viewer` role is not granted at the project level, THEN the system MUST fail the workflow step polling with a 403 permission denied error. (Unwanted)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
*   `terraform/security.tf` (Modified to add the project-level IAM member binding)

### New Signatures
A new `google_project_iam_member` resource will be declared in `terraform/security.tf`:
```hcl
resource "google_project_iam_member" "elt_runner_run_viewer" {
  project = var.compute_project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}
```

### Error Handling
The Cloud Workflows `wait_job` step polls the execution operation returned by the `run_job` step using `googleapis.run.v2.projects.locations.operations.get`.
- Without this role, the execution fails during polling with:
  `Permission 'run.operations.get' denied on resource 'projects/elt-coc/locations/us-central1/operations/...'`
- Granting `roles/run.viewer` at the project level authorizes the service account to access the operation resources and query their status.

### Discarded Alternatives
*   **Alternative 1: Granting `roles/run.developer` at the project level**
    *   *Why discarded*: While `roles/run.developer` contains `run.operations.get`, granting it at the project level would allow the workflow's service account to create, update, or delete all Cloud Run jobs/services in the project. This violates the principle of least privilege, as the workflow only needs to run a specific job (authorized via `google_cloud_run_v2_job_iam_member.run_developer` on that specific job resource) and view operations.
*   **Alternative 2: Granting `roles/run.viewer` on the specific Cloud Run Job**
    *   *Why discarded*: Cloud Run operations are project-level resources (under `projects/{project_id}/locations/{region}/operations/{operation_id}`). Applying a resource-level IAM binding on the specific job does not authorize access to the project's operation resource namespace. Therefore, a project-level role containing `run.operations.get` (like `roles/run.viewer`) is required.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Define the `google_project_iam_member.elt_runner_run_viewer` resource in `terraform/security.tf`.
- [x] T2 — Run `terraform validate` inside the `terraform/` directory to ensure configuration correctness.

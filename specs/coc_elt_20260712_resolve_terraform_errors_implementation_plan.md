---
title: "Resolve Terraform Apply Errors and Document Deployment Process"
project_id: "coc-elt"
nyutu_uuid: "a5462a25-55d2-4d4e-805d-0b5ae5ea2dfd"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "bug-fix"
  - "deployment"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_terraform_errors_implementation_plan.md"
---

# Implementation Plan - Resolve Terraform Apply Errors

This plan details the steps to resolve 4 distinct Terraform apply errors identified during the infrastructure provisioning:
1. Enabling the Dataform API in the Compute project.
2. Bootstrapping the Cloud Run Job with a public placeholder image.
3. Fixing a race condition/dependency error for the Cloud Run Developer IAM binding (404 error).
4. Documenting a 2-step targeted apply process for authorizing the Cloud Build v2 GitHub connection.

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Dataform API)**: The system MUST enable `"dataform.googleapis.com"` in the Compute project services (`terraform/services.tf`) to fix the Workflows compilation error.
*   **R2 (Bootstrap Cloud Run Image)**: The system MUST configure the Cloud Run Job `elt_job` to use the public bootstrap placeholder image `"gcr.io/cloudrun/hello"` in `terraform/compute.tf` to prevent job creation failure when the custom image is not yet available in the registry.
*   **R3 (Dynamic IAM Job Reference)**: The system MUST update the `google_cloud_run_v2_job_iam_member.run_developer` resource name parameter in `terraform/security.tf` to reference the Cloud Run Job resource name dynamically (`google_cloud_run_v2_job.elt_job.name`) to enforce correct resource creation order.
*   **R4 (2-Step Apply Documentation)**: The system MUST document the 2-step target apply process in `README.md` and the cross-project ELT pipeline walkthrough (`specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md`) to guide operators through Cloud Build v2 connection manual authorization before provisioning repositories and triggers.
*   **IF** the developer attempts a full `terraform apply` without first authorizing the Cloud Build connection, **THEN** the system MUST handle or document the expected failure and guide them back to the 2-step targeted process.

---

## 2. Technical Decisions (HOW it will be built)

### File Changes
We will create/modify the following files:
*   `terraform/services.tf` (Modify)
*   `terraform/compute.tf` (Modify)
*   `terraform/security.tf` (Modify)
*   `README.md` (Modify/Write)
*   `specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md` (Modify)

### Signatures and Configurations

1.  **Dataform API Enablement** in `terraform/services.tf`:
    ```hcl
    resource "google_project_service" "compute_services" {
      for_each = toset([
        "iam.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "compute.googleapis.com",
        "secretmanager.googleapis.com",
        "run.googleapis.com",
        "workflows.googleapis.com",
        "cloudscheduler.googleapis.com",
        "cloudbuild.googleapis.com",
        "dataform.googleapis.com" # Added to fix workflows compilation error
      ])
      project            = var.compute_project_id
      service            = each.key
      disable_on_destroy = false
    }
    ```

2.  **Bootstrap Cloud Run Job Image** in `terraform/compute.tf`:
    ```hcl
    resource "google_cloud_run_v2_job" "elt_job" {
      name     = "coc-elt-job"
      location = var.region
      project  = var.compute_project_id

      template {
        template {
          service_account = google_service_account.elt_runner.email

          containers {
            image = "gcr.io/cloudrun/hello" # Changed from custom build image to prevent creation failure
            ...
          }
        }
      }
    }
    ```

3.  **Dynamic IAM Binding Reference** in `terraform/security.tf`:
    ```hcl
    resource "google_cloud_run_v2_job_iam_member" "run_developer" {
      project  = var.compute_project_id
      location = var.region
      name     = google_cloud_run_v2_job.elt_job.name # Changed from hardcoded "coc-elt-job" to prevent 404
      role     = "roles/run.developer"
      member   = "serviceAccount:${google_service_account.elt_runner.email}"

      depends_on = [google_project_service.compute_services]
    }
    ```

4.  **2-Step Target Apply Process Documentation** in `README.md` and `specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md`:
    Document the following workflow for deployment:
    - **Step 1: Target the Connection Creation**:
      Run `terraform apply -target=google_cloudbuildv2_connection.github_conn` to provision only the connection, its required services, and Secret Manager access.
    - **Step 2: Manually Authorize GitHub Connection**:
      Go to GCP Console -> Cloud Build -> Repositories -> 2nd Gen tab, select the connection `coc-elt-connection`, and authorize it to GitHub.
    - **Step 3: Run Full Apply**:
      Run `terraform apply` to provision the repository connection and webhook trigger safely without errors.

### Discarded Alternatives

*   **Alternative**: Maintaining the custom image `gcr.io/${var.compute_project_id}/coc-elt-pipeline:latest` in `compute.tf` and trying to run a Cloud Build job first.
    *   *Reason for Discarding*: The build trigger cannot be created until the Cloud Build connection is established, and the connection depends on the Terraform apply. Trying to build the image first creates a chicken-and-egg situation. Bootstrapping with `gcr.io/cloudrun/hello` breaks this cycle.
*   **Alternative**: Using automated retry loops for Cloud Build connection.
    *   *Reason for Discarding*: Interactive OAuth authorization cannot be completed programmatically without GCP user tokens, making manual console authorization mandatory.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `"dataform.googleapis.com"` to the `for_each` list in `terraform/services.tf`.
- [x] T2 — Change the image in `google_cloud_run_v2_job.elt_job` container configuration to `"gcr.io/cloudrun/hello"` in `terraform/compute.tf`.
- [x] T3 — Update the `name` attribute in `google_cloud_run_v2_job_iam_member.run_developer` to `google_cloud_run_v2_job.elt_job.name` in `terraform/security.tf`.
- [x] T4 — Write the 2-step target apply process instructions to `README.md`.
- [x] T5 — Add the 2-step target apply instructions to the walkthrough `specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md`.
- [x] T6 — Run `terraform validate` inside `terraform/` to verify configurations.

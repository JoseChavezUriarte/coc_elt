---
title: "Resolve Cloud Build trigger 400 / service account error by using coc-elt-runner service account"
project_id: "coc-elt"
nyutu_uuid: "ec4625be-e1be-422e-afe1-e3dc0deff4a9"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "cloudbuild"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_cloudbuild_sa_error_implementation_plan.md"
---

# Implementation Plan - Resolve Cloud Build Trigger 400 Service Account Error

This implementation plan details the steps to resolve the 400 Bad Request / service account error on the Cloud Build trigger by configuring the trigger to run as the user-managed service account `coc-elt-runner` (`google_service_account.elt_runner`) and provisioning it with the required roles in the Compute project.

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Log Writer Role)**: The system MUST grant the `coc-elt-runner` service account the `roles/logging.logWriter` role in the Compute project to allow it to write build logs. (Ubiquitous)
*   **R2 (Storage Admin Role)**: The system MUST grant the `coc-elt-runner` service account the `roles/storage.admin` role in the Compute project to allow it to push Docker images to the Google Container Registry (GCR). (Ubiquitous)
*   **R3 (Configure Trigger Service Account)**: The system MUST configure the Cloud Build trigger `google_cloudbuild_trigger.github_trigger` to run using the `coc-elt-runner` service account by setting the `service_account` attribute. (Ubiquitous)
*   **R4 (Successful Apply)**: WHEN Terraform applies the configuration, the system MUST successfully associate the `coc-elt-runner` service account with the Cloud Build trigger and provision the roles. (Event)
*   **R5 (Error Handling)**: IF the required IAM roles are not correctly provisioned before the Cloud Build trigger runs, THEN the system MUST fail the build trigger run with a descriptive error. (Unwanted)
*   **R6 (Least Privilege Boundary)**: WHILE the Cloud Build trigger execution is active, the system MUST NOT permit the build to write outside of the specified container registry and logging destinations. (State)

---

## 2. Technical Decisions (HOW it will be built)

### File Changes
We will modify the following files:
*   `terraform/security.tf` (Modify)
*   `terraform/cicd.tf` (Modify)

### Signatures and Configurations

1.  **Add IAM Roles in `terraform/security.tf`**:
    We will append the following resources to grant `roles/logging.logWriter` and `roles/storage.admin` to the `coc-elt-runner` service account (`google_service_account.elt_runner`) in the Compute project:

    ```hcl
    resource "google_project_iam_member" "elt_runner_logging_writer" {
      project = var.compute_project_id
      role    = "roles/logging.logWriter"
      member  = "serviceAccount:${google_service_account.elt_runner.email}"

      depends_on = [google_project_service.compute_services]
    }

    resource "google_project_iam_member" "elt_runner_storage_admin" {
      project = var.compute_project_id
      role    = "roles/storage.admin"
      member  = "serviceAccount:${google_service_account.elt_runner.email}"

      depends_on = [google_project_service.compute_services]
    }
    ```

2.  **Configure Cloud Build Trigger Service Account in `terraform/cicd.tf`**:
    We will modify the `google_cloudbuild_trigger.github_trigger` resource to include the `service_account` parameter, pointing to the `coc-elt-runner` service account:

    ```hcl
    resource "google_cloudbuild_trigger" "github_trigger" {
      project     = var.compute_project_id
      location    = var.region
      name        = "coc-elt-trigger"
      description = "Trigger for Clash of Clans ELT pipeline on main branch push"
      
      service_account = "projects/${var.compute_project_id}/serviceAccounts/${google_service_account.elt_runner.email}"

      repository_event_config {
        repository = google_cloudbuildv2_repository.github_repo.id
        push {
          branch = "^main$"
        }
      }

      filename = "cloudbuild.yaml"

      depends_on = [google_project_service.compute_services]
    }
    ```

### Least Privilege & Security Audit
*   **Role Selection**: We are using granular predefined roles (`roles/logging.logWriter` and `roles/storage.admin`) rather than broad permissions like `roles/editor` or `roles/owner` for the user-managed service account.
*   **Separation of Duties (SoD)**: The `coc-elt-runner` service account is dedicated specifically to this ELT pipeline and its container builds, isolating it from other workloads.
*   **No Static Keys**: This configuration relies on IAM-based execution context and Cloud Build's native service account impersonation rather than exporting static JSON service account keys.

### Discarded Alternatives

*   **Alternative 1**: Modifying the default Cloud Build service account (`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`) permissions.
    *   *Reason for Discarding*: Using the default Cloud Build service account violates the principle of least privilege, as it typically possesses excessive broad default permissions. Using a user-managed service account (`coc-elt-runner`) allows restricting its scopes strictly to the tasks at hand.
*   **Alternative 2**: Assigning `roles/storage.objectAdmin` instead of `roles/storage.admin`.
    *   *Reason for Discarding*: While `storage.objectAdmin` is slightly more restricted, `storage.admin` is the standard recommended role for pushing Docker images to GCR in Compute projects, and is explicitly requested by the user.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add the `google_project_iam_member.elt_runner_logging_writer` resource to `terraform/security.tf`.
- [x] T2 — Add the `google_project_iam_member.elt_runner_storage_admin` resource to `terraform/security.tf`.
- [x] T3 — Update `google_cloudbuild_trigger.github_trigger` in `terraform/cicd.tf` to set the `service_account` attribute.
- [x] T4 — Run `terraform validate` in the `terraform/` directory.
- [x] T5 — Run `terraform plan` to verify the exact IAM and trigger changes.

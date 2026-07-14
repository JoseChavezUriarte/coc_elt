---
title: "Resolve 400 Bad Request in compile_dataform GCP Workflow Step"
project_id: "coc-elt"
nyutu_uuid: "d399cd82-e284-46b8-80db-c094f082dcfb"
artifact_type: "Architectural Decision"
tags:
  - "terraform"
  - "gcp-workflows"
  - "dataform"
  - "security"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_resolve-dataform-400-error_implementation_plan.md"
---

# Implementation Plan: Resolve 400 Bad Request in `compile_dataform` Step (Revised)

This implementation plan details the Terraform configuration updates required to resolve the 400 Bad Request error (git reference 'main' could not be resolved) in the `compile_dataform` step of GCP Workflows, utilizing dynamic secret version resolution, consolidated propagation delay, and decoupled resource dependencies.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following Dataform Git connectivity and permission requirements:

*   **R1 (Dataform Git Remote Connection)**: The system MUST configure the Dataform repository `coc-elt` to connect to the remote GitHub repository specified by `var.github_repository_url`.
*   **R2 (Default Branch Resolution)**: The system MUST set the Dataform repository's default branch to `"main"`.
*   **R3 (Dynamic Secret Version Resolution)**: The system MUST dynamically fetch the latest version of the GitHub OAuth token secret using a `google_secret_manager_secret_version` data block.
*   **R4 (Dynamic Git Authentication)**: The system MUST authenticate connection to the remote GitHub repository by referencing the dynamic ID of the secret version: `data.google_secret_manager_secret_version.github_token_latest.name`.
*   **R5 (Secrets Manager Access Control)**: The system MUST grant the `roles/secretmanager.secretAccessor` role to the Dataform Service Agent `service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com` on the GitHub OAuth token secret in the Compute project.
*   **R6 (IAM Propagation Consolidation)**: The system MUST ensure `time_sleep.wait_for_dataform_iam` waits for `google_secret_manager_secret_iam_member.dataform_secret_accessor` to prevent race conditions during IAM propagation.
*   **R7 (Decoupled Repository Dependency)**: The Dataform repository resource `google_dataform_repository.coc_elt` MUST depend strictly and solely on `time_sleep.wait_for_dataform_iam`.
*   **R8 (Config Validation)**: IF the Terraform configuration contains syntax errors or invalid references, THEN the system MUST fail during validation.
*   **R9 (Plan Verification)**: WHEN planning changes, the system MUST successfully generate a Terraform plan without errors.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified
*   **Modify**: `terraform/security.tf` - Define the Secrets Manager accessor policy, dynamic secret version lookup, and update the time sleep propagation delay block.
*   **Modify**: `terraform/bigquery.tf` - Configure the remote Git repository settings and decouple repository dependencies.

### 2.2 Analysis and Design
The 400 Bad Request error (`git reference 'main' could not be resolved`) occurs because the `coc-elt` Dataform repository is currently a local-only repository (it has no `git_remote_settings` block). When the GCP Workflow execution requests a dynamic compilation of `main`, the Dataform API cannot resolve this reference because it has no remote source repository from which to fetch branches or commits.

To resolve this issue:
1.  **Dynamic Secret Lookup**: Rather than hardcoding `/versions/latest`, we query `latest` dynamically. This ensures that Terraform compiles a plan pinned to the exact metadata state of the active secret version.
2.  **Grant Secret Access**: Dataform requires the GitHub OAuth token to authenticate with the remote repository. The Google-managed Dataform Service Agent for the data project (`service-DATA_PROJECT_NUMBER@gcp-sa-dataform.iam.gserviceaccount.com`) needs the `roles/secretmanager.secretAccessor` role on the token secret in the compute project.
3.  **Consolidated IAM Propagation**: Adding `google_secret_manager_secret_iam_member.dataform_secret_accessor` to `time_sleep.wait_for_dataform_iam`'s `depends_on` block guarantees that the 60-second delay absorbs the Secret Manager permission propagation time.
4.  **Decoupled Dependency**: The `google_dataform_repository.coc_elt` resource will depend strictly on `time_sleep.wait_for_dataform_iam` to simplify the dependency graph while maintaining execution safety.

### 2.3 Signatures & Code Changes

#### 2.3.1 Modify `terraform/security.tf`
Add the data source, the IAM resource, and update the sleep resource:
```hcl
data "google_secret_manager_secret_version" "github_token_latest" {
  project = var.compute_project_id
  secret  = data.google_secret_manager_secret.github_token.secret_id
  version = "latest"
}

resource "google_secret_manager_secret_iam_member" "dataform_secret_accessor" {
  project   = var.compute_project_id
  secret_id = data.google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}

resource "time_sleep" "wait_for_dataform_iam" {
  create_duration = "60s"

  depends_on = [
    google_service_account_iam_member.dataform_runner_sa_user,
    google_service_account_iam_member.dataform_runner_sa_token_creator,
    google_service_account_iam_member.developer_sa_user,
    google_service_account_iam_member.elt_runner_dataform_sa_user,
    google_secret_manager_secret_iam_member.dataform_secret_accessor
  ]
}
```

#### 2.3.2 Modify `terraform/bigquery.tf`
Update the `google_dataform_repository.coc_elt` resource to connect to Git and simplify `depends_on`:
```hcl
resource "google_dataform_repository" "coc_elt" {
  provider        = google-beta
  project         = var.data_project_id
  region          = var.region
  name            = "coc-elt"
  service_account = google_service_account.dataform_runner.email

  git_remote_settings {
    url                                 = var.github_repository_url
    default_branch                      = "main"
    authentication_token_secret_version = data.google_secret_manager_secret_version.github_token_latest.name
  }

  depends_on = [
    time_sleep.wait_for_dataform_iam
  ]
}
```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `data.google_secret_manager_secret_version.github_token_latest` and `google_secret_manager_secret_iam_member.dataform_secret_accessor` in `terraform/security.tf`.
- [x] T2 — Update `depends_on` list of `time_sleep.wait_for_dataform_iam` to include `google_secret_manager_secret_iam_member.dataform_secret_accessor`.
- [x] T3 — Update `google_dataform_repository.coc_elt` in `terraform/bigquery.tf` to include `git_remote_settings` pointing to `data.google_secret_manager_secret_version.github_token_latest.name` and restrict `depends_on` strictly to `time_sleep.wait_for_dataform_iam`.
- [x] T4 — Run `terraform validate` inside the `terraform/` directory.
- [x] T5 — Run `terraform plan` inside the `terraform/` directory.

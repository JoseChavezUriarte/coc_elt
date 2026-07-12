---
title: "Import and Use Pre-existing Secret for GitHub Connection in Terraform"
project_id: "coc_elt"
nyutu_uuid: "1bb1e994-ea56-4c8f-b0b5-33cb0f580299"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "secret_manager"
  - "cloud_build"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_import_github_token_secret_implementation_plan.md"
---

# Implementation Plan - Import and Use Pre-existing Secret for GitHub Connection in Terraform

This plan details the steps to import and configure access to a pre-existing GitHub connection OAuth token secret (`github_conn-github-oauthtoken-61aafa`) in Secret Manager, grant accessor permissions to the Cloud Build service agent, and use it to authenticate the GitHub connection.

## 1. Requirements (WHAT is needed)

The requirements are defined using the EARS (Easy Approach to Requirements Syntax) notation.

*   **R1** — The system MUST declare a `google_secret_manager_secret` data source in `terraform/cicd.tf` pointing to the pre-existing secret ID `"github_conn-github-oauthtoken-61aafa"` in the Compute project.
*   **R2** — The system MUST grant the Cloud Build Service Agent (`service-[PROJECT_NUMBER]@gcp-sa-cloudbuild.iam.gserviceaccount.com`) the `roles/secretmanager.secretAccessor` role on this secret using `google_secret_manager_secret_iam_member`.
*   **R3** — The system MUST update the `google_cloudbuildv2_connection.github_conn` resource to include a `github_config.authorizer_credential` block pointing to the `latest` version of this secret.
*   **R4** — The system MUST add `depends_on` in `google_cloudbuildv2_connection.github_conn` targeting the IAM accessor permission resource to ensure that IAM permissions are fully active before the connection is established.
*   **IF** the secret `"github_conn-github-oauthtoken-61aafa"` does not exist in the target GCP Compute project, **THEN** the system MUST fail during the Terraform plan/apply stage with a clear data source lookup error.

## 2. Technical Decisions (HOW it will be built)

### File Changes

We will modify the following file:
*   `terraform/cicd.tf`

### Signatures and Configurations

1.  **Data Source**: We will add the data source definition to `terraform/cicd.tf`:
    ```terraform
    data "google_secret_manager_secret" "github_token" {
      project   = var.compute_project_id
      secret_id = "github_conn-github-oauthtoken-61aafa"
    }
    ```

2.  **IAM Resource**: We will add the `google_secret_manager_secret_iam_member` resource to `terraform/cicd.tf`:
    ```terraform
    resource "google_secret_manager_secret_iam_member" "cloudbuild_secret_accessor" {
      project   = var.compute_project_id
      secret_id = data.google_secret_manager_secret.github_token.secret_id
      role      = "roles/secretmanager.secretAccessor"
      member    = "serviceAccount:service-${data.google_project.compute_project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
    }
    ```
    *Note: `data.google_project.compute_project.number` is already defined in `terraform/security.tf` and is globally accessible within the root module.*

3.  **Connection Update**: We will update `google_cloudbuildv2_connection.github_conn` in `terraform/cicd.tf` as follows:
    ```terraform
    resource "google_cloudbuildv2_connection" "github_conn" {
      project  = var.compute_project_id
      location = var.region
      name     = "coc-elt-connection"

      github_config {
        app_installation_id = var.github_app_installation_id
        authorizer_credential {
          oauth_token_secret_version = "${data.google_secret_manager_secret.github_token.id}/versions/latest"
        }
      }

      depends_on = [
        google_project_service.compute_services,
        google_secret_manager_secret_iam_member.cloudbuild_secret_accessor
      ]
    }
    ```

### Discarded Alternatives

*   **Alternative**: Declaring a `google_secret_manager_secret` resource and trying to import it into the state.
    *   *Reason for Discarding*: The secret is pre-existing and managed externally. Attempting to manage its lifecycle via resource declaration makes it vulnerable to deletion during terraform destroy, and violates the requirement to treat it as a pre-existing external asset. A `data` source is the correct mechanism for external resources.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `data.google_secret_manager_secret.github_token` in `terraform/cicd.tf`.
- [x] T2 — Add `google_secret_manager_secret_iam_member.cloudbuild_secret_accessor` in `terraform/cicd.tf`.
- [x] T3 — Update `google_cloudbuildv2_connection.github_conn` to include `github_config.authorizer_credential` and update its `depends_on` list in `terraform/cicd.tf`.
- [x] T4 — Run `terraform fmt` on `terraform/cicd.tf` to ensure style consistency.

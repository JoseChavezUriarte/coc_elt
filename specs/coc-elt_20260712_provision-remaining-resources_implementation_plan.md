---
title: "Provision Remaining Terraform Resources for CI/CD and Dataform"
project_id: "coc-elt"
nyutu_uuid: "4e0df36a-88d8-460b-a60b-549ad04fadc4"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "cloudbuild"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260712_provision-remaining-resources_implementation_plan.md"
---

# Provision Remaining Terraform Resources for CI/CD and Dataform

This plan details the provisioning of the remaining GCP infrastructure components using Terraform:
1. A basic `google_dataform_repository` in the Data Project.
2. Cloud Build v2 Connection, Repository, and Trigger configuration on the `main` branch.
3. Relevant input variables for GitHub integration.
4. Dynamic project number retrieval for Compute Project.
5. IAM permissions for the Cloud Build service account to manage Run developers and Service Account usage.

---

## 1. Requirements (WHAT is needed) — EARS Notation

- **R1:** The system MUST declare a basic `google_dataform_repository` named "coc-elt" in the Data Project (`var.data_project_id`) inside `terraform/bigquery.tf`.
- **R2:** The system MUST define input variables `github_app_installation_id` (Type: number) and `github_repository_url` (Type: string) inside `terraform/variables.tf`.
- **R3:** The system MUST declare a `google_cloudbuildv2_connection` named "coc-elt-connection" inside `terraform/cicd.tf` utilizing `github_config` with `app_installation_id = var.github_app_installation_id`.
- **R4:** The system MUST declare a `google_cloudbuildv2_repository` named "coc-elt" inside `terraform/cicd.tf` pointing to `var.github_repository_url` and associated with the connection.
- **R5:** The system MUST declare a `google_cloudbuild_trigger` named "coc-elt-trigger" inside `terraform/cicd.tf` using the v2 repository configuration for pushes on the `main` branch.
- **R6:** The system MUST declare the `google_project` data source named "compute_project" in `terraform/security.tf` to retrieve the Compute project number.
- **R7:** The system MUST assign the `roles/run.developer` role to the default Cloud Build service account (`serviceAccount:<compute_project_number>@cloudbuild.gserviceaccount.com`) on the Compute project in `terraform/security.tf`.
- **R8:** The system MUST assign the `roles/iam.serviceAccountUser` role to the default Cloud Build service account on the `elt_runner` service account in `terraform/security.tf`.
- **R9:** The system MUST configure explicit `depends_on = [google_project_service.compute_services]` constraints for all newly created Compute project resources (connection, repository, trigger, and IAM bindings).
- **R10 (Unwanted):** IF the GitHub App installation ID is not configured, THEN the Cloud Build connection provisioning MUST fail.
- **R11 (Unwanted):** IF the Compute project services are not fully enabled, THEN provisioning of the new Compute project resources MUST be blocked.

---

## 2. Technical Decisions (HOW it will be built)

### Files Impacted

*   **Create:** `terraform/cicd.tf`
    *   Defines the Cloud Build connection, repository, and trigger.
*   **Modify:** `terraform/bigquery.tf`
    *   Appends the basic `google_dataform_repository` configuration.
*   **Modify:** `terraform/variables.tf`
    *   Adds `github_app_installation_id` and `github_repository_url`.
*   **Modify:** `terraform/security.tf`
    *   Adds the `google_project` data source and the IAM permissions for the Cloud Build service account.

### Code / Resource Signatures

#### **`terraform/variables.tf`**
```hcl
variable "github_app_installation_id" {
  type        = number
  description = "The GitHub App Installation ID for Cloud Build."
}

variable "github_repository_url" {
  type        = string
  description = "The URL of the GitHub repository."
}
```

#### **`terraform/bigquery.tf`**
```hcl
resource "google_dataform_repository" "coc_elt" {
  project = var.data_project_id
  region  = var.region
  name    = "coc-elt"
}
```

#### **`terraform/security.tf`**
```hcl
data "google_project" "compute_project" {
  project_id = var.compute_project_id
}

resource "google_project_iam_member" "cloudbuild_run_developer" {
  project = var.compute_project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${data.google_project.compute_project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}

resource "google_service_account_iam_member" "cloudbuild_sa_user" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.compute_project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}
```

#### **`terraform/cicd.tf`**
```hcl
resource "google_cloudbuildv2_connection" "github_conn" {
  project  = var.compute_project_id
  location = var.region
  name     = "coc-elt-connection"

  github_config {
    app_installation_id = var.github_app_installation_id
  }

  depends_on = [google_project_service.compute_services]
}

resource "google_cloudbuildv2_repository" "github_repo" {
  project           = var.compute_project_id
  location          = var.region
  name              = "coc-elt"
  parent_connection = google_cloudbuildv2_connection.github_conn.id
  remote_uri        = var.github_repository_url

  depends_on = [google_project_service.compute_services]
}

resource "google_cloudbuild_trigger" "github_trigger" {
  project     = var.compute_project_id
  location    = var.region
  name        = "coc-elt-trigger"
  description = "Trigger for Clash of Clans ELT pipeline on main branch push"

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

### Error Handling & Constraints
*   **Validation:** Use `terraform validate` to enforce type matching on incoming variable definitions.
*   **API Enablement:** Dependency `depends_on = [google_project_service.compute_services]` ensures resources are not provisioned before APIs (e.g. `cloudbuild.googleapis.com`) are fully enabled.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `github_app_installation_id` and `github_repository_url` to `terraform/variables.tf`.
- [x] T2 — Declare `google_dataform_repository.coc_elt` in `terraform/bigquery.tf`.
- [x] T3 — Add `data.google_project.compute_project` to `terraform/security.tf`.
- [x] T4 — Add `google_project_iam_member.cloudbuild_run_developer` and `google_service_account_iam_member.cloudbuild_sa_user` to `terraform/security.tf`.
- [x] T5 — Create `terraform/cicd.tf` and declare `google_cloudbuildv2_connection.github_conn`, `google_cloudbuildv2_repository.github_repo`, and `google_cloudbuild_trigger.github_trigger`.
- [x] T6 — Run `terraform init` and `terraform validate` to verify the configuration syntax.

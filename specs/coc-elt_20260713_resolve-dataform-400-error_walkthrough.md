---
title: "Resolve 400 Bad Request in compile_dataform GCP Workflow Step Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "32f87163-b75c-4667-ba4e-2e699d55d030"
artifact_type: "Bug Fix Logic"
tags:
  - "terraform"
  - "gcp-workflows"
  - "dataform"
  - "security"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_resolve-dataform-400-error_walkthrough.md"
---

# Walkthrough: Resolve 400 Bad Request in `compile_dataform` Step

This document outlines the changes implemented to resolve the 400 Bad Request error (`git reference 'main' could not be resolved`) in the Dataform compilation step of GCP Workflows.

## 1. Implementation Details

### 1.1 Secret Access and Dynamic Lookup in Security Config
Modified [terraform/security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) to:
- Declare the `google_secret_manager_secret_version.github_token_latest` data source to fetch the active metadata of the secret.
- Provision `google_secret_manager_secret_iam_member.dataform_secret_accessor` granting `roles/secretmanager.secretAccessor` to the Dataform Service Agent:
  `serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com` on the GitHub token.
- Update `time_sleep.wait_for_dataform_iam` to depend on `google_secret_manager_secret_iam_member.dataform_secret_accessor` to ensure the 60-second propagation window absorbs this new IAM binding.

### 1.2 Git Remote Settings in BigQuery Config
Modified [terraform/bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf) to:
- Configure the `git_remote_settings` block in `google_dataform_repository.coc_elt`, connecting the Dataform repository to `var.github_repository_url` on the `"main"` branch using `data.google_secret_manager_secret_version.github_token_latest.name` for authentication.
- Ensure that the repository's `depends_on` block only references `time_sleep.wait_for_dataform_iam`, simplifying the dependency graph while safeguarding against IAM propagation race conditions.

## 2. Plan Verification

Ran `terraform validate` and `terraform plan` in the `terraform/` directory.

### 2.1 Terraform Validate Output
```
Success! The configuration is valid.
```

### 2.2 Terraform Plan Output
```
Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create
  ~ update in-place

Terraform will perform the following actions:

  # google_dataform_repository.coc_elt will be updated in-place
  ~ resource "google_dataform_repository" "coc_elt" {
        id                                         = "projects/swift-capsule-492817-a7/locations/us-central1/repositories/coc-elt"
        name                                       = "coc-elt"
        # (10 unchanged attributes hidden)

      + git_remote_settings {
          + authentication_token_secret_version = "projects/51301996950/secrets/github_conn-github-oauthtoken-61aafa/versions/1"
          + default_branch                      = "main"
          + url                                 = "https://github.com/JoseChavezUriarte/coc_elt.git"
        }
    }

  # google_secret_manager_secret_iam_member.dataform_secret_accessor will be created
  + resource "google_secret_manager_secret_iam_member" "dataform_secret_accessor" {
      + etag      = (known after apply)
      + id        = (known after apply)
      + member    = "serviceAccount:service-649397721167@gcp-sa-dataform.iam.gserviceaccount.com"
      + project   = "elt-coc"
      + role      = "roles/secretmanager.secretAccessor"
      + secret_id = "github_conn-github-oauthtoken-61aafa"
    }

Plan: 1 to add, 1 to change, 0 to destroy.
```

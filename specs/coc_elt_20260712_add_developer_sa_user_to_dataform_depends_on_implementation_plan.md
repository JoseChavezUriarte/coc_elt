---
title: "Add developer_sa_user to Dataform Repository depends_on"
project_id: "coc_elt"
nyutu_uuid: "5f5ff134-48d7-4128-9c4c-60a6dfaa5940"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_add_developer_sa_user_to_dataform_depends_on_implementation_plan.md"
---

# Implementation Plan - Add developer_sa_user to Dataform Repository depends_on

This plan outlines the changes required to ensure that the `google_dataform_repository.coc_elt` resource explicitly depends on the completion of the `google_service_account_iam_member.developer_sa_user` resource configuration.

## 1. Requirements (WHAT is needed)

The requirements are defined using the EARS (Easy Approach to Requirements Syntax) notation.

*   **R1** (Ubiquitous): The system MUST append `google_service_account_iam_member.developer_sa_user` to the `depends_on` array of the `google_dataform_repository.coc_elt` resource in [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf).
*   **R2** (Ubiquitous): The system MUST verify the syntax and configuration validity using `terraform validate` within the `terraform/` directory.
*   **R3** (Unwanted): IF any syntax error or invalid resource reference is introduced during modification, THEN `terraform validate` MUST report a configuration error and fail.

## 2. Technical Decisions (HOW it will be built)

### File Changes

We will modify the following file:
*   [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf)

### Signatures and Configurations

1.  **Repository Update**: We will update the `google_dataform_repository.coc_elt` resource definition in `terraform/bigquery.tf` to append `google_service_account_iam_member.developer_sa_user` to the `depends_on` block:
    ```terraform
    resource "google_dataform_repository" "coc_elt" {
      provider        = google-beta
      project         = var.data_project_id
      region          = var.region
      name            = "coc-elt"
      service_account = google_service_account.elt_runner.email

      depends_on = [
        google_service_account_iam_member.dataform_sa_user,
        google_service_account_iam_member.dataform_sa_token_creator,
        google_service_account_iam_member.developer_sa_user,
      ]
    }
    ```

### Discarded Alternatives

*   **Alternative**: Reference specific indexed instances of the `developer_sa_user` resource inside `depends_on` (e.g. using keys like `google_service_account_iam_member.developer_sa_user["key"]`).
    *   *Reason for Discarding*: Since `google_service_account_iam_member.developer_sa_user` is defined using `for_each`, referencing the resource as a whole (without index keys) in `depends_on` is the standard and correct Terraform pattern to ensure that the repository depends on all service account user IAM policy member resources.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Append `google_service_account_iam_member.developer_sa_user` to the `depends_on` list of `google_dataform_repository.coc_elt` in `terraform/bigquery.tf`.
- [x] T2 — Run `terraform validate` in the `terraform/` directory to verify the configuration.

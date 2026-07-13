---
title: "Resolve 403 Permission Denied in run_dataform GCP Workflow Step Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "e1f3a6cb-b8ba-4b8b-8705-40e1e37bfa05"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp-workflows"
  - "iam"
  - "dataform"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_resolve-workflow-dataform-403_walkthrough.md"
---

# Walkthrough: Resolve 403 Permission Denied in `run_dataform` Step

This document walks through the modifications made to Terraform resources to solve the 403 Permission Denied error in the `run_dataform` step of the GCP Workflow.

## 1. Implementation Details

### 1.1 Modifying `terraform/security.tf`
- Added the `google_service_account_iam_member.elt_runner_dataform_sa_user` resource block:
  ```hcl
  resource "google_service_account_iam_member" "elt_runner_dataform_sa_user" {
    service_account_id = google_service_account.dataform_runner.name
    role               = "roles/iam.serviceAccountUser"
    member             = "serviceAccount:${google_service_account.elt_runner.email}"
  }
  ```
  This resource grants the workflow runner service account (`coc-elt-runner`) the `roles/iam.serviceAccountUser` role on the Dataform runner service account (`coc-dataform-runner`), allowing the workflow to run Dataform executions under that identity.

- Updated the `time_sleep.wait_for_dataform_iam` block to include the new resource in its `depends_on` list, preventing race conditions from IAM propagation delay during initial deployment:
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

## 2. Test Verification

### 2.1 Verification with Terraform Validate
Ran `terraform validate` in the `terraform/` directory to ensure that syntax and resource references are correct:
```bash
terraform validate
```
Output:
```
Success! The configuration is valid.
```

### 2.2 Verification with Terraform Plan
Ran `terraform plan` in the `terraform/` directory to inspect the generated plan.
Output summary:
```
Plan: 1 to add, 1 to change, 0 to destroy.
```
The new IAM resource `google_service_account_iam_member.elt_runner_dataform_sa_user` is scheduled for creation.

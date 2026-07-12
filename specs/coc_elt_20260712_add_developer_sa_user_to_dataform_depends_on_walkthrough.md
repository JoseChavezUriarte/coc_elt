---
title: "Add developer_sa_user to Dataform Repository depends_on Walkthrough"
project_id: "coc_elt"
nyutu_uuid: "c610e6c0-c3fe-488e-a67f-078cfee287d0"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_add_developer_sa_user_to_dataform_depends_on_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T13:56:30-05:00
- **Objective**: Ensure that Terraform forces the completion of the `google_service_account_iam_member.developer_sa_user` resource creation before attempting to update the Dataform repository.

### Executed Commands
- `terraform validate`
- `git add .`
- `git commit -m "fix(terraform): add developer_sa_user to Dataform depends_on to prevent race conditions"`

### State Mutations
- **Modified**:
  - `terraform/bigquery.tf`
  - `specs/coc_elt_20260712_add_developer_sa_user_to_dataform_depends_on_implementation_plan.md`
- **Created**:
  - `specs/coc_elt_20260712_add_developer_sa_user_to_dataform_depends_on_walkthrough.md`

### Verification Artifacts
- Successful validation via `terraform validate` (Success! The configuration is valid).

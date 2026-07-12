---
title: "Resolve Dataform strict act-as permission error Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "f06d8b3b-7e82-44e9-a549-ab6ddb94ce66"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "dataform"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_dataform_service_account_error_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T13:35:22-05:00
- **Objective**: Resolve the Dataform strict act-as permission error by configuring the default execution service account and granting necessary roles (`roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator`) to the Dataform service agent.

### Executed Commands
- `terraform validate`
- `git add .`
- `git commit -m "fix(terraform): resolve dataform strict act-as permission error"`

### State Mutations
- **Modified**:
  - `terraform/bigquery.tf`
  - `terraform/security.tf`
  - `specs/coc_elt_20260712_resolve_dataform_service_account_error_implementation_plan.md`
- **Created**:
  - `specs/coc_elt_20260712_resolve_dataform_service_account_error_walkthrough.md`

### Verification Artifacts
- Successful validation via `terraform validate` (Success! The configuration is valid).

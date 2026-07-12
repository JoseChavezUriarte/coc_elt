---
title: "Resolve Cloud Workflows run_job 403 Permission Error Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "d0f107d6-9f34-400a-8e12-edb6050c7c1f"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "workflows"
  - "cloudrun"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_workflow_403_error_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T13:12:00-05:00
- **Objective**: Grant the `coc-elt-runner` service account the `roles/run.viewer` role to authorize polling Cloud Run operations in Cloud Workflows.

### Executed Commands
- `terraform validate`
- `git add .`
- `git commit -m "fix(workflows): grant run.viewer role to elt_runner to allow operation polling"`

### State Mutations
- **Modified**:
  - `terraform/security.tf`
  - `specs/coc_elt_20260712_resolve_workflow_403_error_implementation_plan.md`
- **Created**:
  - `specs/coc_elt_20260712_resolve_workflow_403_error_walkthrough.md`

### Verification Artifacts
- Successful validation via `terraform validate` (Success! The configuration is valid).

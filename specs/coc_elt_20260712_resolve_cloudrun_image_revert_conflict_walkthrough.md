---
title: "Resolve Cloud Run Job image revert conflict Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "a50a140b-e08f-4495-b732-97cd3b4019de"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "cloudrun"
  - "gcp"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_cloudrun_image_revert_conflict_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T13:46:00-05:00
- **Objective**: Prevent `terraform apply` from reverting the deployed pipeline container image back to the bootstrap image (`gcr.io/cloudrun/hello`).

### Executed Commands
- `terraform validate`
- `git add .`
- `git commit -m "fix(terraform): ignore Cloud Run Job container image updates in lifecycle"`

### State Mutations
- **Modified**:
  - `terraform/compute.tf`
  - `specs/coc_elt_20260712_resolve_cloudrun_image_revert_conflict_implementation_plan.md`
- **Created**:
  - `specs/coc_elt_20260712_resolve_cloudrun_image_revert_conflict_walkthrough.md`

### Verification Artifacts
- Successful validation via `terraform validate` (Success! The configuration is valid).

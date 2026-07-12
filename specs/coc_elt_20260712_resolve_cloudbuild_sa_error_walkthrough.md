---
title: "Resolve Cloud Build trigger 400 / service account error by using coc-elt-runner service account"
project_id: "coc-elt"
nyutu_uuid: "5a080895-9b68-4d75-9362-9925099cfe56"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "cloudbuild"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_cloudbuild_sa_error_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T10:35:00-05:00
- **Objective**: Resolve Cloud Build 400 bad request / service account error by configuring the trigger to run as `coc-elt-runner` service account and granting it Logging Writer and Storage Admin roles.

### Executed Commands
- `terraform validate` inside `terraform/` to verify configurations.
- `git add .` and `git commit` to commit the modifications.

### State Mutations
- **Created**:
  - `specs/coc_elt_20260712_resolve_cloudbuild_sa_error_walkthrough.md`
- **Modified**:
  - `terraform/security.tf`
  - `terraform/cicd.tf`
  - `specs/coc_elt_20260712_resolve_cloudbuild_sa_error_implementation_plan.md`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Separating security resource concerns (`security.tf`) from CI/CD pipeline triggers (`cicd.tf`).
- **Least Privilege Principle**: Utilizing a dedicated user-managed service account (`coc-elt-runner`) for trigger execution with specific logging and storage access, avoiding the default Cloud Build service account.

### Validation Artifacts
- Output of `terraform validate` indicating configuration is valid.

### Technical Debt
- None identified.

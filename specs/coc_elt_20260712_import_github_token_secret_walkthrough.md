---
title: "Import and Use Pre-existing Secret for GitHub Connection in Terraform"
project_id: "coc-elt"
nyutu_uuid: "229414f4-589d-461a-ad69-fd786bd07cdd"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "secret_manager"
  - "cloud_build"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_import_github_token_secret_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T09:55:00-05:00
- **Objective**: Import a pre-existing GitHub connection OAuth token secret, grant secret accessor role to the Cloud Build service agent, and use it in the Google Cloud Build v2 connection resource.

### Executed Commands
- `terraform fmt` (run inside `terraform/` directory)
- `terraform validate` (run inside `terraform/` directory)
- `git commit`

### State Mutations
- **Created**:
  - `specs/coc_elt_20260712_import_github_token_secret_walkthrough.md`
- **Modified**:
  - `terraform/cicd.tf`
  - `specs/coc_elt_20260712_import_github_token_secret_implementation_plan.md`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Handled the GitHub Token integration specifically within the `cicd.tf` configuration, isolating secret access and IAM policies related to CI/CD connection.
- **Dependency Inversion (DIP)**: Used a `google_secret_manager_secret` data source to reference the externally created and managed secret, avoiding hardcoded secret values and lifecycle management of non-owned resources in this module.
- **Least Privilege**: Granted `roles/secretmanager.secretAccessor` strictly to the Cloud Build service agent service account on the specific secret needed, minimizing the security footprint.

### Validation Artifacts
- Successful execution of `terraform validate` inside the `terraform` directory.

### Technical Debt
- None identified.

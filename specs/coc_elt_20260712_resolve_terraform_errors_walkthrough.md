---
title: "Resolve Terraform Apply Errors and Document Deployment Process Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "bdd749d0-be09-4b24-a275-2610906a166a"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "bug-fix"
  - "deployment"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_terraform_errors_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T10:15:00-05:00
- **Objective**: Resolve Terraform apply errors by enabling missing APIs, bootstrapping the Cloud Run Job, resolving IAM dependency race conditions, and documenting the 2-step targeted deployment workflow.

### Executed Commands
- `terraform validate` inside `terraform/` to verify configurations.
- `git add .` and `git commit` to commit all modifications to git.

### State Mutations
- **Created**:
  - `specs/coc_elt_20260712_resolve_terraform_errors_walkthrough.md`
- **Modified**:
  - `terraform/services.tf`
  - `terraform/compute.tf`
  - `terraform/security.tf`
  - `README.md`
  - `specs/coc-elt_20260711_cross-project-elt-pipeline_walkthrough.md`
  - `specs/coc_elt_20260712_resolve_terraform_errors_implementation_plan.md`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: API enablement (`services.tf`), computing resources (`compute.tf`), and IAM security bindings (`security.tf`) are decoupled and keep their respective responsibilities.
- **Dependency Inversion (DIP)**: By using a dynamic reference (`google_cloud_run_v2_job.elt_job.name`) instead of a hardcoded string, Terraform can infer dependency graph ordering correctly, preventing a resource-not-found 404 race condition.
- **Bootstrapping Pattern**: Cloud Run job starts with a public bootstrap container image (`gcr.io/cloudrun/hello`) to solve the chicken-and-egg dependency where CI/CD triggers build the custom container but cannot be provisioned until the job configuration exists.

### Validation Artifacts
- Successful `terraform validate` run confirming configuration validity.

### Technical Debt
- Manual intervention is required to authorize the Cloud Build GitHub connection in GCP Console. This is an OAuth constraint of GCP and cannot be fully automated via Terraform.

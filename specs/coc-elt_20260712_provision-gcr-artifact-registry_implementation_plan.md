---
title: "Provision Backing Artifact Registry Repository for GCR"
project_id: "coc-elt"
nyutu_uuid: "9ddf92eb-b617-445d-b3b2-041e80634aa0"
artifact_type: "Infrastructure Pattern"
tags:
  - "gcp"
  - "terraform"
  - "artifact-registry"
  - "gcr"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260712_provision-gcr-artifact-registry_implementation_plan.md"
---

# Implementation Plan - Provision Backing Artifact Registry Repository for GCR in Terraform

This document defines the requirements, technical decisions, and concrete tasks to explicitly provision the backing Artifact Registry repository for GCR in Terraform.

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Artifact Registry API)**: The system MUST enable `"artifactregistry.googleapis.com"` in the `google_project_service.compute_services` resource inside `terraform/services.tf`.
- **R2 (GCR Artifact Registry Repository)**: The system MUST declare a `google_artifact_registry_repository` resource named `gcr_repo` in `terraform/cicd.tf`.
- **R3 (Repository Configuration)**: WHILE provisioning `gcr_repo`, the system MUST configure `location` to `"us"`, `repository_id` to `"gcr.io"`, and `format` to `"DOCKER"`.
- **R4 (Dependency Link)**: The system MUST add a dependency link (`depends_on`) from the `google_artifact_registry_repository.gcr_repo` resource to the `google_project_service.compute_services` resource to ensure correct provisioning order.
- **R5 (API Enablement Failure)**: IF the `"artifactregistry.googleapis.com"` service fails to enable, THEN the system MUST fail the provisioning of `google_artifact_registry_repository.gcr_repo`.

---

## 2. Technical Decisions (HOW it will be built)

- **Files**:
  - `terraform/services.tf` (modified)
  - `terraform/cicd.tf` (modified)

- **Signatures**:
  - Add `"artifactregistry.googleapis.com"` to the `for_each` set in `google_project_service.compute_services`.
  - Add the resource `google_artifact_registry_repository.gcr_repo`.

- **Error Handling**:
  - Terraform built-in resource provisioning error handling. By declaring `depends_on = [google_project_service.compute_services]`, we ensure Terraform waits for the API to be enabled before creating the repository, preventing "API not enabled" errors.

- **Discarded Alternatives**:
  - *Discarded Alternative 1*: Provisioning without `depends_on`. Discarded because it introduces a race condition where repository creation could fail if the API enablement is still in progress.
  - *Discarded Alternative 2*: Using a single-region location (e.g. `us-central1`). Discarded because `gcr.io` requires the multi-region `"us"` location to map correctly to the legacy container registry endpoint.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `"artifactregistry.googleapis.com"` to the `for_each` set of `google_project_service.compute_services` in `terraform/services.tf`.
- [x] T2 — Declare the `google_artifact_registry_repository` named `gcr_repo` in `terraform/cicd.tf`. Configure the project, location, repository ID, format, and dependency link.
- [x] T3 — Validate the plan using `terraform plan`.
- [x] T4 — Apply changes using `terraform apply`.

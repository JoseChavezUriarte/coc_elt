---
title: "Provision Backing Artifact Registry Repository for GCR"
project_id: "coc-elt"
nyutu_uuid: "ca2d9a93-ddf9-4108-bcc9-118864ea3991"
artifact_type: "Infrastructure Pattern"
tags:
  - "gcp"
  - "terraform"
  - "artifact-registry"
  - "gcr"
  - "walkthrough"
source_uri: "specs/coc-elt_20260712_provision-gcr-artifact-registry_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T10:44:57-05:00
- **Objective**: Provision the backing Artifact Registry repository for GCR in Terraform to support the Clash of Clans pipeline deployment.

### Executed Commands
- `terraform validate` (run in `terraform/` directory)
- `git add terraform/services.tf terraform/cicd.tf specs/coc-elt_20260712_provision-gcr-artifact-registry_implementation_plan.md specs/coc-elt_20260712_provision-gcr-artifact-registry_walkthrough.md`
- `git commit -m "feat(infra): provision backing Artifact Registry repository for GCR"`

### State Mutations
- `[Modified] terraform/services.tf`
- `[Modified] terraform/cicd.tf`
- `[Modified] specs/coc-elt_20260712_provision-gcr-artifact-registry_implementation_plan.md`
- `[Created] specs/coc-elt_20260712_provision-gcr-artifact-registry_walkthrough.md`

### Architectural Decisions (ADR) and SOLID
- **Architectural Decision**: Provisioning `gcr.io` as an Artifact Registry repository with DOCKER format in location `"us"`. This ensures backwards compatibility with the GCR API while using the modern Artifact Registry service.
- **SOLID Compliance**:
  - *Single Responsibility*: `services.tf` is solely responsible for service API enablement, while `cicd.tf` is responsible for CI/CD resources.
  - *Dependency Inversion/Liskov*: The repository depends on service enablement (`depends_on = [google_project_service.compute_services]`), ensuring correct deployment ordering.

### Validation Artifacts
- Output of `terraform validate`:
```
Success! The configuration is valid.
```

### Technical Debt
- None.

---
title: "Extract Cloud Workflows into External Template File"
project_id: "coc-elt"
nyutu_uuid: "947bd6e1-0bda-49e8-952b-6c85b89ad755"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "workflow"
  - "walkthrough"
source_uri: "specs/coc-elt_20260712_extract-workflow-template_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T08:05:00-05:00
- **Objective**: Extract the Cloud Workflows source contents from `terraform/compute.tf` into a new external template file `terraform/workflow.yaml`.

### Executed Commands
- `terraform validate` (run in `terraform/` directory)

### State Mutations
- **Created**:
  - `terraform/workflow.yaml`
  - `specs/coc-elt_20260712_extract-workflow-template_implementation_plan.md`
  - `specs/coc-elt_20260712_extract-workflow-template_walkthrough.md`
- **Modified**:
  - `terraform/compute.tf`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Separating infrastructure provisioning configuration (`compute.tf`) from application logic definitions (`workflow.yaml`). This makes it easier to read and maintain the workflow pipeline code independently of Terraform resources.
- **Open/Closed Principle (OCP)**: The workflow definition is parameterized via HCL `templatefile`, making it open to extensions (new regional parameters, etc.) without altering the HCL resource structure.

### Validation Artifacts
- Successful execution of `terraform validate` inside the `terraform` directory.

### Technical Debt
- None identified.

---
title: "Extract Cloud Workflows into External Template File"
project_id: "coc-elt"
nyutu_uuid: "c2d7487d-c09b-4702-acd9-f418cc85c8c1"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "workflow"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260712_extract-workflow-template_implementation_plan.md"
---

# Extract Cloud Workflows into External Template File

This plan implements extracting the Cloud Workflows source contents from `terraform/compute.tf` into `terraform/workflow.yaml`.

## 1. Requirements

- **R1 (Template File Creation)**: Create `terraform/workflow.yaml` containing the YAML workflows definition.
  - Parameterize project and region variables as `${compute_project_id}`, `${region}`, and `${data_project_id}`.
  - Escape runtime expressions as `$${expression}` (e.g. `$${operation.name}`).
- **R2 (Compute Config Update)**: Modify `terraform/compute.tf` to replace inline heredoc with `templatefile` reference.
- **R3 (Validation)**: Run `terraform validate` to verify correctness.

## 2. Technical Decisions

- **SOLID Principles**: Applying Single Responsibility Principle (SRP) by moving the workflow definition out of the Terraform resource file into its own dedicated YAML template.

## 3. Implementation Tasks

- [x] T1 — Create `terraform/workflow.yaml` with the parameterized and escaped workflows YAML.
- [x] T2 — Replace inline `source_contents` in `terraform/compute.tf` with the `templatefile` call.
- [x] T3 — Run `terraform validate` to verify the configuration.

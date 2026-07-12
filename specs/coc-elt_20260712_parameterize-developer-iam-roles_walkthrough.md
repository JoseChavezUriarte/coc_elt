---
title: "Configure Dynamic Parameterization for Developer IAM Roles Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "969b3b33-7c98-4aeb-aef2-7a0cfce68202"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "iam"
  - "walkthrough"
source_uri: "specs/coc-elt_20260712_parameterize-developer-iam-roles_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T13:53:14-05:00
- **Objective**: Implement dynamic parameterization for developer IAM roles (granting `serviceAccountUser` role on the ELT runner service account to a configurable set of developer emails).

### Executed Commands
- `terraform validate` (run in `terraform/` directory)

### State Mutations
- **Created**:
  - `specs/coc-elt_20260712_parameterize-developer-iam-roles_walkthrough.md`
- **Modified**:
  - `terraform/variables.tf` (added variable `dataform_developer_emails` of type `set(string)`)
  - `terraform/terraform.tfvars` (added `chavezur.jose@gmail.com` to the list of developer emails)
  - `terraform/security.tf` (replaced hardcoded email with parameterized `google_service_account_iam_member.developer_sa_user` using `for_each`)
  - `specs/coc-elt_20260712_parameterize-developer-iam-roles_implementation_plan.md` (checked off tasks T1 to T4)
  - `specs/nyutu_index.json` (indexed the implementation plan and walkthrough)

### Architectural Decisions (ADR) and SOLID
- **Open/Closed Principle (OCP)**: The service account assignment is now open to adding new developers (via configuration changes in `terraform.tfvars` or variables) but closed to modification of the IAM binding declaration in the core configuration file (`security.tf`).
- **DRY (Don't Repeat Yourself)**: Using `for_each` dynamically loops over a configured set instead of having duplicate resource blocks for each individual developer.
- **Redundancy Removal**: Removed redundant `depends_on = [google_project_service.compute_services]` on the IAM member resource, because the IAM member depends implicitly on `google_service_account.elt_runner.name`, which itself depends on `google_project_service.compute_services`.

### Validation Artifacts
- Successful execution of `terraform validate` inside the `terraform/` directory.

### Technical Debt
- None identified.

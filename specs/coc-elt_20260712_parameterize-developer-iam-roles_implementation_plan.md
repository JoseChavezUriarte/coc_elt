---
title: "Configure Dynamic Parameterization for Developer IAM Roles"
project_id: "coc-elt"
nyutu_uuid: "d62192a3-1aac-4889-912c-97b6bc69eed6"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "iam"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260712_parameterize-developer-iam-roles_implementation_plan.md"
---

# Implementation Plan - Configure Dynamic Parameterization for Developer IAM Roles

This implementation plan outlines the details to parameterize the developer IAM role bindings dynamically using Terraform. Rather than hardcoding individual developer emails, we will declare a variable list and loop over it using `for_each`.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1**: The system MUST declare a new variable `dataform_developer_emails` of type `set(string)` in [variables.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/variables.tf). (Ubiquitous)
- **R2**: The system MUST define the `dataform_developer_emails` value containing `"chavezur.jose@gmail.com"` in [terraform.tfvars](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/terraform.tfvars). (Ubiquitous)
- **R3**: The system MUST declare the resource `google_service_account_iam_member.developer_sa_user` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) using a `for_each` loop over `var.dataform_developer_emails`. (Ubiquitous)
- **R4**: The system MUST NOT contain the hardcoded email address `chavezur.jose@gmail.com` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Ubiquitous)
- **R5**: The system MUST NOT include the `depends_on = [google_project_service.compute_services]` block within `google_service_account_iam_member.developer_sa_user`. (Ubiquitous)
- **R6**: WHEN the user runs `terraform validate` in the [terraform](file:///home/scheveningen/documents/proyectos/coc_elt/terraform) directory, the command MUST exit successfully with status 0. (Event)
- **R7**: IF a developer email is added or removed from `var.dataform_developer_emails`, THEN the system MUST dynamically apply the corresponding IAM bindings without modifying the code in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf). (Unwanted)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
* [variables.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/variables.tf) (Modify to declare new variable)
* [terraform.tfvars](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/terraform.tfvars) (Modify to assign variable value)
* [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) (Add `google_service_account_iam_member.developer_sa_user` resource block)

### New Signatures

#### Variables ([variables.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/variables.tf)):
```hcl
variable "dataform_developer_emails" {
  type        = set(string)
  description = "A set of developer email addresses to grant serviceAccountUser permissions on the runner service account."
  default     = []
}
```

#### Values ([terraform.tfvars](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/terraform.tfvars)):
```hcl
dataform_developer_emails = [
  "chavezur.jose@gmail.com"
]
```

#### Resources ([security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf)):
```hcl
resource "google_service_account_iam_member" "developer_sa_user" {
  for_each           = var.dataform_developer_emails
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value}"
}
```

### Dependency Resolution (DAG)
The resource `google_service_account_iam_member.developer_sa_user` references `google_service_account.elt_runner.name` for its `service_account_id` attribute. 
Since `google_service_account.elt_runner` explicitly depends on the activation of compute services via `depends_on = [google_project_service.compute_services]`, the Terraform DAG inherently guarantees that:
1. `google_project_service.compute_services` is created first.
2. `google_service_account.elt_runner` is created second.
3. `google_service_account_iam_member.developer_sa_user` is created third.

Thus, adding `depends_on = [google_project_service.compute_services]` to the IAM member is redundant and can be omitted.

### Error Handling
* Any syntax or type errors in the configurations will be caught during the execution of `terraform validate`.
* Standard GCP IAM assignment failures (e.g. trying to assign an invalid email format) will be validated by the Terraform GCP provider schemas.

### Discarded Alternatives
* **Alternative 1: Hardcoding the emails using a local list block inside `security.tf`**
  - *Why discarded*: Does not solve the goal of dynamic parameterization for different environments/developers, and keeps hardcoded settings in the source policy code.
* **Alternative 2: Using `list(string)` type instead of `set(string)`**
  - *Why discarded*: Terraform `for_each` requires a set or map to guarantee unique and stable keys. A list of strings would require `toset()` in the `for_each` expression. Using `set(string)` directly is cleaner and safer.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Declare `dataform_developer_emails` variable in `terraform/variables.tf`.
- [x] T2 — Add `dataform_developer_emails` values to `terraform/terraform.tfvars`.
- [x] T3 — Add resource `google_service_account_iam_member.developer_sa_user` in `terraform/security.tf` using `for_each` over `var.dataform_developer_emails`.
- [x] T4 — Run `terraform validate` in the `terraform` directory.


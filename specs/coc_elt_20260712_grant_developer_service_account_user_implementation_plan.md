---
title: "Grant iam.serviceAccountUser to developer for local terraform apply"
project_id: "coc-elt"
nyutu_uuid: "269329e0-7cc3-4fd5-81cc-3df6d555988b"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp"
  - "iam"
  - "dataform"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_grant_developer_service_account_user_implementation_plan.md"
---

# Implementation Plan - Grant iam.serviceAccountUser to Developer

This implementation plan details the configuration change required to grant the developer (`chavezur.jose@gmail.com`) the necessary permissions to act as the `coc-elt-runner` service account. This resolves the 403 Forbidden error encountered when executing `terraform apply` locally to create/update the Dataform repository:

`Error 403: The caller does not have permission to act as service account: coc-elt-runner@elt-coc.iam.gserviceaccount.com.`

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1**: The system MUST declare a `google_service_account_iam_member` resource in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) to assign the `roles/iam.serviceAccountUser` role on the `elt_runner` service account to `user:chavezur.jose@gmail.com`. (Ubiquitous)
- **R2**: WHEN the developer executes `terraform validate` in the [terraform](file:///home/scheveningen/documents/proyectos/coc_elt/terraform) directory, the system MUST exit with status 0 (no syntax or configuration errors). (Event)
- **R3**: IF the developer identity `chavezur.jose@gmail.com` attempts to deploy the Dataform repository associated with the `coc-elt-runner` service account, THEN the system MUST ensure the required `iam.serviceAccounts.actAs` permission is explicitly granted beforehand. (Unwanted)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
* [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf) (Add a new resource block)

### New Signatures
We will declare the following resource block in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf):

```hcl
resource "google_service_account_iam_member" "developer_sa_user" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:chavezur.jose@gmail.com"

  depends_on = [google_project_service.compute_services]
}
```

### Error Handling
- Since we are modifying HCL configuration, syntax validation will be caught by `terraform validate`.
- If the developer does not have sufficient administrative permissions to apply this IAM policy change, the initial apply might fail with a permission error. However, assuming the deployer has IAM Admin/Owner permissions on the GCP projects, this resource will apply successfully and subsequently allow the Dataform repository creation to proceed.

### Discarded Alternatives
- **Alternative 1: Using Project-level IAM bindings (`google_project_iam_member`)**
  - *Why discarded*: Granting project-wide Service Account User access is insecure and violates the Least Privilege principle. The role `roles/iam.serviceAccountUser` should be scoped directly to the specific service account (`google_service_account.elt_runner.name`) rather than the entire project.
- **Alternative 2: Passing the developer email as a variable**
  - *Why discarded*: While cleaner, adding a variable requires updating `variables.tf`, `terraform.tfvars`, and potentially CI/CD configs. For this specific development bypass, hardcoding the developer email in `security.tf` is the most direct solution requested.

## 3. Implementation Tasks (Concrete STEPS)

- [ ] T1 — Add `google_service_account_iam_member.developer_sa_user` in [security.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/security.tf).
- [ ] T2 — Run `terraform validate` in the [terraform](file:///home/scheveningen/documents/proyectos/coc_elt/terraform) directory.

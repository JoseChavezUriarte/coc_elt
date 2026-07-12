---
title: "Resolve Cloud Run Job image revert conflict by ignoring template image changes in Terraform"
project_id: "coc-elt"
nyutu_uuid: "62fea5a2-001b-4827-9e9f-1337cd431610"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "cloudrun"
  - "gcp"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_cloudrun_image_revert_conflict_implementation_plan.md"
---

# Implementation Plan - Resolve Cloud Run Job Image Revert Conflict

This implementation plan details the steps to resolve the conflict where running `terraform apply` overrides the currently deployed pipeline container image of the Cloud Run Job with the bootstrap image (`gcr.io/cloudrun/hello`).

This is resolved by adding a `lifecycle` block to the `google_cloud_run_v2_job.elt_job` resource inside `terraform/compute.tf` to ignore changes made to the container image field.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Ignore Image Changes)**: The system MUST ignore changes to the container image inside the `google_cloud_run_v2_job.elt_job` resource by specifying a `lifecycle` block with `ignore_changes = [template[0].template[0].containers[0].image]`. (Ubiquitous)
- **R2 (Terraform Validation)**: WHEN the Terraform configurations are validated, the system MUST pass all validation checks without syntax or configuration errors. (Event)
- **R3 (Error Prevention / Image Preserved)**: WHEN a `terraform apply` is executed, the system MUST NOT overwrite/revert the deployed container image of the `google_cloud_run_v2_job.elt_job` back to the bootstrap image (`gcr.io/cloudrun/hello`). (Event)
- **R4 (Error Handling)**: IF the `lifecycle` block has invalid syntax, THEN `terraform validate` MUST report the syntax error. (Unwanted)
- **R5 (State Updates)**: WHILE other attributes of the Cloud Run Job template (e.g. environment variables, service account) are modified in HCL, the system MUST apply those updates during `terraform apply`. (State)

## 2. Technical Decisions (HOW it will be built)

### Affected Files
*   [terraform/compute.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/compute.tf) (Modified to include the `lifecycle` block in `google_cloud_run_v2_job.elt_job`)

### Resource Modification
We will insert the `lifecycle` block inside the `google_cloud_run_v2_job.elt_job` resource block in [terraform/compute.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/compute.tf#L1-L44):

```hcl
resource "google_cloud_run_v2_job" "elt_job" {
  name                = "coc-elt-job"
  location            = var.region
  project             = var.compute_project_id
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.elt_runner.email

      containers {
        image = "gcr.io/cloudrun/hello"

        env {
          name  = "DATA_PROJECT_ID"
          value = var.data_project_id
        }
        env {
          name  = "CLAN_TAG"
          value = var.clan_tag
        }
        env {
          name = "COC_APIKEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.coc_api_key.secret_id
              version = "latest"
            }
          }
        }
      }

      vpc_access {
        egress = "ALL_TRAFFIC"
        network_interfaces {
          network    = google_compute_network.vpc.name
          subnetwork = google_compute_subnetwork.subnet.name
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }

  depends_on = [google_project_service.compute_services]
}
```

### Error Handling
- Running `terraform validate` will verify the syntax of the added `lifecycle` block.
- Any syntax errors (e.g. incorrect block nesting or incorrect list index addressing) will be caught and must be fixed prior to applying.

### Discarded Alternatives
*   **Alternative 1: Parameterizing the image tag using a Terraform variable and updating it in CI/CD**
    *   *Why discarded*: While possible, this requires the CI/CD pipeline to write the new image tag back to Terraform state or variables, creating a circular dependency/tight coupling between the infrastructure code repository and the application deployment pipeline. It is standard GCP practice to allow the CI/CD deployment tool to directly update the job image, while Terraform defines the initial/bootstrap image and ignores subsequent changes.

## 3. Implementation Tasks (Concrete STEPS)

- [ ] T1 — Add the `lifecycle` block inside the `google_cloud_run_v2_job.elt_job` resource in `terraform/compute.tf`.
- [ ] T2 — Run `terraform validate` in the `terraform/` directory.

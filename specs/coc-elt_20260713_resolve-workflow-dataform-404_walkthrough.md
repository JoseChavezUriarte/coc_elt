---
title: "Resolve 404 Not Found in run_dataform GCP Workflow Step Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "ce8c7de6-ff6a-4352-a980-6eef581a12d2"
artifact_type: "Infrastructure Pattern"
tags:
  - "terraform"
  - "gcp-workflows"
  - "dataform"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_resolve-workflow-dataform-404_walkthrough.md"
---

# Walkthrough: Resolve 404 Not Found in `run_dataform` Step

This document walks through the modifications made to the GCP Workflow configuration to solve the 404 Not Found error in the `run_dataform` step.

## 1. Implementation Details

### 1.1 Modifying `terraform/workflow.yaml`
- Replaced the static Dataform execution reference with a dynamic compilation step (`compile_dataform`):
  ```yaml
  - compile_dataform:
      call: http.post
      args:
        url: https://dataform.googleapis.com/v1beta1/projects/${data_project_id}/locations/${region}/repositories/coc-elt/compilationResults
        auth:
          type: OAuth2
        body:
          gitCommitish: "main"
          codeCompilationConfig:
            defaultDatabase: "${data_project_id}"
      result: compilation
  ```
  This creates a compilation result on-the-fly and overrides `defaultDatabase` using the target database/project ID.

- Updated the `run_dataform` step to refer to the compilation result dynamically using `$${compilation.body.name}` instead of a static compile path that triggers the 404 error:
  ```yaml
  - run_dataform:
      call: http.post
      args:
        url: https://dataform.googleapis.com/v1beta1/projects/${data_project_id}/locations/${region}/repositories/coc-elt/workflowInvocations
        auth:
          type: OAuth2
        body:
          compilationResult: $${compilation.body.name}
      result: df_invocation
  ```

- Added an active polling loop to sleep, retrieve status, and raise failures or return results appropriately:
  ```yaml
  - wait_dataform:
      call: sys.sleep
      args:
        seconds: 15
      next: get_dataform_status
  - get_dataform_status:
      call: http.get
      args:
        url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
        auth:
          type: OAuth2
      result: df_status
  - check_dataform_status:
      switch:
        - condition: $${df_status.body.state == "SUCCEEDED"}
          next: return_result
        - condition: $${df_status.body.state == "FAILED" or df_status.body.state == "CANCELLED"}
          next: raise_dataform_error
      next: wait_dataform
  - raise_dataform_error:
      raise: $${"Dataform workflow invocation " + df_status.body.name + " finished with state: " + df_status.body.state}
  - return_result:
      return: $${df_status.body}
  ```

## 2. Test Verification

### 2.1 Verification with Terraform Validate
Ran `terraform validate` in the `terraform/` directory:
```bash
terraform validate
```
Output:
```
Success! The configuration is valid.
```

### 2.2 Verification with Terraform Plan
Ran `terraform plan` in the `terraform/` directory:
```bash
terraform plan
```
Output:
```
google_project_iam_member.bq_job_user: Refreshing state... [id=swift-capsule-492817-a7/roles/bigquery.jobUser/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_service_account_iam_member.cloudbuild_sa_user: Refreshing state... [id=projects/elt-coc/serviceAccounts/coc-elt-runner@elt-coc.iam.gserviceaccount.com/roles/iam.serviceAccountUser/serviceAccount:51301996950@cloudbuild.gserviceaccount.com]
google_project_iam_member.workflows_invoker: Refreshing state... [id=elt-coc/roles/workflows.invoker/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_bigquery_dataset_iam_member.bq_data_editor: Refreshing state... [id=projects/swift-capsule-492817-a7/datasets/coc_bronze/roles/bigquery.dataEditor/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_secret_manager_secret_iam_member.accessor: Refreshing state... [id=projects/elt-coc/secrets/COC_APIKEY/roles/secretmanager.secretAccessor/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_project_iam_member.elt_runner_artifact_registry_writer: Refreshing state... [id=elt-coc/roles/artifactregistry.repoAdmin/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_workflows_workflow.workflow: Refreshing state... [id=projects/elt-coc/locations/us-central1/workflows/coc-elt-workflow]
google_project_iam_member.elt_runner_logging_writer: Refreshing state... [id=elt-coc/roles/logging.logWriter/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_service_account_iam_member.sa_user_self: Refreshing state... [id=projects/elt-coc/serviceAccounts/coc-elt-runner@elt-coc.iam.gserviceaccount.com/roles/iam.serviceAccountUser/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_project_iam_member.elt_runner_run_viewer: Refreshing state... [id=elt-coc/roles/run.viewer/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
google_project_iam_member.dataform_editor: Refreshing state... [id=swift-capsule-492817-a7/roles/dataform.editor/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]
time_sleep.wait_for_dataform_iam: Refreshing state... [id=2026-07-12T19:11:57Z]
google_cloudbuildv2_repository.github_repo: Refreshing state... [id=projects/elt-coc/locations/us-central1/connections/coc-elt-connection/repositories/coc-elt]
google_dataform_repository.coc_elt: Refreshing state... [id=projects/swift-capsule-492817-a7/locations/us-central1/repositories/coc-elt]
google_compute_router.router: Refreshing state... [id=projects/elt-coc/regions/us-central1/routers/coc-elt-router]
google_compute_subnetwork.subnet: Refreshing state... [id=projects/elt-coc/regions/us-central1/subnetworks/coc-elt-subnet]
google_cloudbuild_trigger.github_trigger: Refreshing state... [id=projects/elt-coc/locations/us-central1/triggers/f070cb8b-cb25-418c-a4c5-7e5d8d687075]
google_cloud_scheduler_job.scheduler: Refreshing state... [id=projects/elt-coc/locations/us-central1/jobs/coc-elt-scheduler]
google_cloud_run_v2_job.elt_job: Refreshing state... [id=projects/elt-coc/locations/us-central1/jobs/coc-elt-job]
google_compute_router_nat.nat: Refreshing state... [id=elt-coc/us-central1/coc-elt-router/coc-elt-nat]
google_cloud_run_v2_job_iam_member.run_developer: Refreshing state... [id=projects/elt-coc/locations/us-central1/jobs/coc-elt-job/roles/run.developer/serviceAccount:coc-elt-runner@elt-coc.iam.gserviceaccount.com]

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  ~ update in-place

Terraform will perform the following actions:

  # google_workflows_workflow.workflow will be updated in-place
  ~ resource "google_workflows_workflow" "workflow" {
        id                      = "projects/elt-coc/locations/us-central1/workflows/coc-elt-workflow"
        name                    = "coc-elt-workflow"
      ~ source_contents         = <<-EOT
            main:
              steps:
                - run_job:
                    call: googleapis.run.v2.projects.locations.jobs.run
                    args:
                      name: "projects/elt-coc/locations/us-central1/jobs/coc-elt-job"
                    result: operation
                - wait_job:
                    call: googleapis.run.v2.projects.locations.operations.get
                    args:
                      name: ${operation.name}
                    result: op_status
                - check_job_status:
                    switch:
                      - condition: ${op_status.done == true}
                        next: check_job_error
                    next: wait_and_poll
                - wait_and_poll:
                    call: sys.sleep
                    args:
                      seconds: 10
                    next: wait_job
                - check_job_error:
                    switch:
                      - condition: ${"error" in op_status}
                        raise: ${op_status.error}
          -         next: run_dataform
          +         next: compile_dataform
          +     - compile_dataform:
          +         call: http.post
          +         args:
          +           url: https://dataform.googleapis.com/v1beta1/projects/swift-capsule-492817-a7/locations/us-central1/repositories/coc-elt/compilationResults
          +           auth:
          +             type: OAuth2
          +           body:
          +             gitCommitish: "main"
          +             codeCompilationConfig:
          +               defaultDatabase: "swift-capsule-492817-a7"
          +         result: compilation
                - run_dataform:
                    call: http.post
                    args:
                      url: https://dataform.googleapis.com/v1beta1/projects/swift-capsule-492817-a7/locations/us-central1/repositories/coc-elt/workflowInvocations
                      auth:
                        type: OAuth2
                      body:
          -             compilationResult: projects/swift-capsule-492817-a7/locations/us-central1/repositories/coc-elt/compilationResults/main
          +             compilationResult: ${compilation.body.name}
                    result: df_invocation
          +     - wait_dataform:
          +         call: sys.sleep
          +         args:
          +           seconds: 15
          +         next: get_dataform_status
          +     - get_dataform_status:
          +         call: http.get
          +         args:
          +           url: https://dataform.googleapis.com/v1beta1/${df_invocation.body.name}
          +           auth:
          +             type: OAuth2
          +         result: df_status
          +     - check_dataform_status:
          +         switch:
          +           - condition: ${df_status.body.state == "SUCCEEDED"}
          +             next: return_result
          +           - condition: ${df_status.body.state == "FAILED" or df_status.body.state == "CANCELLED"}
          +             next: raise_dataform_error
          +         next: wait_dataform
          +     - raise_dataform_error:
          +         raise: ${"Dataform workflow invocation " + df_status.body.name + " finished with state: " + df_status.body.state}
                - return_result:
          -         return: ${df_invocation.body}
          +         return: ${df_status.body}
        EOT
        # (17 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```
The plan shows only the in-place updates to `google_workflows_workflow.workflow`.

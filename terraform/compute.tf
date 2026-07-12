resource "google_cloud_run_v2_job" "elt_job" {
  name     = "coc-elt-job"
  location = var.region
  project  = var.compute_project_id

  template {
    template {
      service_account = google_service_account.elt_runner.email

      containers {
        image = "gcr.io/${var.compute_project_id}/coc-elt-pipeline:latest"

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
              secret  = data.google_secret_manager_secret.coc_api_key.secret_id
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
}

resource "google_workflows_workflow" "workflow" {
  name            = "coc-elt-workflow"
  region          = var.region
  project         = var.compute_project_id
  description     = "Orchestrates the Clash of Clans ELT pipeline: Cloud Run Job -> Dataform"
  service_account = google_service_account.elt_runner.id

  source_contents = <<EOF
main:
  steps:
    - run_job:
        call: googleapis.run.v2.projects.locations.jobs.run
        args:
          name: "projects/${var.compute_project_id}/locations/${var.region}/jobs/coc-elt-job"
        result: operation
    - wait_job:
        call: googleapis.run.v2.projects.locations.operations.get
        args:
          name: \$${operation.name}
        result: op_status
    - check_job_status:
        switch:
          - condition: \$${op_status.done == true}
            next: check_job_error
        next: wait_and_poll
    - wait_and_poll:
        call: sys.sleep
        args:
          seconds: 10
        next: wait_job
    - check_job_error:
        switch:
          - condition: \$${"error" in op_status}
            raise: \$${op_status.error}
        next: run_dataform
    - run_dataform:
        call: googleapis.dataform.v1beta1.projects.locations.repositories.workflowInvocations.create
        args:
          parent: "projects/${var.data_project_id}/locations/${var.region}/repositories/coc-elt"
          body:
            compilationResult: "projects/${var.data_project_id}/locations/${var.region}/repositories/coc-elt/compilationResults/main"
        result: df_invocation
    - return_result:
        return: \$${df_invocation}
EOF
}

resource "google_cloud_scheduler_job" "scheduler" {
  name             = "coc-elt-scheduler"
  description      = "Triggers the ELT Workflow daily"
  schedule         = "0 2 * * *"
  time_zone        = "UTC"
  region           = var.region
  project          = var.compute_project_id
  attempt_deadline = "320s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/projects/${var.compute_project_id}/locations/${var.region}/workflows/${google_workflows_workflow.workflow.name}/executions"

    oauth_token {
      service_account_email = google_service_account.elt_runner.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}

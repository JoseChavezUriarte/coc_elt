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

  depends_on = [google_project_service.compute_services]
}

resource "google_workflows_workflow" "workflow" {
  name            = "coc-elt-workflow"
  region          = var.region
  project         = var.compute_project_id
  description     = "Orchestrates the Clash of Clans ELT pipeline: Cloud Run Job -> Dataform"
  service_account = google_service_account.elt_runner.id

  source_contents = templatefile("${path.module}/workflow.yaml", {
    compute_project_id = var.compute_project_id
    data_project_id    = var.data_project_id
    region             = var.region
  })

  depends_on = [google_project_service.compute_services]
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

  depends_on = [google_project_service.compute_services]
}

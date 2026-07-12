resource "google_cloudbuildv2_connection" "github_conn" {
  project  = var.compute_project_id
  location = var.region
  name     = "coc-elt-connection"

  github_config {
    app_installation_id = var.github_app_installation_id
  }

  depends_on = [google_project_service.compute_services]
}

resource "google_cloudbuildv2_repository" "github_repo" {
  project           = var.compute_project_id
  location          = var.region
  name              = "coc-elt"
  parent_connection = google_cloudbuildv2_connection.github_conn.id
  remote_uri        = var.github_repository_url

  depends_on = [google_project_service.compute_services]
}

resource "google_cloudbuild_trigger" "github_trigger" {
  project     = var.compute_project_id
  location    = var.region
  name        = "coc-elt-trigger"
  description = "Trigger for Clash of Clans ELT pipeline on main branch push"

  repository_event_config {
    repository = google_cloudbuildv2_repository.github_repo.id
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"

  depends_on = [google_project_service.compute_services]
}

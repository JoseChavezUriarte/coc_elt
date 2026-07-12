resource "google_cloudbuildv2_connection" "github_conn" {
  project  = var.compute_project_id
  location = var.region
  name     = "coc-elt-connection"

  github_config {
    app_installation_id = var.github_app_installation_id
    authorizer_credential {
      oauth_token_secret_version = "${data.google_secret_manager_secret.github_token.id}/versions/latest"
    }
  }

  depends_on = [
    google_project_service.compute_services,
    google_secret_manager_secret_iam_member.cloudbuild_secret_accessor
  ]
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

  service_account = "projects/${var.compute_project_id}/serviceAccounts/${google_service_account.elt_runner.email}"

  repository_event_config {
    repository = google_cloudbuildv2_repository.github_repo.id
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"

  depends_on = [google_project_service.compute_services]
}

data "google_secret_manager_secret" "github_token" {
  project   = var.compute_project_id
  secret_id = "github_conn-github-oauthtoken-61aafa"
}

resource "google_secret_manager_secret_iam_member" "cloudbuild_secret_accessor" {
  project   = var.compute_project_id
  secret_id = data.google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.compute_project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

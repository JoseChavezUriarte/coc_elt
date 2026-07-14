resource "google_service_account" "elt_runner" {
  account_id   = "coc-elt-runner"
  display_name = "Clash of Clans ELT Runner SA"
  project      = var.compute_project_id

  depends_on = [google_project_service.compute_services]
}

resource "google_secret_manager_secret" "coc_api_key" {
  secret_id = "COC_APIKEY"
  project   = var.compute_project_id
  replication {
    auto {}
  }

  depends_on = [google_project_service.compute_services]
}

resource "google_secret_manager_secret_version" "coc_api_key_version" {
  secret      = google_secret_manager_secret.coc_api_key.id
  secret_data = "PLACEHOLDER_CHANGE_ME"

  depends_on = [google_project_service.compute_services]
}

resource "google_secret_manager_secret_iam_member" "accessor" {
  project   = var.compute_project_id
  secret_id = google_secret_manager_secret.coc_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.data_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_bigquery_dataset_iam_member" "bq_data_editor" {
  project    = var.data_project_id
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "workflows_invoker" {
  project = var.compute_project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_cloud_run_v2_job_iam_member" "run_developer" {
  project  = var.compute_project_id
  location = var.region
  name     = google_cloud_run_v2_job.elt_job.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_service_account_iam_member" "sa_user_self" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "dataform_editor" {
  project = var.data_project_id
  role    = "roles/dataform.editor"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

data "google_project" "compute_project" {
  project_id = var.compute_project_id
}

resource "google_project_iam_member" "cloudbuild_run_developer" {
  project = var.compute_project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${data.google_project.compute_project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}

resource "google_service_account_iam_member" "cloudbuild_sa_user" {
  service_account_id = google_service_account.elt_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.compute_project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "elt_runner_logging_writer" {
  project = var.compute_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "elt_runner_storage_admin" {
  project = var.compute_project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "elt_runner_artifact_registry_writer" {
  project = var.compute_project_id
  role    = "roles/artifactregistry.repoAdmin"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

resource "google_project_iam_member" "elt_runner_run_viewer" {
  project = var.compute_project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.elt_runner.email}"

  depends_on = [google_project_service.compute_services]
}

data "google_project" "data_project" {
  project_id = var.data_project_id
}

resource "google_service_account" "dataform_runner" {
  account_id   = "coc-dataform-runner"
  display_name = "Clash of Clans Dataform Runner SA"
  project      = var.data_project_id
}

# NOTE: Granting roles/bigquery.dataEditor at the project level is considered technical debt.
# It MUST be refactored to google_bigquery_dataset_iam_member at the dataset level in a future iteration
# once dataset boundaries are fully codified.
resource "google_project_iam_member" "dataform_runner_bq_data_editor" {
  project = var.data_project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dataform_runner.email}"
}

resource "google_project_iam_member" "dataform_runner_bq_job_user" {
  project = var.data_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dataform_runner.email}"
}

resource "google_service_account_iam_member" "dataform_runner_sa_user" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "dataform_runner_sa_token_creator" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "developer_sa_user" {
  for_each           = var.dataform_developer_emails
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value}"
}

resource "google_service_account_iam_member" "elt_runner_dataform_sa_user" {
  service_account_id = google_service_account.dataform_runner.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.elt_runner.email}"
}

data "google_secret_manager_secret_version" "github_token_latest" {
  project = var.compute_project_id
  secret  = data.google_secret_manager_secret.github_token.secret_id
  version = "latest"
}

resource "google_secret_manager_secret_iam_member" "dataform_secret_accessor" {
  project   = var.compute_project_id
  secret_id = data.google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.data_project.number}@gcp-sa-dataform.iam.gserviceaccount.com"
}

resource "time_sleep" "wait_for_dataform_iam" {
  create_duration = "60s"

  depends_on = [
    google_service_account_iam_member.dataform_runner_sa_user,
    google_service_account_iam_member.dataform_runner_sa_token_creator,
    google_service_account_iam_member.developer_sa_user,
    google_service_account_iam_member.elt_runner_dataform_sa_user,
    google_secret_manager_secret_iam_member.dataform_secret_accessor
  ]
}






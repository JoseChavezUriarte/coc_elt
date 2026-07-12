resource "google_bigquery_dataset" "bronze" {
  dataset_id                 = "coc_bronze"
  friendly_name              = "Clash of Clans Bronze Dataset"
  description                = "Contains raw JSON payloads fetched from Clash of Clans API."
  location                   = var.region
  project                    = var.data_project_id
  delete_contents_on_destroy = false
}

locals {
  tables = ["clan", "members", "current_war", "capital_raids"]
}

resource "google_bigquery_table" "tables" {
  for_each   = toset(local.tables)
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  table_id   = "coc_${each.key}"
  project    = var.data_project_id

  time_partitioning {
    type  = "DAY"
    field = "extracted_at"
  }

  schema = jsonencode([
    {
      name = "extracted_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "payload"
      type = "JSON"
      mode = "REQUIRED"
    }
  ])
}

resource "google_dataform_repository" "coc_elt" {
  provider = google-beta
  project  = var.data_project_id
  region   = var.region
  name     = "coc-elt"
}

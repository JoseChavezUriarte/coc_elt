resource "google_storage_bucket" "tf_state" {
  name          = "tf-state-${var.compute_project_id}"
  project       = var.compute_project_id
  location      = var.region
  force_destroy = false

  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

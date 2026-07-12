variable "compute_project_id" {
  type        = string
  description = "The GCP Project ID where compute resources are hosted."
  default     = "elt-coc"
}

variable "data_project_id" {
  type        = string
  description = "The GCP Project ID where BigQuery resources are hosted."
}

variable "region" {
  type        = string
  description = "The region to deploy the resources."
  default     = "us-central1"
}

variable "clan_tag" {
  type        = string
  description = "The Clash of Clans clan tag."
}

variable "github_app_installation_id" {
  type        = number
  description = "The GitHub App Installation ID for Cloud Build."
}

variable "github_repository_url" {
  type        = string
  description = "The URL of the GitHub repository."
}

variable "dataform_developer_emails" {
  type        = set(string)
  description = "A set of developer email addresses to grant serviceAccountUser permissions on the runner service account."
  default     = []
}


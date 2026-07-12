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

variable "state_bucket_name" {
  type        = string
  description = "The name of the GCS bucket to store Terraform state."
}

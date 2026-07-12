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
}

variable "clan_tag" {
  type        = string
  description = "The Clash of Clans clan tag."
}

variable "coc_api_key" {
  type        = string
  description = "The Clash of Clans API key."
  sensitive   = true
}

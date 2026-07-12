resource "google_compute_network" "vpc" {
  name                    = "coc-elt-vpc"
  auto_create_subnetworks = false
  project                 = var.compute_project_id
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "coc-elt-subnet"
  ip_cidr_range            = "10.0.0.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
  project                  = var.compute_project_id
}

resource "google_compute_router" "router" {
  name    = "coc-elt-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.compute_project_id
}

resource "google_compute_address" "nat_ip" {
  name    = "coc-elt-nat-ip"
  region  = var.region
  project = var.compute_project_id
}

resource "google_compute_router_nat" "nat" {
  name                               = "coc-elt-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.nat_ip.self_link]
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  project                            = var.compute_project_id

  subnetwork {
    name                    = google_compute_subnetwork.subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
}

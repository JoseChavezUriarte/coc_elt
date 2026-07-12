output "nat_public_ip" {
  value       = google_compute_address.nat_ip.address
  description = "The static public IP address of the Cloud NAT. Whitelist this in the Clash of Clans API developer portal."
}

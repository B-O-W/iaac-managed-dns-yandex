variable "yc_cloud_id" {
  description = "ID of your Yandex Cloud account"
}

variable "yc_folder_id" {
  description = "ID of your Yandex Cloud folder"
}

variable "domain" {
  description = "Primary domain, e.g. musa.kz"
}

variable "zone_name" {
  description = "DNS zone name in Yandex, e.g. musa-kz-zone"
}

variable "gitlab_access_token" {
  description = "Personal Access Token for Terraform HTTP backend"
  type        = string
  sensitive   = true
}

terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100.0"
    }
  }
}

provider "yandex" {
  service_account_key_file = "${path.module}/key.json"
  cloud_id                 = var.yc_cloud_id
  folder_id                = var.yc_folder_id
  endpoint                 = "api.yandexcloud.kz:443" # Регион Казахстан
}

# Загружаем записи из YAML
locals {
  dns_records = yamldecode(file("${path.module}/records.yaml")).records
}

# Создаем DNS-зону
resource "yandex_dns_zone" "musa" {
  name        = var.zone_name
  description = "Public DNS zone for ${var.domain}"
  zone        = "${var.domain}."
  public      = true
}

# Создаем каждый DNS record, ключом является полное имя с точкой
resource "yandex_dns_recordset" "records" {
  for_each = {
    for rec in local.dns_records :
    "${rec.name}.${var.domain}." => rec
  }

  zone_id = yandex_dns_zone.musa.id
  name    = each.key
  type    = each.value.type
  ttl     = each.value.ttl
  data    = each.value.data
}

# Выводим ID созданной DNS-зоны
output "zone_id" {
  description = "ID созданной DNS-зоны"
  value       = yandex_dns_zone.musa.id
}

terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

# Токен авторизации Яндекс
# See: https://cloud.yandex.ru/docs/tutorials/infrastructure-management/terraform-quickstart
variable "auth_token" {
  type = string
  # Не выводить значение переменной, тк это секретный ключик
  sensitive = true
}

# Id облака и папки Яндекс 
# Получить: `yc resource-manager cloud list`
# Получить: `yc resource-manager folder list`
variable "cloud_properties" {
  type = object({
    cloud_id  = string
    folder_id = string
  })
}

# Настройки сети 
variable "network_properties" {
  type = object({
    # Зона доступности
    # See: https://cloud.yandex.com/en/docs/overview/concepts/geo-scope
    zone = string
  })
}

# Пользователь MySQL
variable "mysql_user" {
  type = object({
    username = string
    password = string
  })
  sensitive = true
}

# Настройки базы данных 
variable "db_properties" {
  type = object({
    name = string
  })
}

# Ключ SSH
variable "ssh_key" {
  type = string 
  sensitive = true
}

# Подключаем провайдера
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs
provider "yandex" {
  token     = var.auth_token
  cloud_id  = var.cloud_properties.cloud_id
  folder_id = var.cloud_properties.folder_id
  zone      = var.network_properties.zone
}

# Создаем сеть
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/vpc_network
resource "yandex_vpc_network" "network-1" {
  name = "network1"
}

# Создаем подсеть (обязательно должна быть хотя бы одна)
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/vpc_subnet
resource "yandex_vpc_subnet" "subnet-1" {
  name           = "subnet1"
  zone           = var.network_properties.zone
  network_id     = yandex_vpc_network.network-1.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# Создаем группу безопасности
# See: https://cloud.yandex.ru/docs/managed-mysql/operations/cluster-create
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/vpc_security_group
resource "yandex_vpc_security_group" "mysql-sg" {
  name       = "mysql-sg"
  network_id = yandex_vpc_network.network-1.id

  ingress {
    description    = "MySQL"
    port           = 3306
    protocol       = "TCP"
    v4_cidr_blocks = [ "0.0.0.0/0" ]
  }
}

# Создаем виртуальную машину для сервера 
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/compute_instance
resource "yandex_compute_instance" "vm-1" {
  name = "ritter-server-vm"

  # Тип платформ
  # See: https://cloud.yandex.ru/docs/compute/concepts/vm-platforms
  platform_id = "standard-v1"

  resources {
    cores         = 2
    memory        = 4
    core_fraction = 20
  }

  # Загрузочный диск, тут пишем настройки для системы
  boot_disk {
    initialize_params {
      # Id операционной системы
      # See: https://cloud.yandex.ru/marketplace/products/yc/ubuntu-20-04-lts
      image_id = "fd86t95gnivk955ulbq8"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-1.id
    nat       = true
  }

  # Указываем данные для подключения по SSH
  metadata = {
    ssh-keys = "vova:${var.ssh_key}"
    user-data = "${file("user-data.txt")}"
    
  }
}

# Создаем базу MySQL 
# See: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/mdb_mysql_cluster
resource "yandex_mdb_mysql_cluster" "db" {
  name        = "ritter-db"
  environment = "PRESTABLE"
  network_id  = yandex_vpc_network.network-1.id
  version     = "8.0"
  security_group_ids  = [ yandex_vpc_security_group.mysql-sg.id ]

  resources {
    resource_preset_id = "s2.micro"
    disk_type_id       = "network-ssd"
    disk_size          = 16
  }

  mysql_config = {
    sql_mode                      = "ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
    max_connections               = 100
    default_authentication_plugin = "MYSQL_NATIVE_PASSWORD"
    innodb_print_all_deadlocks    = true
  }

  database {
    name = var.db_properties.name
  }

  user {
    name     = var.mysql_user.username
    password = var.mysql_user.password
    permission {
      database_name = var.db_properties.name
      roles         = ["ALL"]
    }
  }

  host {
    zone      = var.network_properties.zone
    subnet_id = yandex_vpc_subnet.subnet-1.id
  }

  access {
    web_sql = true
  }
}

# Вывести при создании ресурсов выделенные адреса
output "internal_ip_address_vm_1" {
  value = yandex_compute_instance.vm-1.network_interface.0.ip_address
}

output "external_ip_address_vm_1" {
  value = yandex_compute_instance.vm-1.network_interface.0.nat_ip_address
}

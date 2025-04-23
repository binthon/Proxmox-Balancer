variable "resource_group" {}
variable "location" {}
variable "username" {}
variable "vmid" {}
variable "vm_name" {}
variable "vm_ram" {}
variable "vm_cores" {}
variable "vm_disk" {}
variable "admin_password" {}
variable "admin_username" {}
variable "tenant_id" {
  type        = string
  description = "Azure AD Tenant ID"
}

variable "client_id" {
  type        = string
  description = "Azure Service Principal Client ID"
}

variable "client_secret" {
  type        = string
  description = "Azure Service Principal Secret"
  sensitive   = true
}

variable "subscription_id" {
  type        = string
  description = "Azure Subscription ID"
}
variable "vnet_name" {
  type = string
}


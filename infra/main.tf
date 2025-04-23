provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
}


locals {
  vm_size_map = {
    "1_1" = "Standard_B1s"
    "2_2" = "Standard_B2s"
    "4_2" = "Standard_B2ms"
    "8_4" = "Standard_B4ms"
  }

  selected_size = lookup(local.vm_size_map, "${var.vm_ram}_${var.vm_cores}", "Standard_B1s")
}

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.vmid}"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = var.resource_group
}

resource "azurerm_subnet" "subnet" {
  name                 = "subnet-${var.vmid}"
  resource_group_name = var.resource_group
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_network_interface" "nic" {
  name                = "nic-${var.vmid}"
  location            = var.location
  resource_group_name = var.resource_group

  ip_configuration {
    name = "ipconfig"
    subnet_id = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_linux_virtual_machine" "vm" {
  name                  = var.vm_name
  resource_group_name = var.resource_group
  location              = var.location
  size                  = local.selected_size
  admin_username        = var.admin_username
  admin_password        = var.admin_password
  disable_password_authentication = false

  network_interface_ids = [azurerm_network_interface.nic.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }


  tags = {
    "${var.username}" = tostring(var.vmid)
  }
}

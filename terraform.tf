terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.1"
    }
  }

  backend "azurerm" {
    resource_group_name   = "azureworkshop-demo-rg"
    storage_account_name  = "azureworkshopdemostorage"
    container_name        = "tfstateopenai"
    key                   = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  client_id                  = var.client_id
  tenant_id                  = var.tenant_id
  #client_certificate_path    = "cert.pem"
  #client_certificate_password = var.client_certificate_password
}
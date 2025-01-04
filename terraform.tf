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
}
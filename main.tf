resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.resource_group_location
}

resource "azurerm_cognitive_account" "ca" {
  name                = var.cognitive_account_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = var.cognitive_account_kind
  sku_name            = var.cognitive_account_sku_name
}

resource "azurerm_cognitive_deployment" "cd" {
  name                 = var.cognitive_deployment_name
  cognitive_account_id = azurerm_cognitive_account.ca.id
  model {
    format  = var.cognitive_deployment_model_format
    name    = var.cognitive_deployment_model_name
    version = var.cognitive_deployment_model_version
  }

  sku {
    name     = var.cognitive_deployment_sku_name
    capacity = var.cognitive_deployment_sku_capacity
  }
}
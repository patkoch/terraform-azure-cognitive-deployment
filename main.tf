resource "azurerm_resource_group" "example" {
  name     = "open-ai-test-west-europe-rg"
  location = "West Europe"
}

resource "azurerm_cognitive_account" "example" {
  name                = "open-ai-test-west-europe-ca"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  kind                = "OpenAI"
  sku_name            = "S0"
}

resource "azurerm_cognitive_deployment" "example" {
  name                 = "open-ai-test-west-europe-cd"
  cognitive_account_id = azurerm_cognitive_account.example.id
  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "turbo-2024-04-09"
  }

  sku {
    name = "GlobalStandard"
    capacity = 45
  }
}
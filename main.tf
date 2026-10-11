# Resource Group
module "resource_group" {
  source = "git::https://github.com/patkoch/terraform-modules//azurerm/resource-group?ref=v2.0.0"

  instances = {
    main = {
      name     = var.resource_group_name
      location = var.resource_group_location
      tags     = var.resource_group_tags
    }
  }
}

# Cognitive Account (OpenAI)
module "cognitive_account" {
  source = "git::https://github.com/patkoch/terraform-modules//azurerm/cognitive-account?ref=v2.0.0"

  instances = {
    main = {
      name                          = var.cognitive_account_name
      location                      = module.resource_group.locations["main"]
      resource_group_name           = module.resource_group.names["main"]
      kind                          = var.cognitive_account_kind
      sku_name                      = var.cognitive_account_sku_name
      custom_subdomain_name         = var.cognitive_account_custom_subdomain_name
      local_auth_enabled            = true
      public_network_access_enabled = true

      identity = {
        type = var.cognitive_account_identity_type
      }

      tags = var.cognitive_account_tags
    }
  }

  depends_on = [module.resource_group]
}

# Cognitive Deployment (GPT-4o Model)
module "cognitive_deployment" {
  source = "git::https://github.com/patkoch/terraform-modules//azurerm/cognitive-deployment?ref=v2.0.0"

  instances = {
    main = {
      deployment_name      = var.cognitive_deployment_name
      cognitive_account_id = module.cognitive_account.ids["main"]

      model_format  = var.cognitive_deployment_model_format
      model_name    = var.cognitive_deployment_model_name
      model_version = var.cognitive_deployment_model_version

      sku_name     = var.cognitive_deployment_sku_name
      sku_capacity = var.cognitive_deployment_sku_capacity

      version_upgrade_option = var.cognitive_deployment_version_upgrade_option
    }
  }

  depends_on = [module.cognitive_account]
}

moved {
  from = module.resource_group.azurerm_resource_group.this
  to   = module.resource_group.azurerm_resource_group.this["main"]
}

moved {
  from = module.cognitive_account.azurerm_cognitive_account.this
  to   = module.cognitive_account.azurerm_cognitive_account.this["main"]
}

moved {
  from = module.cognitive_deployment.azurerm_cognitive_deployment.this
  to   = module.cognitive_deployment.azurerm_cognitive_deployment.this["main"]
}
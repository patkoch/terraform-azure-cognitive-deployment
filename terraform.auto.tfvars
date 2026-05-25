resource_group_name     = "open-ai-test-sweden-central-rg"
resource_group_location = "swedencentral"
resource_group_tags = {
  Project     = "OpenAI-Test"
  Environment = "Test"
  ManagedBy   = "Terraform"
}

cognitive_account_name                  = "open-ai-test-sweden-central-ca"
cognitive_account_kind                  = "OpenAI"
cognitive_account_sku_name              = "S0"
cognitive_account_custom_subdomain_name = "open-ai-test-sweden-central"
cognitive_account_identity_type         = "SystemAssigned"
cognitive_account_tags = {
  Project     = "OpenAI-Test"
  Environment = "Test"
  Service     = "OpenAI"
  ManagedBy   = "Terraform"
}

cognitive_deployment_name                   = "open-ai-test-sweden-central-cd"
cognitive_deployment_model_format           = "OpenAI"
cognitive_deployment_model_name             = "gpt-5"
cognitive_deployment_model_version          = "2025-08-07"
cognitive_deployment_sku_name               = "GlobalStandard"
cognitive_deployment_sku_capacity           = 45
cognitive_deployment_version_upgrade_option = "OnceNewDefaultVersionAvailable"

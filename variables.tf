variable "subscription_id" {
  type        = string
  description = "The Azure subscription ID"
}

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group"
}

variable "resource_group_location" {
  type        = string
  description = "Location of the resource group"
}

variable "resource_group_tags" {
  type        = map(string)
  description = "Tags for the resource group"
  default = {
    ManagedBy = "Terraform"
  }
}

variable "cognitive_account_name" {
  type        = string
  description = "Name of the cognitive account"
}

variable "cognitive_account_kind" {
  type        = string
  description = "Type of the cognitive account"
}

variable "cognitive_account_sku_name_test" {
  type        = string
  description = "SKU name of the cognitive account"
}

variable "cognitive_account_custom_subdomain_name" {
  type        = string
  description = "Custom subdomain name of the cognitive account"
  default     = null
}

variable "cognitive_account_identity_type" {
  type        = string
  description = "Type of identity for the cognitive account (SystemAssigned, UserAssigned, or SystemAssigned, UserAssigned)"
  default     = "SystemAssigned"
}

variable "cognitive_account_tags" {
  type        = map(string)
  description = "Tags for the cognitive account"
  default = {
    ManagedBy = "Terraform"
  }
}

variable "cognitive_deployment_name" {
  type        = string
  description = "Name of the cognitive deployment"
}

variable "cognitive_deployment_model_format" {
  type        = string
  description = "Format of the model of the cognitive deployment"
}

variable "cognitive_deployment_model_name" {
  type        = string
  description = "Name of the model of the cognitive deployment"
}

variable "cognitive_deployment_model_version" {
  type        = string
  description = "Version of the model of the cognitive deployment"
}

variable "cognitive_deployment_sku_name" {
  type        = string
  description = "Name of the sku of the cognitive deployment"
}

variable "cognitive_deployment_sku_capacity" {
  type        = number
  description = "Capacity of the sku of the cognitive deployment"
}

variable "cognitive_deployment_version_upgrade_option" {
  type        = string
  description = "Version upgrade option for the cognitive deployment"
  default     = "OnceNewDefaultVersionAvailable"
}
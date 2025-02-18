variable "subscription_id" {
  type        = string
  description = "The Azure subscription ID"
}

# variable "client_id" {
#   type        = string
#   description = "The Azure client ID"
# }

# variable "tenant_id" {
#   type        = string
#   description = "The Azure tenant ID"
# }

# variable "client_certificate_path" {
#   type        = string
#   description = "The path to the client certificate"
# }

# variable "client_certificate_password" {
#   type        = string
#   description = "The password for the client certificate"
# }

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group" 
}

variable "resource_group_location" {
  type = string
  description = "Location of the resource group"
}

variable "cognitive_account_name" {
  type = string
  description = "Name of the cognitive account"
}

variable "cognitive_account_kind" {
  type = string
  description = "Type of the cognitive account"
}

variable "cognitive_account_sku_name" {
  type = string
  description = "SKU name of the cognitive account"
}

variable "cognitive_deployment_name" {
  type = string
  description = "Name of the cognitive deployment"
}

variable "cognitive_deployment_model_format" {
  type = string
  description = "Format of the model of the cognitive deployment"
}

variable "cognitive_deployment_model_name" {
  type = string
  description = "Name of the model of the cognitive deployment"
}

variable "cognitive_deployment_model_version" {
  type = string
  description = "Version of the model of the cognitive deployment"
}

variable "cognitive_deployment_sku_name" {
  type = string
  description = "Name of the sku of the cognitive deployment"
}

variable "cognitive_deployment_sku_capacity" {
  type = number
  description = "Capacity of the sku of the cognitive deployment"
}
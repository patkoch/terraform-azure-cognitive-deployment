# Contains a Terraform configuration to provision a cognitive deployment on Azure

This Terraform configuration is capable of deploying an Azure Open AI Service and a gpt-4 model.
After the deployment, it is possible to conduct a chat by using a Python script with the generated API_Key and a public Endpoint.

<p align="left">
  <img src="pictures/07_azure_portal_open_ai.png" width="80%" height="80%" title="07_azure_portal_open_ai">
</p>

<p align="left">
  <img src="pictures/15_send_requests.png" width="80%" height="80%" title="15_send_requests">
</p>

# Create a terraform.tfvars file

Create a new file inside the checked out directory of this repository, named "terraform.tfvars".
There are 12 values to assign to predefined variables.
The only value to determine for your personal deployment is the "subscription_id" of your Azure subscription.

You can run the following command to find the "subscription_id":

\`\`\`azurecli
az account show
\`\`\`

\`\`\`azurecli
subscription_id = "<add your subscription id here>"
resource_group_name = "open-ai-test-west-europe-rg"
resource_group_location = "West Europe"
cognitive_account_name = "open-ai-test-west-europe-ca"
cognitive_account_kind = "OpenAI"
cognitive_account_sku_name = "S0"
cognitive_deployment_name = "open-ai-test-west-europe-cd"
cognitive_deployment_model_format = "OpenAI"
cognitive_deployment_model_name = "gpt-4"
cognitive_deployment_model_version = "turbo-2024-04-09"
cognitive_deployment_sku_name = "GlobalStandard"
cognitive_deployment_sku_capacity = 45
\`\`\`



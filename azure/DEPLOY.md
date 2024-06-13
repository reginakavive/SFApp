# Azure VM Deployment

This repository contains an Azure Resource Manager (ARM) template for deploying a 64-bit Ubuntu 22.04-LTS Virtual
Machine (VM) named `SFAppVM` with specific inbound ports.

## Prerequisites

1. **Azure CLI**: Ensure you have the Azure CLI installed. You can download and install it
   from [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
2. **Azure Subscription**: Ensure you have an active Azure subscription. If you don't have one, you can create a free
   account [here](https://azure.microsoft.com/en-us/free/).

## Deployment Instructions

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
````

### Step 2: Login to Azure

```bash 
az login
```

If you have multiple subscriptions, set the desired subscription:

```bash
az account set --subscription <subscription-id>
```

### Step 3: Create a Resource Group

Create a resource group (if it doesn't exist)

```bash
az group create --name  eia-transform-rg --location eastus
```

### Step 4: Deploy the ARM Template

You can deploy the ARM template by passing parameters directly through the command line or using a parameters file.

#### Method 1: Using Command Line Parameters

```bash
az deployment group create --resource-group eia-transform-rg --template-file azure/azuredeploy.json --parameters adminUsername=azureuser adminPassword=P@ssw0rd! nicName=myNIC nsgName=myNSG
```

#### Method 2: Using a Parameters File

Create a file named `azuredeploy.parameters.json` with the following content:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "adminUsername": {
      "value": "{{user}}"
    },
    "adminPassword": {
      "value": "{{password}}"
    },
    "nicName": {
      "value": "myNIC"
    },
    "nsgName": {
      "value": "myNSG"
    }
  }
}
```

#### Deploy the ARM template using the JSON file and parameters file

```bash 
az deployment group create --resource-group MyResourceGroup --template-file azuredeploy.json --parameters @azuredeploy.parameters.json
```

## Template Details

### azuredeploy.json

This ARM template creates:

- A Network Security Group (NSG) with rules to allow `SSH (port 22)`, `HTTP (port 80)`, and `HTTPS (port 443)` traffic.
- A Network Interface (NIC) associated with the NSG.
- A Virtual Machine (VM) named `SFAppVM` running `Ubuntu 22.04-LTS`.
- A Public IP address.
- A Virtual Network (VNet) and a Subnet.

### Parameters

- `adminUsername`: The admin username for the VM.
- `adminPassword`: The admin password for the VM.
- `nicName`: The name of the Network Interface.
- `nsgName`: The name of the Network Security Group.

### Security Considerations

Ensure that the `adminPassword` parameter value meets Azure's password complexity requirements.
Update the `NSG` rules as necessary to limit access to only trusted IP addresses.
Consider using Azure Key Vault to manage and secure sensitive information such as passwords.

##  Cleanup

To delete the resource group and all resources associated with it:

```bash
az group delete --name MyResourceGroup --yes --no-wait
```

This command deletes the resources created during the tutorial, and is guaranteed to deallocate them in the correct order. The `--no-wait` parameter keeps the CLI from blocking while the deletion takes place. If you want to wait until the deletion is complete or watch it progress, use the group wait command.

```bash
az group wait --name MyResourceGroup --deleted
```
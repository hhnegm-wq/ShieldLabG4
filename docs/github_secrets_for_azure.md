# GitHub Secrets for Azure Workflows

Use GitHub Environment secrets (preferred) or repository secrets.

## 1. Required secrets (deploy + infra)

- AZURE_CLIENT_ID
- AZURE_TENANT_ID
- AZURE_SUBSCRIPTION_ID
- AZURE_RESOURCE_GROUP
- AZURE_WEBAPP_NAME
- AZURE_LOCATION
- AZURE_APP_NAME_PREFIX
- AZURE_STORAGE_ACCOUNT_NAME

## 2. Recommended IaC tuning secrets

- AZURE_APP_SERVICE_SKU (example: S1)
- AZURE_JOBS_QUEUE_NAME (example: simulation-jobs)
- AZURE_INPUT_CONTAINER_NAME (example: simulation-input)
- AZURE_OUTPUT_CONTAINER_NAME (example: simulation-output)
- AZURE_ENABLE_EASY_AUTH (true or false)
- AZURE_WORKER_PRINCIPAL_ID (object ID of AKS/Batch worker managed identity)

## 3. API job-submit runtime secrets

- AZURE_QUEUE_NAME
- AZURE_INPUT_CONTAINER_NAME
- AZURE_OUTPUT_CONTAINER_NAME
- AZURE_STORAGE_ACCOUNT_URL (managed identity path) or AZURE_STORAGE_CONNECTION_STRING (fallback)

## 4. Optional Easy Auth secrets

- AZURE_EASYAUTH_CLIENT_ID
- AZURE_EASYAUTH_CLIENT_SECRET
- AZURE_EASYAUTH_ISSUER

If optional Easy Auth secrets are missing, deployment still runs and skips auth configuration.

## 5. OIDC prerequisites

Before using AZURE_CLIENT_ID/TENANT_ID/SUBSCRIPTION_ID in workflows:

1. Create a Federated Credential in Entra app registration for GitHub Actions.
1. Scope it to your repository and target branch/environment.
1. Grant deployment RBAC to that service principal at resource-group scope.

## 6. Minimum RBAC for CI principal

- Contributor on target resource group (for provisioning/deploying).
- User Access Administrator only if workflow must assign role bindings dynamically.

## 7. Where secrets are consumed

- .github/workflows/provision-infra.yml
- .github/workflows/deploy-appservice.yml
- api/main.py

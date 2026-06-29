# ShieldLabG4 Public Deployment (Azure App Service)

This guide scaffolds production hosting for the Streamlit platform with HTTPS and optional Microsoft Entra ID authentication, then explains how Geant4 simulations should run in cloud architecture.

## 1. What Was Scaffolded

Files added:

- infra/main.bicep
- infra/main.parameters.example.json
- requirements.appservice.txt
- .github/workflows/deploy-appservice.yml

Existing workflow already enforcing release gate:

- .github/workflows/release-validation-gate.yml

Infrastructure workflow added:

- .github/workflows/provision-infra.yml (what-if + deploy from infra/main.bicep)

Worker scaffold added:

- worker/queue_worker.py
- worker/Dockerfile
- worker/requirements.txt
- worker/README.md

Authentication and secrets docs added:

- docs/azure_entra_authz_setup.md
- docs/github_secrets_for_azure.md

Deployment chain:

1. Release Validation Gate succeeds on push to main/master.
1. Deploy Azure App Service workflow auto-runs via workflow_run.
1. Commit is deployed to Azure App Service.

## 2. Why App Service Works for Public Access

App Service gives:

- Public HTTPS endpoint by default (TLS termination managed by Azure).
- Horizontal scaling and managed runtime.
- Optional Easy Auth (Microsoft Entra ID) in front of your app.

## 3. Provision Infrastructure (IaC)

Use Bicep to create App Service plan + Web App + HTTPS-only + optional Easy Auth config skeleton.

```bash
az group create -n <rg-name> -l <region>
az deployment group create \
  -g <rg-name> \
  -f infra/main.bicep \
  -p @infra/main.parameters.example.json
```

Notes:

- Set unique appNamePrefix in parameters.
- For Easy Auth, create an Entra App Registration and provide issuer/client values.

## 4. Configure GitHub Secrets

Required for deployment workflow:

- AZURE_CLIENT_ID
- AZURE_TENANT_ID
- AZURE_SUBSCRIPTION_ID
- AZURE_RESOURCE_GROUP
- AZURE_WEBAPP_NAME
- AZURE_LOCATION
- AZURE_APP_NAME_PREFIX

Optional for Easy Auth auto-configuration:

- AZURE_EASYAUTH_CLIENT_ID
- AZURE_EASYAUTH_CLIENT_SECRET
- AZURE_EASYAUTH_ISSUER

Recommended additional IaC secrets:

- AZURE_APP_SERVICE_SKU
- AZURE_JOBS_QUEUE_NAME
- AZURE_INPUT_CONTAINER_NAME
- AZURE_OUTPUT_CONTAINER_NAME
- AZURE_ENABLE_EASY_AUTH

## 5. Runtime Entry on App Service

Workflow enforces startup command:

```text
python -m streamlit run ui/app.py --server.port 8000 --server.address 0.0.0.0
```

And app settings:

- WEBSITES_PORT=8000
- SCM_DO_BUILD_DURING_DEPLOYMENT=true

Dependencies are resolved from requirements.appservice.txt.

## 6. Geant4 in the Cloud: Recommended Architecture

Do not run heavy Geant4 Monte Carlo jobs inside the App Service web process.
Use split architecture:

1. App Service (frontend/API)

- Hosts Streamlit UI and lightweight orchestration endpoints.
- Authenticates users and collects simulation requests.

1. Queue

- Azure Storage Queue or Service Bus stores simulation jobs.

1. Compute worker pool

- Azure Batch, AKS jobs, or VM Scale Set workers with Geant4 installed.
- Workers pull job payload, execute macro, write outputs to storage.

1. Artifact storage

- Azure Blob Storage for CSV/Excel/figures/provenance artifacts.

1. Results retrieval

- UI polls job status and renders/downloads artifacts when complete.

Benefits:

- Web tier stays responsive for many users.
- Compute scales independently by demand.
- Better reliability, lower blast radius, and cleaner cost control.

## 7. Minimal Production Guardrails

- Keep HTTPS-only enabled.
- Enable Easy Auth for non-public/internal users.
- Store secrets in Key Vault or GitHub encrypted secrets.
- Restrict CORS to known origins if API endpoints are exposed.
- Add autoscale rules for App Service and worker pool.
- Keep release gate + UI no-skip smoke as mandatory before deploy.

## 8. First End-to-End Validation

After secrets are set:

1. Push to main/master.
1. Confirm Release Validation Gate passes.
1. Confirm Deploy Azure App Service workflow runs automatically.
1. Open https://\<webapp-name\>.azurewebsites.net and verify login/landing behavior.
1. Submit one small simulation and validate artifact generation path.

# ShieldLab G4 — Production Deployment Runbook

**Audience:** you (no Azure expertise required).
**Goal:** publish the Streamlit app to a public HTTPS URL on Azure App Service.
**Method:** the GitHub Actions pipeline already in this repo (manual-trigger).
**No local installs needed** — the one command block runs in **Azure Cloud Shell** (a terminal inside the Azure Portal).

> **What the agent already did for you**
> - Set the non-sensitive deploy config as GitHub secrets: `AZURE_LOCATION=eastus`,
>   `AZURE_APP_SERVICE_SKU=B1`, `AZURE_RESOURCE_GROUP=shieldlabg4-rg`,
>   `AZURE_JOBS_QUEUE_NAME`, `AZURE_INPUT_CONTAINER_NAME`,
>   `AZURE_OUTPUT_CONTAINER_NAME`, `AZURE_ENABLE_EASY_AUTH=false`.
> - Made `Provision Azure Infrastructure` and `Deploy Azure App Service`
>   **manual-only** (they never run by accident).
> - Chosen sensible defaults: **B1 plan (~$13/month)**, **East US**, **auth off**
>   at first (the app has its own login; you can add Microsoft sign-in later).
>
> **What still needs you:** an Azure subscription + running ONE command block to
> connect GitHub to Azure. Then the agent (or you) triggers two buttons.

---

## Cost, in plain terms

| Resource | Purpose | Approx. cost |
|----------|---------|-------------|
| App Service **B1** (Linux) | runs the web app | **~$13 / month** |
| Storage account | job queue + result files | a few cents / month |
| Application Insights | monitoring | free tier |

You can **delete everything** anytime (Step 6) to stop all charges.

---

## Step 1 — Get an Azure subscription (one-time)

If you already have one, skip to Step 2.

1. Go to <https://azure.microsoft.com/free> → **Start free** (gives free credit),
   or use a pay-as-you-go subscription.
2. Sign in with a Microsoft account.

---

## Step 2 — Connect GitHub to Azure (run once, in Cloud Shell)

This creates a secure, password-less identity that lets GitHub deploy on your
behalf. **You do not install anything.**

1. Open <https://portal.azure.com> and click the **Cloud Shell** icon (`>_`) in
   the top bar. Choose **Bash** if prompted.
2. Paste this **entire block** and press Enter. It prints three IDs at the end.

```bash
# ---- ShieldLab G4: one-time GitHub -> Azure setup ----
REPO="hhnegm-wq/ShieldLabG4"
RG="shieldlabg4-rg"
LOCATION="eastus"
APP_NAME="shieldlabg4-github-deployer"

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Resource group that will hold everything
az group create -n "$RG" -l "$LOCATION" -o none

# App registration + service principal
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
az ad sp create --id "$APP_ID" -o none

# Let it manage ONLY this resource group
az role assignment create --assignee "$APP_ID" --role Contributor \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG" -o none

# Trust GitHub Actions from this repo's 'production' environment + main branch
az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"gh-env-production\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${REPO}:environment:production\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" -o none
az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"gh-main\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${REPO}:ref:refs/heads/main\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" -o none

echo ""
echo "=========== COPY THESE THREE VALUES ==========="
echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
echo "==============================================="
```

3. Copy the three `AZURE_...` values it prints.

---

## Step 3 — Give the agent the three IDs (or set them yourself)

**Easiest:** paste the three values into the chat and say *"set these secrets."*
The agent will run the commands below for you.

Or run them yourself (from this repo folder, `gh` is already logged in):

```powershell
gh secret set AZURE_CLIENT_ID       --body "<paste AZURE_CLIENT_ID>"
gh secret set AZURE_TENANT_ID       --body "<paste AZURE_TENANT_ID>"
gh secret set AZURE_SUBSCRIPTION_ID --body "<paste AZURE_SUBSCRIPTION_ID>"

# Pick a GLOBALLY-UNIQUE name (lowercase letters+digits, <= 20 chars).
# The site will be https://<PREFIX>-web.azurewebsites.net
$PREFIX = "shieldlabg4" + (Get-Random -Maximum 9999)
gh secret set AZURE_APP_NAME_PREFIX --body "$PREFIX"
gh secret set AZURE_WEBAPP_NAME     --body "$PREFIX-web"
```

---

## Step 4 — Provision the infrastructure (one click)

1. Go to the repo → **Actions** tab →
   **Provision Azure Infrastructure** → **Run workflow** → keep `production` →
   **Run**.
2. Wait ~3–5 min. It creates the App Service, storage, and monitoring.

*(The agent can trigger this for you: `gh workflow run "Provision Azure Infrastructure"`.)*

---

## Step 5 — Deploy the app (one click) → your live URL

1. **Actions** tab → **Deploy Azure App Service** → **Run workflow** →
   type `deploy` in the confirm box → **Run**.
2. Wait ~3–5 min. When green, your app is live at:

   ```
   https://<PREFIX>-web.azurewebsites.net
   ```

*(Agent shortcut: `gh workflow run "Deploy Azure App Service" -f confirm=deploy`.)*

> **Note on Geant4:** the web app serves the analytical UI and API. Heavy Geant4
> Monte-Carlo jobs are designed to run on a separate worker (container/AKS) that
> pulls from the storage queue — that's a later, optional stage. The public site
> works fully for the analytical shielding workspace without it.

---

## Step 6 — Stop all charges (when you want)

Delete the whole resource group — removes every resource and billing:

```bash
az group delete -n shieldlabg4-rg --yes --no-wait
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Provision fails: *"AADSTS700016 / no matching federated credential"* | Re-run the Step 2 block; ensure `subject` matches `repo:hhnegm-wq/ShieldLabG4:environment:production`. |
| Provision fails: *"name already taken"* | Your `AZURE_APP_NAME_PREFIX` isn't globally unique — set a different one (Step 3) and re-run. |
| Deploy green but site shows *"Application Error"* | Wait 1–2 min (cold start), then reload. Check **App Service → Log stream** in the Portal. |
| Want Microsoft sign-in in front of the app | Set `AZURE_ENABLE_EASY_AUTH=true` and provide the EasyAuth secrets (see `docs/azure_entra_authz_setup.md`), then re-provision. |

---

## Run the app locally anytime (no Azure)

```powershell
make ui           # or:
$env:PYTHONPATH='python;ui'; python -m streamlit run ui/app.py --server.port 8501
```
Then open <http://localhost:8501>.

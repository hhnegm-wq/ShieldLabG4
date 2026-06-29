# Microsoft Entra ID Setup and Role Mapping

This document defines how to configure Microsoft Entra ID authentication for ShieldLabG4 on Azure App Service and map user access to authorization roles.

## 1. App registrations

Create two app registrations in Entra ID:

1. ShieldLabG4-Web (client app)

- Platform: Web
- Redirect URI:
  - https://\<webapp-name\>.azurewebsites.net/.auth/login/aad/callback
- Accounts: single tenant (recommended for enterprise)

1. ShieldLabG4-API (optional)

- Use only if you split API endpoints to a separate service.
- Expose API scopes if needed for downstream calls.

## 2. Easy Auth values

From the ShieldLabG4-Web app registration, capture:

- Application (client) ID -> AZURE_EASYAUTH_CLIENT_ID
- Directory (tenant) ID -> used in issuer URL
- Client secret value -> AZURE_EASYAUTH_CLIENT_SECRET
- Issuer URL format -> AZURE_EASYAUTH_ISSUER
  - [Issuer URL example](https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0)

## 3. App Service authentication policy

Configured by workflow and IaC:

- Authentication enabled.
- Unauthenticated clients redirected to Entra login.
- Token store enabled.

After login, identity headers (for reverse proxy-style checks) are available to backend services through App Service auth integration.

## 4. Authorization model (recommended)

Use Entra security groups as role sources and map them to app roles:

- ShieldLabG4.Admin
- ShieldLabG4.Operator
- ShieldLabG4.Viewer

Suggested capabilities:

- Admin:
  - Manage settings, trigger deployments, modify role policy docs.
- Operator:
  - Submit simulation jobs, rerun failed jobs, view full results.
- Viewer:
  - Browse dashboards and download approved artifacts only.

## 5. Role claim strategy

Recommended flow:

1. Assign Entra groups to users.
1. Emit group/role claims in token.
1. In app/backend layer, map claim values to internal permissions.
1. Enforce least privilege for action endpoints.

## 6. Azure RBAC for managed identities

For web and worker managed identities, assign only required roles:

Web App identity:

- Storage Queue Data Contributor (submit jobs)
- Storage Blob Data Reader (read input templates) and Data Contributor when writing metadata

Worker identity:

- Storage Queue Data Contributor (consume/delete jobs)
- Storage Blob Data Contributor (read studies, write outputs/logs)

## 7. Security baseline checks

- Use HTTPS only.
- Rotate client secrets periodically.
- Prefer managed identity over connection strings in cloud runtime.
- Keep production auth values in GitHub environment secrets.
- Audit Entra sign-ins and role assignments monthly.

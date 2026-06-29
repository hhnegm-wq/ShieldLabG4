# Data governance (ShieldLab G4)

## Classifications

| Class       | Examples                                         | Storage                                  | Retention            |
|-------------|--------------------------------------------------|------------------------------------------|----------------------|
| Public      | Methods doc, reference datasets w/ open license  | Public blob container, repo              | Indefinite           |
| Operational | Build artefacts, CI logs                          | Private container, redacted              | 90 days              |
| Tenant      | User study JSON, run results, manifests          | Tenant-scoped prefix `tenants/<id>/...`  | 365 days (default)   |
| Secrets     | API keys, signing keys, license hashes           | Azure Key Vault                          | Rotated quarterly    |

The platform does **not** intentionally process PII. License-key emails
collected by the billing path live with the billing provider, not in
ShieldLab storage.

## Tenant isolation

- Every blob/queue path is prefixed with `tenants/<tenant_id>/`.
- Worker runs are constrained to the requesting tenant's prefix only.
- Cross-tenant reads are forbidden by RBAC and verified by an integration
  test in Phase 4.

## Retention

- Default tenant data TTL: 365 days from last access. Tenants on the
  `archive` plan may extend to 5 years.
- Operational logs: 90 days, then aggregated metrics retained for 13 months.
- Backups must **not** be committed to source control (`backups/` is in
  `.gitignore`); they live in a separate cool-tier container.

## Deletion

- A tenant deletion request triggers `purge_tenant(tenant_id)` which:
  1. Deletes all blobs under `tenants/<id>/`.
  2. Drops queue messages addressed to that tenant.
  3. Records the event in the audit log.
- Confirmed within 30 days (GDPR Art. 17).

## Audit

- Every API call is logged with: timestamp, API-key fingerprint (first 12
  hex chars of SHA-256), endpoint, status code, request size, latency.
- Logs are append-only, signed, and retained 13 months.

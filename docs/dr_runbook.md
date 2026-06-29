# Disaster recovery runbook

## Scope
Recovery of ShieldLab G4 SaaS (API + worker + storage) after a region-level
outage or accidental destructive action.

## Backup strategy
- Storage: Azure GZRS (geo-zone-redundant), automatic.
- Configuration: Bicep templates in `infra/`, version-pinned.
- Secrets: Azure Key Vault with soft-delete (90 d) + purge protection.
- Database (when added): point-in-time restore enabled, 35 d window.

## Drill cadence
Quarterly. Documented in `docs/dr_drill_log.md` (created on first drill).

## Procedure (region-loss scenario)
1. **Declare incident.** On-call SRE invokes Sev-1, opens incident channel.
2. **Failover storage.** Initiate GZRS failover (Azure Portal → Storage
   account → Geo replication → Failover). RPO ≤ 15 min.
3. **Redeploy infra to paired region.**
   ```powershell
   az deployment sub create -l <paired-region> -f infra/main.bicep `
     -p infra/main.parameters.example.json
   ```
4. **Restore secrets.** From Key Vault soft-delete:
   ```powershell
   az keyvault secret recover --vault-name <vault> --name <secret>
   ```
5. **Re-point DNS / Front Door** to the new region.
6. **Smoke test.** Run `pytest -m "unit or integration" tests/`.
7. **Communicate.** Update status page; post-incident review within 48 h.

## Procedure (data-corruption scenario)
1. Stop the worker(s) (`az aks scale --node-count 0`).
2. Identify corruption scope from audit logs.
3. Restore affected blobs from soft-delete (`az storage blob undelete`).
4. Replay queue messages from the dead-letter queue (Phase 2 deliverable).
5. Resume workers; reconcile.

## Contacts
- On-call SRE rotation: PagerDuty schedule `shieldlab-sre`.
- Security: `security@shieldlab-g4.invalid`.

# Security Policy

## Supported versions
The latest minor release receives security fixes. Older versions are best-effort.

## Reporting a vulnerability
- Email: security@shieldlab-g4.invalid (or open a GitHub Security Advisory).
- Do **not** open public issues for vulnerabilities.
- Expect an acknowledgement within 3 business days and a remediation plan within
  10 business days for High/Critical findings.

## Threat model (summary)

The platform is multi-tier:

| Tier                  | Primary risks                                          | Controls                                                   |
|-----------------------|--------------------------------------------------------|------------------------------------------------------------|
| Streamlit UI          | XSS via untrusted study data, session hijack           | Input sanitisation, no eval, JWT/API-key auth              |
| FastAPI REST          | Unauthenticated access, DoS, prompt-injection of jobs  | API-key auth, strict CORS allowlist, per-key rate limit    |
| Worker (queue→Geant4) | Remote code via maliciously crafted study JSON         | Pydantic schema, sandboxed exec, resource limits           |
| Azure storage         | Data exfiltration / tenant cross-read                  | Tenant-scoped prefixes, RBAC, private endpoints (Phase 4)  |

## Hardening defaults (Phase 0)

- API CORS is **localhost-only** unless `SHIELDLAB_CORS_ORIGINS` is set.
- Wildcard CORS is **rejected** outside `SHIELDLAB_DEV=1`.
- API keys are **SHA-256 hashed**; plaintext keys never leave the request.
- Per-key rate limit defaults to 60 req/min (`SHIELDLAB_RATE_LIMIT_PER_MIN`).
- The legacy "release_gate" badge now requires both CI green and `science_gate`
  green; CI cannot ship a build that the science gate rejects.
- `backups/` is `.gitignore`d; CI fails if the directory reappears in `git ls-files`.

## Out of scope
- Issues that require physical access to the host.
- Self-XSS in the Streamlit dev mode (`SHIELDLAB_DEV=1`).
- Vulnerabilities in third-party services we depend on (report to that vendor).

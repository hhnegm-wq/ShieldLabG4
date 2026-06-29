# ShieldLab G4 — Security Hardening Report
**Date:** 2026-05-16  
**Scope:** Full OWASP Top 10 audit of `api/`, `ui/`, `ui/pages/`, `ui/auth.py`  
**Outcome:** All identified issues FIXED. Tests green (170 passed, 5 skipped). No CVEs found.

---

## Methodology
- Full source read: `api/main.py`, `api/security.py`, `api/middleware/quota.py`, `ui/auth.py`, `ui/pages/run_study.py`
- Grep sweeps for: `subprocess`, `shell=True`, `eval`, `exec`, `str(exc)`, `pickle.load`, `yaml.load`, `SECRET`, hardcoded credentials
- Dependency CVE scan: `pip-audit` against `api/requirements.txt`
- Test gate: 170 passed, 5 skipped (same as pre-audit baseline)

---

## Findings & Fixes

### HIGH — Information Disclosure via Raw Exception Text (OWASP A05)
**File:** `api/main.py`  
**Finding:** All 6 physics endpoints and the job submission endpoint used  
`raise HTTPException(status_code=500, detail=str(exc))` — exposing full Python  
exception messages (including internal paths, module names, stack hints) to API clients.  
**Fix:** Replaced every `str(exc)` / `f"...{exc}"` 500 response with `_raise_internal_error(exc)`,  
a helper that:
- Generates a random 12-hex correlation ID
- Logs the full exception server-side via `logging.exception()`
- Returns only `"An internal error occurred. Reference ID: <id>"` to the client  

**Files changed:** `api/main.py`

---

### HIGH — No Global HTTP Request Body Size Limit (OWASP A05 / DoS)
**File:** `api/main.py`  
**Finding:** No global middleware enforced a maximum request body size.  
While `JobSubmitRequest` validated a 256 KB study payload *after* deserialization,  
the other endpoints (`/shielding`, `/estar`, `/ion`, `/dose-rate`, `/compare`) had  
no body size guard at the middleware level.  
**Fix:** Added `RequestSizeLimitMiddleware` (ASGI-native, outermost middleware):
- Reads the `Content-Length` header before routing
- Rejects with HTTP 413 if body exceeds **2 MB**
- Zero serialization overhead for oversized requests  

**Files changed:** `api/main.py`

---

### HIGH — Study File Upload: No Size Limit, Write-Before-Validate (OWASP A05 / A03)
**File:** `ui/pages/run_study.py`  
**Finding:** Uploaded JSON study files were written to disk *before* JSON parsing, and  
there was no size cap — a malicious oversized upload would exhaust memory during `.decode()`.  
**Fix:**
1. Read upload bytes and check against **512 KB** hard cap before any processing
2. Parse JSON and validate *before* writing to disk
3. If JSON is invalid, stop with an error message — no file artifact is created  

**Files changed:** `ui/pages/run_study.py`

---

### MEDIUM — Security Response Headers Missing (OWASP A05)
**File:** `api/main.py`  
**Finding:** API responses contained no OWASP-recommended security headers.  
**Fix:** Added `SecurityHeadersMiddleware` (ASGI-native) applying headers to every response:
- `X-Content-Type-Options: nosniff` — prevents MIME sniffing
- `X-Frame-Options: DENY` — prevents clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0` — disables legacy XSS filter (modern browsers ignore it; set to 0 per OWASP recommendation)
- `Cache-Control: no-store` — prevents API responses from being cached  

**Files changed:** `api/main.py`

---

### MEDIUM — Subprocess Arguments Not Validated (OWASP A03 / Defence-in-Depth)
**File:** `ui/pages/run_study.py`  
**Finding:** User-controlled text inputs (`wsl_distro`, `geant4_setup`, `executable_str`)  
were passed directly to `subprocess.Popen` as list elements. While `shell=False` prevents  
shell injection, passing null bytes or excessively long strings is unexpected and can  
cause subprocess failures or unexpected behavior on some platforms.  
**Fix:** Added `_safe_arg()` helper that:
- Strips whitespace
- Rejects null bytes (`\x00`)
- Rejects strings exceeding 512 characters
- Stops execution with a clear error message if any check fails  

**Files changed:** `ui/pages/run_study.py`

---

### MEDIUM — API Query Parameter Length Unrestricted (OWASP A03)
**File:** `api/main.py`  
**Finding:** `GET /api/v1/compendium` and `GET /api/v1/isotopes` accepted `search` and  
`category` query parameters with no length limit. These are used in Python string  
operations over in-memory lists — no SQL injection surface — but arbitrarily long  
search strings are wasteful and should be bounded.  
**Fix:** Added `max_length` constraints via FastAPI `Query()`:
- `search`: `max_length=200`
- `category`: `max_length=100`  

FastAPI/Pydantic enforces these and returns HTTP 422 automatically.  
**Files changed:** `api/main.py`

---

### MEDIUM — Ion Particle Identifier Not Validated (OWASP A03)
**File:** `api/main.py`  
**Finding:** `IonRequest.particle` was a free-form string with no validation.  
An unexpected value would propagate into `compute_ion_table()` in the physics library.  
**Fix:** Added `check_particle` field validator enforcing an allowlist:
- Named particles: `proton`, `alpha`, `deuteron`, `triton`, `He3`
- ZAID notation: `Z:A` pattern (e.g. `6:12`), enforced with `re.fullmatch(r"\d{1,3}:\d{1,3}", v)`
- Invalid values return HTTP 422  

**Files changed:** `api/main.py`

---

### MEDIUM — JWT Decode Missing `exp` Claim Enforcement (OWASP A07)
**File:** `ui/auth.py`  
**Finding:** `jwt.decode()` was called without `options={"require": ["exp"]}`.  
A JWT issued with no `exp` claim would be accepted and never expire — creating  
a permanent access token if the secret were ever leaked.  
**Fix:** Added `options={"require": ["exp"]}` to the `jwt.decode()` call.  
PyJWT will now raise `MissingRequiredClaimError` for tokens lacking an expiry,  
which is caught by the existing `except Exception` block and resolves to `None` (no access).  
**Files changed:** `ui/auth.py`

---

## Items Confirmed Safe (No Fix Required)

| Area | Finding |
|------|---------|
| `api/security.py` — API key verification | Uses `hmac.compare_digest` — constant-time, safe |
| `api/security.py` — CORS | Refuses `*` outside `SHIELDLAB_DEV=1`; explicit allowlist |
| `api/security.py` — Rate limiting | Thread-safe in-memory token bucket, 60 req/min default |
| `api/middleware/quota.py` — Quota | Sliding window per-key CPU+job quotas |
| `ui/auth.py` — License key | `hmac.compare_digest` — constant-time, safe |
| `ui/pages/run_study.py` — Popen | `shell=False`, list-form args — no shell injection |
| `ui/pages/run_study.py` — Path traversal | `_safe_uploaded_study_path()` and `_validated_build_dir()` both use `is_within_directory()` checks |
| `api/main.py` — Azure storage secrets | Read from env vars only; no hardcoded credentials |
| `api/main.py` — Output prefix | `output_prefix` validated: no `..`, no backslash, no control chars |
| Dependency scan (`pip-audit`) | **No known vulnerabilities** in `api/requirements.txt` |

---

## OWASP Top 10 Coverage Summary

| ID | Category | Status |
|----|----------|--------|
| A01 | Broken Access Control | Confirmed: CORS allowlist, API key gate, path traversal guards present |
| A02 | Cryptographic Failures | Confirmed: No hardcoded secrets; HS256 JWT with `exp` now required |
| A03 | Injection | Fixed: particle allowlist, query max_length, subprocess arg validation |
| A04 | Insecure Design | Confirmed: Rate limiting + quota middleware present |
| A05 | Security Misconfiguration | Fixed: Security headers added, request size limit added, upload validated |
| A06 | Vulnerable Components | Confirmed: pip-audit reports no known CVEs |
| A07 | Auth Failures | Fixed: JWT `exp` enforcement added |
| A08 | Software & Data Integrity | Confirmed: No unsafe deserialization (pickle/marshal/unsafe yaml) found |
| A09 | Logging & Monitoring | Fixed: Internal errors now logged with correlation ID; no secrets in logs |
| A10 | SSRF | N/A: No user-controlled URL fetch paths identified |

---

## Test Gate
```
pytest -q --ignore=backups -m "not geant4 and not publication and not ui and not network"
170 passed, 5 skipped — PASS
```

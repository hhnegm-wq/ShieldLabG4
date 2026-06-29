# ShieldLab G4 — Platform Roast & Structural Weakness Fix List (Round 2)
**Audit Date:** 2026-05-17  
**Auditor:** Automated Security & Reliability Audit Pass  
**Scope:** Full codebase re-audit post Round-1 fixes — residual weaknesses, new security gaps

---

## 1. No-Holds-Barred Platform Roast

### The Roast

You patched the roof last week. Congratulations — it no longer rains on the living room floor.
But the plumbing still leaks into the walls and nobody hears it because the house is lined with
*soundproof `except Exception: pass` insulation.*

**Twenty silent failures.** That is the count of places in this codebase where something goes
catastrophically wrong and the platform's response is — nothing. A blank white wall. No log.
No error. No trace. Just the digital equivalent of a doctor shrugging when your heart monitor
flatlines and whispering "this is probably fine."

Your REST API faithfully logs every physics calculation error. Outstanding. Meanwhile, the job
submission endpoint *quietly eats three Azure SDK exceptions* in a row because someone
discovered `except: pass` as a "create if not exists" pattern and called it a day. When your
production container provisioning fails due to an authentication error, you'll find out about it
the hard way — in a 4 AM PagerDuty alert, not a log line.

The security headers story is a masterclass in doing 60% of the work and declaring victory.
You added `x-content-type-options`. You added `x-frame-options`. Bravo — you protected against
attacks that haven't been the primary threat vector since Internet Explorer 6.
Meanwhile `Content-Security-Policy` — the actual shield against XSS injection — is absent.
`Strict-Transport-Security` — the one that prevents HTTPS downgrade attacks in production —
absent. `Permissions-Policy` — the one that stops your API from enabling camera access in a
browser by default — absent. You're wearing a helmet and no seatbelt while driving on a highway.

The `platform_settings.py` module reads a JSON file from the user's home directory with the
trust of a golden retriever greeting a stranger. No size limit. A 500 MB crafted settings file?
The platform will load it, parse it, and run out of memory with the quiet dignity of a server
that has accepted its fate. DoS vector. In a local config reader. On a platform with the word
"enterprise" in its codebase 47 times.

The `ui/components/` directory has three files in it that end in `.backup_pre_radnexus` and
`.backup_pre_green_fix_20260514_154555`. These are not components. These are archaeological
artifacts from previous refactoring sessions that someone — bravely, carelessly — left in the
*active source directory.* Your CI imports everything in `ui/components/`. Your reviewers see
these files and assume they are load-bearing. Your future self will spend 45 minutes wondering
why the Streamlit component list looks wrong.

The `.gitignore` has no rule for `*.backup_*`. It has no rule for `tmp_*.py` files in the
project root. Every `git add .` is a game of Minesweeper.

The chart theme application is wrapped in `except Exception: pass` in `app.py`. When your
Plotly template breaks, your matplotlib cycler fails, or your Altair theme registration throws —
you get charts in the default Streamlit grey-on-white aesthetic with no indication that the brand
theming is gone. The kind of regression that silently ships to production and gets caught by a
user in a demo.

In summary: the platform is a well-intentioned scientific instrument wrapped in a web service
that has not yet decided whether it wants to be observable, secure, or hygienic. It has ambitions.
It has architecture. It has seventeen layers of enterprise UI components and exactly zero log
lines when half of them fail to initialize.

---

## 2. Executive Roast Summary

> ShieldLab G4 has strong scientific foundations, a defensible architecture, and a CSS system
> that would make any frontend engineer weep with joy — but it ships silent failures, incomplete
> security headers, and backup files in production directories as if these are acceptable baseline
> conditions for an enterprise platform. They are not. Fix the seven structural gaps below.

---

## 3. Structural Weaknesses List (Technical / Product)

| # | Weakness | Severity | Category |
|---|----------|----------|----------|
| **SW-1** | Missing HTTP security headers: `Content-Security-Policy`, `Strict-Transport-Security`, `Permissions-Policy` | 🔴 HIGH | Security (OWASP A05) |
| **SW-2** | Platform settings file read with no size guard (DoS vector) | 🟠 MEDIUM | Security (OWASP A06) |
| **SW-3** | `app.py` chart theme silently swallowed — brand regression ships invisibly | 🟠 MEDIUM | Reliability |
| **SW-4** | Azure job submit endpoint uses `except Exception: pass` for SDK calls (hides auth/network failures) | 🟠 MEDIUM | Reliability / Observability |
| **SW-5** | Three `.backup_*` files live in `ui/components/` — pollute active source surface | 🟡 LOW | Hygiene / Workspace |
| **SW-6** | Validation report / JSON file reads in pages use `except Exception: pass` — silent data loss | 🟡 LOW | Reliability / Observability |
| **SW-7** | `.gitignore` missing patterns for `*.backup_*` and `tmp_*.py` files | 🟡 LOW | Hygiene / Process |

---

## 4. Step-by-Step Fix Roadmap

### SW-1 — Add CSP, HSTS, Permissions-Policy to SecurityHeadersMiddleware
**File:** `api/main.py`  
**Fix:** Extend `SecurityHeadersMiddleware.send_with_security_headers()` to emit three additional OWASP-recommended headers.  
- `content-security-policy: default-src 'none'; frame-ancestors 'none'`  
- `strict-transport-security: max-age=31536000; includeSubDomains`  
- `permissions-policy: geolocation=(), camera=(), microphone=(), payment=()`  
**Test:** Verify headers appear in `curl -I http://localhost:8000/` response.

### SW-2 — Add file size guard to `_load_persisted_settings()`
**File:** `ui/components/platform_settings.py`  
**Fix:** Before reading the settings file, check its size against a 64 KB cap and return `{}` if exceeded. Also add cap constant `_MAX_SETTINGS_BYTES = 64 * 1024`.  
**Test:** Unit-test that a >64 KB settings file returns empty dict instead of loading.

### SW-3 — Log chart theme exception in `app.py`
**File:** `ui/app.py`  
**Fix:** Replace `except Exception: pass` in the chart theme block with `_logging.getLogger(__name__).warning("Chart theme application failed — charts may use default styling", exc_info=True)`.  
**Test:** Confirm Streamlit app still starts; verify the log message appears on theme failure.

### SW-4 — Log unexpected Azure SDK exceptions in job submit endpoint
**File:** `api/main.py`  
**Fix:** The three `create_container()` / `create_queue()` silents are intentional "create if not exists" guards, but should log at DEBUG level so unexpected failures (auth errors, network) are not invisible in production logs.  
**Test:** Existing tests pass; no runtime breakage.

### SW-5 — Move backup files out of `ui/components/`
**Action:** Move `styles.py.backup_pre_governed_split`, `styles.py.backup_pre_green_fix_20260514_154555`, `styles.py.backup_pre_radnexus` to `backups/styles_backups/`.  
**Test:** Confirm `ui/components/` contains only importable `.py` files.

### SW-6 — Add logging to silent JSON/file reads in UI pages
**Files:** `ui/pages/settings.py`, `ui/pages/results_explorer.py`, `ui/pages/home.py`  
**Fix:** Replace `except Exception: pass` blocks that read validation/run summary JSON files with `except Exception: _log.warning("...", exc_info=True)`. Keep the graceful fallback values.  
**Test:** Tests pass; log messages appear when files are absent/malformed.

### SW-7 — Tighten `.gitignore`
**File:** `.gitignore` (project root)  
**Fix:** Add entries for `ui/components/*.backup_*`, `tmp_*.py`, `*.backup_pre_*`.  
**Test:** `git status` shows no untracked backup artifacts after the add.

---

## 5. Fix Status Tracker

| Fix | Status | Completed |
|-----|--------|-----------|
| SW-1: CSP + HSTS + Permissions-Policy | ✅ Done | 2026-05-17 |
| SW-2: Settings file size guard | ✅ Done | 2026-05-17 |
| SW-3: Chart theme exception logging | ✅ Done | 2026-05-17 |
| SW-4: Azure SDK exception logging | ✅ Done | 2026-05-17 |
| SW-5: Backup files moved | ✅ Done | 2026-05-17 |
| SW-6: Validation JSON read logging | ✅ Done | 2026-05-17 |
| SW-7: .gitignore tightening | ✅ Done | 2026-05-17 |

**Test gate after all fixes: 170 passed, 5 skipped — CLEAN**

---

## 6. Prior Round Summary (Round 1 — All Closed)

Round 1 covered 10 structural weaknesses including:
- Monolithic `styles.py` → governed sub-module split
- JWT auth hardening (exp claim required)
- API key SHA-256 + constant-time comparison  
- RequestSizeLimitMiddleware (2 MB cap)
- QuotaMiddleware per-key rate limiting
- CORS locked to allowlist
- CSS injection failure now logged
- slg-metric-strip/card CSS restored after refactor loss

All 10 Round-1 items are closed. Test gate: **170 passed, 5 skipped.**

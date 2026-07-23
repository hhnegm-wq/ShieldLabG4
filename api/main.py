"""ShieldLab G4 — FastAPI REST Service.

Endpoints
---------
GET  /                          Health check
POST /api/v1/shielding          Compute MAC, LAC, HVL, TVL, MFP, EBF for a material
POST /api/v1/estar              ESTAR electron stopping-power table
POST /api/v1/ion                Ion (proton/alpha/heavy-ion) range & stopping power
POST /api/v1/dose-rate          H*(10) dose-equivalent rate for point/line/disk source
POST /api/v1/compare            Multi-material comparison (up to 8 materials)
POST /api/v1/jobs/submit        Queue simulation job for cloud worker execution
GET  /api/v1/compendium         List or search the NIST COMPENDIUM material database
GET  /api/v1/isotopes           List or search the ICRP-107 isotope library
GET  /api/v1/version            Package version

Authentication
--------------
Pro-tier endpoints require  X-API-Key: <key>  header.
In this open-core version the key check is a stub (always passes when key is
present).  Replace `_verify_api_key` with real Stripe/Auth0 logic before
deploying.

Usage example (curl):
    curl -X POST http://localhost:8000/api/v1/shielding \\
         -H "Content-Type: application/json" \\
         -H "X-API-Key: dev" \\
         -d '{"material": {"Pb": 1.0}, "density": 11.35,
              "energies_MeV": [0.1, 0.662, 1.25]}'

Run:
    cd D:/projects/ShieldLabG4
    set PYTHONPATH=python;ui
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Bootstrap PYTHONPATH so shieldlab package is importable
_ROOT = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT / "python"), str(_ROOT / "ui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from typing import Annotated, Any, NoReturn
import numpy as np

from starlette.types import ASGIApp, Receive, Scope, Send

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from shieldlab import __version__

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ShieldLab G4 REST API",
    description=(
        "Analytical radiation-shielding calculations: MAC, HVL, TVL, MFP, EBF, "
        "ESTAR, ion range, dose rate, and multi-material comparison."
    ),
    version=__version__,
    contact={"name": "ShieldLab G4 Team", "url": "https://shieldlab-g4.io"},
    license_info={"name": "AGPL-3.0 (free tier); Commercial (pro tier)"},
)

from api.security import allowed_origins, verify_api_key, default_rate_limiter
from api.telemetry import TracingMiddleware, configure_json_logging
from api.middleware.quota import QuotaMiddleware

_RATE_LIMITER = default_rate_limiter()

configure_json_logging()
_LOG = logging.getLogger(__name__)

# ── Security middleware ───────────────────────────────────────────────────────

_MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024  # 2 MB hard cap on all HTTP request bodies


class RequestSizeLimitMiddleware:
    """Reject HTTP requests whose declared or actual body exceeds the size cap."""

    def __init__(self, app: ASGIApp, max_bytes: int = _MAX_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Reject immediately when Content-Length header exceeds cap.
        raw_headers: dict[bytes, bytes] = {k.lower(): v for k, v in scope.get("headers", [])}
        cl_header = raw_headers.get(b"content-length")
        if cl_header is not None and int(cl_header) > self.max_bytes:
            from starlette.responses import Response as _Resp
            await _Resp(
                content=b'{"detail":"Request body too large."}',
                status_code=413,
                media_type="application/json",
            )(scope, receive, send)
            return

        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    """Add OWASP-recommended security headers to every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"x-xss-protection", b"0"),
                    (b"cache-control", b"no-store"),
                    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                    (b"permissions-policy", b"geolocation=(), camera=(), microphone=(), payment=()"),
                ])
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


app.add_middleware(TracingMiddleware)
app.add_middleware(QuotaMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    allow_credentials=False,
    max_age=600,
)
# SecurityHeadersMiddleware wraps CORS so headers appear on all responses
app.add_middleware(SecurityHeadersMiddleware)
# RequestSizeLimitMiddleware is outermost — rejects oversized bodies before routing
app.add_middleware(RequestSizeLimitMiddleware)


def _verify_api_key(x_api_key: str | None) -> None:
    """Verify API key + apply per-key rate limit (Phase 0 hardening)."""
    fp = verify_api_key(x_api_key)
    _RATE_LIMITER.hit(fp)


def _raise_internal_error(exc: Exception) -> NoReturn:
    """Log the full exception server-side; return only a safe correlation ID to the client."""
    err_id = uuid4().hex[:12]
    _LOG.exception("Internal server error [%s]", err_id)
    raise HTTPException(
        status_code=500,
        detail=f"An internal error occurred. Reference ID: {err_id}",
    ) from exc

# ── Request / response models ─────────────────────────────────────────────────

class ShieldingRequest(BaseModel):
    material: dict[str, float] = Field(
        ...,
        description="Element-symbol → weight fraction mapping, e.g. {'Pb': 1.0}",
        examples=[{"Pb": 1.0}],
    )
    density: float = Field(..., gt=0, description="Material density in g/cm³")
    energies_MeV: list[float] = Field(
        default=[0.1, 0.3, 0.5, 0.662, 1.0, 1.25],
        description="Photon energies (MeV), 1–500 points",
    )
    gp_material: str = Field(
        default="Water",
        description="G-P buildup factor material key (Water, Concrete, Iron, Lead, etc.)",
    )
    thickness_cm: float | None = Field(
        default=None,
        description="Optional thickness (cm) for transmission T(x) output",
    )

    @field_validator("energies_MeV")
    @classmethod
    def check_energies(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("At least one energy is required.")
        if len(v) > 500:
            raise ValueError("Maximum 500 energy points per request.")
        if any(e <= 0 or e > 100 for e in v):
            raise ValueError("Energies must be in (0, 100] MeV.")
        return v

    @field_validator("material")
    @classmethod
    def check_fractions(cls, v: dict) -> dict:
        if not v:
            raise ValueError("material must have at least one element.")
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weight fractions must sum to ~1.0 (got {total:.4f}).")
        return v


class ESTARRequest(BaseModel):
    material: dict[str, float] = Field(..., description="Element → weight fraction")
    density: float = Field(..., gt=0)
    energies_MeV: list[float] = Field(
        default=None,
        description="Electron energies (MeV); defaults to ESTAR standard grid",
    )

    @field_validator("energies_MeV", mode="before")
    @classmethod
    def default_energies(cls, v):
        if v is None:
            return [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        return v


class IonRequest(BaseModel):
    material: dict[str, float]
    density: float = Field(..., gt=0)
    particle: str = Field(default="proton", description="'proton', 'alpha', or ZAID like '6:12'")
    energies_MeV_u: list[float] = Field(
        default=None,
        description="Ion kinetic energies in MeV/u; defaults to standard grid",
    )

    @field_validator("energies_MeV_u", mode="before")
    @classmethod
    def default_ion_energies(cls, v):
        if v is None:
            return [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 200.0]
        return v

    @field_validator("particle")
    @classmethod
    def check_particle(cls, v: str) -> str:
        import re as _re
        # Allow named particles or ZAID notation (Z:A, e.g. 6:12)
        if v in {"proton", "alpha", "deuteron", "triton", "He3"}:
            return v
        if _re.fullmatch(r"\d{1,3}:\d{1,3}", v):
            return v
        raise ValueError(
            "particle must be 'proton', 'alpha', 'deuteron', 'triton', 'He3', "
            "or ZAID notation like '6:12'."
        )


class DoseRateRequest(BaseModel):
    activity_Bq: float = Field(..., gt=0)
    energies_MeV: list[float]
    intensities: list[float] = Field(
        default=None,
        description="Photon yields per disintegration (same length as energies_MeV); default all=1.0",
    )
    distances_m: list[float] = Field(
        default=None,
        description="Distances in m; defaults to [0.1, 0.5, 1.0, 2.0, 5.0]",
    )
    geometry: str = Field(
        default="point",
        description="'point', 'line', or 'disk'",
    )
    line_length_cm: float | None = None
    disk_radius_cm: float | None = None

    @field_validator("geometry")
    @classmethod
    def check_geom(cls, v: str) -> str:
        if v not in {"point", "line", "disk"}:
            raise ValueError("geometry must be 'point', 'line', or 'disk'.")
        return v

    @field_validator("intensities", mode="before")
    @classmethod
    def default_intensities(cls, v):
        return v  # handled in endpoint

    @field_validator("distances_m", mode="before")
    @classmethod
    def default_distances(cls, v):
        if v is None:
            return [0.1, 0.5, 1.0, 2.0, 5.0]
        return v


class CompareRequest(BaseModel):
    materials: list[dict] = Field(
        ...,
        description="List of {name, mass_fracs: {el: wf}, density} dicts (max 8)",
    )
    energies_MeV: list[float] = Field(
        default=None,
        description="Shared energy grid (MeV); defaults to XCOM standard grid",
    )
    gp_material: str = Field(default="Water")

    @field_validator("materials")
    @classmethod
    def check_mats(cls, v):
        if not 1 <= len(v) <= 8:
            raise ValueError("Between 1 and 8 materials required.")
        return v


_MAX_STUDY_JSON_BYTES = 256 * 1024  # 256 KB — guards against oversized payloads
_MAX_RUN_ARGS = 20
_MAX_RUN_ARG_LEN = 256


class JobSubmitRequest(BaseModel):
    study: dict[str, Any] = Field(..., description="Study JSON payload for shieldlab.io.runner")
    run_args: list[str] = Field(default_factory=list, description="Optional args passed to shieldlab.io.runner")
    output_prefix: str | None = Field(
        default=None,
        description="Optional output blob prefix (must not contain '..' or control characters)",
    )

    @field_validator("study")
    @classmethod
    def check_study_size(cls, v: dict) -> dict:
        raw = json.dumps(v, ensure_ascii=True).encode()
        if len(raw) > _MAX_STUDY_JSON_BYTES:
            raise ValueError(
                f"study payload exceeds {_MAX_STUDY_JSON_BYTES // 1024} KB limit."
            )
        return v

    @field_validator("run_args")
    @classmethod
    def check_run_args(cls, v: list[str]) -> list[str]:
        if len(v) > _MAX_RUN_ARGS:
            raise ValueError(f"run_args may contain at most {_MAX_RUN_ARGS} items.")
        for arg in v:
            if len(arg) > _MAX_RUN_ARG_LEN:
                raise ValueError(
                    f"Each run_arg must be ≤ {_MAX_RUN_ARG_LEN} characters."
                )
        return v

    @field_validator("output_prefix")
    @classmethod
    def check_output_prefix(cls, v: str | None) -> str | None:
        import re
        if v is None:
            return v
        if ".." in v or re.search(r"[\x00-\x1f\\]", v):
            raise ValueError(
                "output_prefix must not contain '..', backslashes, or control characters."
            )
        return v.strip("/")


# Job queue + blob storage are provided by the pluggable backend abstraction in
# ``shieldlab.backends`` (LocalBackend for free/demo mode; AzureBackend for
# production), selected via SHIELDLAB_BACKEND or auto-detected. See submit_job.


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/v1/version", tags=["meta"])
def version() -> dict:
    return {"shieldlab_version": __version__}


@app.post("/api/v1/shielding", tags=["physics"])
def shielding(
    req: ShieldingRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Compute MAC, LAC, HVL₁, TVL₁, MFP, EBF, EABF, Zeff, FNRCS for a material."""
    _verify_api_key(x_api_key)
    try:
        from shieldlab.physics.shielding_params import compute_shielding_table
        E = np.array(req.energies_MeV)
        df = compute_shielding_table(
            req.material, req.density, E,
            gp_mat=req.gp_material,
            thickness_cm=req.thickness_cm,
        )
        return {"status": "ok", "data": df.to_dict(orient="records")}
    except Exception as exc:
        _raise_internal_error(exc)


@app.post("/api/v1/estar", tags=["physics"])
def estar(
    req: ESTARRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Compute ESTAR electron stopping-power table (NIST method)."""
    _verify_api_key(x_api_key)
    try:
        from shieldlab.physics.nist_estar import compute_estar_table
        E = np.array(req.energies_MeV)
        df = compute_estar_table(req.material, req.density, E)
        return {"status": "ok", "data": df.to_dict(orient="records")}
    except Exception as exc:
        _raise_internal_error(exc)


@app.post("/api/v1/ion", tags=["physics"])
def ion(
    req: IonRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Compute ion stopping-power / range table (Bethe-Bloch, PSTAR/ASTAR)."""
    _verify_api_key(x_api_key)
    try:
        from shieldlab.physics.ion_range import compute_ion_table
        E = np.array(req.energies_MeV_u)
        df = compute_ion_table(req.material, req.density, req.particle, E)
        return {"status": "ok", "data": df.to_dict(orient="records")}
    except Exception as exc:
        _raise_internal_error(exc)


@app.post("/api/v1/dose-rate", tags=["physics"])
def dose_rate_endpoint(
    req: DoseRateRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Compute H*(10) dose-equivalent rate vs distance for a gamma source."""
    _verify_api_key(x_api_key)
    try:
        from shieldlab.physics.dose_rate import (
            dose_rate_point, dose_rate_line, dose_rate_disk, fluence_to_h10
        )
        E  = np.array(req.energies_MeV)
        I  = np.array(req.intensities if req.intensities else [1.0] * len(E))
        ds = req.distances_m or [0.1, 0.5, 1.0, 2.0, 5.0]
        rows = []
        for d_m in ds:
            d_cm = d_m * 100.0
            if req.geometry == "point":
                H = dose_rate_point(req.activity_Bq, E, I, d_cm)
            elif req.geometry == "line":
                L = req.line_length_cm or 100.0
                H = dose_rate_line(req.activity_Bq / max(L, 1e-9), L, E, I, d_cm)
            else:
                R = req.disk_radius_cm or 10.0
                import math as _math
                H = dose_rate_disk(
                    req.activity_Bq / (_math.pi * R**2), R, E, I, d_cm
                )
            rows.append({"distance_m": d_m, "H_star_10_uSv_h": round(H, 8)})
        return {"status": "ok", "geometry": req.geometry, "data": rows}
    except Exception as exc:
        _raise_internal_error(exc)


@app.post("/api/v1/compare", tags=["physics"])
def compare(
    req: CompareRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Compare MAC, HVL, TVL for multiple materials on a shared energy grid."""
    _verify_api_key(x_api_key)
    try:
        from shieldlab.physics.shielding_params import compute_shielding_table
        if req.energies_MeV is None:
            from shieldlab.physics.shielding_params import XCOM_ENERGY_GRID
            E = XCOM_ENERGY_GRID
        else:
            E = np.array(req.energies_MeV)

        results = {}
        for mat in req.materials:
            name = mat.get("name", "unknown")
            mf   = mat["mass_fracs"]
            rho  = mat["density"]
            df   = compute_shielding_table(mf, rho, E, gp_mat=req.gp_material)
            results[name] = df.to_dict(orient="records")
        return {"status": "ok", "data": results}
    except Exception as exc:
        _raise_internal_error(exc)


@app.get("/api/v1/compendium", tags=["data"])
def compendium(
    search: str = Query(default="", description="Name/formula search string", max_length=200),
    category: str = Query(default="", description="Filter by category", max_length=100),
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Search the NIST COMPENDIUM material database."""
    _verify_api_key(x_api_key)
    from shieldlab.data.compendium import COMPENDIUM, search as _search, list_names
    cat = category or None
    if search:
        results = _search(search, category=cat)
    else:
        results = [m for m in COMPENDIUM if (not cat or m["category"] == cat)]
    # Return lightweight summary (no full mass_fracs to keep response compact)
    return {
        "status": "ok",
        "count": len(results),
        "materials": [
            {"name": m["name"], "formula": m["formula"],
             "density": m["density"], "category": m["category"]}
            for m in results
        ],
    }


@app.get("/api/v1/isotopes", tags=["data"])
def isotopes(
    search: str = Query(default="", description="Symbol or name search", max_length=200),
    category: str = Query(default="", description="Filter by category", max_length=100),
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Search the ICRP-107 isotope library."""
    _verify_api_key(x_api_key)
    from shieldlab.data.isotopes import ISOTOPES, half_life_str
    cat = category or None
    ql  = search.lower()
    results = [
        iso for iso in ISOTOPES
        if (not ql or ql in iso["symbol"].lower())
        and (not cat or iso["category"] == cat)
    ]
    return {
        "status": "ok",
        "count": len(results),
        "isotopes": [
            {
                "symbol":      iso["symbol"],
                "Z": iso["Z"], "A": iso["A"],
                "half_life":   half_life_str(iso["half_life_s"]),
                "decay_mode":  iso["decay_mode"],
                "principal_gammas": iso["gammas"][:3],
                "category":    iso["category"],
            }
            for iso in results
        ],
    }


@app.post("/api/v1/jobs/submit", tags=["jobs"])
def submit_job(
    req: JobSubmitRequest,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Submit a simulation job: store the study payload and enqueue a worker message.

    Uses the pluggable ``shieldlab.backends`` abstraction — LocalBackend
    (filesystem + SQLite, free/demo) or AzureBackend (Queue + Blob), selected by
    ``SHIELDLAB_BACKEND`` or auto-detected from the environment.
    """
    _verify_api_key(x_api_key)

    try:
        from shieldlab.backends import get_backend, load_config as _load_backend_config

        backend_cfg = _load_backend_config()
        backend = get_backend(backend_cfg)
        backend.ensure_ready()

        input_container = backend_cfg.input_container
        job_id = f"job-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        blob_name = f"studies/{job_id}.json"
        output_prefix = req.output_prefix or f"jobs/{job_id}/"
        study_blob_path = f"{input_container}/{blob_name}"

        backend.put_blob(
            input_container, blob_name, json.dumps(req.study, ensure_ascii=True).encode("utf-8")
        )
        backend.enqueue(
            json.dumps(
                {
                    "job_id": job_id,
                    "study_blob_path": study_blob_path,
                    "output_prefix": output_prefix,
                    "run_args": req.run_args,
                },
                ensure_ascii=True,
            )
        )

        return {
            "status": "queued",
            "job_id": job_id,
            "backend": type(backend).__name__,
            "queue_name": backend_cfg.queue_name,
            "study_blob_path": study_blob_path,
            "output_prefix": output_prefix,
        }
    except Exception as exc:
        _raise_internal_error(exc)


@app.get("/api/v1/jobs/{job_id}/result", tags=["jobs"])
def job_result(
    job_id: str,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """List result artifacts for a submitted job (default output prefix).

    Returns ``status='complete'`` with artifact names once the worker has
    produced output, otherwise ``status='pending'``.
    """
    _verify_api_key(x_api_key)

    import re

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id.")

    try:
        from shieldlab.backends import get_backend, load_config as _load_backend_config

        backend_cfg = _load_backend_config()
        backend = get_backend(backend_cfg)
        prefix = f"jobs/{job_id}/"
        try:
            artifacts = backend.list_blobs(backend_cfg.output_container, prefix)
        except NotImplementedError:
            artifacts = []
        return {
            "status": "complete" if artifacts else "pending",
            "job_id": job_id,
            "artifacts": artifacts,
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_internal_error(exc)

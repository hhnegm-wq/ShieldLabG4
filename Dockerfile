# syntax=docker/dockerfile:1
#
# Shared runtime image for the ShieldLab G4 local/free stack (UI + API + worker).
# One image, three roles — the role is chosen by the command in docker-compose.
# Runs on the LocalBackend (filesystem + SQLite): no cloud account required.
#
#   docker build -t shieldlabg4:local .
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    SHIELDLAB_BACKEND=local \
    SHIELDLAB_LOCAL_DATA_DIR=/data

WORKDIR /app

# Copy source and install the full UI + API + worker Python stack. The shieldlab
# package (matplotlib/openpyxl/pandas/pypdf), FastAPI, uvicorn, Streamlit and
# PyJWT all resolve from requirements.appservice.txt (which runs `-e ./python`).
COPY . .
RUN python -m pip install --upgrade pip "setuptools>=83.0.0" wheel \
    && python -m pip install -r requirements.appservice.txt

# Non-root runtime user; /data is the shared local-backend volume mount point.
RUN useradd --system --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000 8501

# Default role is the API; docker-compose overrides the command per service.
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

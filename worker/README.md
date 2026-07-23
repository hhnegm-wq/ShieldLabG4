# ShieldLabG4 Worker Service

This service consumes simulation jobs from Azure Queue Storage, runs ShieldLab workflows (including Geant4 execution when available), and uploads generated artifacts to Azure Blob Storage.

## Queue message schema

Each queue message body is JSON:

```json
{
  "job_id": "job-20260506-001",
  "study_blob_path": "simulation-input/studies/gamma_lead_sweep.json",
  "output_prefix": "jobs/job-20260506-001/",
  "run_args": ["--skip-geant4"]
}
```

- `job_id`: unique identifier for tracking.
- `study_blob_path`: `<container>/<blob-path>` for study JSON input.
- `output_prefix`: destination prefix in output blob container.
- `run_args`: optional extra args passed to `python -m shieldlab.io.runner`.

## Backend selection

The worker (and the API) talk to a **pluggable storage/queue backend**, so the
full pipeline runs with or without a cloud account:

- `SHIELDLAB_BACKEND=local` — **free/demo mode**: filesystem blobs + a SQLite
  queue under `SHIELDLAB_LOCAL_DATA_DIR` (default `./.shieldlab_data`). No cloud,
  no external services. Ideal for a single Linux VM (e.g. Oracle Cloud Always
  Free) or a laptop.
- `SHIELDLAB_BACKEND=azure` — Azure Queue Storage + Blob Storage (production).
- *unset* — auto-detected: `azure` if an Azure storage env var is present,
  otherwise `local`.

## Runtime configuration

Queue / container names (both backends):

- `SHIELDLAB_QUEUE_NAME` (or `AZURE_QUEUE_NAME`; default `simulation-jobs`)
- `SHIELDLAB_INPUT_CONTAINER` (or `AZURE_INPUT_CONTAINER_NAME`; default `simulation-input`)
- `SHIELDLAB_OUTPUT_CONTAINER` (or `AZURE_OUTPUT_CONTAINER_NAME`; default `simulation-output`)

Local backend:

- `SHIELDLAB_LOCAL_DATA_DIR` — data root (default `./.shieldlab_data`)

Azure backend (one of):

- `AZURE_STORAGE_ACCOUNT_URL` (example: `https://mystorage.blob.core.windows.net`) with managed identity
- `AZURE_STORAGE_CONNECTION_STRING` (fallback)

Worker loop (both backends):

- `SHIELDLAB_RESULTS_DIR` (default: `./build/results`)
- `SHIELDLAB_WORKER_POLL_SECONDS` (default: `10`)
- `SHIELDLAB_WORKER_VISIBILITY_TIMEOUT` (default: `300`)
- `SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT` (default: `5`) — messages dequeued more than this many times are moved to the poison (dead-letter) queue

## Local run (free / no cloud)

```bash
python -m pip install -e ./python
export SHIELDLAB_BACKEND=local            # filesystem + SQLite, no Azure
export SHIELDLAB_LOCAL_DATA_DIR=./.shieldlab_data
python worker/queue_worker.py
```

The API (`api/main.py`) uses the same backend, so a job submitted via
`POST /api/v1/jobs/submit` in local mode lands in the SQLite queue for this
worker to pick up and its artifacts are written under
`SHIELDLAB_LOCAL_DATA_DIR/blobs/<output-container>/` — a fully local,
cloud-free pipeline. Switch to Azure later by setting `SHIELDLAB_BACKEND=azure`
plus the Azure storage variables; no code changes required.

## AKS / Batch run

Build and publish this worker container, then run it as:

- AKS Deployment with horizontal pod autoscaling based on queue depth, or
- Azure Batch pool job using the same image.

Use Managed Identity and assign RBAC roles on storage:

- Storage Queue Data Contributor
- Storage Blob Data Contributor

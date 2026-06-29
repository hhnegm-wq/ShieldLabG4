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

## Runtime configuration

Required:

- `AZURE_STORAGE_ACCOUNT_URL` (example: `https://mystorage.blob.core.windows.net`)
- `AZURE_QUEUE_NAME`
- `AZURE_INPUT_CONTAINER_NAME`
- `AZURE_OUTPUT_CONTAINER_NAME`

Optional:

- `AZURE_STORAGE_CONNECTION_STRING` (fallback if managed identity is not used)
- `SHIELDLAB_RESULTS_DIR` (default: `./build/results`)
- `SHIELDLAB_WORKER_POLL_SECONDS` (default: `10`)
- `SHIELDLAB_WORKER_VISIBILITY_TIMEOUT` (default: `300`)
- `SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT` (default: `5`) — messages dequeued more than this many times are moved to the `<queue>-poison` dead-letter queue

## Local run

```bash
python -m pip install -r requirements.appservice.txt
python -m pip install -r worker/requirements.txt
python worker/queue_worker.py
```

## AKS / Batch run

Build and publish this worker container, then run it as:

- AKS Deployment with horizontal pod autoscaling based on queue depth, or
- Azure Batch pool job using the same image.

Use Managed Identity and assign RBAC roles on storage:

- Storage Queue Data Contributor
- Storage Blob Data Contributor

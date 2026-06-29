# AKS Worker Deployment

This manifest deploys the queue worker container to AKS using Workload Identity.

## Files

- worker-deployment.yaml

## Apply

```bash
kubectl apply -f deploy/aks/worker-deployment.yaml
```

## Required setup

1. Enable AKS Workload Identity on your cluster.
1. Create a user-assigned managed identity for worker pods.
1. Update service account annotation in worker-deployment.yaml with that client ID.
1. Create secret for storage account URL:

```bash
kubectl -n shieldlab create secret generic shieldlab-worker-secrets \
  --from-literal=azure_storage_account_url="https://<storage-account>.blob.core.windows.net"
```

## RBAC for worker managed identity

Assign these roles at storage account scope:

- Storage Queue Data Contributor
- Storage Blob Data Contributor

For queue-depth autoscaling, consider adding KEDA with Azure Queue trigger in a follow-up step.

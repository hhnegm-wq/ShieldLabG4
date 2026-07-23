# Free-tier deployment (Docker / Oracle Cloud Always Free)

Run the **whole platform — UI + API + worker** on one Linux VM with **no cloud
account fees**, using the LocalBackend (filesystem + SQLite). One command.

> This is the cloud-free path. For the managed Azure path see
> [production_deployment_runbook.md](../docs/production_deployment_runbook.md).

## 1. Get a free VM

[Oracle Cloud **Always Free**](https://www.oracle.com/cloud/free/) provides an
ARM Ampere VM (up to 4 OCPU / 24 GB RAM) free forever. Create an **Ubuntu 22.04**
instance. (Any Ubuntu VM / VPS works identically.)

## 2. Install Docker (once)

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
```

## 3. Deploy (one command)

```bash
git clone https://github.com/hhnegm-wq/ShieldLabG4.git
cd ShieldLabG4
docker compose up -d --build
```

- **UI:**  `http://<VM-public-ip>:8501`
- **API:** `http://<VM-public-ip>:8000`

The first build takes a few minutes (it installs the Python stack); subsequent
starts are instant.

## 4. Open the ports

Allow inbound TCP **8501** and **8000** in **both** the Oracle VCN *Security
List* (ingress rules) **and** on the VM:

```bash
sudo iptables -I INPUT -p tcp --dport 8501 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
```

## Manage

```bash
docker compose ps          # status + health
docker compose logs -f     # follow logs
docker compose restart     # restart all services
docker compose down        # stop (data kept in the 'shieldlab-data' volume)
docker compose down -v     # stop AND delete the data volume
```

## Custom ports

```bash
UI_PORT=80 API_PORT=8080 docker compose up -d
```

## Notes

- **Geant4 Monte-Carlo** is not baked into the container; the worker runs the
  analytical pipeline. Submit study jobs with `run_args: ["--skip-geant4"]`, or
  simply use the analytical UI features (attenuation, multi-material comparison,
  dose-rate, compendium, isotopes) which need no worker at all.
- API + worker share the SQLite queue and blob store via the `shieldlab-data`
  Docker volume; the UI talks to the API over HTTP.
- **Move to Azure later** with `SHIELDLAB_BACKEND=azure` plus the Azure storage
  variables — **no code changes**.

## HTTPS (recommended for real users)

Put a reverse proxy with automatic TLS in front, e.g. **Caddy**:

```caddyfile
your-domain.com {
    reverse_proxy localhost:8501
}
api.your-domain.com {
    reverse_proxy localhost:8000
}
```

or expose it instantly without opening ports using a **Cloudflare Tunnel**.

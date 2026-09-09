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

## Secure it for the public internet

The stack is **secure-by-default**: with no API keys configured, every protected
API route returns `503` until you set them. Before exposing it to real users:

### 1. Configure API keys + secrets

```bash
cp .env.example .env      # .env is git-ignored; never commit it
# Generate a key and its SHA-256 hash:
KEY=$(openssl rand -hex 32); echo "key=$KEY"; printf '%s' "$KEY" | sha256sum
# Then edit .env and set ONE of:
#   SHIELDLAB_API_KEYS=<the-key>              # simplest
#   SHIELDLAB_API_KEY_HASHES=<the-sha256>     # keeps no plaintext on disk
# plus a strong SHIELDLAB_JWT_SECRET for UI Pro tokens.
```

### 1b. Optional real user accounts (Supabase)

If you want hosted sign-in/sign-up/password reset for real users instead of the
local license/JWT fallback, set these in `.env` after you create or resume a
Supabase project:

```bash
SHIELDLAB_SUPABASE_URL=https://<project-ref>.supabase.co
SHIELDLAB_SUPABASE_ANON_KEY=<public-anon-key>
SHIELDLAB_SUPABASE_REDIRECT_TO=https://shield.example.com/
```

Then apply `deploy/supabase_init.sql` in the Supabase SQL editor. It creates the
`public.user_profiles` table, sync trigger, and row-level security policies that
ShieldLab G4 expects for hosted account metadata (`tier`, `role`).

Recommended initial roles:

- `viewer` → free read-only/default user
- `operator` → pro job-submitting user
- `admin` → pro admin user

The Streamlit UI automatically shows an account panel when the Supabase values
are present; without them the existing self-hosted license/JWT flow continues to
work.

### 2. Turn on automatic HTTPS (bundled Caddy)

A Caddy reverse proxy ships as an opt-in `proxy` profile. It terminates TLS
(automatic Let's Encrypt for a real domain), redirects HTTP→HTTPS, and forwards
to the API + UI on the internal network — so you expose only **80/443**:

```bash
# point your domain's DNS A/AAAA record at the VM first, then:
SHIELDLAB_DOMAIN=shield.example.com SHIELDLAB_TRUST_PROXY=1 \
  docker compose --profile proxy up -d --build
```

- **UI:**  `https://shield.example.com/`
- **API:** `https://shield.example.com/api/v1/...`

Open only **80** and **443** (and drop 8000/8501) in the Oracle Security List:

```bash
sudo iptables -I INPUT -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
```

`SHIELDLAB_TRUST_PROXY=1` lets the app read the real client IP from the proxy
for its built-in **per-IP rate limiting** (flood / brute-force protection); the
`SHIELDLAB_GLOBAL_RATE_LIMIT_PER_MIN` (default 120) tunes it. Keep it `0` when
running without the proxy so a forged `X-Forwarded-For` cannot spoof the source.

This Caddy profile has been validated against the Streamlit nested-route issue:
direct loads like `/study_builder` no longer emit `/_stcore/*` 404 noise once
requests are routed through the proxy.

> No domain yet? A **Cloudflare Tunnel** gives instant TLS without opening any
> inbound ports.

## Optional: full Geant4 worker on Docker

The default free-tier stack keeps the worker analytical-only. When you need a
real Geant4-capable worker on a Linux host with Docker, use the dedicated
override file:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.geant4.yml \
  --profile proxy up -d --build
```

This swaps the default worker image for a Geant4-enabled one built from
`worker/Dockerfile.geant4`, compiles `build/ShieldLabG4` inside the container,
and stores the Geant4 datasets in the named `geant4-data` volume mounted at
`/g4data`. The first
startup downloads the missing datasets, so expect it to take materially longer
than the analytical-only path.

For small VMs, keep `SHIELDLAB_RUN_MANAGER=serial`.


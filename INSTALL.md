# Installation & Deployment Manual

This guide covers every deployment scenario from a quick local test to a production setup behind a reverse proxy on Unraid.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Option A — Docker Compose with PostgreSQL (Recommended)](#2-option-a--docker-compose-with-postgresql-recommended)
3. [Option B — Standalone SQLite (Lightweight / Unraid)](#3-option-b--standalone-sqlite-lightweight--unraid)
4. [Option C — Unraid via Community Applications](#4-option-c--unraid-via-community-applications)
5. [Option D — Local Development (no Docker)](#5-option-d--local-development-no-docker)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [Reverse Proxy Configuration](#7-reverse-proxy-configuration)
   - [Nginx Proxy Manager](#71-nginx-proxy-manager-npm)
   - [Cloudflare Tunnel](#72-cloudflare-tunnel-cloudflared)
   - [Traefik v3](#73-traefik-v3)
8. [SMTP / E-mail Setup](#8-smtp--e-mail-setup)
9. [First Login & Admin Setup](#9-first-login--admin-setup)
10. [Updating](#10-updating)
11. [Backup & Restore](#11-backup--restore)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker | ≥ 24 | `docker --version` |
| Docker Compose | ≥ 2.24 (plugin) | `docker compose version` |
| Git | any | For cloning the repo |
| Open port | 8080 (default) | Configurable |

> **Unraid users** — Docker and Docker Compose are pre-installed. Skip to [Option C](#4-option-c--unraid-via-community-applications) or [Option B](#3-option-b--standalone-sqlite-lightweight--unraid).

---

## 2. Option A — Docker Compose with PostgreSQL (Recommended)

Best for production. Ships with a dedicated PostgreSQL 16 container.

### Step 1 — Clone the repository

```bash
git clone https://github.com/Qballjos/homey_known_issue_page.git
cd homey_known_issue_page
```

### Step 2 — Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` in your editor and set **at minimum** these values:

```env
# Your public-facing URL (important for email confirmation links!)
APP_URL=https://status.yourdomain.com

# Generate with: openssl rand -hex 32
SECRET_KEY=paste-your-64-char-random-string-here

# Admin credentials (auto-created on first boot)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=ChooseAStrongPassword!

# PostgreSQL password
POSTGRES_PASSWORD=ChooseAStrongDatabasePassword!
```

> ⚠️ **Never** commit a real `.env` file. It is already listed in `.gitignore`.

### Step 3 — Start the stack

```bash
docker compose up -d
```

Docker will:
1. Build the application image from the local `Dockerfile`
2. Start a PostgreSQL 16 container (`known-issues-db`)
3. Start the application container (`known-issues-app`) once the database is healthy
4. Automatically create all tables and the admin account on first boot

### Step 4 — Verify

```bash
# Check both containers are running
docker compose ps

# Tail the logs
docker compose logs -f app

# Health endpoint
curl http://localhost:8080/health
# Expected: {"status":"healthy","database":"ok"}
```

Open **http://localhost:8080** in your browser.

---

## 3. Option B — Standalone SQLite (Lightweight / Unraid)

No external database needed. All data is stored in a single file. Ideal for Unraid with a single container.

### Step 1 — Create the data directory

```bash
# On a regular server / NAS
mkdir -p /opt/known-issues/data

# On Unraid
mkdir -p /mnt/user/appdata/known-issues/data
```

### Step 2 — Generate a secret key

```bash
openssl rand -hex 32
# Copy the output — you'll need it below
```

### Step 3 — Run the container

```bash
docker run -d \
  --name known-issues \
  --restart unless-stopped \
  -p 8080:8000 \
  -v /mnt/user/appdata/known-issues/data:/app/data \
  -e DATABASE_URL=sqlite:///./data/known_issues.db \
  -e APP_URL=http://YOUR-SERVER-IP:8080 \
  -e SECRET_KEY=PASTE-YOUR-SECRET-KEY-HERE \
  -e ADMIN_EMAIL=admin@example.com \
  -e ADMIN_PASSWORD=ChangeThisPassword! \
  ghcr.io/qballjos/homey-known-issues:latest
```

Replace:
- `YOUR-SERVER-IP` with your server/Unraid IP (e.g. `192.168.1.50`)
- All credential placeholders with real values

### Step 4 — Verify

```bash
docker logs known-issues
curl http://YOUR-SERVER-IP:8080/health
```

---

## 4. Option C — Unraid via Community Applications

> **Requires:** Unraid 6.10+ with the Community Applications plugin installed.

### Step 1 — Search Community Applications

1. Go to **Apps** tab in the Unraid web UI.
2. Search for **Known Issues Status Page**.
3. Click **Install**.

### Step 2 — Configure the container

The template pre-fills safe defaults. Review and adjust:

| Field | Default | Required |
|---|---|---|
| **Web Port** | `8080` | Adjust if port is in use |
| **Appdata Storage** | `/mnt/user/appdata/known-issues/data` | Keep default or adjust path |
| **Public URL** | `http://[IP]:8080` | Set to your actual public URL if behind a reverse proxy |
| **Secret Key** | *(empty — auto-generated)* | Paste output of `openssl rand -hex 32` |
| **Admin Email** | `admin@example.com` | Your login email |
| **Admin Password** | `admin123!` | **Change this immediately!** |
| **Database URL** | `sqlite:///./data/known_issues.db` | Leave as-is for SQLite |

### Step 3 — Apply and Start

Click **Apply**. Unraid will pull the image and start the container.

### Step 4 — Access

- **Public page:** `http://UNRAID-IP:8080`
- **Admin dashboard:** `http://UNRAID-IP:8080/admin`

### Manual template install (without CA)

If the app is not yet in the CA store, you can load the template manually:

1. Copy [`unraid/known-issues.xml`](unraid/known-issues.xml) to `/boot/config/plugins/dockerMan/templates-user/` on your Unraid server.
2. Refresh the Docker tab → click **Add Container** → select **known-issues-platform** from the template dropdown.

---

## 5. Option D — Local Development (no Docker)

### Step 1 — Python virtual environment

```bash
git clone https://github.com/Qballjos/homey_known_issue_page.git
cd homey_known_issue_page

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Configuration

```bash
cp .env.example .env
# Edit .env — leave SMTP_HOST empty for local email capture
```

Minimal `.env` for local dev:

```env
APP_URL=http://localhost:8080
SECRET_KEY=dev-only-not-for-production-use
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123!
DATABASE_URL=sqlite:///./data/known_issues.db
AUTO_SEED=true
COOKIE_SECURE=false
```

### Step 3 — Run

```bash
# Option 1: via Makefile
make dev

# Option 2: directly
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Step 4 — Run tests

```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v tests/
```

---

## 6. Environment Variables Reference

All variables can be set in `.env` (Docker Compose) or as `-e` flags (standalone Docker run).

### Application

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Smart Home Known Issues` | Displayed in browser title and emails |
| `APP_URL` | `http://localhost:8080` | **Public** URL — used in confirmation and notification email links. Must be reachable by subscribers. |
| `SECRET_KEY` | *(required)* | 64+ character random string. Generate: `openssl rand -hex 32` |
| `SESSION_COOKIE_NAME` | `known_issues_session` | Name of the session cookie |
| `COOKIE_SECURE` | `true` | Set `true` in production (HTTPS). `false` for plain HTTP dev. |

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(set by compose)* | SQLite: `sqlite:///./data/known_issues.db` · PostgreSQL: `postgresql://user:pass@host:5432/db` |
| `POSTGRES_DB` | `known_issues_db` | PostgreSQL database name (Compose only) |
| `POSTGRES_USER` | `known_issues` | PostgreSQL username (Compose only) |
| `POSTGRES_PASSWORD` | *(required)* | PostgreSQL password (Compose only) |

### Admin Account

| Variable | Default | Description |
|---|---|---|
| `ADMIN_EMAIL` | `admin@example.com` | Email address for the initial admin account |
| `ADMIN_PASSWORD` | `admin123!` | Password for the initial admin account. **Change this!** |

### SMTP / Email

| Variable | Default | Description |
|---|---|---|
| `SMTP_HOST` | *(empty)* | SMTP server hostname. Leave empty to capture emails in memory (dev mode). |
| `SMTP_PORT` | `587` | SMTP port (587 = STARTTLS, 465 = SSL, 25 = plain) |
| `SMTP_USERNAME` | *(empty)* | SMTP login username |
| `SMTP_PASSWORD` | *(empty)* | SMTP login password |
| `SMTP_FROM` | `noreply@status.example.com` | From address in outgoing emails |
| `SMTP_TLS` | `true` | Enable STARTTLS |

### Seeding

| Variable | Default | Description |
|---|---|---|
| `AUTO_SEED` | `true` | Populate database with realistic sample issues on first boot. Set `false` in production. |

---

## 7. Reverse Proxy Configuration

The container listens internally on port `8000`. The application respects `X-Forwarded-For`, `X-Forwarded-Proto`, and `Host` headers automatically.

**After configuring a reverse proxy, update your `.env`:**
```env
APP_URL=https://status.yourdomain.com
COOKIE_SECURE=true
```
Then restart: `docker compose restart app` (or `docker restart known-issues`).

---

### 7.1 Nginx Proxy Manager (NPM)

1. In NPM, go to **Proxy Hosts** → **Add Proxy Host**.
2. Fill in:
   - **Domain Names:** `status.yourdomain.com`
   - **Scheme:** `http`
   - **Forward Hostname / IP:** your server IP (e.g. `192.168.1.50`)
   - **Forward Port:** `8080`
3. Enable toggles:
   - ✅ Block Common Exploits
   - ✅ Websockets Support
4. **SSL tab:**
   - Request a Let's Encrypt certificate.
   - ✅ Force SSL
   - ✅ HTTP/2 Support

---

### 7.2 Cloudflare Tunnel (cloudflared)

1. Open **Cloudflare Zero Trust** → **Networks** → **Tunnels**.
2. Select your tunnel → **Public Hostnames** → **Add a public hostname**.
3. Configure:
   - **Subdomain:** `status`
   - **Domain:** `yourdomain.com`
   - **Type:** `HTTP`
   - **URL:** `localhost:8080` (or `192.168.1.50:8080`)
4. Update `.env` on the server:
   ```env
   APP_URL=https://status.yourdomain.com
   COOKIE_SECURE=true
   ```

---

### 7.3 Traefik v3

Add labels to the `app` service in `docker-compose.yml`:

```yaml
services:
  app:
    # ... existing config ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.known-issues.rule=Host(`status.yourdomain.com`)"
      - "traefik.http.routers.known-issues.entrypoints=websecure"
      - "traefik.http.routers.known-issues.tls.certresolver=letsencrypt"
      - "traefik.http.services.known-issues.loadbalancer.server.port=8000"
    networks:
      - internal_network
      - traefik_proxy   # your existing Traefik network
```

Remove the `ports:` section from the `app` service — Traefik handles routing directly via the Docker network.

---

## 8. SMTP / E-mail Setup

The platform uses SMTP for:
- **Double opt-in confirmation** emails (subscribe flow)
- **Issue update notifications** to confirmed subscribers

### Production SMTP

Example providers and their settings:

| Provider | SMTP_HOST | SMTP_PORT | SMTP_TLS |
|---|---|---|---|
| Mailgun | `smtp.mailgun.org` | `587` | `true` |
| Postmark | `smtp.postmarkapp.com` | `587` | `true` |
| Gmail (App Password) | `smtp.gmail.com` | `587` | `true` |
| SendGrid | `smtp.sendgrid.net` | `587` | `true` |
| Self-hosted (Mailcow etc.) | your server | `587` | `true` |

### Local dev — No SMTP required

Leave `SMTP_HOST=` empty. The app captures all outgoing emails in memory and logs them to the container stdout. You can retrieve them via:

```bash
docker logs known-issues-app 2>&1 | grep "OUTBOX"
# or via the admin debug endpoint (dev mode only):
curl http://localhost:8080/api/admin/email-outbox \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 9. First Login & Admin Setup

1. Navigate to `http://YOUR-URL/admin`
2. Log in with the credentials from your `.env`:
   - **Email:** value of `ADMIN_EMAIL`
   - **Password:** value of `ADMIN_PASSWORD`
3. **Immediately after first login:**
   - Go to **Settings** and change your password to something unique.
   - Set `AUTO_SEED=false` in `.env` and restart if you don't want sample data.

### Admin capabilities

| Action | Location |
|---|---|
| Create / edit / publish issues | `/admin/issues` |
| Add timeline updates & trigger email notifications | Issue editor → Timeline tab |
| View subscriber counts per issue | Issue detail |
| Manage products & versions | `/admin/products` |
| Audit log | `/admin/audit` |
| API token (Bearer) | Shown on Dashboard |

---

## 10. Updating

### Docker Compose stack

```bash
cd homey_known_issue_page

# Pull latest code
git pull

# Rebuild and restart — zero-downtime rolling restart
docker compose build app
docker compose up -d app
```

### Standalone Docker run (pre-built image)

```bash
docker pull ghcr.io/qballjos/homey-known-issues:latest
docker stop known-issues
docker rm known-issues
# Re-run the docker run command from Step 3 of Option B
```

> Database schema migrations are applied automatically on startup. Your data is preserved as long as the data volume is intact.

---

## 11. Backup & Restore

### SQLite backup

```bash
# Backup
cp /mnt/user/appdata/known-issues/data/known_issues.db \
   /mnt/user/backups/known_issues_$(date +%Y%m%d).db

# Restore (stop the container first)
docker stop known-issues
cp /mnt/user/backups/known_issues_20261010.db \
   /mnt/user/appdata/known-issues/data/known_issues.db
docker start known-issues
```

### PostgreSQL backup (Docker Compose)

```bash
# Backup
docker exec known-issues-db pg_dump \
  -U known_issues known_issues_db \
  > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i known-issues-db psql \
  -U known_issues known_issues_db \
  < backup_20261010.sql
```

---

## 12. Troubleshooting

### Container exits immediately

```bash
docker logs known-issues-app
```

Common causes:
- `SECRET_KEY` is missing or too short (min 32 chars)
- `DATABASE_URL` is misconfigured
- PostgreSQL not yet ready (Compose waits for healthcheck automatically)

### Cannot reach admin — 403 / redirect loop

- Ensure `COOKIE_SECURE=false` when **not** behind HTTPS
- Clear browser cookies for the domain and try again

### Email confirmation links are broken

- `APP_URL` in `.env` must match the public URL your users can actually reach
- Do not include a trailing slash: ✅ `https://status.domain.com` ✗ `https://status.domain.com/`

### Health endpoint returns unhealthy

```bash
curl -v http://localhost:8080/health
docker exec known-issues-app python -c "from app.database import init_db; init_db(); print('DB OK')"
```

### Port 8080 already in use

Change the host port in `docker-compose.yml`:
```yaml
ports:
  - "8181:8000"   # use 8181 instead
```
Or in the standalone `docker run` command: `-p 8181:8000`.

### Logs

```bash
# Live logs
docker compose logs -f app

# Standalone
docker logs -f known-issues
```

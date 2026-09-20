# Smart Home Known Issues & Status Platform

[![Tests](https://img.shields.io/badge/tests-17%20passed-success)](https://github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Unraid Ready](https://img.shields.io/badge/Unraid-Compatible-E04E39)](INSTALL.md#4-option-c--unraid-via-community-applications)
[![Install Guide](https://img.shields.io/badge/Install%20Guide-📖-green)](INSTALL.md)

Een moderne, professionele, self-hosted webapplicatie voor het publiceren en beheren van officiële technische "Known Issues" en platformstatus voor smart-home ecosystemen.

Geïnspireerd op de minimalistische visuele stijl van **Homey** (royale witruimte, donkere typografie, frisse groene accentkleur, zachte afgeronde kaarten en subtiele schaduwen) zonder beschermde merknamen of logo's te gebruiken.

---

## 🌟 Belangrijkste Functies

- **Publieke Statuspagina**:
  - Directe systeem-status banner (*"Everything Operational"* of *"X Active Known Issues"*).
  - Volledige issue-kaarten met samenvatting, impact, getroffenen producten, firmwareversies, datums en workarounds.
  - Multi-facet zoeken en filteren op status (`Investigating`, `Identified`, `Fix in development`, `Monitoring`) en apparaten/producten.
  - Archiefpagina voor opgeloste problemen (`/resolved`) inclusief permanente fixes en firmwareversies.
- **Double Opt-In Notificaties**:
  - Bezoekers abonneren zich per issue met e-mailadres via cryptografisch veilige double opt-in verificatie.
  - Directe 1-klik uitschrijfkoppeling (`/unsubscribe/{token}`) in elke notificatiemail.
  - 100% AVG / GDPR-conform: geen tracking pixels, geen advertenties, geen marketing-nieuwsbrieven.
  - Privacy policy pagina (`/privacy`).
- **Impact Meting**:
  - Real-time teller van getroffen abonnees per issue (*"127 affected users subscribed"*).
  - Admin ziet uitsplitsing in actieve, pending en uitgeschreven gebruikers.
- **Uitgebreid Admin Dashboard (`/admin`)**:
  - Beveiligde sessie-authenticatie met `bcrypt` wachtwoord hashing.
  - Real-time overzicht: totalen per status, actieve issues, abonneestatistieken, recente updates.
  - Volledige issue-editor: aanmaken, bewerken, verwijderen, publiceren, verbergen.
  - Tijdlijnbeheer met checkbox `[✓] Send email notification to subscribers` (opt-out voor kleine typefouten).
  - Configureerbare drempelwaarde (publishing threshold) voor automatische promotie van interne issues.
  - Onwijzigbare audit trail (`/admin/audit`).
- **Volledige REST API**:
  - Swagger/OpenAPI documentatie via `/docs`.
  - Publieke endpoints voor issues en abonnementsbeheer.
  - Beveiligde administratieve endpoints met Bearer token authenticatie.
- **Self-Hosted & Unraid**:
  - Zelfstandig in Docker via `docker compose up -d`.
  - Persistent volume voor database en applicatiedata.
  - Healthcheck op `/health`.
  - Werkt naadloos achter reverse proxies (Traefik, Cloudflare Tunnel, Nginx Proxy Manager).

---

## 📁 Projectstructuur

```
homey_known_issue_page/
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Productie compose met PostgreSQL & Healthcheck
├── .env.example                # Documentatie van alle omgevingsvariabelen
├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, etc.)
├── README.md                   # Volledige documentatie & handleiding
├── app/
│   ├── main.py                 # FastAPI applicatie, lifespan, middlewares, healthcheck
│   ├── config.py               # Pydantic Settings configuratie
│   ├── database.py             # SQLAlchemy 2.0 engine, sessions & init_db
│   ├── seed.py                 # Automatische database seeding met realistische data
│   ├── models/                 # SQLAlchemy datamodellen
│   │   ├── user.py             # Admin gebruikers & wachtwoord hashes
│   │   ├── product.py          # Smart home apparaten & firmware versies
│   │   ├── issue.py            # Known issues (slug, status, workaround, etc.)
│   │   ├── timeline.py         # Chronologische tijdlijn updates
│   │   ├── subscription.py     # Double opt-in subscriptions & tokens
│   │   └── audit.py            # Audit logging van admin acties
│   ├── schemas/                # Pydantic validatiemodellen voor REST API
│   ├── auth/                   # Bcrypt hashing, signed session tokens & middleware
│   ├── email/                  # SMTP afhandeling, templates & dev outbox
│   ├── services/               # Zakelijke logica (issue service & subscription service)
│   ├── routes/                 # Routing
│   │   ├── public.py           # Publieke pagina's (/, /issues/{slug}, /resolved, etc.)
│   │   ├── admin.py            # Admin console & dashboard (/admin)
│   │   └── api.py              # REST API endpoints (/api/...)
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html           # Basislayout met Inter font & Tailwind CDN
│   │   ├── components/         # Herbruikbare componenten (header, card, banner, modal)
│   │   ├── public/             # Publieke pagina's
│   │   └── admin/              # Admin interface pagina's
│   └── static/                 # Statische assets (CSS met Homey stijlelementen)
└── tests/                      # Pytest test suite (17 geautomatiseerde tests)
```

---

## 🚀 Snelle Start (Docker Compose)

### 1. Repository klonen & configuratie aanmaken

```bash
git clone https://github.com/your-org/homey_known_issue_page.git
cd homey_known_issue_page

# Kopieer voorbeeldconfiguratie
cp .env.example .env
```

### 2. `.env` instellen

Bewerk `.env` met een veilige geheime sleutel en je gewenste domeinnaam:

```env
APP_NAME=Smart Home Known Issues
APP_URL=https://status.jouwdomein.nl
SECRET_KEY=genereer-hier-een-lange-willekeurige-reeks-tekens
ADMIN_EMAIL=admin@jouwdomein.nl
ADMIN_PASSWORD=KiesHierEenSterkWachtwoord!
POSTGRES_PASSWORD=GenereerEenSterkDatabaseWachtwoord
```

### 3. Starten met Docker Compose

```bash
docker compose up -d
```

De applicatie is direct bereikbaar op:
- **Publieke statuspagina:** [http://localhost:8080](http://localhost:8080)
- **Admin dashboard:** [http://localhost:8080/admin](http://localhost:8080/admin)
- **Interactieve API documentatie:** [http://localhost:8080/docs](http://localhost:8080/docs)
- **Healthcheck:** [http://localhost:8080/health](http://localhost:8080/health)

---

## 🔑 Standaard Admin Login

Bij de eerste keer starten controleert de applicatie automatisch of er al een administrator bestaat. Indien niet aanwezig, wordt direct het account uit je `.env` aangemaakt:

- **E-mail:** `admin@example.com` (of de waarde van `ADMIN_EMAIL`)
- **Wachtwoord:** `admin123!` (of de waarde van `ADMIN_PASSWORD`)

> **Belangrijk:** Wijzig na het eerste inloggen direct je wachtwoord of configureer van tevoren een eigen wachtwoord in `.env`.

---

## 🖥️ Unraid Installatie

Deze applicatie is ontworpen om soepel te draaien op Unraid via Docker Compose of als aangepaste Docker Container.

### Mapstructuur op Unraid (Appdata)

Maak de map aan op je Unraid array/cache:
```bash
mkdir -p /mnt/user/appdata/known-issues/data
```

### Unraid Configuratie Variabelen

| Instelling | Waarde / Voorbeeld | Beschrijving |
| :--- | :--- | :--- |
| **Container Port** | `8000` | Interne poort van de webapplicatie |
| **Host Port** | `8080` (of vrije poort naar keuze) | Poort op je Unraid server |
| **Volume Mappings** | `/mnt/user/appdata/known-issues/data` ➔ `/app/data` | Persistente applicatiedata |
| **DATABASE_URL** | `sqlite:///./data/known_issues.db` *(eenvoudig)* OF `postgresql://...` | Database verbinding |
| **APP_URL** | `https://status.jouwdomein.nl` | Publieke URL achter je reverse proxy |
| **SECRET_KEY** | `willekeurige-sleutel-64-tekens` | Sleutel voor cryptografische tokens |
| **ADMIN_EMAIL** | `admin@jouwdomein.nl` | E-mailadres voor initiële admin |
| **ADMIN_PASSWORD** | `JeWachtwoord` | Wachtwoord voor initiële admin |

> **Tip:** Voor een compacte standalone installatie op Unraid zonder aparte Postgres-container kun je `DATABASE_URL=sqlite:///./data/known_issues.db` gebruiken. SQLite draait volledig ingebakken en bewaart de database veilig in `/mnt/user/appdata/known-issues/data/known_issues.db`!

---

## 🛡️ Reverse Proxy Configuratie

De container gebruikt Uvicorn met `--proxy-headers` en `--forwarded-allow-ips *`. Hierdoor worden `X-Forwarded-For`, `X-Forwarded-Proto` en `Host` automatisch gerespecteerd.

### 1. Nginx Proxy Manager (NPM)
- **Domain Names:** `status.jouwdomein.nl`
- **Forward Hostname / IP:** IP-adres van je server (bijv. `192.168.1.50`)
- **Forward Port:** `8080`
- **Schakel in:** `Block Common Exploits`, `Websockets Support`
- **SSL Tab:** Schakel `Force SSL` en `HTTP/2 Support` in.

### 2. Cloudflare Tunnel (cloudflared)
Voeg een Public Hostname toe in het Cloudflare Zero Trust Dashboard:
- **Subdomain:** `status` | **Domain:** `jouwdomein.nl`
- **Type:** `HTTP`
- **URL:** `localhost:8080` (of interne container IP)
- Stel in `.env`: `APP_URL=https://status.jouwdomein.nl` en `COOKIE_SECURE=true`.

### 3. Traefik (Docker labels)
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.status.rule=Host(`status.jouwdomein.nl`)"
  - "traefik.http.routers.status.entrypoints=websecure"
  - "traefik.http.routers.status.tls.certresolver=letsencrypt"
  - "traefik.http.services.status.loadbalancer.server.port=8000"
```

---

## 📧 E-mailnotificaties & Double Opt-In

Het abonnementssysteem werkt volgens het **Double Opt-In** principe:
1. De bezoeker vult zijn e-mailadres in op de issue-kaart of detailpagina.
2. De backend maakt een subscription aan met de status `pending` en genereert een veilige unieke bevestigingstoken.
3. Er wordt een bevestigingsmail gestuurd naar de gebruiker met een verificatielink:
   `https://status.example.com/subscribe/confirm?token=...`
4. Na bevestiging wordt de status `confirmed`.
5. Zodra een beheerder in `/admin` een tijdlijn-update toevoegt met het vinkje `[✓] Send email notification to subscribers`, ontvangen alle actieve abonnees direct een nette, responsieve update-e-mail.
6. Elke e-mail bevat onderaan een directe 1-klik uitschrijflink:
   `https://status.example.com/unsubscribe/...`

### Lokale Ontwikkeling & Testen Zonder SMTP
Wanneer `SMTP_HOST` leeg blijft in `.env`, bewaart de applicatie alle verzonden e-mails in een intern geheugenlog (`outbox`). Hierdoor werkt de complete applicatie, inclusief double opt-in en notificaties, direct zonder dat je verplicht een SMTP-server hoeft in te stellen!

---

## 🔌 REST API Overzicht

| Methode | Endpoint | Beschrijving | Authenticatie |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/issues` | Lijst van publieke issues (filters: `q`, `status`, `product`) | Publiek |
| `GET` | `/api/issues/{id_or_slug}` | Details van een issue inclusief tijdlijn | Publiek |
| `POST` | `/api/issues` | Nieuw issue aanmaken | Admin (Bearer token) |
| `PUT` | `/api/issues/{id}` | Bestaand issue bijwerken | Admin (Bearer token) |
| `DELETE` | `/api/issues/{id}` | Issue verwijderen | Admin (Bearer token) |
| `POST` | `/api/issues/{id}/updates` | Tijdlijnupdate toevoegen & optioneel mailen | Admin (Bearer token) |
| `POST` | `/api/issues/{id}/subscribe` | Abonneren op issue (Double Opt-In trigger) | Publiek (Rate-limited) |
| `POST` | `/api/subscriptions/confirm` | Abonnement verifiëren via token | Publiek |
| `POST` | `/api/subscriptions/unsubscribe` | Uitschrijven via token | Publiek |
| `GET` | `/api/admin/stats` | Systeembrede statistieken en impact | Admin (Bearer token) |
| `GET` | `/health` | Container & database healthcheck | Publiek |

---

## 🧪 Tests Uitvoeren

De testsuite dekt alle vereisten af met 17 geautomatiseerde tests (admin login, sessies, issue lifecycle, double opt-in, uitschrijven, email triggers, rate limiting en REST API autorisatie):

```bash
# In virtuele omgeving
source .venv/bin/activate
PYTHONPATH=. pytest -v tests/
```

---

## 🔒 Beveiliging & Privacy (AVG)

- **Geen Tracking:** Geen Google Analytics, tracking pixels of advertentie-scripts.
- **Gegevensminimalisatie:** Alleen e-mailadres, status en tokens worden versleuteld opgeslagen.
- **Wachtwoorden:** Gehasht met `bcrypt` (12 rounds cost factor).
- **Rate Limiting:** Ingebouwd tegen brute-force op login (max 8 pogingen/min) en subscription flood (max 15/min).
- **Security Headers:** Standaard voorzien van `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, en `Referrer-Policy`.

---

## 📖 Documentatie

| Document | Beschrijving |
|---|---|
| [INSTALL.md](INSTALL.md) | Volledige installatie- en deploymenthandleiding (Docker, SQLite, Unraid, reverse proxy, SMTP, backup) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Richtlijnen voor bijdragen aan het project |
| [SECURITY.md](SECURITY.md) | Responsible disclosure & beveiligingsbeleid |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Gedragsregels voor de community |

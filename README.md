# Shortly — URL Shortener

**Production-grade URL shortening with custom aliases, link expiry, QR codes, REST API & click analytics**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/gagannchandra/shortly-url-shortener/ci.yml?style=flat-square&label=CI)](https://github.com/gagannchandra/shortly-url-shortener/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

[**Live Demo**](https://your-demo-link.com) · [**API Docs**](#api-documentation) · [**Report Bug**](https://github.com/gagannchandra/shortly-url-shortener/issues)

---

## Overview

**Shortly** is a full-stack URL shortening service that converts long URLs into clean, shareable links — with optional custom aliases, configurable link expiry, per-link click analytics, and inline QR code generation. Built on a layered Flask backend (factory pattern, service layer, Blueprint routing), MongoDB for persistence, and a zero-framework JavaScript frontend.

> Demonstrates production-grade web service design: RESTful API architecture, MongoDB with TTL indexes for auto-expiry, rate limiting, security headers via CSP, Docker + Compose deployment, and a GitHub Actions CI pipeline — all without a frontend framework.

---

## What's New in v2.0.0

| Area | v1.1.0 | v2.0.0 |
|---|---|---|
| **Database** | SQLite + SQLAlchemy ORM | MongoDB 7.0 + PyMongo |
| **Architecture** | Flat module layout | App factory · Blueprint routing · Service layer |
| **Link Expiry** | Not supported | TTL per link (1–365 days), auto-deleted by MongoDB TTL index |
| **QR Codes** | Not supported | Inline base64 PNG, generated on-demand via `segno` |
| **Rate Limiting** | Not supported | Flask-Limiter (200/day · 50/hr global; 10/min on `/api/shorten`) |
| **Security Headers** | Not supported | Flask-Talisman: CSP, HSTS, clickjacking prevention |
| **Health Check** | Not supported | `GET /api/health` (HEAD supported for uptime monitors) |
| **Analytics API** | HTML page only | JSON endpoint + 14-day chart data |
| **Error Handling** | 404 / 500 pages | 404 / 429 / 500 — JSON for API, HTML for browser |
| **Docker** | Not included | Multi-stage Dockerfile + `docker-compose.yml` |
| **CI** | Not included | GitHub Actions — lint, pytest, Docker image build |
| **Tests** | Not included | pytest suite with `mongomock` |
| **Logging** | Not included | Dev-friendly console · Structured JSON in production |

---

## Features

| Feature | Details |
|---|---|
| 🔗 **URL Shortening** | Cryptographically secure random 6-char codes (base62, ~56B combinations) |
| ✏️ **Custom Aliases** | Alphanumeric + hyphen/underscore, 4–30 chars, reserved-word protection |
| ⏳ **Link Expiry** | Optional `ttl_days` (1–365); MongoDB TTL index deletes docs automatically |
| 📊 **Click Analytics** | Total clicks · last-clicked timestamp · 14-day daily chart |
| 📱 **QR Code** | Inline base64 PNG returned with every shortened link, also on analytics page |
| 🔌 **REST API** | Clean JSON endpoints with consistent `{data, status}` / `{error, status}` shape |
| 🏥 **Health Check** | `GET /api/health` pings MongoDB and reports service status |
| ⚡ **No-Reload UI** | Vanilla JS + Fetch API — no frontend framework overhead |
| 🛡️ **Rate Limiting** | Per-IP limits via Flask-Limiter; `X-RateLimit-*` headers returned to clients |
| 🔒 **Security Headers** | CSP, `frame-ancestors: none`, `referrer-policy`, HTTPS enforcement via Talisman |
| 🐳 **Docker** | Multi-stage image (builder + non-root runtime) + Compose with MongoDB & Mongo Express |
| 🔁 **CI/CD** | GitHub Actions: test on every push, build Docker image on `main` |

---

## Tech Stack

```
Backend      → Python 3.12, Flask 3, PyMongo 4, Flask-Limiter, Flask-Talisman
Database     → MongoDB 7.0 (TTL index for link expiry, unique index on short_code)
QR Codes     → segno
Frontend     → HTML5, CSS3, Vanilla JavaScript (Fetch API)
Config       → python-dotenv, env-based config classes (Dev / Test / Prod)
Deploy       → Gunicorn + Railway / Render (Procfile) · Docker + Compose
CI           → GitHub Actions (pytest + mongomock + Docker build)
Testing      → pytest, pytest-flask, mongomock
```

---

## Project Structure

```
shortly/
├── run.py                      # App entry point
├── Procfile                    # Gunicorn for Railway / Render
├── Dockerfile                  # Multi-stage build (builder + non-root runtime)
├── docker-compose.yml          # App + MongoDB + Mongo Express (dev profile)
├── mongo-init.js               # MongoDB init script (collections + indexes)
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/ci.yml        # Lint → test → Docker build
├── app/
│   ├── __init__.py             # App factory — wires Flask, Limiter, Talisman, Blueprints
│   ├── config.py               # DevelopmentConfig / TestingConfig / ProductionConfig
│   ├── db.py                   # MongoDB client, connection pool, index creation
│   ├── models.py               # Data access layer (CRUD + click recording)
│   ├── routes/
│   │   ├── api.py              # Blueprint: /api/shorten, /api/analytics, /api/health
│   │   └── views.py            # Blueprint: /, /about, /analytics/<code>, /<code>
│   ├── services/
│   │   └── url_service.py      # Business logic: shorten, redirect, analytics, QR
│   ├── utils/
│   │   └── validators.py       # URL normalisation + alias + TTL validation
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── main.js         # Shortener form logic
│   │       └── analytics.js    # Chart rendering
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── analytics.html
│       ├── about.html
│       ├── 404.html
│       ├── 429.html            # Rate limit exceeded page
│       └── 500.html
└── tests/
    ├── conftest.py
    └── test_api.py
```

---

## Getting Started

### Prerequisites
- Python 3.12+
- MongoDB 6+ running locally **or** a free [MongoDB Atlas](https://mongodb.com/atlas) cluster
- Git

### 1. Clone the repository
```bash
git clone https://github.com/gagannchandra/shortly-url-shortener.git
cd shortly-url-shortener
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env`:
```env
FLASK_ENV=development

# Generate with: python -c "import secrets; print(secrets.token_hex(24))"
SECRET_KEY=your-secret-key-here

# Local MongoDB
MONGO_URI=mongodb://localhost:27017/shortly
MONGO_DB_NAME=shortly

# Optional — defaults to in-memory if omitted (single instance dev only)
# REDIS_URL=redis://localhost:6379

SHORT_CODE_LENGTH=6
FORCE_HTTPS=false
LOG_LEVEL=INFO
```

### 5. Run the app
```bash
python run.py
```

MongoDB indexes are created automatically on first startup. Visit **http://127.0.0.1:5000** 🚀

---

## Docker (Recommended)

Spin up the full stack — app + MongoDB + Mongo Express UI — with a single command:

```bash
# Copy and fill in .env
cp .env.example .env

# Start app + MongoDB (production-like)
docker compose up -d

# Also start Mongo Express UI at http://localhost:8081
docker compose --profile dev up -d
```

The app is available at **http://localhost:8000**.

To build and run just the app image:
```bash
docker build -t shortly .
docker run -p 8000:8000 --env-file .env shortly
```

---

## API Documentation

All API responses share a consistent envelope:

```json
// Success
{ "data": { ... }, "status": 201 }

// Error
{ "error": "Reason here.", "status": 400 }
```

---

### `POST /api/shorten`

Shorten a URL programmatically.

**Request body**
```json
{
  "long_url": "https://example.com/very/long/path",
  "custom_alias": "mybrand",
  "ttl_days": 30
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `long_url` | string | ✅ | Auto-prepends `https://` if scheme is missing |
| `custom_alias` | string | ❌ | Letters, numbers, hyphens, underscores; 4–30 chars |
| `ttl_days` | integer | ❌ | 1–365; omit for a permanent link |

**Success — `201 Created`**
```json
{
  "data": {
    "short_url": "https://your-domain.com/mybrand",
    "short_code": "mybrand",
    "analytics_url": "https://your-domain.com/analytics/mybrand",
    "qr_code": "data:image/png;base64,iVBORw0KGgo...",
    "created_at": "2025-06-01T10:00:00+00:00",
    "expires_at": "2025-07-01T10:00:00+00:00"
  },
  "status": 201
}
```

> `expires_at` is `null` for permanent links.

**Error responses**

| Code | Reason |
|---|---|
| `400 Bad Request` | Missing/malformed URL, invalid alias format, invalid `ttl_days` |
| `409 Conflict` | The requested `custom_alias` is already taken |
| `429 Too Many Requests` | Rate limit exceeded (10 req/min per IP on this endpoint) |

---

### `GET /api/analytics/<short_code>`

Returns analytics data for a given short code as JSON. Used by the analytics page to render the chart.

**Success — `200 OK`**
```json
{
  "data": {
    "short_code": "mybrand",
    "long_url": "https://example.com/very/long/path",
    "clicks": 42,
    "created_at": "2025-06-01T10:00:00+00:00",
    "expires_at": null,
    "last_clicked_at": "2025-06-05T14:32:00+00:00",
    "chart_data": [
      { "date": "2025-05-23", "clicks": 3 },
      { "date": "2025-05-24", "clicks": 0 },
      ...
    ]
  },
  "status": 200
}
```

`chart_data` always contains the last 14 days (days with no clicks are included as `0`).

**Error**

| Code | Reason |
|---|---|
| `404 Not Found` | Short code doesn't exist or has expired |

---

### `GET /api/health`

Health check — verifies MongoDB connectivity. Also accepts `HEAD` (for UptimeRobot / uptime monitors).

**`200 OK`** — database is reachable
```json
{ "status": "ok", "database": "ok", "service": "shortly" }
```

**`503 Service Unavailable`** — database is unreachable
```json
{ "status": "degraded", "database": "error", "service": "shortly" }
```

---

## Deployment

### Railway / Render

The `Procfile` is included for one-command deployment:

```
web: gunicorn --workers 2 --bind 0.0.0.0:$PORT --timeout 30 --access-logfile - --log-level info run:app
```

Set these environment variables in your host dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Long random string |
| `MONGO_URI` | MongoDB Atlas connection string |
| `MONGO_DB_NAME` | `shortly` |
| `FLASK_ENV` | `production` |
| `FORCE_HTTPS` | `true` |

No other changes needed — indexes are created automatically on first boot.

### Redis (optional, recommended for production)

By default, rate limiting uses in-memory storage, which doesn't persist across restarts or scale across multiple workers. For production, point `REDIS_URL` at a Redis instance:

```env
REDIS_URL=redis://your-redis-host:6379
```

---

## Running Tests

```bash
# Run the full test suite (uses mongomock — no real MongoDB needed)
pytest tests/ -v

# With coverage
pytest tests/ -v --tb=short
```

Tests use `mongomock` to mock MongoDB in memory, so no external database is required to run them.

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

Built by [Gagan Chandra](https://github.com/gagannchandra) · B.Tech CSE (AI) · PSIT Kanpur

</div>

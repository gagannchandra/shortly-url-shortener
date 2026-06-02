# Shortly — URL Shortener

**Production-grade URL shortening with custom aliases, link expiry, QR codes, REST API & click analytics**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/gagannchandra/shortly-url-shortener/ci.yml?style=flat-square&label=CI)](https://github.com/gagannchandra/shortly-url-shortener/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

[**Live Demo**](https://shortly.gaganchandra.in/) · [**API Docs**](#api-documentation) · [**Report Bug**](https://github.com/gagannchandra/shortly-url-shortener/issues)

---

## Overview

**Shortly** is a full-stack URL shortening service — paste a long URL, get a short one. Supports custom aliases, optional link expiry, per-link click analytics, and inline QR code generation.

I built v1 as a weekend project with Flask + SQLite to learn the basics. v2 is the proper rebuild: MongoDB (with TTL indexes that auto-expire links — genuinely one of the cooler things I learned during this), a proper app factory with Blueprint routing and a service layer, rate limiting, security headers, Docker, and a CI pipeline. Same idea, done right.

---

## What's New in v2.0.0

v2 is a ground-up rewrite. Here's what changed:

| Area | v1.1.0 | v2.0.0 |
|---|---|---|
| **Database** | SQLite + SQLAlchemy ORM | MongoDB 7.0 + PyMongo |
| **Architecture** | Flat module layout | App factory · Blueprint routing · Service layer |
| **Link Expiry** | ✗ | TTL per link (1–365 days), auto-deleted by MongoDB TTL index |
| **QR Codes** | ✗ | Inline base64 PNG, generated on-demand via `segno` |
| **Rate Limiting** | ✗ | Flask-Limiter (200/day · 50/hr global; 10/min on `/api/shorten`) |
| **Security Headers** | ✗ | Flask-Talisman: CSP, HSTS, clickjacking prevention |
| **Health Check** | ✗ | `GET /api/health` (HEAD supported for uptime monitors) |
| **Analytics API** | HTML page only | JSON endpoint + 14-day chart data |
| **Error Handling** | 404 / 500 pages | 404 / 429 / 500 — JSON for API, HTML for browser |
| **Docker** | ✗ | Multi-stage Dockerfile + `docker-compose.yml` |
| **CI** | ✗ | GitHub Actions — pytest, Docker build on `main` |
| **Tests** | ✗ | pytest suite with `mongomock` (no real DB needed) |
| **Logging** | ✗ | Readable console in dev · Structured JSON in production |

---

## Features

| Feature | Details |
|---|---|
| 🔗 **URL Shortening** | Cryptographically secure random 6-char codes (base62, ~56B combinations) |
| ✏️ **Custom Aliases** | Alphanumeric + hyphen/underscore, 4–30 chars, reserved-word protection |
| ⏳ **Link Expiry** | Optional `ttl_days` (1–365); MongoDB TTL index handles cleanup automatically |
| 📊 **Click Analytics** | Total clicks · last-clicked timestamp · 14-day daily chart |
| 📱 **QR Code** | Returned inline with every new link, and on the analytics page |
| 🔌 **REST API** | Consistent `{data, status}` / `{error, status}` envelope on all endpoints |
| 🏥 **Health Check** | `GET /api/health` pings MongoDB and reports service status |
| ⚡ **No-Reload UI** | Vanilla JS + Fetch API — no framework, no build step |
| 🛡️ **Rate Limiting** | Per-IP limits; `X-RateLimit-*` headers so clients know where they stand |
| 🔒 **Security Headers** | CSP, `frame-ancestors: none`, referrer policy, HTTPS enforcement |
| 🐳 **Docker** | Multi-stage image (non-root runtime) + Compose with MongoDB & Mongo Express |
| 🔁 **CI/CD** | GitHub Actions: test on every push, build Docker image on `main` |

---

## Tech Stack

```
Backend      → Python 3.12, Flask 3, PyMongo 4, Flask-Limiter, Flask-Talisman
Database     → MongoDB 7.0  (TTL index for expiry, unique index on short_code)
QR Codes     → segno
Frontend     → HTML5, CSS3, Vanilla JavaScript (Fetch API)
Config       → python-dotenv, env-based config classes (Dev / Test / Prod)
Deploy       → Gunicorn + Railway / Render (Procfile)  ·  Docker + Compose
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
├── mongo-init.js               # DB init script — collections + indexes
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/ci.yml        # Test → Docker build pipeline
├── app/
│   ├── __init__.py             # App factory — wires Flask, Limiter, Talisman, Blueprints
│   ├── config.py               # DevelopmentConfig / TestingConfig / ProductionConfig
│   ├── db.py                   # MongoDB client, connection pool, index creation
│   ├── models.py               # Data access layer (CRUD + atomic click recording)
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
│   │       ├── main.js         # Shortener form
│   │       └── analytics.js    # Chart rendering
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── analytics.html
│       ├── about.html
│       ├── 404.html
│       ├── 429.html
│       └── 500.html
└── tests/
    ├── conftest.py
    └── test_api.py
```

---

## Getting Started

### Prerequisites
- Python 3.12+
- MongoDB 6+ locally **or** a free [MongoDB Atlas](https://mongodb.com/atlas) cluster
- Git

If you just want to run the whole stack without installing MongoDB separately, skip to the [Docker section](#docker-recommended) — it's easier.

### 1. Clone the repo
```bash
git clone https://github.com/gagannchandra/shortly-url-shortener.git
cd shortly-url-shortener
```

### 2. Create a virtual environment
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

# Generate a key: python -c "import secrets; print(secrets.token_hex(24))"
SECRET_KEY=your-secret-key-here

# Local MongoDB
MONGO_URI=mongodb://localhost:27017/shortly
MONGO_DB_NAME=shortly

# Optional — rate limiting defaults to in-memory if this is omitted.
# Fine for a single instance; use Redis if you're running multiple workers.
# REDIS_URL=redis://localhost:6379

SHORT_CODE_LENGTH=6
FORCE_HTTPS=false
LOG_LEVEL=INFO
```

### 5. Run
```bash
python run.py
```

Indexes are created automatically on first boot. Visit **http://127.0.0.1:5000** 🚀

---

## Docker (Recommended)

The easiest way to run everything locally. One command gets you the app, MongoDB, and optionally a Mongo Express UI to poke around the database.

```bash
cp .env.example .env          # fill in SECRET_KEY at minimum

# App + MongoDB
docker compose up -d

# App + MongoDB + Mongo Express at http://localhost:8081
docker compose --profile dev up -d
```

App runs at **http://localhost:8000**.

To build and run just the app image on its own:
```bash
docker build -t shortly .
docker run -p 8000:8000 --env-file .env shortly
```

---

## API Documentation

Every response uses a consistent envelope so you always know what to expect:

```json
// Success
{ "data": { ... }, "status": 201 }

// Error
{ "error": "Reason here.", "status": 400 }
```

---

### `POST /api/shorten`

Shorten a URL. The only required field is `long_url`.

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
| `long_url` | string | ✅ | Missing `https://`? It gets added automatically. |
| `custom_alias` | string | ❌ | Letters, numbers, hyphens, underscores; 4–30 chars |
| `ttl_days` | integer | ❌ | 1–365; leave it out for a permanent link |

**`201 Created`**
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

`expires_at` is `null` for permanent links. `qr_code` is a ready-to-use base64 data URI.

**Errors**

| Code | Reason |
|---|---|
| `400` | Missing/malformed URL, invalid alias, bad `ttl_days` |
| `409` | That custom alias is already taken |
| `429` | Rate limit hit (10 req/min per IP on this endpoint) |

---

### `GET /api/analytics/<short_code>`

Fetch analytics for a short code. This is what the analytics page calls to render the chart.

**`200 OK`**
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
      { "date": "2025-05-24", "clicks": 0 }
    ]
  },
  "status": 200
}
```

`chart_data` always has 14 entries (one per day). Days with zero clicks are included as `0` so the chart never has gaps.

| Code | Reason |
|---|---|
| `404` | Short code doesn't exist or has already expired |

---

### `GET /api/health`

Checks if the app can reach MongoDB. Also responds to `HEAD` for uptime monitors like UptimeRobot.

**`200 OK`**
```json
{ "status": "ok", "database": "ok", "service": "shortly" }
```

**`503 Service Unavailable`**
```json
{ "status": "degraded", "database": "error", "service": "shortly" }
```

---

## Deployment

### Railway / Render

The `Procfile` is ready to go:

```
web: gunicorn --workers 2 --bind 0.0.0.0:$PORT --timeout 30 --access-logfile - --log-level info run:app
```

Set these in your host's environment dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A long random string |
| `MONGO_URI` | MongoDB Atlas connection string |
| `MONGO_DB_NAME` | `shortly` |
| `FLASK_ENV` | `production` |
| `FORCE_HTTPS` | `true` |

That's it — indexes are created on first boot, nothing else to configure.

### A note on rate limiting + Redis

By default, rate limiting state lives in memory, which means it resets on restart and doesn't work correctly across multiple workers. If you're deploying with more than one Gunicorn worker (or just want limits to survive restarts), add a Redis URL:

```env
REDIS_URL=redis://your-redis-host:6379
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use `mongomock` to fake MongoDB in memory, so you don't need a running database to run them. The CI pipeline runs the same suite against a real MongoDB 7.0 container on every push.

---

## License

MIT. See [`LICENSE`](LICENSE).

---

<div align="center">

Built by [Gagan Chandra](https://github.com/gagannchandra) · B.Tech CSE (AI) · PSIT Kanpur

</div>

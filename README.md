# Shortly

> A fast, production-grade URL shortener with analytics, QR codes, and link expiry.

[![CI](https://github.com/gagannchandra/shortly-url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/gagannchandra/shortly-url-shortener/actions)
![Version](https://img.shields.io/badge/version-2.0-blueviolet)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

| Feature | Details |
|---|---|
| **URL Shortening** | Auto-generated 6-char codes, cryptographically secure |
| **Custom Aliases** | Letters, numbers, hyphens, underscores (4–30 chars) |
| **Link Expiry** | Optional TTL (1 day – 1 year), auto-deleted via MongoDB TTL index |
| **QR Code** | Inline PNG QR code, downloadable |
| **Analytics** | Total clicks, 14-day chart, last-click timestamp |
| **Rate Limiting** | Per-IP limiting on shorten endpoint (10 req/min) |
| **Security Headers** | Flask-Talisman CSP, HSTS, referrer policy |
| **Health Check** | `GET /api/health` for uptime monitoring |

---

## Tech Stack

- **Backend:** Python 3.12, Flask 3.1, Gunicorn
- **Database:** MongoDB 7 (PyMongo), TTL index for auto-expiry
- **Frontend:** Vanilla JS (zero dependencies), Canvas charts
- **Security:** Flask-Talisman, Flask-Limiter, CSP headers
- **Deployment:** Docker, Gunicorn, Render / Railway / VPS ready
- **Testing:** Pytest, mongomock (22 tests)

---

## Quick Start

### Prerequisites

- Python 3.12+
- MongoDB (local or [Atlas](https://cloud.mongodb.com))

### Setup

```bash
# Clone and enter
git clone https://github.com/gagannchandra/shortly-url-shortener.git
cd shortly-url-shortener

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → set SECRET_KEY and MONGO_URI

# Run
python run.py
```

App available at `http://localhost:5000`

---

### Docker Compose (Recommended)

Spins up the app + MongoDB together:

```bash
cp .env.example .env
# Edit .env → set SECRET_KEY

docker compose up --build
```

```bash
# With Mongo Express UI (for dev):
docker compose --profile dev up
```

| Service | URL |
|---|---|
| Shortly app | `http://localhost:8000` |
| Mongo Express | `http://localhost:8081` |

---

## Deployment Guide

### Option 1 — Render.com (Recommended for free tier)

**Step 1: Set up MongoDB Atlas**

1. Create a free cluster at [atlas.mongodb.com](https://cloud.mongodb.com)
2. Create a database user with read/write privileges
3. Under **Network Access**, add `0.0.0.0/0` to allow all IPs (required for Render)
4. Copy your connection string:
   ```
   mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   ```

**Step 2: Deploy on Render**

1. Fork this repo to your GitHub account
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your forked repo
4. Configure the service:

   | Setting | Value |
   |---|---|
   | **Runtime** | Python 3 |
   | **Build command** | `pip install -r requirements.txt` |
   | **Start command** | `gunicorn --workers 2 --bind 0.0.0.0:$PORT --timeout 30 --access-logfile - --log-level info run:app` |

5. Add these **Environment Variables**:

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | A long random string (use `python -c "import secrets; print(secrets.token_hex(32))"`) |
   | `MONGO_URI` | Your MongoDB Atlas connection string |
   | `MONGO_DB_NAME` | `shortly` |
   | `FLASK_ENV` | `production` |
   | `FORCE_HTTPS` | `true` |
   | `LOG_LEVEL` | `INFO` |

6. Click **Deploy**

> **Note:** The free tier on Render spins down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.

---

### Option 2 — Railway

1. Fork this repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your forked repo
4. Add a **MongoDB** plugin from the Railway dashboard
5. Set environment variables (same as Render above, but use Railway's MongoDB URI)
6. Railway auto-detects the `Procfile` and deploys

```
# Railway provides these automatically when you add MongoDB plugin:
# MONGO_URI is auto-injected
```

---

### Option 3 — VPS / Docker (DigitalOcean, AWS EC2, etc.)

**Step 1: SSH into your server and clone**

```bash
git clone https://github.com/gagannchandra/shortly-url-shortener.git
cd shortly-url-shortener
```

**Step 2: Configure environment**

```bash
cp .env.example .env
nano .env
```

Set these values in `.env`:
```env
FLASK_ENV=production
SECRET_KEY=<generate-a-64-char-hex-string>
MONGO_URI=mongodb://admin:your-secure-password@mongo:27017/shortly?authSource=admin
MONGO_DB_NAME=shortly
MONGO_ROOT_USER=admin
MONGO_ROOT_PASS=your-secure-password
FORCE_HTTPS=true
LOG_LEVEL=INFO
```

**Step 3: Deploy with Docker Compose**

```bash
docker compose up -d --build
```

**Step 4: Set up a reverse proxy (Nginx)**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Step 5: Add SSL with Certbot**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

### Option 4 — Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Deploy:

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set MONGO_URI="your-atlas-connection-string"
heroku config:set MONGO_DB_NAME=shortly
heroku config:set FLASK_ENV=production
heroku config:set FORCE_HTTPS=true

git push heroku main
```

> Heroku auto-detects the `Procfile` for the start command.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Flask secret key for session security |
| `MONGO_URI` | ✅ | `mongodb://localhost:27017/shortly` | MongoDB connection string |
| `MONGO_DB_NAME` | ✅ | `shortly` | Database name |
| `FLASK_ENV` | ❌ | `development` | `development` or `production` |
| `FORCE_HTTPS` | ❌ | `false` | Set `true` when behind HTTPS proxy |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SHORT_CODE_LENGTH` | ❌ | `6` | Length of generated short codes |
| `MONGO_ROOT_USER` | ❌ | `admin` | Docker Compose MongoDB root user |
| `MONGO_ROOT_PASS` | ❌ | `password` | Docker Compose MongoDB root password |
| `REDIS_URL` | ❌ | — | Redis URL for distributed rate limiting |

---

## API Reference

All API responses follow this shape:

```json
{ "data": { ... }, "status": 200 }
// or
{ "error": "message", "status": 400 }
```

### `POST /api/shorten`

Create a short URL.

**Request body:**
```json
{
  "long_url":     "https://example.com/very/long/path",
  "custom_alias": "mybrand",
  "ttl_days":     7
}
```
Only `long_url` is required.

**Response `201`:**
```json
{
  "data": {
    "short_url":     "https://sho.rt/mybrand",
    "short_code":    "mybrand",
    "analytics_url": "https://sho.rt/analytics/mybrand",
    "qr_code":       "data:image/png;base64,...",
    "created_at":    "2024-01-15T10:30:00+00:00",
    "expires_at":    "2024-01-22T10:30:00+00:00"
  },
  "status": 201
}
```

| Status | Meaning |
|---|---|
| `201` | Short URL created successfully |
| `400` | Invalid URL, alias, or TTL |
| `409` | Custom alias already taken |
| `429` | Rate limit exceeded |

### `GET /<short_code>`

Redirects to the original URL (HTTP 302).

### `GET /api/analytics/<short_code>`

Returns analytics data including 14-day click chart.

### `GET /api/health`

Returns service and database health status.

---

## Project Structure

```
shortly/
├── app/
│   ├── __init__.py          # App factory, extensions wiring
│   ├── config.py            # Config classes (dev / test / prod)
│   ├── db.py                # MongoDB connection + index management
│   ├── models.py            # Data access layer (CRUD)
│   ├── routes/
│   │   ├── api.py           # REST API endpoints
│   │   └── views.py         # Page routes + redirect
│   ├── services/
│   │   └── url_service.py   # Business logic (shorten, QR, analytics)
│   ├── utils/
│   │   └── validators.py    # Input validation
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/{main,analytics}.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── analytics.html
│       ├── about.html
│       └── {404,429,500}.html
├── tests/
│   ├── conftest.py          # Fixtures (mongomock)
│   └── test_api.py          # 22 API tests
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # App + MongoDB + Mongo Express
├── Procfile                 # Heroku/Railway start command
├── .github/workflows/ci.yml # CI pipeline
├── requirements.txt
├── run.py                   # Entry point
└── .env.example             # Environment template
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short
```

22 tests covering: shorten, redirect, analytics, validation, error paths.

---

## Changelog

### v2.0 (Latest)
- Redesigned UI with modern dark theme and glassmorphism
- Floating icon background animation
- Toggle switches for custom alias and expiry options
- QR code generation with inline preview
- Analytics dashboard with 14-day click chart
- Rate limiting on shorten endpoint
- Flask-Talisman security headers (CSP, HSTS)
- Multi-stage Docker build with non-root user
- Docker Compose with MongoDB + Mongo Express
- 22 automated API tests with mongomock
- Comprehensive deployment guide

### v1.0
- Basic URL shortening with auto-generated codes
- Custom alias support
- Simple analytics page
- MongoDB backend

---

## License

MIT

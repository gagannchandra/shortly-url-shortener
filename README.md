# Shortly

> A fast, production-grade URL shortener with analytics, QR codes, and link expiry.

[![CI](https://github.com/your-username/shortly/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/shortly/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green)

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

- **Backend:** Python 3.12, Flask 3.1
- **Database:** MongoDB 7 (PyMongo), TTL index for auto-expiry
- **Frontend:** Vanilla JS (zero dependencies), Canvas charts
- **Deployment:** Docker, Gunicorn, Render / Railway ready

---

## Local Development

### Prerequisites

- Python 3.12+
- MongoDB (local or Atlas)

### Setup

```bash
# Clone and enter
git clone https://github.com/your-username/shortly.git
cd shortly

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY and MONGO_URI

# Run
python run.py
```

App available at `http://localhost:5000`

---

### Docker Compose (Recommended)

Spins up the app + MongoDB together:

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY

docker compose up --build

# With Mongo Express UI:
docker compose --profile dev up
```

- App: `http://localhost:8000`
- Mongo Express: `http://localhost:8081`

---

## API Reference

All API responses have the shape:

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

### `GET /<short_code>`

Redirects to the original URL (HTTP 301).

### `GET /api/analytics/<short_code>`

Returns analytics data including 14-day click chart.

### `GET /api/health`

Returns service health status.

---

## Deployment: Render.com

1. Fork this repo
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your repo
4. Set environment variables:
   - `SECRET_KEY` → a long random string
   - `MONGO_URI` → your MongoDB Atlas connection string
   - `MONGO_DB_NAME` → `shortly`
   - `FLASK_ENV` → `production`
   - `FORCE_HTTPS` → `true`
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn --workers 2 --bind 0.0.0.0:$PORT run:app`

### MongoDB Atlas Setup

1. Create a free cluster at [atlas.mongodb.com](https://cloud.mongodb.com)
2. Create a database user
3. Whitelist `0.0.0.0/0` in Network Access (or Render's IP ranges)
4. Get your connection string and set it as `MONGO_URI`

---

## Project Structure

```
shortly/
├── app/
│   ├── __init__.py        # App factory, extensions wiring
│   ├── config.py          # Config classes (dev / test / prod)
│   ├── db.py              # MongoDB connection + index management
│   ├── models.py          # Data access layer (CRUD)
│   ├── routes/
│   │   ├── api.py         # REST API endpoints
│   │   └── views.py       # Page routes + redirect
│   ├── services/
│   │   └── url_service.py # Business logic (shorten, QR, analytics)
│   ├── utils/
│   │   └── validators.py  # Input validation
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/{main,analytics}.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── analytics.html
│       └── {404,429,500}.html
├── tests/
│   ├── conftest.py        # Fixtures (mongomock)
│   └── test_api.py        # 22 API tests
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
├── requirements.txt
├── run.py
└── .env.example
```

---

## Running Tests

```bash
pytest tests/ -v
```

22 tests covering: shorten, redirect, analytics, validation, error paths.

---

## License

MIT

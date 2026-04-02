# Shortly — URL Shortener

A fast, minimal URL shortener built with Flask and vanilla JavaScript. Supports custom aliases, click analytics, and instant redirects.

**Live Demo → [Link](https://gagannchandra.pythonanywhere.com/)**

---

## Features

- Shorten any URL instantly
- Custom alias support (e.g. `/my-brand`)
- Click analytics per short link
- Duplicate alias detection with inline error feedback
- Fully responsive, dark-mode UI
- No frameworks — pure vanilla JS frontend

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, SQLAlchemy |
| Database | SQLite |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Deployment | Railway |

## Getting Started

**Prerequisites:** Python 3.8+

```bash
# Clone the repo
git clone https://github.com/yourusername/shortly-url-shortener.git
cd shortly-url-shortener

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=your-secret-key-here" > .env

# Run the app
python app.py
```

App runs at `http://localhost:5000`

## Project Structure

```
shortly-url-shortener/
├── app.py              # Flask app, routes, DB models
├── utils.py            # Short code generator
├── requirements.txt
├── Procfile            # Railway deployment config
├── .env                # Local env vars (never committed)
└── templates/
    ├── index.html      # Homepage
    ├── analytics.html  # Link analytics page
    ├── 404.html
    └── 500.html
```

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Homepage |
| `POST` | `/api/shorten` | Shorten a URL |
| `GET` | `/<short_code>` | Redirect to original URL |
| `GET` | `/analytics/<short_code>` | View click analytics |

**POST /api/shorten**

```json
// Request
{ "long_url": "https://example.com", "custom_alias": "my-link" }

// Success 201
{ "short_url": "https://your-domain.com/my-link" }

// Error 400 / 409
{ "error": "This custom alias is already in use." }
```

## Deployment

Deployed on Railway with a persistent volume for SQLite storage.

```bash
# Production server
gunicorn app:app
```

Set `SECRET_KEY` in Railway → Variables before deploying.

---

Built by [Gagan Chandra](https://github.com/gagannchandra)

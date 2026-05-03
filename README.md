# OTT Image Extractor API — Render Edition

A dedicated FastAPI service for scraping OTT platform metadata using Playwright. Optimized for Render deployment.

## 🚀 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info & status |
| `/ott/zee5?url=` | GET | Extract ZEE5 poster, title & year |
| `/ott/bms?url=` | GET | Extract BookMyShow poster, title & year |

## 📦 Deployment on Render

### Option 1: Docker Deployment (Recommended)

1. Fork/clone this repo
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **New +** → **Web Service**
4. Connect your GitHub repo
5. Select **Runtime: Docker**
6. Choose plan: **Standard** (2 GB RAM recommended for Playwright)
7. Click **Create Web Service**

### Option 2: Blueprint Deploy (One-click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port (auto-set by Render) |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |

## 🧪 Example Requests

### ZEE5
```bash
curl "https://your-service.onrender.com/ott/zee5?url=https://www.zee5.com/movies/details/assi/0-0-1z5946669"
```

### BookMyShow
```bash
curl "https://your-service.onrender.com/ott/bms?url=https://in.bookmyshow.com/movie-url"
```

## 📊 Response Format

```json
{
  "success": true,
  "ott": "ZEE5",
  "url": "https://www.zee5.com/...",
  "title": "Movie Name",
  "year": 2024,
  "images": {
    "portrait": "https://akamaividz2.zee5.com/..."
  },
  "api_update": "@SteveBotz"
}
```

## ⚠️ Resource Requirements

| Resource | Usage | Render Plan |
|----------|-------|-------------|
| RAM | 300-500 MB | Standard (2 GB) |
| Disk | 200 MB | Any |
| Cold Start | 3-5 sec | — |

**Note:** Playwright requires significant RAM. Free tier (512 MB) may cause timeouts. Use **Standard plan** for reliable performance.

## 🛠️ Tech Stack

- **FastAPI** — Web framework
- **Playwright** — Browser automation
- **BeautifulSoup4** — HTML parsing
- **Docker** — Containerization
- **Render** — Cloud hosting

## 📄 License

MIT — Made with ❤️ by @SteveBotz

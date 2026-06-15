# StarChart

> A custom star map generator that captures the night sky exactly as it looked from any place on Earth, at any moment in time — printed and shipped as a keepsake.

StarChart is the backend powering a live print-on-demand web app. Customers choose a special date (a wedding, a birth, a first meeting), enter their location, and the service renders an accurate star map of that night's sky. The image is then used to produce a printed graphic shipped directly to them.

The backend integrates with NASA's astronomical data (via JPL's planetary ephemeris and the Hipparcos star catalog) to compute real star positions with scientific accuracy — not an approximation or illustration.

---

## How it works

1. A customer fills in their date, time, and location on the storefront
2. The API computes the exact star positions visible from that spot at that moment, using NASA ephemeris data
3. A high-resolution circular star map is rendered and returned as a PNG
4. The image is attached to their order and sent to print

Repeat requests for the same date/location are served instantly from cache.

## Tech stack

| Layer | Technology |
|---|---|
| API | Python / FastAPI |
| Astronomy engine | Skyfield + NASA JPL DE421 ephemeris + Hipparcos star catalog |
| Rendering | Matplotlib |
| Cache | SQLite (short-term deduplication) |
| Storage | PostgreSQL (permanent order images) |
| Storefront integration | Shopify Liquid + vanilla JS |

## API Overview

All endpoints require an `X-API-Key` header.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/starmaps/generate` | Generate a star map image |
| `POST` | `/api/v1/starmaps/{cache_id}/save` | Save a generated map permanently |
| `GET` | `/api/v1/starmaps/{id}` | Retrieve a saved map |
| `GET` | `/api/v1/starmaps` | List saved maps |
| `DELETE` | `/api/v1/starmaps/{id}` | Delete a saved map |
| `GET` | `/health` | Health check |

**Example generate request:**
```json
{
  "latitude": 48.8566,
  "longitude": 2.3522,
  "year": 2019,
  "month": 6,
  "day": 21,
  "hour": 23,
  "minute": 30,
  "timezone_offset": 2,
  "title": "The Night We Met"
}
```

Returns a `image/png` with an `X-Cache-Id` header for saving the result.

## Running locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set API_KEY and DATABASE_URL
python run.py
```

NASA ephemeris data (~70 MB) downloads automatically on first run. Map generation takes 2–5 seconds per request.

## Shopify integration

The repo includes a Shopify Liquid section (`sections/starmap-generator.liquid`) — a two-panel UI with a live star map preview and a date/location form. It reads API credentials from Shopify theme settings and attaches the generated image to the cart item at checkout.

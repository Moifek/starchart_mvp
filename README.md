# StarChart MVP

A FastAPI-based REST API that generates circular star map images showing the night sky for a specific date and GPS location.

## Features

- **Generate star maps on-demand** - Given lat/lon/date/time, produce a PNG image
- **Two-tier storage:**
  - SQLite cache (local) for fast, short-term storage
  - PostgreSQL for permanent storage of saved images
- **API key authentication**
- **Returns images as raw bytes** (`image/png`)

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Run development server
python run.py
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

All endpoints require `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/starmaps/generate` | Generate star map image |
| POST | `/api/v1/starmaps/{cache_id}/save` | Save to permanent storage |
| GET | `/api/v1/starmaps/{id}` | Get saved star map image |
| GET | `/api/v1/starmaps` | List saved star maps |
| DELETE | `/api/v1/starmaps/{id}` | Delete saved star map |
| GET | `/health` | Health check |

## Example Usage

```bash
# Generate a star map
curl -X POST http://localhost:8000/api/v1/starmaps/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "year": 2024,
    "month": 1,
    "day": 15,
    "hour": 22,
    "minute": 0,
    "timezone_offset": -5,
    "title": "The Night We Met"
  }' --output starmap.png

# Save the generated map (using cache_id from X-Cache-Id header)
curl -X POST http://localhost:8000/api/v1/starmaps/{cache_id}/save \
  -H "X-API-Key: your-api-key"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `CACHE_DATABASE_PATH` | SQLite cache file path | `data/cache.db` |
| `CACHE_MAX_AGE_HOURS` | Cache entry TTL | `24` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `false` |

## Notes

- First run downloads ~70MB of astronomy data (Hipparcos catalog, JPL ephemeris)
- Image generation takes 2-5 seconds depending on hardware
- Coordinates rounded to 4 decimal places (~11m precision) for caching


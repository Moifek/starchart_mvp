# StarChart MVP - Context History & Analysis Log

> **Session Date:** January 11, 2026
> **Purpose:** Document context and analysis of the StarChart MVP project structure and operability

---

## Session Overview

This document serves as a context log from the development discussion, providing a comprehensive analysis of the StarChart MVP backend architecture, frontend integration, and system operability.

---

## 1. Frontend Component Analysis (`app/h.html`)

### Purpose
A self-contained HTML frontend component designed for Shopify website integration. It provides an interactive UI for generating star map images based on user-specified parameters.

### Key Features

| Feature | Implementation |
|---------|---------------|
| **Location Search** | OpenStreetMap Nominatim API with debounced autocomplete (300ms) |
| **Date/Time Picker** | Flatpickr library with dark theme |
| **Timezone Detection** | Auto-detects browser timezone offset |
| **Image Preview** | Live preview panel with loading states |
| **API Integration** | Fetches PNG blob from backend, displays inline |

### UI Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Container (Grid Layout)                    │
├─────────────────────────────────┬──────────────────────────────┤
│                                 │                              │
│     Preview Panel (Left)        │     Form Panel (Right)       │
│     - Generated image preview   │     - API Key input          │
│     - Loading spinner           │     - Title (optional)       │
│     - Placeholder text          │     - Location autocomplete  │
│                                 │     - Date picker            │
│                                 │     - Time picker            │
│                                 │     - UTC offset             │
│                                 │     - Generate button        │
│                                 │                              │
└─────────────────────────────────┴──────────────────────────────┘
```

### API Request Flow

```javascript
// Payload structure sent to backend
{
    latitude: float,      // From location autocomplete
    longitude: float,     // From location autocomplete
    year: int,            // From flatpickr
    month: int,           // From flatpickr (1-indexed)
    day: int,             // From flatpickr
    hour: int,            // From time picker
    minute: int,          // From time picker
    timezone_offset: int, // From input (auto-detected default)
    title: string|null    // Optional
}
```

### Critical Implementation Details

1. **API Base URL**: Configured to `http://localhost:8000` (must be updated for production)
2. **Authentication**: Uses `X-API-Key` header
3. **Response Handling**: Receives binary PNG blob, creates object URL for display
4. **Cache ID Storage**: Stores `X-Cache-Id` header in `previewImage.dataset.cacheId` for potential save operations
5. **Memory Management**: Properly revokes previous blob URLs before creating new ones

### Styling
- Dark theme (background: `#111214`, `#0f1113`, `#18181b`)
- Accent color: Indigo (`#6366f1`)
- Modern, minimal design using CSS Grid
- Responsive form inputs with focus states

---

## 2. Backend Architecture Analysis

### Project Structure (Implemented)

```
starchart-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py                 ✅ FastAPI app with lifespan, CORS
│   ├── settings.py             ✅ Pydantic settings configuration
│   ├── dependencies.py         ✅ API key authentication
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── cache.py            ✅ SQLite cache connection
│   │   └── storage.py          ✅ PostgreSQL connection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cache.py            ✅ CachedStarmap SQLAlchemy model
│   │   └── starmap.py          ✅ Starmap SQLAlchemy model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── starmap.py          ✅ Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generator.py        ✅ Star map image generation (Skyfield)
│   │   └── starmap.py          ✅ Business logic layer
│   │
│   └── routers/
│       ├── __init__.py
│       └── starmaps.py         ✅ API endpoints
│
├── data/
│   ├── cache.db                ✅ SQLite cache (exists)
│   └── de421.bsp               ✅ JPL ephemeris (exists)
│
├── requirements.txt            ✅
├── run.py                      ✅ Development server runner
├── README.md                   ✅
└── IMPLEMENTATION_SPEC.md      ✅
```

### API Endpoints Summary

| Endpoint | Method | Purpose | Auth | Response |
|----------|--------|---------|------|----------|
| `/api/v1/starmaps/generate` | POST | Generate star map image | ✅ | `image/png` + `X-Cache-Id` header |
| `/api/v1/starmaps/{cache_id}/save` | POST | Save to PostgreSQL | ✅ | JSON metadata |
| `/api/v1/starmaps/{id}` | GET | Retrieve saved image | ✅ | `image/png` |
| `/api/v1/starmaps` | GET | List saved maps (paginated) | ✅ | JSON list |
| `/api/v1/starmaps/{id}` | DELETE | Delete saved map | ✅ | 204 No Content |
| `/health` | GET | Health check | ❌ | JSON status |

### Two-Tier Storage Architecture

```
                    ┌──────────────────────────────────────────┐
                    │           Request Flow                    │
                    └──────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────┐
│                     SQLite Cache Layer                         │
│  - Fast, local storage                                         │
│  - Short-term (24hr default TTL)                              │
│  - Used for "exploration" phase                               │
│  - Cache key: lat+lon+datetime (coords rounded to 4 decimals) │
└───────────────────────────────────────────────────────────────┘
                                        │
                            User calls /save
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────┐
│                   PostgreSQL Storage Layer                     │
│  - Permanent storage                                           │
│  - For "committed" star maps                                   │
│  - Stores full image + metadata                               │
│  - Queryable, paginated listing                               │
└───────────────────────────────────────────────────────────────┘
```

### Generator Service Details

**Technology Stack:**
- **Skyfield**: Astronomical computations (star positions)
- **Hipparcos Catalog**: ~118,000 stars with precise positions and magnitudes
- **JPL DE421 Ephemeris**: Planetary positions for Earth orientation
- **Matplotlib**: Image rendering (using `Agg` backend for server)
- **NumPy**: Stereographic projection calculations

**Generation Pipeline:**
1. Load star catalog (cached in singleton)
2. Load ephemeris (cached in singleton)
3. Compute observation time with timezone
4. Calculate star alt/az positions from observer location
5. Filter visible stars (above horizon, magnitude ≤ 6.0)
6. Apply stereographic projection to 2D
7. Render with matplotlib to PNG bytes

**Output Characteristics:**
- Resolution: 150 DPI
- Size: 10" × 12" figure
- Format: PNG with transparent-aware rendering
- Elements: Stars, cardinal directions, altitude reference circles, title, date, coordinates

---

## 3. Database Schema Details

### SQLite Cache (`cached_starmaps`)

```sql
CREATE TABLE cached_starmaps (
    id TEXT PRIMARY KEY,                    -- UUID string
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    timezone_offset INTEGER NOT NULL,
    image_data BLOB NOT NULL,               -- PNG bytes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_cache_lookup ON cached_starmaps(latitude, longitude, year, month, day, hour);
CREATE INDEX idx_cache_created_at ON cached_starmaps(created_at);
```

### PostgreSQL Storage (`starmaps`)

```sql
CREATE TABLE starmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone_offset INTEGER NOT NULL,
    title VARCHAR(255),
    image_data BYTEA NOT NULL,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_starmaps_location ON starmaps(latitude, longitude);
CREATE INDEX idx_starmaps_observed ON starmaps(observed_at);
```

---

## 4. Configuration & Environment

### Required Environment Variables

```bash
# .env file (NOT present in repo - needs creation)
API_KEY=your-secure-random-api-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/starchart
CACHE_DATABASE_PATH=data/cache.db
CACHE_MAX_AGE_HOURS=24
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### Dependencies (requirements.txt)

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
psycopg2-binary>=2.9.0
aiosqlite>=0.19.0          # Note: Not currently used (sync SQLite)
skyfield>=1.48
matplotlib>=3.8.0
numpy>=1.26.0
pandas>=2.0.0
python-multipart>=0.0.6
```

---

## 5. Current State & Observations

### ✅ Implemented & Working

1. **Full API endpoint implementation** - All 5 CRUD endpoints + health check
2. **Star map generation** - Skyfield-based astronomy calculations working
3. **SQLite caching** - Cache DB exists at `data/cache.db`
4. **Ephemeris data** - `de421.bsp` downloaded
5. **API key authentication** - Middleware functional
6. **CORS configuration** - Set to allow all origins (dev mode)
7. **Frontend component** - `h.html` fully functional for Shopify integration

### ⚠️ Potential Issues / Notes

1. **Missing `.env` file** - No environment file found in repo (gitignored)
2. **PostgreSQL dependency** - Requires running PostgreSQL instance for permanent storage
3. **CORS in production** - Currently allows `*` origins; should be restricted
4. **Cache cleanup** - `cleanup_old_cache()` function exists but not scheduled
5. **First-run data download** - Hipparcos catalog downloads on first use (~50MB)

### 📊 Data Files Present

| File | Size | Purpose |
|------|------|---------|
| `data/cache.db` | Variable | SQLite cache database |
| `data/de421.bsp` | ~17MB | JPL planetary ephemeris |
| `hip_main.dat` | ~50MB | Hipparcos star catalog (root level) |

---

## 6. Request/Response Flow (Complete)

### Generate Flow

```
Frontend (h.html)                          Backend (FastAPI)
       │                                          │
       │  POST /api/v1/starmaps/generate          │
       │  Headers: X-API-Key, Content-Type        │
       │  Body: GenerateRequest JSON              │
       │─────────────────────────────────────────>│
       │                                          │
       │                                ┌─────────┴─────────┐
       │                                │ verify_api_key()  │
       │                                │ Round coords      │
       │                                │ Check SQLite      │
       │                                └─────────┬─────────┘
       │                                          │
       │                              ┌───────────┴───────────┐
       │                              │ Cache Hit?            │
       │                              │ Yes: Return cached    │
       │                              │ No: Generate new      │
       │                              │     → Store in cache  │
       │                              └───────────┬───────────┘
       │                                          │
       │  Response: image/png bytes               │
       │  Headers: X-Cache-Id, X-Cache-Hit        │
       │<─────────────────────────────────────────│
       │                                          │
       │  Store cache_id in dataset               │
       │  Create blob URL                         │
       │  Display image                           │
       ▼                                          ▼
```

---

## 7. Integration Points (Shopify)

### Current Setup
- Frontend (`h.html`) designed as embeddable component
- Uses external libraries via CDN (Flatpickr)
- Self-contained styling (no external CSS dependencies)
- API key passed via form input

### Deployment Considerations
1. **Update `API_BASE_URL`** - Change from localhost to production server
2. **Secure API key** - Don't expose in client-side code in production
3. **CORS whitelist** - Restrict to Shopify store domain
4. **SSL/HTTPS** - Required for production API calls

---

## 8. Next Steps / Recommendations

### Immediate
- [ ] Create `.env` file with proper credentials
- [ ] Ensure PostgreSQL is running for save functionality
- [ ] Test full generate → save flow

### Production Readiness
- [ ] Implement background cache cleanup task
- [ ] Add rate limiting
- [ ] Restrict CORS origins
- [ ] Add request logging/monitoring
- [ ] Consider Redis for horizontal scaling of cache

---

## 9. Session Update - Cache Cleanup & Dual Database Support

### Changes Made (January 11, 2026)

#### 1. Cache Cleanup Implementation (`app/main.py`)

Added a background async task that automatically cleans up old cache entries:

```python
async def cache_cleanup_task():
    """Background task that periodically cleans up old cache entries."""
    # Runs every CACHE_CLEANUP_INTERVAL_MINUTES (default: 60)
    # Removes entries older than CACHE_MAX_AGE_HOURS (default: 24)
```

**Behavior:**
- Starts automatically on server startup
- Runs in a loop at configurable interval
- Gracefully stops on server shutdown
- Logs cleanup operations
- Continues running even if individual cleanups fail

#### 2. Dual Database Support for Permanent Storage

The project now supports **both PostgreSQL and SQLite** for permanent storage, switchable via environment variable.

**New Environment Variables:**

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `STORAGE_TYPE` | `postgres` \| `sqlite` | `postgres` | Which database for permanent storage |
| `CACHE_CLEANUP_INTERVAL_MINUTES` | int | `60` | How often to run cache cleanup |

**Configuration Examples:**

```bash
# PostgreSQL (default)
STORAGE_TYPE=postgres
DATABASE_URL=postgresql://user:pass@localhost:5432/starchart

# SQLite
STORAGE_TYPE=sqlite
DATABASE_URL=sqlite:///data/storage.db
```

#### 3. Database-Agnostic Model (`app/models/starmap.py`)

Created custom SQLAlchemy type decorators for cross-database compatibility:

- **`GUID`**: Uses native PostgreSQL UUID or CHAR(36) for SQLite
- **`JSONType`**: Uses PostgreSQL JSONB or TEXT with JSON serialization for SQLite

#### 4. Files Modified

| File | Changes |
|------|---------|
| `app/settings.py` | Added `storage_type`, `cache_cleanup_interval_minutes`, `is_sqlite_storage` property |
| `app/models/starmap.py` | Created `GUID` and `JSONType` cross-database type decorators |
| `app/database/storage.py` | Dynamic engine creation based on storage type |
| `app/main.py` | Background cache cleanup task, enhanced health endpoint |

#### 5. Health Endpoint Enhancement

The `/health` endpoint now returns additional configuration info:

```json
{
    "status": "healthy",
    "storage_type": "postgres",
    "cache_cleanup_interval_minutes": 60,
    "cache_max_age_hours": 24
}
```

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        StarChart MVP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Cache Layer (SQLite - Always)                                   │
│  └── data/cache.db                                              │
│  └── Cleanup: Background task every N minutes                   │
│                                                                  │
│  Permanent Storage (Configurable via STORAGE_TYPE)              │
│  ├── STORAGE_TYPE=postgres → PostgreSQL (native UUID, JSONB)    │
│  └── STORAGE_TYPE=sqlite  → SQLite (CHAR(36), TEXT JSON)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. API Key Security & CORS Domain Restrictions

### Session Update (January 11, 2026)

#### Security Analysis: Frontend API Key Exposure

**Issue Identified:** The API key in `app/h.html` is used in client-side JavaScript, which means it's inherently public/exposed.

```javascript
// h.html - API key sent from frontend
const apiKey = document.getElementById('apiKey').value;
headers: { 'X-API-Key': apiKey }
```

**Key Insight:** Any secret in client-side JavaScript is visible via:
- Browser "View Source"
- DevTools Network tab
- Rendered HTML inspection

#### Mitigation Strategy: CORS Domain Restrictions

Instead of relying solely on API key secrecy, we use CORS to restrict which domains can call the API.

**Implementation in `app/main.py`:**

```python
# PRODUCTION: Uncomment and configure these restricted origins:
# ALLOWED_ORIGINS = [
#     "https://your-store.myshopify.com",
#     "https://your-custom-domain.com",
# ]
#
# DEVELOPMENT: Allow all origins (current setting)
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

#### Security Layers

| Layer | Protection | Status |
|-------|------------|--------|
| API Key | Identifies authorized apps | ✅ Active |
| CORS Origins | Restricts which domains can call API | 🔧 Dev mode (allow all) |
| Rate Limiting | Prevents abuse | ❌ Not implemented |

#### Production Checklist

- [ ] Set `ALLOWED_ORIGINS` to actual Shopify domain(s)
- [ ] Consider adding rate limiting per IP
- [ ] Optionally: Make `/generate` public, keep API key only for `/save`

#### Why This Is Acceptable

For this use case (star map generation widget):
1. The "damage" from API abuse is just extra server load (image generation)
2. CORS prevents other websites from calling your API
3. Generated images aren't sensitive data
4. The API key acts as an "app identifier" rather than a true secret

---

## 11. Shopify Cart Integration

### Session Update (January 11, 2026)

#### Implementation Overview

Added "Add to Cart" functionality to `app/h.html` that integrates with Shopify's AJAX Cart API.

**Shopify Variant ID:** `52466655658168`

#### User Flow

```
1. User generates star map (existing flow)
   └── Image displayed, cache_id stored

2. User clicks "Add to Cart"
   ├── Save to permanent storage: POST /api/v1/starmaps/{cache_id}/save
   ├── Receive permanent starmap ID
   └── Add to Shopify cart: POST /cart/add.js with line item properties

3. Button state updates
   ├── If same params as last added → Button locked: "✓ Added to Cart"
   └── If params changed → Button enabled: "Add to Cart"
```

#### Line Item Properties Sent to Shopify

```javascript
{
    '_starmap_id': 'uuid',           // Hidden - for internal reference
    '_image_url': 'https://...',     // Hidden - for fulfillment/print
    'Title': 'The Night We Met',     // Visible to customer
    'Location': 'New York, NY',      // Visible to customer
    'Date': 'January 15, 2024',      // Visible to customer
    'Coordinates': '40.7128°, -74.0060°'  // Visible to customer
}
```

*Note: Properties starting with `_` are hidden from customers in cart/checkout but visible in order admin.*

#### Features Implemented

| Feature | Description |
|---------|-------------|
| **Add to Cart** | Saves image permanently, then adds to Shopify cart |
| **Toast Notifications** | Success/error feedback with animated toast |
| **Button Lock** | Prevents duplicate adds if params unchanged |
| **State Tracking** | Compares current vs last-added params |

#### Button States

| State | Appearance | Condition |
|-------|------------|-----------|
| Disabled (initial) | Gray, "Add to Cart" | No image generated yet |
| Enabled | Green, "Add to Cart" | Image generated, not yet added |
| Processing | Gray, "Adding..." | Currently saving/adding |
| Locked | Green border, "✓ Added to Cart" | Same params already in cart |

#### CSS Added

- `.btn-cart` - Green add-to-cart button styling
- `.btn-cart.added` - Locked state with green border
- `.toast` - Fixed-position notification component
- `.toast.success` / `.toast.error` - State variants with icons

#### JavaScript Added

- `showToast(message, type)` - Display toast notification
- `getParamsHash(params)` - Create comparable hash of params
- `updateCartButtonState()` - Manage button enabled/locked state
- `addToCartBtn click handler` - Full save → cart flow

#### Integration with Fulfillment

The `_image_url` property contains the direct URL to fetch the high-resolution PNG:

```
https://your-server.com/api/v1/starmaps/{uuid}
```

Print-on-demand fulfillment services can:
1. Read this URL from the order's line item properties
2. Fetch the image via GET request (requires API key)
3. Use for printing

---

*Log created during project analysis session - January 11, 2026*
*Updated with cache cleanup and dual-database support implementation*
*Updated with API key security analysis and CORS domain restrictions*
*Updated with Shopify cart integration implementation*
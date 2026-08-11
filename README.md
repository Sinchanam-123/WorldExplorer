# 🌍 World Explorer

A full-stack country information web app built with **FastAPI** (Python backend) and plain **HTML/CSS/JavaScript** (frontend). Search any of 20 countries and get a dedicated detail page with real photos, geography, culture, economy data, fun facts, and more.

---

## 📸 Pages

### Homepage
- Hero section with live search autocomplete
- Featured destinations grid with real photos
- Browse by region (Asia, Europe, Americas, Africa, Oceania)
- All 20 countries with filter pills

### Country Detail Page
- Full-bleed hero photo with flag, name and badges
- Photo strip (click to enlarge in lightbox)
- Quick stats: population, area, density
- Geography & Identity table
- Culture & Society table
- Economy & Data table + Gini inequality index
- Famous Landmarks & Attractions (with photos)
- Fun facts
- Sidebar with travel-guide content: Famous Foods to Try, Best Time to Visit, Major Cities, Native Name, TLD, calling code, and Google Maps link

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Sinchanam-123/WorldExplorer.git
cd world-explorer
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --forwarded-allow-ips=""
```

> `--forwarded-allow-ips=""` stops uvicorn trusting `X-Forwarded-For` when nothing is proxying it, which keeps the rate limiter honest. See [Before deploying this publicly](#before-deploying-this-publicly).

Backend runs at → `http://localhost:8000`

You can test it in your browser:
```
http://localhost:8000/country/japan
http://localhost:8000/country/brazil
```

### 3. Open the frontend

Just open `frontend/index.html` in your browser — no build step needed.

```bash
# macOS
open frontend/index.html

# Windows
start frontend/index.html

# Or use VS Code Live Server (recommended)
```

> ⚠️ If you open the file directly (not via Live Server), make sure your browser allows local file CORS requests, or use VS Code's Live Server extension.

---

## 📁 Project Structure

```
world-explorer/
├── backend/
│   ├── main.py              # FastAPI app
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Homepage
│   └── country.html         # Country detail page
├── .gitignore
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/countries/all` | Summary list of all 20 countries |
| GET | `/country/{name}` | Full data for one country |
| GET | `/search/{query}` | Search autocomplete (returns up to 6 results) |

### Example — `/country/japan`

```json
{
  "name": "Japan",
  "official": "Japan",
  "flag_emoji": "🇯🇵",
  "capital": "Tokyo",
  "region": "Asia",
  "subregion": "Eastern Asia",
  "population": 125681593,
  "area": 377930,
  "population_density": 332.6,
  "currencies": [{ "code": "JPY", "name": "Japanese yen", "symbol": "¥" }],
  "languages": ["Japanese"],
  "timezones": ["UTC+09:00"],
  "calling_code": "+81",
  "drives_on": "Left",
  "borders": [],
  "landlocked": false,
  "independent": true,
  "un_member": true,
  "fun_facts": ["..."],
  "images": ["https://images.unsplash.com/..."]
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, FastAPI, httpx, slowapi |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Data | [mledoze/countries](https://github.com/mledoze/countries) JSON mirror (free, no key needed) |
| Photos | Unsplash + Wikimedia Commons (curated per country) |
| Flags | flagcdn.com |
| Fonts | Google Fonts (Playfair Display + DM Sans) |

---

## 🔒 Security Features

- **Input validation** — country names checked against a character allowlist, max 100 chars. Angle brackets, quotes and slashes are rejected before any lookup.
- **XSS prevention** — all upstream data is inserted with `textContent` or HTML-escaped first, and `safeUrl()` forces `https:` on every image and link. Verified by rendering a poisoned country record: scripts do not execute and `javascript:` URLs collapse to `#`.
- **CORS restricted** — explicit origin list, no wildcard, and credentials are *not* enabled, so no cookie or auth header is ever exposed cross-origin.
- **Rate limiting** — 60 req/min on `/` and country lookup, 30 req/min on search and listing.
- **No API keys** — only free public data sources; nothing sensitive in the codebase or git history.
- **Pinned dependencies** — exact versions in `requirements.txt`, so a fresh install can't silently pull a different release.

### Before deploying this publicly

These are fine for local use but are **not** production-safe as-is:

1. **Rate limiting is bypassable behind a trusted proxy.** `uvicorn[standard]` honours `X-Forwarded-For` from `127.0.0.1` by default and rewrites the client IP, so rotating that header resets the limit bucket. Run with `--forwarded-allow-ips=""` when there is no proxy in front, or set it to your proxy's IP only.
2. **Remove the `"null"` CORS origin.** It's there so opening `index.html` from disk works. Any site can get `Origin: null` via a sandboxed iframe, so leaving it in lets third parties read the API and spend its rate limit.
3. **Add the real front-end origin** to `allow_origins` and drop the localhost entries.
4. **Consider disabling the auto-generated docs** (`FastAPI(docs_url=None, redoc_url=None)`) — `/docs` and `/openapi.json` are public. Harmless here since the data is public, but it does advertise the full API surface.

---

## 🌍 Countries Included

Japan · Brazil · India · Germany · Nigeria · France · Australia · South Korea · Mexico · South Africa · Indonesia · Argentina · Egypt · Iceland · Thailand · Norway · Kenya · Canada · Portugal · Chile

> The backend resolves **any country in the world** from the dataset, so `/country/italy` returns its capital, area, languages, currencies and borders.
>
> The 20 above are the *curated* set. The upstream dataset carries no population, timezone, flag-image or gini data, so those are embedded in the backend for these 20 only — along with photos, fun facts and the travel-guide sidebar. For anything else the API returns `null` for those figures and the page shows "N/A" rather than inventing a number. Flags and the Google Maps link are derived from the country's ISO code, so they work everywhere.

---

## 📚 What I Learned

- Building a REST API with **FastAPI**
- Async HTTP requests with **httpx** and `asyncio.gather` for parallel fetching
- Connecting a frontend to a Python backend (CORS, JSON)
- Securing a web app (input validation, rate limiting, XSS prevention)
- DOM manipulation without a framework
- Clean project structure for a full-stack app

---

Made by Sinchana M Prasad

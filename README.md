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
python -m uvicorn main:app --reload
```

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
| Data | REST Countries API (free, no key needed) |
| Photos | Unsplash (curated per country) |
| Flags | flagcdn.com |
| Fonts | Google Fonts (Playfair Display + DM Sans) |

---

## 🔒 Security Features

- **Input validation** — country names validated with regex allowlist, max 100 chars
- **Rate limiting** — 60 req/min on country lookup, 30 req/min on search and listing
- **CORS restricted** — only localhost origins allowed (no wildcard)
- **XSS prevention** — all API data escaped before DOM insertion; `safeUrl()` on all links and images
- **No API keys** — uses only free public APIs, nothing sensitive in the codebase

---

## 🌍 Countries Included

Japan · Brazil · India · Germany · Nigeria · France · Australia · South Korea · Mexico · South Africa · Indonesia · Argentina · Egypt · Iceland · Thailand · Norway · Kenya · Canada · Portugal · Chile

> The backend works for **any country in the world** via the REST Countries API — the 20 above just have curated photos and fun facts built in.

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

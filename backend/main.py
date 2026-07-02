"""
World Explorer — FastAPI Backend
Data source: github.com/mledoze/countries (free, no API key needed).
Static fields (population, timezones, flags etc.) are embedded directly
so they are always accurate and never depend on the external source.
Images are curated Unsplash photos, picked individually per country.
"""

import asyncio
import re

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


# ---------------------------------------------------------------------------
# App & middleware
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)
app     = FastAPI(title="World Explorer API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "null",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Free GitHub mirror — no API key, no rate limits
DATA_URL = "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"

# In-memory cache — loaded once on first request
_CACHE: list[dict] = []


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

MAX_QUERY_LEN = 100
ALLOWED_CHARS = re.compile(r"^[a-zA-Z\s\-'\.]+$")


def validate_country_name(name: str) -> str:
    """Strip and validate country name. Raises HTTP 400 on bad input."""
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Country name cannot be empty.")
    if len(name) > MAX_QUERY_LEN:
        raise HTTPException(status_code=400, detail=f"Query too long (max {MAX_QUERY_LEN} chars).")
    if not ALLOWED_CHARS.match(name):
        raise HTTPException(status_code=400, detail="Invalid characters in country name.")
    return name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_calling_code(idd: dict) -> str:
    root     = idd.get("root", "")
    suffixes = idd.get("suffixes") or [""]
    return (root + suffixes[0]).strip()


def build_currencies(raw: dict) -> list[dict]:
    return [
        {"code": code, "name": info.get("name", code), "symbol": info.get("symbol", "")}
        for code, info in raw.items()
    ]


# ---------------------------------------------------------------------------
# Complete static data for all 20 countries
# These fields are guaranteed correct and don't rely on the external API.
# ---------------------------------------------------------------------------

STATIC: dict[str, dict] = {
    "Japan": {
        "population":     125681593,
        "native_name":    "日本",
        "timezones":      ["UTC+09:00"],
        "drives_on":      "Left",
        "car_signs":      ["J"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/jp.png",
        "flag_svg":       "https://flagcdn.com/jp.svg",
        "google_maps":    "https://www.google.com/maps/place/Japan",
        "continents":     ["Asia"],
        "capital_latlng": [35.68, 139.69],
        "gini":           {"2013": 32.9},
        "un_member":      True,
        "independent":    True,
    },
    "Brazil": {
        "population":     215313498,
        "native_name":    "Brasil",
        "timezones":      ["UTC-03:00"],
        "drives_on":      "Right",
        "car_signs":      ["BR"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/br.png",
        "flag_svg":       "https://flagcdn.com/br.svg",
        "google_maps":    "https://www.google.com/maps/place/Brazil",
        "continents":     ["South America"],
        "capital_latlng": [-15.78, -47.93],
        "gini":           {"2019": 53.4},
        "un_member":      True,
        "independent":    True,
    },
    "India": {
        "population":     1428627663,
        "native_name":    "भारत",
        "timezones":      ["UTC+05:30"],
        "drives_on":      "Left",
        "car_signs":      ["IND"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/in.png",
        "flag_svg":       "https://flagcdn.com/in.svg",
        "google_maps":    "https://www.google.com/maps/place/India",
        "continents":     ["Asia"],
        "capital_latlng": [28.61, 77.21],
        "gini":           {"2019": 35.7},
        "un_member":      True,
        "independent":    True,
    },
    "Germany": {
        "population":     83369843,
        "native_name":    "Deutschland",
        "timezones":      ["UTC+01:00"],
        "drives_on":      "Right",
        "car_signs":      ["D"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/de.png",
        "flag_svg":       "https://flagcdn.com/de.svg",
        "google_maps":    "https://www.google.com/maps/place/Germany",
        "continents":     ["Europe"],
        "capital_latlng": [52.52, 13.40],
        "gini":           {"2016": 31.7},
        "un_member":      True,
        "independent":    True,
    },
    "Nigeria": {
        "population":     218541212,
        "native_name":    "Nigeria",
        "timezones":      ["UTC+01:00"],
        "drives_on":      "Right",
        "car_signs":      ["WAN"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/ng.png",
        "flag_svg":       "https://flagcdn.com/ng.svg",
        "google_maps":    "https://www.google.com/maps/place/Nigeria",
        "continents":     ["Africa"],
        "capital_latlng": [9.07, 7.40],
        "gini":           {"2018": 35.1},
        "un_member":      True,
        "independent":    True,
    },
    "France": {
        "population":     68305148,
        "native_name":    "France",
        "timezones":      ["UTC+01:00"],
        "drives_on":      "Right",
        "car_signs":      ["F"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/fr.png",
        "flag_svg":       "https://flagcdn.com/fr.svg",
        "google_maps":    "https://www.google.com/maps/place/France",
        "continents":     ["Europe"],
        "capital_latlng": [48.86, 2.35],
        "gini":           {"2018": 32.4},
        "un_member":      True,
        "independent":    True,
    },
    "Australia": {
        "population":     26177413,
        "native_name":    "Australia",
        "timezones":      ["UTC+08:00", "UTC+09:30", "UTC+10:00", "UTC+11:00"],
        "drives_on":      "Left",
        "car_signs":      ["AUS"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/au.png",
        "flag_svg":       "https://flagcdn.com/au.svg",
        "google_maps":    "https://www.google.com/maps/place/Australia",
        "continents":     ["Oceania"],
        "capital_latlng": [-35.28, 149.13],
        "gini":           {"2018": 34.3},
        "un_member":      True,
        "independent":    True,
    },
    "South Korea": {
        "population":     51744876,
        "native_name":    "대한민국",
        "timezones":      ["UTC+09:00"],
        "drives_on":      "Right",
        "car_signs":      ["ROK"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/kr.png",
        "flag_svg":       "https://flagcdn.com/kr.svg",
        "google_maps":    "https://www.google.com/maps/place/South+Korea",
        "continents":     ["Asia"],
        "capital_latlng": [37.55, 126.99],
        "gini":           {"2016": 31.4},
        "un_member":      True,
        "independent":    True,
    },
    "Mexico": {
        "population":     127504125,
        "native_name":    "México",
        "timezones":      ["UTC-06:00"],
        "drives_on":      "Right",
        "car_signs":      ["MEX"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/mx.png",
        "flag_svg":       "https://flagcdn.com/mx.svg",
        "google_maps":    "https://www.google.com/maps/place/Mexico",
        "continents":     ["North America"],
        "capital_latlng": [19.43, -99.13],
        "gini":           {"2018": 45.4},
        "un_member":      True,
        "independent":    True,
    },
    "South Africa": {
        "population":     60414495,
        "native_name":    "South Africa",
        "timezones":      ["UTC+02:00"],
        "drives_on":      "Left",
        "car_signs":      ["ZA"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/za.png",
        "flag_svg":       "https://flagcdn.com/za.svg",
        "google_maps":    "https://www.google.com/maps/place/South+Africa",
        "continents":     ["Africa"],
        "capital_latlng": [-25.74, 28.19],
        "gini":           {"2014": 63.0},
        "un_member":      True,
        "independent":    True,
    },
    "Indonesia": {
        "population":     277534122,
        "native_name":    "Indonesia",
        "timezones":      ["UTC+07:00", "UTC+08:00", "UTC+09:00"],
        "drives_on":      "Left",
        "car_signs":      ["RI"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/id.png",
        "flag_svg":       "https://flagcdn.com/id.svg",
        "google_maps":    "https://www.google.com/maps/place/Indonesia",
        "continents":     ["Asia"],
        "capital_latlng": [-6.21, 106.85],
        "gini":           {"2021": 38.2},
        "un_member":      True,
        "independent":    True,
    },
    "Argentina": {
        "population":     46654581,
        "native_name":    "Argentina",
        "timezones":      ["UTC-03:00"],
        "drives_on":      "Right",
        "car_signs":      ["RA"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/ar.png",
        "flag_svg":       "https://flagcdn.com/ar.svg",
        "google_maps":    "https://www.google.com/maps/place/Argentina",
        "continents":     ["South America"],
        "capital_latlng": [-34.61, -58.37],
        "gini":           {"2019": 42.9},
        "un_member":      True,
        "independent":    True,
    },
    "Egypt": {
        "population":     105914499,
        "native_name":    "مِصر",
        "timezones":      ["UTC+02:00"],
        "drives_on":      "Right",
        "car_signs":      ["ET"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/eg.png",
        "flag_svg":       "https://flagcdn.com/eg.svg",
        "google_maps":    "https://www.google.com/maps/place/Egypt",
        "continents":     ["Africa"],
        "capital_latlng": [30.06, 31.25],
        "gini":           {"2019": 31.5},
        "un_member":      True,
        "independent":    True,
    },
    "Iceland": {
        "population":     376248,
        "native_name":    "Ísland",
        "timezones":      ["UTC+00:00"],
        "drives_on":      "Right",
        "car_signs":      ["IS"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/is.png",
        "flag_svg":       "https://flagcdn.com/is.svg",
        "google_maps":    "https://www.google.com/maps/place/Iceland",
        "continents":     ["Europe"],
        "capital_latlng": [64.15, -21.95],
        "gini":           {"2017": 26.1},
        "un_member":      True,
        "independent":    True,
    },
    "Thailand": {
        "population":     71801279,
        "native_name":    "ไทย",
        "timezones":      ["UTC+07:00"],
        "drives_on":      "Left",
        "car_signs":      ["T"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/th.png",
        "flag_svg":       "https://flagcdn.com/th.svg",
        "google_maps":    "https://www.google.com/maps/place/Thailand",
        "continents":     ["Asia"],
        "capital_latlng": [13.75, 100.52],
        "gini":           {"2019": 34.9},
        "un_member":      True,
        "independent":    True,
    },
    "Norway": {
        "population":     5474360,
        "native_name":    "Norge",
        "timezones":      ["UTC+01:00"],
        "drives_on":      "Right",
        "car_signs":      ["N"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/no.png",
        "flag_svg":       "https://flagcdn.com/no.svg",
        "google_maps":    "https://www.google.com/maps/place/Norway",
        "continents":     ["Europe"],
        "capital_latlng": [59.91, 10.74],
        "gini":           {"2018": 25.0},
        "un_member":      True,
        "independent":    True,
    },
    "Kenya": {
        "population":     55100586,
        "native_name":    "Kenya",
        "timezones":      ["UTC+03:00"],
        "drives_on":      "Left",
        "car_signs":      ["EAK"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/ke.png",
        "flag_svg":       "https://flagcdn.com/ke.svg",
        "google_maps":    "https://www.google.com/maps/place/Kenya",
        "continents":     ["Africa"],
        "capital_latlng": [-1.28, 36.82],
        "gini":           {"2015": 40.8},
        "un_member":      True,
        "independent":    True,
    },
    "Canada": {
        "population":     38781292,
        "native_name":    "Canada",
        "timezones":      ["UTC-05:00"],
        "drives_on":      "Right",
        "car_signs":      ["CDN"],
        "start_of_week":  "Sunday",
        "flag_png":       "https://flagcdn.com/w320/ca.png",
        "flag_svg":       "https://flagcdn.com/ca.svg",
        "google_maps":    "https://www.google.com/maps/place/Canada",
        "continents":     ["North America"],
        "capital_latlng": [45.42, -75.70],
        "gini":           {"2019": 33.3},
        "un_member":      True,
        "independent":    True,
    },
    "Portugal": {
        "population":     10247605,
        "native_name":    "Portugal",
        "timezones":      ["UTC+00:00"],
        "drives_on":      "Right",
        "car_signs":      ["P"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/pt.png",
        "flag_svg":       "https://flagcdn.com/pt.svg",
        "google_maps":    "https://www.google.com/maps/place/Portugal",
        "continents":     ["Europe"],
        "capital_latlng": [38.72, -9.13],
        "gini":           {"2018": 33.5},
        "un_member":      True,
        "independent":    True,
    },
    "Chile": {
        "population":     19629590,
        "native_name":    "Chile",
        "timezones":      ["UTC-04:00"],
        "drives_on":      "Right",
        "car_signs":      ["RCH"],
        "start_of_week":  "Monday",
        "flag_png":       "https://flagcdn.com/w320/cl.png",
        "flag_svg":       "https://flagcdn.com/cl.svg",
        "google_maps":    "https://www.google.com/maps/place/Chile",
        "continents":     ["South America"],
        "capital_latlng": [-33.46, -70.65],
        "gini":           {"2020": 44.4},
        "un_member":      True,
        "independent":    True,
    },
}

# Aliases so find_country can map alternate API names → our STATIC keys
NAME_ALIASES: dict[str, str] = {
    "korea, republic of":        "South Korea",
    "republic of korea":         "South Korea",
    "south korea":               "South Korea",
    "corea del sur":             "South Korea",
    "south africa":              "South Africa",
    "republic of south africa":  "South Africa",
    "brasil":                    "Brazil",
    "égypte":                    "Egypt",
    "allemagne":                 "Germany",
    "norvège":                   "Norway",
}


# ---------------------------------------------------------------------------
# Data fetching & searching
# ---------------------------------------------------------------------------

async def fetch_all_raw() -> list[dict]:
    """Load all country data from GitHub mirror. Cached after first call."""
    global _CACHE
    if _CACHE:
        return _CACHE
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            r = await client.get(DATA_URL)
            r.raise_for_status()
            _CACHE = r.json()
            print(f"Loaded {len(_CACHE)} countries.")
            return _CACHE
        except Exception as exc:
            print(f"Failed to load country data: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Cannot reach country data source. Check your internet connection.",
            )


def resolve_static_key(common_name: str) -> str:
    """Map an API common name to our STATIC dict key."""
    if common_name in STATIC:
        return common_name
    lower = common_name.lower()
    if lower in NAME_ALIASES:
        return NAME_ALIASES[lower]
    for key in STATIC:
        if key.lower() == lower:
            return key
    return common_name


def find_country(data: list[dict], name: str) -> dict | None:
    """Find a country by common name, official name, or alt spellings."""
    name_lower = name.lower()
    for c in data:
        n = c.get("name", {})
        if (
            n.get("common",   "").lower() == name_lower or
            n.get("official", "").lower() == name_lower or
            any(a.lower() == name_lower for a in c.get("altSpellings", []))
        ):
            return c
    for c in data:
        n = c.get("name", {})
        if (
            name_lower in n.get("common",   "").lower() or
            name_lower in n.get("official", "").lower()
        ):
            return c
    return None


# ---------------------------------------------------------------------------
# Curated images — hand-picked Unsplash photos, 3 distinct subjects each
# ---------------------------------------------------------------------------

COUNTRY_IMAGES: dict[str, list[str]] = {
    "Japan": [
        "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=1200&q=80",
        "https://images.unsplash.com/photo-1492571350019-22de08371fd3?w=800&q=80",
        "https://images.unsplash.com/photo-1480796927426-f609979314bd?w=800&q=80",
    ],
    "Brazil": [
        "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=1200&q=80",
        "https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?w=800&q=80",
        "https://images.unsplash.com/photo-1518639192441-8fce0a366e2e?w=800&q=80",
    ],
    "India": [
        "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&q=80",
        "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&q=80",
        "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=800&q=80",
    ],
    "Germany": [
        "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1200&q=80",
        "https://images.unsplash.com/photo-1554072675-66db59dba46f?w=800&q=80",
        "https://images.unsplash.com/photo-1449452198679-05c7fd30f416?w=800&q=80",
    ],
    "Nigeria": [
        "https://images.unsplash.com/photo-1555990793-da11153b2473?w=1200&q=80",
        "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=800&q=80",
        "https://images.unsplash.com/photo-1570637093408-8d9949f5b699?w=800&q=80",
    ],
    "France": [
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200&q=80",
        "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800&q=80",
        "https://images.unsplash.com/photo-1431274172761-fca41d930114?w=800&q=80",
    ],
    "Australia": [
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&q=80",
        "https://images.unsplash.com/photo-1529108190281-9a4f620bc2d8?w=800&q=80",
        "https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?w=800&q=80",
    ],
    "South Korea": [
        "https://images.unsplash.com/photo-1538669715315-155098f0fb1d?w=1200&q=80",
        "https://images.unsplash.com/photo-1617469767053-d3b523a0b982?w=800&q=80",
        "https://images.unsplash.com/photo-1583431978668-c3e0f7ba8503?w=800&q=80",
    ],
    "Mexico": [
        "https://images.unsplash.com/photo-1518638150340-f706e86654de?w=1200&q=80",
        "https://images.unsplash.com/photo-1585464231875-d9ef1f5ad396?w=800&q=80",
        "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=800&q=80",
    ],
    "South Africa": [
        "https://images.unsplash.com/photo-1576485375217-d6a95e34d043?w=1200&q=80",
        "https://images.unsplash.com/photo-1521618755572-156ae0cdd74d?w=800&q=80",
        "https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=800&q=80",
    ],
    "Indonesia": [
        "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=1200&q=80",
        "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=800&q=80",
        "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&q=80",
    ],
    "Argentina": [
        "https://images.unsplash.com/photo-1589909202802-8f4aadce1849?w=1200&q=80",
        "https://images.unsplash.com/photo-1612294037637-ec400ca7fc0e?w=800&q=80",
        "https://images.unsplash.com/photo-1567763914977-02dc2cb2e5df?w=800&q=80",
    ],
    "Egypt": [
        "https://images.unsplash.com/photo-1539768942893-daf53e448371?w=1200&q=80",
        "https://images.unsplash.com/photo-1580418827493-f2b22c0a76cb?w=800&q=80",
        "https://images.unsplash.com/photo-1601921004897-b7d582002468?w=800&q=80",
    ],
    "Iceland": [
        "https://images.unsplash.com/photo-1531168556467-80aace0d0144?w=1200&q=80",
        "https://images.unsplash.com/photo-1504893524553-b855bce32c67?w=800&q=80",
        "https://images.unsplash.com/photo-1476610182048-b716b8518aae?w=800&q=80",
    ],
    "Thailand": [
        "https://images.unsplash.com/photo-1528181304800-259b08848526?w=1200&q=80",
        "https://images.unsplash.com/photo-1506665531195-3566af2b4dfa?w=800&q=80",
        "https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=800&q=80",
    ],
    "Norway": [
        "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=1200&q=80",
        "https://images.unsplash.com/photo-1601134467661-3d775b999c9b?w=800&q=80",
        "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800&q=80",
    ],
    "Kenya": [
        "https://images.unsplash.com/photo-1547970810-dc1eac37d174?w=1200&q=80",
        "https://images.unsplash.com/photo-1489392191049-fc10c97e64b6?w=800&q=80",
        "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?w=800&q=80",
    ],
    "Canada": [
        "https://images.unsplash.com/photo-1517935706615-2717063c2225?w=1200&q=80",
        "https://images.unsplash.com/photo-1569681157854-bb4d04a24d9a?w=800&q=80",
        "https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=800&q=80",
    ],
    "Portugal": [
        "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&q=80",
        "https://images.unsplash.com/photo-1513735539092-fe0b8a76c7e6?w=800&q=80",
        "https://images.unsplash.com/photo-1548707309-dcebeab9ea9b?w=800&q=80",
    ],
    "Chile": [
        "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=1200&q=80",
        "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=800&q=80",
        "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=800&q=80",
    ],
}


# ---------------------------------------------------------------------------
# Fun facts
# ---------------------------------------------------------------------------

FUN_FACTS: dict[str, list[str]] = {
    "Japan":        ["Home to the world's oldest company, Kongo Gumi, founded in 578 AD", "Has more vending machines per capita than any other country", "Cherry blossom (Sakura) season lasts only about 2 weeks each year"],
    "Brazil":       ["Has the largest rainforest in the world — the Amazon", "Hosts the world's biggest carnival festival in Rio de Janeiro", "Brazil is the only country in South America that speaks Portuguese"],
    "India":        ["Home to the world's largest democracy with 1.4 billion people", "Chess was invented in India around 600 AD", "About 40% of the population is vegetarian — the highest proportion worldwide"],
    "Germany":      ["Has over 1,500 different types of beer brewed nationwide", "Home to the world's first printed book — the Gutenberg Bible (1455)", "Germany has 20,000 castles and castle ruins — more than any other country"],
    "Nigeria":      ["Africa's most populous nation and largest economy", "Has over 500 ethnic groups and languages", "Nollywood is the world's second-largest film industry by volume"],
    "France":       ["The most visited country in the world, receiving 90M+ tourists per year", "France has won the most Nobel Prizes in Literature of any country", "The Louvre is the world's most visited art museum"],
    "Australia":    ["Has the world's longest fence — the Dingo Fence at 5,614 km", "More kangaroos than humans live in Australia", "The Great Barrier Reef is the largest living structure on Earth"],
    "South Korea":  ["Has the world's fastest average internet speeds", "K-pop is a multi-billion dollar global industry", "South Korea has the world's highest percentage of university graduates"],
    "Mexico":       ["Home to the world's smallest volcano — Cuexcomate at just 13 m tall", "Chocolate, tomatoes and chili peppers all originate from Mexico", "Mexico City is built on an ancient Aztec lake bed and sinks ~10 cm per year"],
    "South Africa": ["Has 11 official languages — the most of any country", "Home to the world's largest diamond mine", "Nelson Mandela served 27 years in prison before becoming president"],
    "Indonesia":    ["World's largest archipelago with over 17,000 islands", "Has the world's fourth-largest population", "Home to Rafflesia arnoldii — the world's largest individual flower"],
    "Argentina":    ["Invented the ballpoint pen and fingerprinting", "Has the highest literacy rate in South America at 99%", "Argentina has won the FIFA World Cup 3 times"],
    "Egypt":        ["Home to the only surviving ancient wonder — the Great Pyramid of Giza", "The Nile is the world's longest river at 6,650 km", "Ancient Egypt invented paper, ink, and the first 365-day calendar"],
    "Iceland":      ["Has the world's oldest parliament — the Althing, established in 930 AD", "Runs almost entirely on renewable geothermal and hydro energy", "Has no mosquitoes — too cold for them to complete their life cycle"],
    "Thailand":     ["Has the world's largest solid gold Buddha statue", "Never been colonised by a European power", "Bangkok holds the record for the world's longest official city name"],
    "Norway":       ["Has the world's longest road tunnel — Lærdal Tunnel at 24.5 km", "Invented the cheese slicer, aerosol can, and Bluetooth", "Ranks #1 on the UN Human Development Index consistently"],
    "Kenya":        ["Home to the Great Rift Valley, one of Earth's great geological wonders", "Kenyan runners have dominated Olympic distance running for decades", "The Maasai Mara hosts the world's greatest annual wildlife migration"],
    "Canada":       ["Has the longest coastline in the world at 202,080 km", "Invented basketball, insulin, and the telephone", "Is home to 20% of all the world's fresh water"],
    "Portugal":     ["Oldest nation-state in Europe, with borders unchanged since 1139", "Invented the egg tart (Pastel de Nata), now enjoyed worldwide", "Portuguese is the 6th most spoken language in the world"],
    "Chile":        ["The world's longest country from north to south at 4,300 km", "Home to the Atacama Desert — the driest non-polar desert on Earth", "Chile produces roughly one-third of the world's copper"],
}

DEFAULT_FACTS = ["A fascinating country with a rich culture and history."]

# Famous dishes to try (3 per country) — travel-guide content, not in any data table
FAMOUS_FOODS: dict[str, list[str]] = {
    "Japan":        ["Sushi", "Ramen", "Tempura"],
    "Brazil":       ["Feijoada", "Pão de Queijo", "Brigadeiro"],
    "India":        ["Biryani", "Masala Dosa", "Butter Chicken"],
    "Germany":      ["Bratwurst", "Schnitzel", "Pretzels"],
    "Nigeria":      ["Jollof Rice", "Suya", "Pounded Yam"],
    "France":       ["Croissant", "Coq au Vin", "Crème Brûlée"],
    "Australia":    ["Meat Pie", "Vegemite Toast", "Lamington"],
    "South Korea":  ["Kimchi", "Bibimbap", "Korean BBQ"],
    "Mexico":       ["Tacos", "Mole", "Tamales"],
    "South Africa": ["Bobotie", "Biltong", "Bunny Chow"],
    "Indonesia":    ["Nasi Goreng", "Satay", "Rendang"],
    "Argentina":    ["Asado", "Empanadas", "Dulce de Leche"],
    "Egypt":        ["Koshari", "Ful Medames", "Molokhia"],
    "Iceland":      ["Skyr", "Lamb Soup", "Rye Bread"],
    "Thailand":     ["Pad Thai", "Tom Yum", "Green Curry"],
    "Norway":       ["Salmon", "Brunost (Brown Cheese)", "Lefse"],
    "Kenya":        ["Ugali", "Nyama Choma", "Sukuma Wiki"],
    "Canada":       ["Poutine", "Maple Syrup", "Butter Tarts"],
    "Portugal":     ["Pastéis de Nata", "Bacalhau", "Francesinha"],
    "Chile":        ["Empanadas", "Pastel de Choclo", "Completo"],
}

# Best time to visit + short climate note — travel-guide content
BEST_TIME: dict[str, str] = {
    "Japan":        "Mar–May (cherry blossoms) and Oct–Nov (autumn leaves). Mild and dry.",
    "Brazil":       "Sep–Nov — warm, fewer crowds, before peak summer rains.",
    "India":        "Oct–Mar — cool, dry season; avoids the intense summer heat and monsoon.",
    "Germany":      "May–Sep — warm summers, festivals and long daylight hours.",
    "Nigeria":      "Nov–Mar — the dry season, cooler and easier for travel.",
    "France":       "Apr–Jun and Sep–Oct — pleasant weather without summer crowds.",
    "Australia":    "Sep–Nov and Mar–May — mild temperatures across most regions.",
    "South Korea":  "Apr–Jun (spring blossoms) and Sep–Nov (crisp autumn).",
    "Mexico":       "Dec–Apr — dry season with warm, sunny days.",
    "South Africa": "May–Sep — dry winter, ideal for safaris and wildlife.",
    "Indonesia":    "Apr–Oct — the dry season, best for beaches and temples.",
    "Argentina":    "Sep–Nov and Mar–May — mild spring and autumn weather.",
    "Egypt":        "Oct–Apr — cooler temperatures for exploring the pyramids.",
    "Iceland":      "Jun–Aug (midnight sun) or Sep–Mar (northern lights).",
    "Thailand":     "Nov–Mar — cool, dry season with sunny skies.",
    "Norway":       "Jun–Aug (fjords, midnight sun) or Nov–Mar (aurora).",
    "Kenya":        "Jun–Oct — dry season and the great wildebeest migration.",
    "Canada":       "Jun–Sep (warm summers) or Dec–Mar (winter sports).",
    "Portugal":     "Mar–May and Sep–Oct — warm, sunny, fewer tourists.",
    "Chile":        "Oct–Mar — spring to autumn across its long geography.",
}

# Major cities beyond the capital (3 per country)
MAJOR_CITIES: dict[str, list[str]] = {
    "Japan":        ["Osaka", "Kyoto", "Yokohama"],
    "Brazil":       ["São Paulo", "Rio de Janeiro", "Salvador"],
    "India":        ["Mumbai", "Bangalore", "Kolkata"],
    "Germany":      ["Munich", "Hamburg", "Frankfurt"],
    "Nigeria":      ["Lagos", "Kano", "Ibadan"],
    "France":       ["Marseille", "Lyon", "Nice"],
    "Australia":    ["Sydney", "Melbourne", "Brisbane"],
    "South Korea":  ["Busan", "Incheon", "Daegu"],
    "Mexico":       ["Guadalajara", "Monterrey", "Cancún"],
    "South Africa": ["Cape Town", "Johannesburg", "Durban"],
    "Indonesia":    ["Surabaya", "Bandung", "Bali (Denpasar)"],
    "Argentina":    ["Córdoba", "Rosario", "Mendoza"],
    "Egypt":        ["Alexandria", "Giza", "Luxor"],
    "Iceland":      ["Akureyri", "Hafnarfjörður", "Keflavík"],
    "Thailand":     ["Chiang Mai", "Phuket", "Pattaya"],
    "Norway":       ["Bergen", "Trondheim", "Stavanger"],
    "Kenya":        ["Mombasa", "Kisumu", "Nakuru"],
    "Canada":       ["Toronto", "Montreal", "Vancouver"],
    "Portugal":     ["Porto", "Braga", "Faro"],
    "Chile":        ["Valparaíso", "Concepción", "Antofagasta"],
}

TAGLINES: dict[str, str] = {
    "Japan":        "Ancient temples meet neon-lit cities. From Mount Fuji to Tokyo's buzzing streets — unlike anywhere on Earth.",
    "Brazil":       "The Amazon, Carnival and Rio. The world's most vibrant and diverse nation.",
    "India":        "A billion stories, the Taj Mahal, and spices that changed the world.",
    "Germany":      "Castles, culture and 1,500 types of beer. The powerhouse heart of Europe.",
    "Nigeria":      "Africa's most populous nation — vibrant, powerful and rising fast.",
    "France":       "The Eiffel Tower, world-class cuisine and 90 million visitors a year.",
    "Australia":    "The Opera House, the Outback and the world's greatest living reef.",
    "South Korea":  "K-pop, ancient palaces and the fastest internet speeds on Earth.",
    "Mexico":       "Chichen Itza, mariachi music and the birthplace of chocolate.",
    "South Africa": "Table Mountain, big five safaris and eleven official languages.",
    "Indonesia":    "17,000 islands, Bali's temples and the world's largest archipelago.",
    "Argentina":    "Tango, Patagonia's wilds and three FIFA World Cup titles.",
    "Egypt":        "The Great Pyramids, the Nile and 5,000 years of civilisation.",
    "Iceland":      "Waterfalls, northern lights and the world's oldest parliament.",
    "Thailand":     "Golden temples, tropical beaches and the world's best street food.",
    "Norway":       "Dramatic fjords, northern lights and the happiest people on Earth.",
    "Kenya":        "The Maasai Mara, Great Rift Valley and the greatest migration.",
    "Canada":       "The Rockies, Niagara Falls and the world's longest coastline.",
    "Portugal":     "Fado music, egg tarts and the oldest national borders in Europe.",
    "Chile":        "The Atacama Desert, Torres del Paine and a third of global copper.",
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "World Explorer API is running",
        "endpoints": {
            "all_countries":  "/countries/all",
            "single_country": "/country/{name}",
            "search":         "/search/{query}",
        },
    }


@app.get("/countries/all")
@limiter.limit("30/minute")
async def get_all_countries(request: Request):
    """Return summary list of all 20 curated countries."""
    all_data = await fetch_all_raw()
    results  = []

    for display_name in COUNTRY_IMAGES:
        c = find_country(all_data, display_name)
        if not c:
            continue
        s = STATIC.get(display_name, {})
        results.append({
            "name":        display_name,
            "flag_emoji":  c.get("flag", ""),
            "flag_png":    s.get("flag_png", ""),
            "region":      c.get("region", ""),
            "subregion":   c.get("subregion", ""),
            "capital":     (c.get("capital") or ["N/A"])[0],
            "population":  s.get("population", 0),
            "cover_image": COUNTRY_IMAGES[display_name][0],
            "tagline":     TAGLINES.get(display_name, "Explore this incredible country."),
        })

    return results


@app.get("/country/{name}")
@limiter.limit("60/minute")
async def get_country(name: str, request: Request):
    """Return full data for a single country."""
    safe_name = validate_country_name(name)
    all_data  = await fetch_all_raw()
    c         = find_country(all_data, safe_name)

    if not c:
        raise HTTPException(status_code=404, detail=f"Country '{safe_name}' not found.")

    api_common   = c["name"].get("common", safe_name)
    static_key   = resolve_static_key(api_common)
    s            = STATIC.get(static_key, {})

    if not s:
        static_key = resolve_static_key(safe_name)
        s          = STATIC.get(static_key, {})

    display_name = static_key if static_key in STATIC else api_common
    idd          = c.get("idd") or {}
    pop          = s.get("population", c.get("population", 0))
    area         = c.get("area") or 0

    return {
        # Identity
        "name":               display_name,
        "official":           c["name"].get("official", display_name),
        "native_name":        s.get("native_name", display_name),
        "tagline":            TAGLINES.get(display_name, "Explore this incredible country."),
        "flag_emoji":         c.get("flag", ""),
        "flag_svg":           s.get("flag_svg", ""),
        "flag_png":           s.get("flag_png", ""),
        "coat_of_arms":       "",
        "alt_spellings":      c.get("altSpellings", []),

        # Geography
        "capital":            (c.get("capital") or ["N/A"])[0],
        "capital_latlng":     s.get("capital_latlng", []),
        "region":             c.get("region", "N/A"),
        "subregion":          c.get("subregion", "N/A"),
        "continents":         s.get("continents", [c.get("region", "")]),
        "latlng":             c.get("latlng", []),
        "landlocked":         c.get("landlocked", False),
        "borders":            c.get("borders", []),
        "area":               area,

        # Population
        "population":         pop,
        "population_density": round(pop / area, 1) if area > 0 else 0,

        # Culture
        "currencies":         build_currencies(c.get("currencies") or {}),
        "languages":          list((c.get("languages") or {}).values()),
        "timezones":          s.get("timezones", ["N/A"]),
        "calling_code":       build_calling_code(idd) or "N/A",
        "drives_on":          s.get("drives_on", "N/A"),
        "car_signs":          s.get("car_signs", []),
        "tld":                c.get("tld", []),
        "start_of_week":      s.get("start_of_week", "N/A"),
        "demonyms":           (c.get("demonyms") or {}).get("eng", {}),

        # Status
        "independent":        s.get("independent", c.get("independent", False)),
        "un_member":          s.get("un_member", c.get("unMember", False)),

        # Extra
        "google_maps":        s.get("google_maps", ""),
        "gini":               s.get("gini", {}),

        # Curated
        "images":    COUNTRY_IMAGES.get(display_name, COUNTRY_IMAGES.get(static_key, [])),
        "fun_facts": FUN_FACTS.get(display_name, FUN_FACTS.get(static_key, DEFAULT_FACTS)),

        # Travel-guide extras (sidebar) — deliberately different from the data tables
        "famous_foods": FAMOUS_FOODS.get(display_name, FAMOUS_FOODS.get(static_key, [])),
        "best_time":    BEST_TIME.get(display_name, BEST_TIME.get(static_key, "")),
        "major_cities": MAJOR_CITIES.get(display_name, MAJOR_CITIES.get(static_key, [])),
    }


@app.get("/search/{query}")
@limiter.limit("30/minute")
async def search_countries(query: str, request: Request):
    """Return up to 6 matching countries for autocomplete.

    Only searches within the 20 curated countries this app supports —
    not the full global dataset — so results stay relevant to what the
    rest of the app (cover photos, fun facts, etc.) actually has data for.
    """
    safe_query  = validate_country_name(query)

    # Require at least 2 characters for search — a single letter matches
    # too many countries to be a useful autocomplete result.
    if len(safe_query) < 2:
        return []

    all_data    = await fetch_all_raw()
    query_lower = safe_query.lower()

    # Restrict the search space to our 20 supported countries only
    supported_names = set(COUNTRY_IMAGES.keys())
    curated_data = [c for c in all_data if c["name"].get("common", "") in supported_names]

    matches = [
        c for c in curated_data
        if query_lower in c["name"].get("common",   "").lower()
        or query_lower in c["name"].get("official", "").lower()
    ][:6]

    return [
        {
            "name":    c["name"].get("common", ""),
            "flag":    c.get("flag", ""),
            "region":  c.get("region", ""),
            "capital": (c.get("capital") or ["N/A"])[0],
        }
        for c in matches
    ]

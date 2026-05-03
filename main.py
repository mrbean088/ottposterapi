import re
import json
from datetime import datetime

from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright

app = FastAPI(title="OTT Image Extractor API — Render Edition")

UPDATES = "@SteveBotz"

# ── ZEE5 Headers ─────────────────────────────────────────────────────────────
ZEE5_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Chromium";v="139", "Google Chrome";v="139", "Not?A_Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com/",
}


# ═══════════════════════════════════════════════════════════════════════════════
# ZEE5 SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_zee5(url: str) -> dict:
    """Fetch and extract data from ZEE5 URL using Playwright."""

    # Extract content ID from URL for fallback
    content_id = None
    id_match = re.search(r'/(0-\d+-[a-z0-9]+)/?$', url) or re.search(r'/(0-\d+-[a-z0-9]+)(?:\?|/|$)', url)
    if id_match:
        content_id = id_match.group(1)

    soup = None

    # ── METHOD 1: Playwright (best results) ─────────────────────────────────
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context(
                user_agent=ZEE5_HEADERS["User-Agent"]
            )
            page = await context.new_page()

            # Stealth: hide webdriver
            await page.evaluate(
                "() => { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}) }"
            )

            await page.goto(url, timeout=60000)
            html = await page.content()
            await browser.close()
            soup = BeautifulSoup(html, "html.parser")
    except Exception:
        soup = None

    # ── METHOD 2: Extract from videoObject JSON ─────────────────────────────
    if soup:
        script_tag = soup.find("script", id="videoObject")
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)

                # Title
                title = data.get("name", [{}])[0].get("@value", "")
                if not title:
                    title = data.get("name", "")

                # Release Year
                release_date = data.get("uploadDate", "")
                year = None
                try:
                    year = datetime.strptime(release_date, "%Y-%m-%d").year
                except Exception:
                    year = None

                # Poster
                poster_url = ""
                thumbs = data.get("thumbnailUrl", [])
                if thumbs and isinstance(thumbs, list) and len(thumbs) > 0:
                    poster_url = thumbs[0]
                elif isinstance(thumbs, str):
                    poster_url = thumbs

                if poster_url:
                    match = re.search(r"(\/resources\/.*)", poster_url)
                    if match:
                        clean_poster = f"https://akamaividz2.zee5.com/image/upload{match.group(1)}"
                    else:
                        clean_poster = poster_url

                    return {
                        "success": True,
                        "ott": "ZEE5",
                        "url": url,
                        "title": title or "Unknown Title",
                        "year": year,
                        "images": {
                            "portrait": clean_poster,
                        },
                        "api_update": UPDATES,
                    }
            except Exception:
                pass

    # ── METHOD 3: Extract from meta tags ────────────────────────────────────
    if soup:
        og_title = soup.find("meta", property="og:title")
        title = og_title.get("content", "") if og_title else ""

        og_image = soup.find("meta", property="og:image")
        poster_url = og_image.get("content", "") if og_image else ""

        if title and poster_url:
            year_match = re.search(r'(\d{4})', title)
            year = year_match.group(1) if year_match else None

            return {
                "success": True,
                "ott": "ZEE5",
                "url": url,
                "title": title,
                "year": year,
                "images": {
                    "portrait": poster_url,
                },
                "api_update": UPDATES,
            }

    # ── METHOD 4: Direct CDN construction from content ID ───────────────────
    if content_id:
        slug_match = re.search(r'/details/([^/]+)/', url)
        title = slug_match.group(1).replace('-', ' ').title() if slug_match else "ZEE5 Content"

        return {
            "success": True,
            "ott": "ZEE5",
            "url": url,
            "title": title,
            "year": None,
            "images": {
                "landscape": f"https://akamaividz2.zee5.com/image/upload/resources/{content_id}/list/1920x1080.jpg",
                "portrait": f"https://akamaividz2.zee5.com/image/upload/resources/{content_id}/portrait/260x260.jpg",
            },
            "api_update": UPDATES,
        }

    raise ValueError("Could not extract ZEE5 data. The page may be blocked or the URL format is unsupported.")


# ═══════════════════════════════════════════════════════════════════════════════
# BMS SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_bms(url: str) -> dict:
    """Fetch title, year, and landscape poster from BookMyShow using Playwright."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # Stealth: hide webdriver
        await page.evaluate(
            "() => { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}) }"
        )

        await page.goto(url, timeout=60000)
        content = await page.content()
        await browser.close()

    soup = BeautifulSoup(content, "html.parser")

    # Extract title
    og_title = soup.find("meta", property="og:title")
    title_text = og_title.get("content") if og_title else "Unknown Title"

    # Extract year from title
    year_match = re.search(r"\((\d{4})\)", title_text)
    year = year_match.group(1) if year_match else None

    # Clean title - remove year from title
    clean_title = re.sub(r"\s*\(\d{4}\)", "", title_text).strip() if year else title_text.strip()

    # Extract landscape poster
    og_image = soup.find("meta", property="og:image")
    poster_url = og_image.get("content") if og_image else None

    return {
        "success": True,
        "ott": "BookMyShow",
        "url": url,
        "title": clean_title,
        "year": year,
        "images": {
            "landscape": poster_url,
        } if poster_url else {},
        "api_update": UPDATES,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "api": "OTT Image Extractor API — Render Edition",
        "status": "Running Smoothly 🚀",
        "endpoints": {
            "zee5": "/ott/zee5?url=https://www.zee5.com/...",
            "bms": "/ott/bms?url=https://in.bookmyshow.com/...",
        },
        "api_updates": UPDATES,
    }


@app.get("/ott/zee5")
async def zee5_extractor(
    url: str = Query(None, description="ZEE5 movie/series URL")
):
    """
    Extract portrait poster, title & year from a ZEE5 URL using Playwright.

    Example:
        /ott/zee5?url=https://www.zee5.com/movies/details/assi/0-0-1z5946669
    """
    if not url:
        return JSONResponse({
            "success": False,
            "error": "Missing url parameter. Usage: /ott/zee5?url=<zee5_url>",
            "api_update": UPDATES,
        }, status_code=400)

    if "zee5.com" not in url:
        return JSONResponse({
            "success": False,
            "error": "Invalid URL. Only ZEE5 URLs are supported.",
            "api_update": UPDATES,
        }, status_code=400)

    try:
        result = await _fetch_zee5(url)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Failed to extract data: {str(e)}",
            "api_update": UPDATES,
        }, status_code=500)


@app.get("/ott/bms")
async def bms_extractor(
    url: str = Query(None, description="BookMyShow movie/series URL")
):
    """
    Extract landscape poster, title & year from a BookMyShow URL using Playwright.

    Example:
        /ott/bms?url=https://in.bookmyshow.com/...
    """
    if not url:
        return JSONResponse({
            "success": False,
            "error": "Missing url parameter. Usage: /ott/bms?url=<bms_url>",
            "api_update": UPDATES,
        }, status_code=400)

    if "bookmyshow.com" not in url:
        return JSONResponse({
            "success": False,
            "error": "Invalid URL. Only BookMyShow URLs are supported.",
            "api_update": UPDATES,
        }, status_code=400)

    try:
        result = await _fetch_bms(url)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Failed to extract data: {str(e)}",
            "api_update": UPDATES,
        }, status_code=500)

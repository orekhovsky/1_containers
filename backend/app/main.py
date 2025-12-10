import os
import secrets
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import create_short_link, get_original_url, count_links, get_short_code_by_url

# === Логирование ===
LOG_DIR = os.getenv("LOG_DIR")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=f"{LOG_DIR}/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("url_shortener")

# === Конфиг ===
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
if not PUBLIC_BASE_URL:
    raise ValueError("PUBLIC_BASE_URL environment variable is required")
PUBLIC_BASE_URL = PUBLIC_BASE_URL.rstrip("/")

logger.info(f"Application starting with PUBLIC_BASE_URL={PUBLIC_BASE_URL}")

app = FastAPI(title="URL Shortener (DB)")

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application started")
    logger.info("Database connection will be established on first request")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ShortenRequest(BaseModel):
    url: str


def generate_short_code() -> str:
    return secrets.token_urlsafe(6)


@app.post("/shorten")
async def shorten_url(req: Request, request: ShortenRequest):
    url = request.url.strip()
    logger.info(f"Received shorten request for URL: {url}")
    
    if not url.startswith(("http://", "https://")):
        logger.warning(f"Invalid URL format: {url}")
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )

    existing_short_code = await get_short_code_by_url(url)
    if existing_short_code:
        short_url = f"{PUBLIC_BASE_URL}/{existing_short_code}"
        logger.info(f"URL already exists, returning existing short link: {existing_short_code} -> {url}")
        return {"short_code": existing_short_code, "short_url": short_url}

    attempts = 0
    for attempt in range(5):
        attempts = attempt + 1
        short_code = generate_short_code()
        logger.debug(f"Attempt {attempts}/5: Generated short_code: {short_code}")
        success = await create_short_link(short_code, url)
        if success:
            short_url = f"{PUBLIC_BASE_URL}/{short_code}"
            logger.info(f"Successfully created short link: {short_code} -> {url} (attempt {attempts})")
            return {"short_code": short_code, "short_url": short_url}
        else:
            logger.warning(f"Short code collision: {short_code} already exists, retrying...")
    
    logger.error(f"Failed to generate unique short code after {attempts} attempts for URL: {url}")
    raise HTTPException(status_code=500, detail="Failed to generate short code")


@app.get("/health")
async def health():
    logger.debug("Health check requested")
    try:
        total = await count_links()
        logger.debug(f"Health check: OK, stored_urls={total}")
        return {"status": "ok", "stored_urls": total}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    logger.info(f"Redirect request for short_code: {short_code}")
    long_url = await get_original_url(short_code)
    
    if not long_url:
        logger.warning(f"Short code not found: {short_code}")
        raise HTTPException(status_code=404, detail="Short code not found")

    logger.info(f"Redirecting {short_code} -> {long_url}")
    return RedirectResponse(url=long_url)
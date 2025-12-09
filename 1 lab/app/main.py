import os
import secrets
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# === Логирование ===
os.makedirs("/app/logs", exist_ok=True)
logging.basicConfig(
    filename="/app/logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === In-memory storage ===
url_store = {}

app = FastAPI(title="URL Shortener (In-Memory)")

class ShortenRequest(BaseModel):
    url: str

@app.post("/shorten")
async def shorten_url(request: ShortenRequest):
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    short_code = secrets.token_urlsafe(6)
    url_store[short_code] = url
    logging.info(f"Created: {short_code} -> {url}")
    return {"short_code": short_code, "short_url": f"http://localhost:8000/{short_code}"}

@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    long_url = url_store.get(short_code)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")
    logging.info(f"Redirecting {short_code} -> {long_url}")
    return RedirectResponse(url=long_url)

@app.get("/health")
async def health():
    return {"status": "ok", "stored_urls": len(url_store)}
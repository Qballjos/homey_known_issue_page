import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import init_db, SessionLocal
from app.seed import seed_database
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB schema is ready and optionally seed
    init_db()
    if settings.AUTO_SEED:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    yield
    # Shutdown: Clean up if needed


app = FastAPI(
    title=settings.APP_NAME,
    description="Official Known Issues and System Status Platform for Smart Home Ecosystems.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# Reverse proxy support (Traefik, Cloudflare Tunnel, Nginx Proxy Manager)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Rate limiting in-memory store for subscription and login
import time
from collections import defaultdict

RATE_LIMITS = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    now = time.time()

    # Rate limit subscriptions
    if path.endswith("/subscribe") and request.method == "POST":
        key = f"sub_{client_ip}"
        RATE_LIMITS[key] = [t for t in RATE_LIMITS[key] if now - t < 60]
        if len(RATE_LIMITS[key]) >= 15:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many subscription requests. Please wait a minute and try again."}
            )
        RATE_LIMITS[key].append(now)

    # Rate limit admin login attempts
    if path == "/admin/login" and request.method == "POST":
        key = f"login_{client_ip}"
        RATE_LIMITS[key] = [t for t in RATE_LIMITS[key] if now - t < 60]
        if len(RATE_LIMITS[key]) >= 8:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many login attempts. Please wait a minute before trying again."}
            )
        RATE_LIMITS[key].append(now)

    return await call_next(request)


# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Health Check Endpoint
@app.get("/health", tags=["Health"])
def health_check():
    db_status = "connected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app_name": settings.APP_NAME,
        "database": db_status,
    }


# Include Routers
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(api_router)

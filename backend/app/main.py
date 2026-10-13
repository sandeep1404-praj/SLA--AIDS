"""
ContentFlow AI — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.indexes import create_indexes
from app.api.routes import auth, articles, calendars, posts, dashboard, exports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await create_indexes()
    gemini_key = (settings.gemini_api_key or "").strip()
    if not gemini_key or gemini_key == "your_gemini_api_key":
        print("[WARN] GEMINI_API_KEY is not set — AI calendar generation will fail until backend/.env is configured")
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="ContentFlow AI API",
    description="Transform articles into 7-day social media content calendars using Google Gemini.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(calendars.router)
app.include_router(posts.router)
app.include_router(dashboard.router)
app.include_router(exports.router)


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "ContentFlow AI API", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}

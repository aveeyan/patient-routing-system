# app/main.py

"""FastAPI application for the AI-Powered Patient Triage Chatbot."""

# Standard Imports
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

# Third Party Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Local Imports
from app.api.routes.triage import router as triage_router
from app.api.routes.speech import router as speech_router
from ai.speech import _load_model
from core.config import settings
from core.logger import logger
from db.session import engine
from db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, clean up on shutdown."""
    logger.info("Starting up — creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Warm up the Whisper model so the first patient request isn't slow
    logger.info("Warming up Whisper model")
    await asyncio.get_event_loop().run_in_executor(None, _load_model)
    logger.info("Whisper model ready")

    yield
    logger.info("Shutting down")
    await engine.dispose()


app = FastAPI(
    title="Patient Triage Chatbot",
    description="AI-powered patient triage and routing system",
    version="0.0.1",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/templates/media"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triage_router, prefix="/triage", tags=["Triage"])
app.include_router(speech_router, prefix="/speech", tags=["Speech"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "patient-routing-system"}

# UI
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the chat interface."""
    index_path = TEMPLATES_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text())

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard interface."""
    dashboard_path = TEMPLATES_DIR / "dashboard.html"
    return HTMLResponse(content=dashboard_path.read_text())

"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from purisa.config.settings import get_settings
from purisa.database.connection import init_database
from purisa.api.routes import router
from purisa.services.scheduler import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Purisa Bot Detection API")

    # Initialize settings
    settings = get_settings()
    logger.info(f"Loaded settings: API running on {settings.api_host}:{settings.api_port}")

    # Initialize database
    try:
        init_database(settings.database_url)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Start background scheduler (optional - can be disabled for testing)
    # Uncomment to enable automatic background collection and analysis
    # global scheduler
    # scheduler = BackgroundScheduler()
    # scheduler.start()
    # logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down Purisa Bot Detection API")

    # Shutdown scheduler if running
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="Purisa Bot Detection API",
    description="Multi-platform social media bot detection system",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Purisa Bot Detection API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "api_prefix": "/api"
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "purisa.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

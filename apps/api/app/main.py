import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("=== Starting InsurTech API ===")

try:
    from app.config import get_settings
    settings = get_settings()
    logger.info(f"Settings loaded. environment={settings.environment}")
except Exception as e:
    logger.error(f"FATAL: Failed to load settings: {e}\n{traceback.format_exc()}")
    raise

try:
    from app.routers import articles, sources, auth, subscriptions, search, admin, verify, ingestion_logs
    logger.info("All routers imported successfully")
except Exception as e:
    logger.error(f"FATAL: Failed to import routers: {e}\n{traceback.format_exc()}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.environment != "test":
        try:
            from app.services.ingestion.scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Scheduler failed to start: {e}")
    yield
    # Shutdown
    if settings.environment != "test":
        try:
            from app.services.ingestion.scheduler import stop_scheduler
            stop_scheduler()
        except Exception:
            pass


app = FastAPI(
    title="InsurTech Intelligence API",
    description="The best insurtech newsletter platform — global news, AI-powered, personalized.",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = list({
    "http://localhost:3000",
    settings.app_url,
})
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(ingestion_logs.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

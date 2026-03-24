from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import articles, sources, auth, subscriptions, search, admin, verify, ingestion_logs
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.environment != "test":
        from app.services.ingestion.scheduler import start_scheduler
        start_scheduler()
    yield
    # Shutdown
    if settings.environment != "test":
        from app.services.ingestion.scheduler import stop_scheduler
        stop_scheduler()


app = FastAPI(
    title="InsurTech Intelligence API",
    description="The best insurtech newsletter platform — global news, AI-powered, personalized.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.app_url],
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

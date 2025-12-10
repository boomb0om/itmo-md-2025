from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import binance, news
from app.core.logging import get_logger
from app.database import connect_mongo, disconnect_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger = get_logger(__name__)
    # Startup
    await connect_mongo()
    await logger.info("Application started")
    yield
    # Shutdown
    await disconnect_mongo()
    await logger.info("Application stopped")


app = FastAPI(
    title="Crypto Data Collector",
    description="FastAPI application for collecting cryptocurrency price and news data",
    lifespan=lifespan,
)

app.include_router(binance.router, prefix="/api", tags=["binance"])
app.include_router(news.router, prefix="/api", tags=["news"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Crypto Data Collector API"}


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        from app.database import get_db

        db = get_db()
        db.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

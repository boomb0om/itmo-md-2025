from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from app.core.logging import get_logger
from app.database import connect_mongo, disconnect_mongo
from app.services.binance_service import fetch_klines
from app.services.news_service import fetch_news


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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {"message": "Crypto Data Collector API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint"""
    try:
        from app.database import get_db

        db = get_db()
        db.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/fetch-klines")
async def api_fetch_klines(
    symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100
) -> dict[str, Any]:
    """
    Fetch cryptocurrency candlestick data from Binance

    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
        limit: Number of candles to fetch (max 1000)

    Returns:
        Status and count of fetched klines
    """
    logger = get_logger(__name__)
    try:
        result = await fetch_klines(symbol=symbol, interval=interval, limit=limit)
        return result
    except Exception as e:
        await logger.error(f"Error in fetch_klines endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/fetch-news")
async def api_fetch_news(source: str = "cryptopanic", limit: int = 50) -> dict[str, Any]:
    """
    Fetch cryptocurrency news from RSS feeds (mock implementation)

    Args:
        source: News source
        limit: Number of articles to fetch

    Returns:
        Status, count, and list of fetched news articles
    """
    logger = get_logger(__name__)
    try:
        result = await fetch_news(source=source, limit=limit)
        return result
    except Exception as e:
        await logger.error(f"Error in fetch_news endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

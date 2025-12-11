from typing import Any

from fastapi import APIRouter

from app.service.binance_service import fetch_klines

router = APIRouter(prefix="/binance")


@router.get("/fetch-klines")
async def api_fetch_klines(
    symbol: str = "BTCUSDT", interval: str = "5m", limit: int = 100
) -> dict[str, Any]:
    """Return kline data for the given symbol, interval, and limit."""
    result = await fetch_klines(symbol=symbol, interval=interval, limit=limit)
    return result

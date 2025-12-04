from datetime import datetime
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.database import get_db


def save_request_to_mongo(
    url: str,
    request: dict,
    response: dict | str,
    status_code: int,
    created_at: datetime,
    update_at: datetime,
):
    """
    Save request and response to MongoDB

    :param url:
    :param request:
    :param response:
    :param status_code:
    :param created_at:
    :param update_at:
    :return:
    """
    url_masked = url.split("?")[0]

    db = get_db()
    collection = db["requests_log"]
    collection.insert_one(
        {
            "url": url_masked,
            "request": request,
            "response": response,
            "status_code": status_code,
            "created_at": created_at,
            "update_at": update_at,
        }
    )


async def fetch_klines(symbol: str, interval: str, limit: int = 100) -> dict[str, Any]:
    """
    Fetch candlestick data from Binance API

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Time interval (1m, 5m, 1h, 1d, etc.)
        limit: Number of candles (max 1000)

    Returns:
        Dictionary with klines data
    """
    logger = get_logger(__name__)
    settings = get_settings()
    url = f"{settings.binance.base_url}/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}

    await logger.info(f"Sending request to Binance API for {symbol}")
    created_at = datetime.now()

    try:
        async with httpx.AsyncClient(timeout=settings.binance.timeout) as http_client:
            response = await http_client.get(url, params=params)
            response.raise_for_status()

        updated_at = datetime.now()
        data = response.json()

        await logger.info("Saving request to MongoDB")
        save_request_to_mongo(
            url,
            params,
            data,
            response.status_code,
            created_at,
            updated_at,
        )

        await logger.info(f"Successfully fetched {len(data)} klines for {symbol}")

        return {
            "binance_response_status": response.status_code,
            "binance_response_data_size": len(data),
        }

    except httpx.HTTPStatusError as e:
        updated_at = datetime.now()
        await logger.error(f"Binance API error: {e.response.status_code} - {e.response.text}")

        await logger.info("Saving failed request to MongoDB")
        save_request_to_mongo(
            url,
            params,
            {"error": str(e), "text": e.response.text},
            e.response.status_code,
            created_at,
            updated_at,
        )

        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching data from Binance API: {e.response.text}",
        ) from e

    except Exception as e:
        updated_at = datetime.now()
        await logger.error(f"Error fetching klines: {e}")

        await logger.info("Saving failed request to MongoDB")
        save_request_to_mongo(
            url,
            params,
            {"error": str(e)},
            500,
            created_at,
            updated_at,
        )

        raise HTTPException(status_code=500, detail=f"Error fetching klines: {e!s}") from e

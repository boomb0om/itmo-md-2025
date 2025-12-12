from datetime import datetime
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.database import get_db


async def fetch_klines(symbol: str, interval: str, limit: int = 100) -> dict[str, Any]:
    """Collect klines from Binance, dedupe by open_time and persist to MongoDB."""
    logger = get_logger(__name__)
    settings = get_settings()
    url = f"{settings.binance.base_url}/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}

    await logger.info(f"Sending request to Binance API for {symbol}")

    try:
        async with httpx.AsyncClient(timeout=settings.binance.timeout) as http_client:
            response = await http_client.get(url, params=params)
            response.raise_for_status()

        data = response.json()

        db = get_db()
        collection = db["binance_data"]

        klines_docs = []
        for kline in data:
            open_time = datetime.fromtimestamp(kline[0] / 1000)
            doc = {
                "symbol": symbol.upper(),
                "interval": interval,
                "open_time": open_time,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": datetime.fromtimestamp(kline[6] / 1000),
                "quote_asset_volume": float(kline[7]),
                "number_of_trades": int(kline[8]),
                "taker_buy_base_asset_volume": float(kline[9]),
                "taker_buy_quote_asset_volume": float(kline[10]),
                "created_at": datetime.now(),
            }
            klines_docs.append(doc)

        new_docs = []
        if klines_docs:
            # Get existing (interval, open_time) pairs to avoid duplicates
            open_times = [doc["open_time"] for doc in klines_docs]
            existing_records = collection.find(
                {"interval": interval, "open_time": {"$in": open_times}},
                {"interval": 1, "open_time": 1},
            )
            # Create set of (interval, open_time) tuples
            existing_pairs = set(
                (record["interval"], record["open_time"]) for record in existing_records
            )

            # Filter out klines that already exist
            new_docs = [
                doc
                for doc in klines_docs
                if (doc["interval"], doc["open_time"]) not in existing_pairs
            ]

            if new_docs:
                try:
                    collection.insert_many(new_docs, ordered=False)
                    await logger.info(f"Inserted {len(new_docs)} new klines")
                except Exception as e:
                    # Handle potential duplicate key errors (race condition)
                    await logger.warning(f"Some klines may already exist: {e}")
            else:
                await logger.info("All klines already exist in database")

        total_fetched = len(klines_docs)
        item_count = len(new_docs)
        skipped = total_fetched - item_count

        msg = (
            f"Fetched {total_fetched} klines for {symbol}, "
            f"added {item_count} new, skipped {skipped} duplicates"
        )
        await logger.info(msg)

        return {
            "binance_response_status": response.status_code,
            "binance_response_data_size": len(data),
            "message": msg,
        }

    except httpx.HTTPStatusError as e:
        await logger.error(f"Binance API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching data from Binance API: {e.response.text}",
        ) from e

    except Exception as e:
        await logger.error(f"Error fetching klines: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching klines: {e!s}") from e

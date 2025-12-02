import httpx
from datetime import datetime
from typing import List, Dict, Any

from src.core.settings import binance_settings
from src.core.logging import logger
from src.database import get_db


async def fetch_klines(
    symbol: str,
    interval: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Fetch candlestick data from Binance API
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Time interval (1m, 5m, 1h, 1d, etc.)
        limit: Number of candles (max 1000)
    
    Returns:
        Dictionary with status and data
    """
    url = f"{binance_settings.base_url}/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval.upper(),
        "limit": min(limit, 1000)
    }
    
    created_at = datetime.utcnow()
    
    try:
        async with httpx.AsyncClient(timeout=binance_settings.timeout) as http_client:
            response = await http_client.get(url, params=params)
            response.raise_for_status()
            klines_data = response.json()
        
        updated_at = datetime.utcnow()
        
        # Process klines data
        processed_data = []
        for kline in klines_data:
            processed_kline = {
                "symbol": symbol.upper(),
                "interval": interval.upper(),
                "open_time": datetime.fromtimestamp(kline[0] / 1000),
                "close_time": datetime.fromtimestamp(kline[6] / 1000),
                "open_price": float(kline[1]),
                "high_price": float(kline[2]),
                "low_price": float(kline[3]),
                "close_price": float(kline[4]),
                "volume": float(kline[5]),
                "quote_volume": float(kline[7]),
                "trades_count": int(kline[8]),
                "taker_buy_base_volume": float(kline[9]),
                "taker_buy_quote_volume": float(kline[10]),
                "fetched_at": datetime.utcnow()
            }
            processed_data.append(processed_kline)
        
        # Save request/response log
        db = get_db()
        requests_collection = db["requests_log"]
        requests_collection.insert_one({
            "url": url,
            "request": params,
            "response": {"count": len(klines_data)},
            "status_code": response.status_code,
            "created_at": created_at,
            "update_at": updated_at
        })
        
        # Save processed klines
        klines_collection = db["klines"]
        klines_collection.insert_many(processed_data)
        
        await logger.info(f"Fetched {len(processed_data)} klines for {symbol}")
        
        return {
            "status": "success",
            "count": len(processed_data),
            "symbol": symbol.upper(),
            "interval": interval.upper()
        }
        
    except httpx.HTTPStatusError as e:
        await logger.error(f"Binance API error: {e.response.status_code} - {e.response.text}")
        
        # Log failed request
        db = get_db()
        requests_collection = db["requests_log"]
        requests_collection.insert_one({
            "url": url,
            "request": params,
            "response": {"error": str(e)},
            "status_code": e.response.status_code,
            "created_at": created_at,
            "update_at": datetime.utcnow()
        })
        
        raise
    except Exception as e:
        await logger.error(f"Error fetching klines: {e}")
        raise


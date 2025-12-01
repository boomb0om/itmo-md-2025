from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import httpx
from datetime import datetime
from typing import Optional
import os
from contextlib import asynccontextmanager

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:admin@localhost:27017/crypto_data?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "crypto_data")

client: Optional[MongoClient] = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client, db
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        db = client[MONGODB_DB]
        print("Successfully connected to MongoDB")
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    if client:
        client.close()
        print("MongoDB connection closed")


app = FastAPI(
    title="Data collector app",
    lifespan=lifespan
)


@app.get("/api/fetch-klines")
async def fetch_klines(
    symbol: str = "BNBBTC",
    interval: str = "1M",
    limit: int = 100
):
    try:
        # Вызов Binance API
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval.upper(),
            "limit": min(limit, 1000)  # Максимум 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url, params=params)
            response.raise_for_status()
            klines_data = response.json()
        
        # Преобразование данных в удобный формат
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
        
        # Сохранение в MongoDB
        collection = db["klines"]
        collection.insert_many(processed_data)
        
        return {"status": "success"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Binance API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Binance API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


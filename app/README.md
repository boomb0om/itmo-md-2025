# App Module

## Purpose
FastAPI application for collecting cryptocurrency price data (Binance API) and news data (RSS feeds), storing all data in MongoDB.

## Stack
- **Framework**: FastAPI
- **Package Manager**: uv
- **Database**: MongoDB
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic-settings
- **Logging**: aiologger
- **Containerization**: Docker + Docker Compose

## Structure
```
app/
├── .env                    # Environment variables (create from .env.example)
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── main.py
└── src/
    ├── core/
    │   ├── settings.py    # Pydantic settings
    │   └── logging.py     # Logger setup
    ├── database.py        # MongoDB connection
    └── services/
        ├── binance_service.py  # Binance API integration
        └── news_service.py     # RSS feed parsing
```

## Start Commands

### Using Docker Compose (recommended)
```bash
cd app
cp .env.example .env
# Edit .env if needed
docker-compose up -d
```

### Local development
```bash
cd app
cp .env.example .env
# Edit .env if needed
uv pip install -e .
uvicorn main:app --reload
```

## Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/fetch-klines?symbol=BTCUSDT&interval=1h&limit=100` - Fetch candlestick data
- `GET /api/fetch-news?source=cryptopanic&limit=50` - Fetch news articles


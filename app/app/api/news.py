from typing import Any

from fastapi import APIRouter

from app.service.news_service import fetch_news

router = APIRouter(prefix="/news")


@router.get("/fetch-news")
async def api_fetch_news(limit: int = 50) -> dict[str, Any]:
    """Fetch the latest news entries up to the provided limit."""
    result = await fetch_news(limit=limit)
    return result

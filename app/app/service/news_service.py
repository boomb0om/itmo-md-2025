from datetime import datetime
from typing import Any

import feedparser
import httpx
from fastapi import HTTPException

from app.core.logging import get_logger
from app.database import get_db


async def fetch_news(source: str = "crypto.news", limit: int = 50) -> dict[str, Any]:
    logger = get_logger(__name__)
    rss_url = "https://crypto.news/feed"

    await logger.info(f"Fetching RSS feed from {rss_url}")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http_client:
        response = await http_client.get(rss_url)
        response.raise_for_status()

    feed = feedparser.parse(response.text)

    if feed.bozo:
        await logger.warning(f"RSS feed parsing warnings: {feed.bozo_exception}")

    items = feed.entries[:limit]

    news_docs = []
    for entry in items:
        pub_date = datetime.now()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except (ValueError, TypeError):
                pass
        elif hasattr(entry, "published") and entry.published:
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(entry.published)
            except (ValueError, TypeError):
                pass

        guid = entry.get("id", entry.get("guid", entry.get("link", "")))

        categories = []
        if hasattr(entry, "tags") and entry.tags:
            categories = [tag.get("term", "") for tag in entry.tags if tag.get("term")]

        doc = {
            "guid": guid,
            "source": source,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": entry.get("description", ""),
            "pub_date": pub_date,
            "categories": categories,
            "created_at": datetime.now(),
        }
        news_docs.append(doc)

    new_docs = []
    if news_docs:
        db = get_db()
        collection = db.get_collection("news_data")
        
        # Get existing guids to avoid duplicates
        existing_guids = set(
            collection.find(
                {"guid": {"$in": [doc["guid"] for doc in news_docs]}},
                {"guid": 1}
            ).distinct("guid")
        )
        
        # Filter out news that already exist
        new_docs = [doc for doc in news_docs if doc["guid"] not in existing_guids]
        
        if new_docs:
            try:
                collection.insert_many(new_docs, ordered=False)
                await logger.info(f"Inserted {len(new_docs)} new news articles")
            except Exception as e:
                # Handle potential duplicate key errors (race condition)
                await logger.warning(f"Some news articles may already exist: {e}")
        else:
            await logger.info("All news articles already exist in database")
    
    item_count = len(new_docs)
    total_fetched = len(news_docs) if news_docs else 0
    skipped = total_fetched - item_count
    
    msg = (
        f"Fetched {total_fetched} news articles from {rss_url}, "
        f"added {item_count} new, skipped {skipped} duplicates"
    )
    await logger.info(msg)
    return {
        "status": "ok",
        "message": msg,
    }

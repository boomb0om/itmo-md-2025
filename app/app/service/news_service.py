from collections.abc import Iterable
from datetime import datetime
from typing import Any

import feedparser
import httpx
from aiologger import Logger
from feedparser import FeedParserDict

from app.core.logging import get_logger
from app.database import get_db


async def _retrieve_feed(rss_url: str, logger: Logger) -> FeedParserDict:
    await logger.info(f"Fetching RSS feed from {rss_url}")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http_client:
        response = await http_client.get(rss_url)
        response.raise_for_status()
    feed = feedparser.parse(response.text)
    if feed.bozo:
        await logger.warning(f"RSS feed parsing warnings: {feed.bozo_exception}")
    return feed


def _parse_pub_date(entry: FeedParserDict) -> datetime:
    pub_date = datetime.now()
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (ValueError, TypeError):
            return pub_date
    if hasattr(entry, "published") and entry.published:
        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(entry.published)
        except (ValueError, TypeError):
            return pub_date
    return pub_date


def _extract_categories(entry: FeedParserDict) -> list[str]:
    if hasattr(entry, "tags") and entry.tags:
        return [tag.get("term", "") for tag in entry.tags if tag.get("term")]
    return []


def _build_news_docs(entries: Iterable[FeedParserDict], source: str) -> list[dict[str, Any]]:
    news_docs: list[dict[str, Any]] = []
    for entry in entries:
        doc = {
            "guid": entry.get("id", entry.get("guid", entry.get("link", ""))),
            "source": source,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": entry.get("description", ""),
            "pub_date": _parse_pub_date(entry),
            "categories": _extract_categories(entry),
            "created_at": datetime.now(),
        }
        news_docs.append(doc)
    return news_docs


async def _save_new_docs(news_docs: list[dict[str, Any]], logger: Logger) -> list[dict[str, Any]]:
    if not news_docs:
        return []

    db = get_db()
    collection = db.get_collection("news_data")
    existing_guids = set(
        collection.find(
            {"guid": {"$in": [doc["guid"] for doc in news_docs]}}, {"guid": 1}
        ).distinct("guid")
    )
    new_docs = [doc for doc in news_docs if doc["guid"] not in existing_guids]

    if not new_docs:
        await logger.info("All news articles already exist in database")
        return []

    try:
        collection.insert_many(new_docs, ordered=False)
        await logger.info(f"Inserted {len(new_docs)} new news articles")
        return new_docs
    except Exception as e:
        await logger.warning(f"Some news articles may already exist: {e}")
        return new_docs


def _build_summary(rss_url: str, total_fetched: int, added: int) -> str:
    skipped = total_fetched - added
    return (
        f"Fetched {total_fetched} news articles from {rss_url}, "
        f"added {added} new, skipped {skipped} duplicates"
    )


async def fetch_news(source: str = "crypto.news", limit: int = 50) -> dict[str, Any]:
    """Fetch news from RSS, deduplicate by guid, and store in MongoDB."""
    logger = get_logger(__name__)
    rss_url = "https://crypto.news/feed"
    feed = await _retrieve_feed(rss_url, logger)

    news_docs = _build_news_docs(feed.entries[:limit], source)
    new_docs = await _save_new_docs(news_docs, logger)

    total_fetched = len(news_docs)
    msg = _build_summary(rss_url, total_fetched, len(new_docs))
    await logger.info(msg)
    return {"status": "ok", "message": msg}

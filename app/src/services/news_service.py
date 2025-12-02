import httpx
from datetime import datetime
from typing import Dict, Any

from src.core.settings import news_settings
from src.core.logging import logger
from src.database import get_db


async def fetch_news(
    source: str = "cryptopanic",
    limit: int = 50
) -> Dict[str, Any]:
    """
    Fetch cryptocurrency news from RSS feeds
    
    Args:
        source: News source (cryptopanic, etc.)
        limit: Number of articles to fetch
    
    Returns:
        Dictionary with status and data
    """
    created_at = datetime.utcnow()
    
    try:
        # Use CryptoPanic API (returns JSON, not RSS)
        rss_url = "https://cryptopanic.com/api/v1/posts/?public=true"
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(rss_url)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
        
        updated_at = datetime.utcnow()
        
        # Process news articles
        processed_data = []
        results = data.get("results", [])[:limit]
        
        for entry in results:
            published_at = datetime.utcnow()
            if entry.get("created_at"):
                try:
                    published_at = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
                except:
                    pass
            
            processed_article = {
                "title": entry.get("title", ""),
                "content": entry.get("title", ""),  # CryptoPanic API doesn't provide full content
                "source": source,
                "url": entry.get("url", ""),
                "published_at": published_at,
                "fetched_at": datetime.utcnow()
            }
            processed_data.append(processed_article)
        
        # Save request/response log
        db = get_db()
        requests_collection = db["requests_log"]
        requests_collection.insert_one({
            "url": rss_url,
            "request": {"source": source, "limit": limit},
            "response": {"count": len(processed_data)},
            "status_code": response.status_code,
            "created_at": created_at,
            "update_at": updated_at
        })
        
        # Save processed news
        news_collection = db["news"]
        news_collection.insert_many(processed_data)
        
        await logger.info(f"Fetched {len(processed_data)} news articles from {source}")
        
        return {
            "status": "success",
            "count": len(processed_data),
            "source": source
        }
        
    except Exception as e:
        await logger.error(f"Error fetching news: {e}")
        
        # Log failed request
        db = get_db()
        requests_collection = db["requests_log"]
        requests_collection.insert_one({
            "url": rss_url if 'rss_url' in locals() else "unknown",
            "request": {"source": source, "limit": limit},
            "response": {"error": str(e)},
            "status_code": 500,
            "created_at": created_at,
            "update_at": datetime.utcnow()
        })
        
        raise


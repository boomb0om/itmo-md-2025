from datetime import datetime, timedelta
from typing import Any

from core.logging import get_logger
from database import get_db
from fastapi import HTTPException


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


def generate_mock_rss_response(source: str = "cryptopanic", limit: int = 50) -> dict[str, Any]:
    """
    Generate mock RSS feed response in JSON format

    Args:
        source: News source name
        limit: Number of articles to generate

    Returns:
        RSS-like response in JSON format
    """
    mock_titles = [
        "Bitcoin Reaches New All-Time High Amid Institutional Adoption",
        "Ethereum 2.0 Staking Reaches 10 Million ETH Milestone",
        "Major Bank Announces Cryptocurrency Trading Services",
        "Regulatory Clarity Boosts Crypto Market Confidence",
        "DeFi Protocol Launches Revolutionary Yield Farming Platform",
        "NFT Marketplace Sees Record-Breaking Sales Volume",
        "Central Bank Digital Currency Pilot Program Expands",
        "Crypto Mining Goes Green with Renewable Energy Initiative",
        "Layer 2 Solutions Drive Ethereum Transaction Costs Down",
        "Stablecoin Market Cap Surpasses $150 Billion",
        "Crypto Exchange Implements Advanced Security Measures",
        "Blockchain Technology Adopted by Major Retailer",
        "Smart Contract Audit Reveals Critical Security Updates",
        "Crypto Tax Regulations Updated in Multiple Jurisdictions",
        "Cross-Chain Bridge Enables Seamless Asset Transfers",
        "Gaming Platform Integrates Cryptocurrency Payments",
        "Crypto Wallet App Reaches 50 Million Users",
        "Decentralized Exchange Volume Hits New Record",
        "Crypto Education Initiative Launches in Universities",
        "Mining Difficulty Adjustment Maintains Network Stability",
    ]

    mock_urls = [
        "https://example.com/news/bitcoin-all-time-high",
        "https://example.com/news/ethereum-staking-milestone",
        "https://example.com/news/bank-crypto-services",
        "https://example.com/news/regulatory-clarity",
        "https://example.com/news/defi-yield-farming",
        "https://example.com/news/nft-marketplace-record",
        "https://example.com/news/cbdc-pilot-expansion",
        "https://example.com/news/green-mining-initiative",
        "https://example.com/news/layer2-transaction-costs",
        "https://example.com/news/stablecoin-market-cap",
        "https://example.com/news/exchange-security-update",
        "https://example.com/news/retailer-blockchain-adoption",
        "https://example.com/news/smart-contract-audit",
        "https://example.com/news/crypto-tax-updates",
        "https://example.com/news/cross-chain-bridge",
        "https://example.com/news/gaming-crypto-payments",
        "https://example.com/news/wallet-app-milestone",
        "https://example.com/news/dex-volume-record",
        "https://example.com/news/crypto-education-initiative",
        "https://example.com/news/mining-difficulty-adjustment",
    ]

    base_time = datetime.now()
    items = []

    for i in range(limit):
        title_index = i % len(mock_titles)
        published_at = base_time - timedelta(hours=i * 2)

        description = (
            f"{mock_titles[title_index]}. "
            f"This is a mock news article about cryptocurrency developments. "
            f"Article #{i + 1} provides insights into the latest trends "
            f"and updates in the crypto space."
        )

        # RSS item structure
        item = {
            "title": mock_titles[title_index],
            "link": mock_urls[title_index] + f"?id={i + 1}",
            "description": description,
            "pubDate": published_at.strftime("%a, %d %b %Y %H:%M:%S %z"),
            "guid": mock_urls[title_index] + f"?id={i + 1}",
        }
        items.append(item)

    # RSS-like structure in JSON format
    rss_response = {
        "rss": {
            "version": "2.0",
            "channel": {
                "title": f"Cryptocurrency News - {source.title()}",
                "link": f"https://example.com/rss/{source}",
                "description": f"Latest cryptocurrency news from {source}",
                "language": "en-us",
                "lastBuildDate": base_time.strftime("%a, %d %b %Y %H:%M:%S %z"),
                "item": items,
            },
        },
    }

    return rss_response


async def fetch_news(source: str = "cryptopanic", limit: int = 50) -> dict[str, Any]:
    """
    Fetch cryptocurrency news from RSS feeds (mock implementation)

    Args:
        source: News source (cryptopanic, etc.)
        limit: Number of articles to fetch

    Returns:
        RSS-like response in JSON format
    """
    logger = get_logger()
    rss_url = "mock://news-api"
    request = {"source": source, "limit": limit}
    created_at = datetime.now()

    try:
        await logger.info(f"Using mock RSS news data for source: {source}")

        response = generate_mock_rss_response(source=source, limit=limit)
        updated_at = datetime.now()
        status_code = 200

        await logger.info("Saving request to MongoDB")
        save_request_to_mongo(
            rss_url,
            request,
            response,
            status_code,
            created_at,
            updated_at,
        )

        item_count = len(response["rss"]["channel"]["item"])
        await logger.info(f"Generated {item_count} news articles from {source}")

        return response

    except Exception as e:
        updated_at = datetime.now()
        await logger.error(f"Error fetching news: {e}")

        await logger.info("Saving failed request to MongoDB")
        save_request_to_mongo(
            rss_url,
            request,
            {"error": str(e)},
            500,
            created_at,
            updated_at,
        )

        raise HTTPException(status_code=500, detail=f"Error fetching news: {e!s}") from e

"""
Fetch latest Bitcoin and Gold news from multiple sources.
Uses RSS feeds and public APIs to gather recent market news.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict


# RSS feeds for crypto and gold news
RSS_FEEDS = {
    "bitcoin": [
        "https://cointelegraph.com/rss/tag/bitcoin",
        "https://bitcoinmagazine.com/.rss/full/",
        "https://coindesk.com/arc/outboundfeeds/rss/",
    ],
    "gold": [
        "https://www.kitco.com/feed/rss/news/gold",
        "https://www.fxstreet.com/rss/gold",
    ],
}


def fetch_rss_feed(url: str, max_items: int = 5) -> List[Dict]:
    """Fetch and parse an RSS feed, returning recent items."""
    items = []
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "ClawTrader/1.0"
        })
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        for item in root.iter("item"):
            title = item.findtext("title", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")

            items.append({
                "title": title.strip(),
                "description": description.strip()[:300],
                "pub_date": pub_date,
                "link": link,
            })
            if len(items) >= max_items:
                break
    except Exception as e:
        print(f"[news_fetcher] Failed to fetch {url}: {e}")

    return items


def fetch_coingecko_price(coin_id: str) -> Dict:
    """Fetch current price and 24h change from CoinGecko."""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get(coin_id, {})
        return {
            "price_usd": data.get("usd"),
            "change_24h": data.get("usd_24h_change"),
            "volume_24h": data.get("usd_24h_vol"),
        }
    except Exception as e:
        print(f"[news_fetcher] Failed to fetch price for {coin_id}: {e}")
        return {}


def fetch_all_news() -> Dict:
    """
    Fetch all news and price data for BTC and Gold.
    Returns a dict with 'bitcoin' and 'gold' keys, each containing
    'news' (list) and 'price' (dict).
    """
    result = {}

    for asset, feeds in RSS_FEEDS.items():
        all_items = []
        for feed_url in feeds:
            all_items.extend(fetch_rss_feed(feed_url, max_items=3))
        result[asset] = {"news": all_items[:8]}

    # Fetch prices
    btc_price = fetch_coingecko_price("bitcoin")
    gold_price = fetch_coingecko_price("tether-gold")  # XAUT as gold proxy

    result.setdefault("bitcoin", {})["price"] = btc_price
    result.setdefault("gold", {})["price"] = gold_price

    return result


if __name__ == "__main__":
    import json
    data = fetch_all_news()
    print(json.dumps(data, indent=2, ensure_ascii=False))

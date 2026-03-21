"""
ClawTrader Threads Bot - Main entry point.

Modes:
  python -m threads_bot.bot          # Run scheduler (continuous)
  python -m threads_bot.bot --once   # Post once and exit
  python -m threads_bot.bot --dry    # Generate post but don't publish
"""
import sys
import io
from datetime import datetime

# Fix Windows console encoding for emoji/CJK output
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from .news_fetcher import fetch_all_news
from .technical_analysis import analyze_all
from .content_generator import generate_post
from .threads_publisher import post_to_threads
from .scheduler import run_scheduler
from .config import TIMEZONE


def create_and_post(dry_run: bool = False) -> None:
    """Full pipeline: fetch data -> analyze -> generate -> post."""
    print(f"\n{'='*50}")
    print(f"[bot] Starting analysis at {datetime.now()}")
    print(f"{'='*50}")

    # Step 1: Fetch news
    print("[bot] Fetching latest news...")
    news = fetch_all_news()
    btc_news_count = len(news.get("bitcoin", {}).get("news", []))
    gold_news_count = len(news.get("gold", {}).get("news", []))
    print(f"[bot] Fetched {btc_news_count} BTC news, {gold_news_count} Gold news")

    # Step 2: Technical analysis
    print("[bot] Running H1 technical analysis...")
    analysis = analyze_all()
    for asset_key in ["bitcoin", "gold"]:
        a = analysis.get(asset_key, {})
        if "error" not in a:
            print(f"[bot] {a['asset']}: ${a['current_price']} | "
                  f"Trend: {a['trend']} | RSI: {a['rsi']}")

    # Step 3: Generate post with Claude
    print("[bot] Generating post content with Claude...")
    post_text = generate_post(analysis, news)
    print(f"\n--- Generated Post ({len(post_text)} chars) ---")
    print(post_text)
    print("--- End Post ---\n")

    # Step 4: Publish to Threads
    if dry_run:
        print("[bot] DRY RUN - not publishing to Threads")
        return

    print("[bot] Publishing to Threads...")
    post_id = post_to_threads(post_text)
    if post_id:
        print(f"[bot] Successfully posted! ID: {post_id}")
    else:
        print("[bot] Failed to post to Threads")


def main():
    args = sys.argv[1:]

    if "--dry" in args:
        print("[bot] Running in DRY RUN mode")
        create_and_post(dry_run=True)
    elif "--once" in args:
        print("[bot] Running once")
        create_and_post(dry_run=False)
    else:
        print(f"[bot] ClawTrader Threads Bot starting...")
        print(f"[bot] Timezone: {TIMEZONE}")
        run_scheduler(create_and_post)


if __name__ == "__main__":
    main()

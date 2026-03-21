"""
ClawTrader Threads Bot - Main entry point.
Pipeline: Kiyotaka screenshot -> Claude vision analysis -> news -> generate post -> publish

Modes:
  python -m threads_bot          # Run scheduler (continuous)
  python -m threads_bot --once   # Post once and exit
  python -m threads_bot --dry    # Generate post but don't publish
"""
import sys
import io
from datetime import datetime

# Fix Windows console encoding for emoji/CJK output
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from .chart_screenshot import capture_btc_chart_sync
from .chart_analyzer import analyze_chart
from .news_fetcher import fetch_all_news
from .content_generator import generate_post
from .threads_publisher import post_to_threads
from .scheduler import run_scheduler
from .config import TIMEZONE


def create_and_post(dry_run: bool = False) -> None:
    """Full pipeline: screenshot -> Claude analyzes chart -> news -> generate -> post."""
    print(f"\n{'='*50}")
    print(f"[bot] ClawTrader starting at {datetime.now()}")
    print(f"{'='*50}")

    # Step 1: Capture BTC H1 chart from Kiyotaka.ai (with CVD + OI)
    print("[bot] Capturing BTC H1 chart from Kiyotaka.ai...")
    chart_path = capture_btc_chart_sync()
    if not chart_path:
        print("[bot] ERROR: Failed to capture chart, aborting")
        return
    print(f"[bot] Chart saved: {chart_path}")

    # Step 2: Claude vision — full chart analysis
    print("[bot] Sending chart to Claude for visual analysis...")
    chart_analysis = analyze_chart(chart_path)
    print(f"\n--- Chart Analysis ---")
    print(chart_analysis)
    print(f"--- End Analysis ---\n")

    # Step 3: Fetch latest BTC news
    print("[bot] Fetching latest BTC news...")
    news = fetch_all_news()
    btc_news_count = len(news.get("bitcoin", {}).get("news", []))
    print(f"[bot] Fetched {btc_news_count} BTC news articles")

    # Step 4: Generate Threads post
    print("[bot] Generating post content...")
    post_text = generate_post(chart_analysis, news)
    print(f"\n--- Post ({len(post_text)} chars) ---")
    print(post_text)
    print(f"--- End Post ---\n")

    # Step 5: Publish to Threads with chart image
    if dry_run:
        print("[bot] DRY RUN — not publishing")
        print(f"[bot] Chart: {chart_path}")
        return

    print("[bot] Publishing to Threads...")
    post_id = post_to_threads(post_text, chart_paths=[chart_path])
    if post_id:
        print(f"[bot] Posted! ID: {post_id}")
    else:
        print("[bot] Failed to post")


def main():
    args = sys.argv[1:]

    if "--dry" in args:
        print("[bot] DRY RUN mode")
        create_and_post(dry_run=True)
    elif "--once" in args:
        create_and_post(dry_run=False)
    else:
        print(f"[bot] ClawTrader Threads Bot — BTC analysis")
        print(f"[bot] Timezone: {TIMEZONE}")
        run_scheduler(create_and_post)


if __name__ == "__main__":
    main()

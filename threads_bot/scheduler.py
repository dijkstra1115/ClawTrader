"""
Scheduler for daily Threads posting at configured times.
"""
import schedule
import time
from datetime import datetime
import pytz
from typing import Callable

from .config import POST_TIMES, TIMEZONE


def create_schedule(job_func: Callable) -> None:
    """
    Schedule the posting job at configured times.
    POST_TIMES is a list like ["08:00", "20:00"].
    """
    tz = pytz.timezone(TIMEZONE)

    for post_time in POST_TIMES:
        post_time = post_time.strip()
        schedule.every().day.at(post_time, tz).do(job_func)
        print(f"[scheduler] Scheduled post at {post_time} ({TIMEZONE})")


def run_scheduler(job_func: Callable) -> None:
    """Run the scheduler loop. Blocks forever."""
    create_schedule(job_func)

    print(f"[scheduler] Bot is running. Next job at: {schedule.next_run()}")
    print("[scheduler] Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[scheduler] Stopped by user.")

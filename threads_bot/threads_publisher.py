"""
Publish posts to Threads using Meta's official Threads API.
Two-step process: create media container, then publish it.
"""
import time
import requests
from typing import Optional

from .config import THREADS_USER_ID, THREADS_ACCESS_TOKEN, THREADS_API_BASE


def create_text_container(text: str) -> Optional[str]:
    """
    Step 1: Create a text media container on Threads.
    Returns the container ID or None on failure.
    """
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }

    try:
        resp = requests.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get("id")
        print(f"[threads] Created container: {container_id}")
        return container_id
    except Exception as e:
        print(f"[threads] Failed to create container: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[threads] Response: {e.response.text}")
        return None


def publish_container(container_id: str) -> Optional[str]:
    """
    Step 2: Publish a media container to Threads.
    Returns the published post ID or None on failure.
    """
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish"
    payload = {
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN,
    }

    try:
        resp = requests.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        post_id = resp.json().get("id")
        print(f"[threads] Published post: {post_id}")
        return post_id
    except Exception as e:
        print(f"[threads] Failed to publish: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[threads] Response: {e.response.text}")
        return None


def post_to_threads(text: str) -> Optional[str]:
    """
    Full flow: create container -> wait -> publish.
    Returns the published post ID or None on failure.
    """
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        print("[threads] ERROR: THREADS_USER_ID and THREADS_ACCESS_TOKEN must be set in .env")
        return None

    # Truncate to 500 chars (Threads limit)
    if len(text) > 500:
        text = text[:497] + "..."

    container_id = create_text_container(text)
    if not container_id:
        return None

    # Wait for server processing as recommended by API docs
    print("[threads] Waiting 5s for server processing...")
    time.sleep(5)

    return publish_container(container_id)


if __name__ == "__main__":
    result = post_to_threads("ClawTrader test post - if you see this, the bot works! 🎉")
    if result:
        print(f"Success! Post ID: {result}")
    else:
        print("Failed to post. Check your .env credentials.")

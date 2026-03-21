"""
Publish posts to Threads using Meta's official Threads API.
Two-step process: create media container, then publish it.
Supports text-only and image posts.
"""
import time
import requests
from typing import Optional, List

from .config import THREADS_USER_ID, THREADS_ACCESS_TOKEN, THREADS_API_BASE


def upload_image_to_imgbb(image_path: str) -> Optional[str]:
    """
    Upload an image to imgBB (free, no API key needed for temp uploads).
    Falls back to 0x0.st if imgBB fails.
    Returns the public URL of the uploaded image.
    """
    # Try 0x0.st (simple, no key needed)
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": f},
                timeout=30,
            )
            resp.raise_for_status()
            url = resp.text.strip()
            print(f"[threads] Uploaded image: {url}")
            return url
    except Exception as e:
        print(f"[threads] Image upload failed: {e}")
        return None


def create_image_container(image_url: str, text: str = "") -> Optional[str]:
    """
    Create an IMAGE media container on Threads.
    Returns the container ID or None on failure.
    """
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }

    try:
        resp = requests.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get("id")
        print(f"[threads] Created image container: {container_id}")
        return container_id
    except Exception as e:
        print(f"[threads] Failed to create image container: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[threads] Response: {e.response.text}")
        return None


def create_text_container(text: str) -> Optional[str]:
    """
    Create a TEXT media container on Threads.
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


def create_carousel_container(image_urls: List[str], text: str = "") -> Optional[str]:
    """
    Create a CAROUSEL container with multiple images.
    Returns the container ID or None on failure.
    """
    # Step 1: Create individual image items
    item_ids = []
    for img_url in image_urls:
        url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
        payload = {
            "media_type": "IMAGE",
            "image_url": img_url,
            "is_carousel_item": "true",
            "access_token": THREADS_ACCESS_TOKEN,
        }
        try:
            resp = requests.post(url, data=payload, timeout=30)
            resp.raise_for_status()
            item_id = resp.json().get("id")
            item_ids.append(item_id)
            print(f"[threads] Created carousel item: {item_id}")
        except Exception as e:
            print(f"[threads] Failed to create carousel item: {e}")
            return None

    # Step 2: Create the carousel container
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(item_ids),
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get("id")
        print(f"[threads] Created carousel container: {container_id}")
        return container_id
    except Exception as e:
        print(f"[threads] Failed to create carousel: {e}")
        return None


def publish_container(container_id: str) -> Optional[str]:
    """
    Publish a media container to Threads.
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


def post_to_threads(text: str, chart_paths: List[str] = None) -> Optional[str]:
    """
    Full flow: upload images (if any) -> create container -> wait -> publish.

    If chart_paths has 1 image: creates an IMAGE post with text.
    If chart_paths has 2+ images: creates a CAROUSEL post with text.
    If no images: creates a TEXT post.

    Returns the published post ID or None on failure.
    """
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        print("[threads] ERROR: THREADS_USER_ID and THREADS_ACCESS_TOKEN must be set in .env")
        return None

    # Truncate to 500 chars (Threads limit)
    if len(text) > 500:
        text = text[:497] + "..."

    container_id = None

    if chart_paths:
        # Upload images first
        image_urls = []
        for path in chart_paths:
            url = upload_image_to_imgbb(path)
            if url:
                image_urls.append(url)

        if len(image_urls) >= 2:
            # Carousel post
            container_id = create_carousel_container(image_urls, text)
        elif len(image_urls) == 1:
            # Single image post
            container_id = create_image_container(image_urls[0], text)
        else:
            # Fallback to text if uploads failed
            print("[threads] Image uploads failed, falling back to text post")
            container_id = create_text_container(text)
    else:
        container_id = create_text_container(text)

    if not container_id:
        return None

    # Wait for server processing as recommended by API docs
    print("[threads] Waiting 5s for server processing...")
    time.sleep(5)

    return publish_container(container_id)


if __name__ == "__main__":
    result = post_to_threads("ClawTrader test post 🎉")
    if result:
        print(f"Success! Post ID: {result}")
    else:
        print("Failed to post. Check your .env credentials.")

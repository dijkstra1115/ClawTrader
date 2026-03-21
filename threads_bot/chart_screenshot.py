"""
Take screenshots of Kiyotaka.ai H1 charts using Playwright.
Captures professional-grade charts with volume profile for Claude analysis.
"""
import os
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "charts")

KIYOTAKA_BASE = "https://chart.kiyotaka.ai"

# Assets to screenshot: (display_name, search_term, filename)
ASSETS = [
    ("Bitcoin", "BTCUSDT", "btc_kiyotaka.png"),
    ("Gold", "XAUUSD", "gold_kiyotaka.png"),
]

TIMEFRAME = "1h"


async def _dismiss_dialogs(page):
    """Close any popups, error dialogs, or overlays on Kiyotaka using JS removal."""
    try:
        # Force-remove ALL dialog overlays via JavaScript
        removed = await page.evaluate("""() => {
            let count = 0;
            // Remove dialog overlays
            document.querySelectorAll('.dialog-overlay, [class*="dialog-overlay"]').forEach(el => {
                el.remove();
                count++;
            });
            // Remove modal backdrops
            document.querySelectorAll('[class*="modal"], [class*="backdrop"]').forEach(el => {
                if (el.style) el.style.display = 'none';
                count++;
            });
            // Remove guest notification banners
            document.querySelectorAll('[class*="guest"], [class*="notification-bar"]').forEach(el => {
                el.remove();
                count++;
            });
            return count;
        }""")
        if removed:
            print(f"[screenshot] Removed {removed} overlay(s) via JS")
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"[screenshot] Dialog dismiss error: {e}")


async def _wait_for_chart_ready(page, timeout: int = 30000):
    """Wait until the chart canvas is rendered and has content."""
    try:
        # Wait for canvas to appear
        await page.wait_for_selector("canvas", timeout=timeout)

        # Poll until the canvas actually has drawn content (non-blank)
        for _ in range(15):
            has_content = await page.evaluate("""() => {
                const canvases = document.querySelectorAll('canvas');
                for (const c of canvases) {
                    if (c.width > 400 && c.height > 200) {
                        const ctx = c.getContext('2d');
                        if (ctx) {
                            const data = ctx.getImageData(
                                Math.floor(c.width/2), Math.floor(c.height/2), 10, 10
                            ).data;
                            // Check if center pixels are non-black/non-transparent
                            for (let i = 0; i < data.length; i += 4) {
                                if (data[i] > 5 || data[i+1] > 5 || data[i+2] > 5) return true;
                            }
                        }
                        // For WebGL canvases, check if gl context exists
                        const gl = c.getContext('webgl') || c.getContext('webgl2');
                        if (gl) return true;
                    }
                }
                return false;
            }""")
            if has_content:
                print("[screenshot] Chart canvas has content")
                # Extra wait for final render
                await page.wait_for_timeout(2000)
                return
            await page.wait_for_timeout(2000)

        # Even if detection failed, wait generously for WebGL render
        print("[screenshot] Canvas content check inconclusive, waiting extra...")
        await page.wait_for_timeout(5000)
    except Exception as e:
        print(f"[screenshot] Chart ready check: {e}, waiting fallback...")
        await page.wait_for_timeout(8000)


async def _set_symbol(page, search_term: str):
    """Search and select a trading symbol on Kiyotaka."""
    try:
        await _dismiss_dialogs(page)

        # Click on the symbol/ticker area at the top-left to open search
        symbol_selectors = [
            '[class*="symbol-info"]',
            '[class*="ticker"]',
            '[class*="symbol"] span',
            '[class*="pair-name"]',
            '[class*="instrument"]',
        ]
        opened = False
        for sel in symbol_selectors:
            elem = await page.query_selector(sel)
            if elem and await elem.is_visible():
                await elem.click(force=True, timeout=5000)
                await page.wait_for_timeout(1500)
                opened = True
                break

        if not opened:
            # Fallback: try clicking on the BTCUSDT text directly
            btc_text = await page.query_selector('text="BTCUSDT"')
            if btc_text:
                await btc_text.click(force=True, timeout=3000)
                await page.wait_for_timeout(1500)

        await _dismiss_dialogs(page)

        # Find the search input that appeared
        search_input = None
        input_selectors = [
            'input[placeholder*="earch"]',
            'input[placeholder*="ymbol"]',
            'input[type="text"]',
            'input[type="search"]',
        ]
        for sel in input_selectors:
            elems = await page.query_selector_all(sel)
            for elem in elems:
                if await elem.is_visible():
                    search_input = elem
                    break
            if search_input:
                break

        if search_input:
            # Clear and type
            await search_input.click(force=True)
            await search_input.fill("")
            await search_input.type(search_term, delay=80)
        else:
            # Just type into the page
            await page.keyboard.type(search_term, delay=80)

        await page.wait_for_timeout(2000)

        # Click first search result
        result_selectors = [
            '[class*="search-result"] >> nth=0',
            '[class*="symbol-list"] >> nth=0',
            '[class*="search"] li >> nth=0',
            '[class*="dropdown"] [class*="item"] >> nth=0',
        ]
        clicked = False
        for sel in result_selectors:
            try:
                elem = await page.query_selector(sel)
                if elem and await elem.is_visible():
                    await elem.click(force=True, timeout=3000)
                    clicked = True
                    break
            except:
                continue

        if not clicked:
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(3000)
        print(f"[screenshot] Symbol set to {search_term}")

    except Exception as e:
        print(f"[screenshot] Could not set symbol to {search_term}: {e}")


async def _set_timeframe(page, timeframe: str):
    """Set the chart timeframe."""
    try:
        await _dismiss_dialogs(page)

        # Force-click the timeframe button
        tf_btn = await page.query_selector(f'button:has-text("{timeframe}")')
        if tf_btn and await tf_btn.is_visible():
            await tf_btn.click(force=True, timeout=5000)
            await page.wait_for_timeout(2000)
            print(f"[screenshot] Timeframe set to {timeframe}")
            return

        tf_selectors = [
            f'[class*="timeframe"] button:has-text("{timeframe}")',
            f'[class*="resolution"] :has-text("{timeframe}")',
            f'span:text-is("{timeframe}")',
        ]
        for sel in tf_selectors:
            try:
                elem = await page.query_selector(sel)
                if elem and await elem.is_visible():
                    await elem.click(force=True, timeout=5000)
                    await page.wait_for_timeout(2000)
                    print(f"[screenshot] Timeframe set to {timeframe}")
                    return
            except:
                continue

        print(f"[screenshot] Could not find timeframe button for {timeframe}")

    except Exception as e:
        print(f"[screenshot] Timeframe error: {e}")


async def _capture_chart(page, filename: str) -> Optional[str]:
    """Take a screenshot of the chart area."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        await _dismiss_dialogs(page)

        # Try to find the main chart canvas
        canvases = await page.query_selector_all("canvas")
        chart_canvas = None
        max_area = 0

        for canvas in canvases:
            box = await canvas.bounding_box()
            if box:
                area = box["width"] * box["height"]
                if area > max_area and box["width"] > 400 and box["height"] > 200:
                    max_area = area
                    chart_canvas = canvas

        if chart_canvas:
            await chart_canvas.screenshot(path=filepath)
            print(f"[screenshot] Chart canvas captured: {filepath}")
        else:
            # Fallback: screenshot the viewport
            await page.screenshot(path=filepath)
            print(f"[screenshot] Viewport captured: {filepath}")

        return filepath

    except Exception as e:
        print(f"[screenshot] Capture failed: {e}")
        return None


async def _take_chart_screenshot(page, search_term: str, filename: str) -> Optional[str]:
    """Full flow for a single asset: navigate -> set symbol -> set timeframe -> screenshot."""
    try:
        # Navigate fresh for each asset
        await page.goto(KIYOTAKA_BASE, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # Force-remove ALL overlays immediately via JS
        await _dismiss_dialogs(page)

        # Check if we got an error page
        error_text = await page.query_selector('text="something went wrong"')
        if error_text:
            print(f"[screenshot] Kiyotaka error page detected")
            # Try "Create new workspace" button with force click
            new_ws_btn = await page.query_selector('button:has-text("Create new workspace")')
            if new_ws_btn:
                await new_ws_btn.click(force=True, timeout=5000)
                await page.wait_for_timeout(5000)
                await _dismiss_dialogs(page)
            else:
                # Try clicking Refresh with force
                refresh_btn = await page.query_selector('button:has-text("Refresh")')
                if refresh_btn:
                    await refresh_btn.click(force=True, timeout=5000)
                    await page.wait_for_timeout(5000)
                    await _dismiss_dialogs(page)
                else:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(5000)
                    await _dismiss_dialogs(page)

        # Set symbol and timeframe
        await _set_symbol(page, search_term)
        await _dismiss_dialogs(page)
        await _set_timeframe(page, TIMEFRAME)

        # Wait for chart to render
        await _wait_for_chart_ready(page)
        await _dismiss_dialogs(page)

        # Capture
        return await _capture_chart(page, filename)

    except Exception as e:
        print(f"[screenshot] Failed for {search_term}: {e}")
        return None


async def capture_all_charts() -> Dict[str, str]:
    """Capture H1 chart screenshots for BTC and Gold from Kiyotaka.ai."""
    results = {}

    async with async_playwright() as p:
        # Must use headed mode with ANGLE for WebGL chart rendering
        # Window is placed offscreen to simulate headless
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--enable-webgl",
                "--use-angle=default",
                "--enable-gpu",
                "--ignore-gpu-blocklist",
                "--window-position=-10000,-10000",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        for name, search_term, filename in ASSETS:
            key = "bitcoin" if "BTC" in search_term else "gold"
            filepath = await _take_chart_screenshot(page, search_term, filename)
            if filepath:
                results[key] = filepath

        await browser.close()

    return results


def capture_charts_sync() -> Dict[str, str]:
    """Synchronous wrapper for capture_all_charts."""
    return asyncio.run(capture_all_charts())


if __name__ == "__main__":
    charts = capture_charts_sync()
    print(f"Captured charts: {charts}")

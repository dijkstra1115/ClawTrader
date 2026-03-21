"""
Take H1 chart screenshot of BTC from velo.xyz/chart with Cumulative Delta indicator.
Uses Playwright. No login required — velo.xyz indicators are free.
The chart is a TradingView embed inside an iframe.
"""
import os
import asyncio
from typing import Optional
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "charts")
VELO_URL = "https://velo.xyz/chart"


async def _dismiss_popups(page):
    """Dismiss velo.xyz popups like the 'Trade now' banner."""
    try:
        later_btn = page.locator('button:has-text("Later")')
        if await later_btn.is_visible(timeout=3000):
            await later_btn.click()
            await page.wait_for_timeout(1000)
            print("[screenshot] Dismissed popup")
    except Exception:
        pass


async def _get_tv_frame(page):
    """Get the TradingView iframe content frame."""
    # Wait for iframe to load
    await page.wait_for_selector("iframe", timeout=15000)
    # Find all iframe elements
    frames = page.frames
    for frame in frames:
        if "tradingview" in frame.url.lower() or frame.name.startswith("tradingview"):
            return frame
    # Fallback: first child frame
    if len(frames) > 1:
        return frames[1]
    return None


async def _open_indicators_dialog(frame):
    """Open TradingView Indicators dialog using keyboard shortcut."""
    # Focus the chart area first, then use '/' shortcut
    chart = frame.locator('[class*="chart-container"]').first
    try:
        await chart.click(force=True)
    except Exception:
        pass
    await frame.press("body", "/")


async def _set_dropdown(frame, page, current: str, target: str, label: str = ""):
    """Click a dropdown showing `current` text and select `target` option."""
    if current == target:
        return
    dropdown = frame.locator(f':text-is("{current}")').last
    if await dropdown.count() == 0:
        # Already set to target or different state — skip
        return
    await dropdown.click(force=True)
    await page.wait_for_timeout(1500)
    option = frame.get_by_role("option", name=target, exact=True)
    if await option.count() > 0:
        await option.click(force=True)
        await page.wait_for_timeout(1000)
        print(f"[screenshot] {label}: {current} -> {target}")
    else:
        # Try text click fallback
        text_el = frame.locator(f':text-is("{target}")')
        if await text_el.count() > 0:
            await text_el.first.click(force=True)
            await page.wait_for_timeout(1000)
            print(f"[screenshot] {label}: {current} -> {target} (text)")


async def _open_settings(page, frame, indicator_name: str) -> bool:
    """Hover over indicator legend and click Settings. Returns True if dialog opened."""
    indicator_label = frame.locator(f'text="{indicator_name}"').first
    await indicator_label.hover()
    await page.wait_for_timeout(1500)

    settings_btn = frame.locator('button[aria-label="Settings"]')
    for i in range(await settings_btn.count() - 1, -1, -1):
        btn = settings_btn.nth(i)
        if await btn.is_visible():
            await btn.click()
            await page.wait_for_timeout(3000)
            return True
    return False


async def _add_cumulative_delta(page, frame):
    """Add <Velo> Aggregated Volume indicator and set View to Cumulative Delta."""
    try:
        # Step 1: Add the indicator
        await _open_indicators_dialog(frame)
        await page.wait_for_timeout(2000)

        agg_vol = frame.get_by_text("<Velo> Aggregated Volume", exact=True)
        await agg_vol.wait_for(timeout=8000)
        await agg_vol.click(force=True)
        await page.wait_for_timeout(2000)
        print("[screenshot] Added <Velo> Aggregated Volume")

        # Close indicators panel
        await frame.press("body", "Escape")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[screenshot] Add Aggregated Volume error: {e}")
        try:
            await frame.press("body", "Escape")
        except Exception:
            pass
        return

    # Step 2: Change Measure to Coins and View to Cumulative Delta
    try:
        await frame.press("body", "Escape")
        await page.wait_for_timeout(1000)

        if not await _open_settings(page, frame, "<Velo> Aggregated Volume"):
            print("[screenshot] Settings button not visible, skipping CVD config")
            return

        # Ensure Inputs tab is active
        inputs_tab = frame.get_by_role("tab", name="Inputs")
        if await inputs_tab.count() > 0:
            await inputs_tab.first.click(force=True)
            await page.wait_for_timeout(1000)

        await _set_dropdown(frame, page, current="USD", target="Coins", label="CVD Measure")
        await _set_dropdown(frame, page, current="Standard", target="Cumulative Delta", label="CVD View")

        ok_btn = frame.get_by_role("button", name="Ok")
        if await ok_btn.count() > 0:
            await ok_btn.click(force=True)
            await page.wait_for_timeout(1000)

    except Exception as e:
        print(f"[screenshot] CVD settings error: {e}")
        try:
            await frame.press("body", "Escape")
        except Exception:
            pass


async def _add_open_interest(page, frame):
    """Add <Velo> Aggregated Open Interest indicator and set Measure to Coins."""
    try:
        await _open_indicators_dialog(frame)
        await page.wait_for_timeout(2000)

        oi = frame.get_by_text("<Velo> Aggregated Open Interest", exact=True)
        await oi.wait_for(timeout=8000)
        await oi.click(force=True)
        await page.wait_for_timeout(2000)
        print("[screenshot] Added <Velo> Aggregated Open Interest")

        # Close indicators panel
        await frame.press("body", "Escape")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[screenshot] Add OI error: {e}")
        try:
            await frame.press("body", "Escape")
        except Exception:
            pass
        return

    # Set Measure to Coins
    try:
        await frame.press("body", "Escape")
        await page.wait_for_timeout(1000)

        if not await _open_settings(page, frame, "<Velo> Aggregated Open Interest"):
            print("[screenshot] OI Settings button not visible, skipping Measure change")
            return

        inputs_tab = frame.get_by_role("tab", name="Inputs")
        if await inputs_tab.count() > 0:
            await inputs_tab.first.click(force=True)
            await page.wait_for_timeout(1000)

        await _set_dropdown(frame, page, current="USD", target="Coins", label="OI Measure")

        ok_btn = frame.get_by_role("button", name="Ok")
        if await ok_btn.count() > 0:
            await ok_btn.click(force=True)
            await page.wait_for_timeout(1000)

    except Exception as e:
        print(f"[screenshot] OI settings error: {e}")
        try:
            await frame.press("body", "Escape")
        except Exception:
            pass


async def _remove_volume_sma(page, frame):
    """Hover over Volume indicator label and click Remove to delete it."""
    try:
        vol_label = frame.locator('text="Volume"').first
        if await vol_label.count() == 0:
            print("[screenshot] Volume label not found, skipping")
            return
        await vol_label.hover()
        await page.wait_for_timeout(1500)

        remove_btn = frame.locator('button[aria-label="Remove"]')
        for i in range(await remove_btn.count() - 1, -1, -1):
            btn = remove_btn.nth(i)
            if await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(1000)
                print("[screenshot] Removed Volume SMA")
                return
        print("[screenshot] Remove button not visible")
    except Exception as e:
        print(f"[screenshot] Remove Volume SMA error: {e}")


async def _wait_for_chart(page, frame):
    """Wait for chart to render."""
    try:
        await frame.wait_for_selector("canvas", timeout=20000)
        await page.wait_for_timeout(3000)
    except Exception:
        await page.wait_for_timeout(5000)


async def _capture_chart(page, filename: str) -> Optional[str]:
    """Take a screenshot of the chart iframe area."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        # Screenshot the iframe element for a clean chart image
        iframe_el = page.locator("iframe").first
        if await iframe_el.is_visible():
            await iframe_el.screenshot(path=filepath)
            print(f"[screenshot] Chart captured: {filepath}")
            return filepath

        # Fallback: full page
        await page.screenshot(path=filepath)
        print(f"[screenshot] Page captured: {filepath}")
        return filepath
    except Exception as e:
        print(f"[screenshot] Capture failed: {e}")
        return None


async def capture_btc_chart() -> Optional[str]:
    """
    Full flow: open velo.xyz/chart -> add Cumulative Delta + OI -> screenshot.
    No login required.
    Returns the filepath of the saved chart image.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--enable-webgl",
                "--use-angle=default",
                "--enable-gpu",
                "--ignore-gpu-blocklist",
                "--window-position=-2000,-2000",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        try:
            await page.goto(VELO_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(8000)
            await _dismiss_popups(page)

            # Get TradingView iframe
            frame = await _get_tv_frame(page)
            if not frame:
                print("[screenshot] TradingView iframe not found")
                return None

            # Wait for chart to load
            await _wait_for_chart(page, frame)

            # Remove Volume SMA indicator
            await _remove_volume_sma(page, frame)

            # Add Cumulative Delta indicator
            await _add_cumulative_delta(page, frame)

            # Add Open Interest indicator
            await _add_open_interest(page, frame)

            # Wait for indicators to render
            await page.wait_for_timeout(3000)

            # Capture chart
            filepath = await _capture_chart(page, "btc_h1.png")
            return filepath

        except Exception as e:
            print(f"[screenshot] Fatal error: {e}")
            return None
        finally:
            await browser.close()


def capture_btc_chart_sync() -> Optional[str]:
    """Synchronous wrapper."""
    return asyncio.run(capture_btc_chart())


if __name__ == "__main__":
    path = capture_btc_chart_sync()
    print(f"Chart: {path}")

import asyncio
import os
import logging
from pyppeteer import launch
from logger import setup_logger

# Disable noisy websocket debug logs
logging.getLogger('websockets').setLevel(logging.ERROR)

logger = setup_logger("screenshot")


async def _take_screenshot(url, save_path, cookies=None):
    """Take a screenshot with simplified browser handling"""
    logger.info(f"Taking screenshot of: {url}")

    # Ensure directory exists
    os.makedirs(save_path, exist_ok=True)
    screenshot_path = os.path.join(save_path, 'screenshot.png')

    browser = None
    try:
        # Create new browser for each screenshot (more reliable)
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = await browser.newPage()
        await page.setViewport({'width': 1920, 'height': 1080})

        # Apply cookies if provided
        if cookies:
            logger.info(f"Applying {len(cookies)} cookies to browser")
            await page.setCookie(*cookies)

        # Navigate with simpler wait strategy to avoid timeout
        await page.goto(url, {
            'timeout': 30000,
            'waitUntil': 'domcontentloaded'  # Less strict wait condition
        })

        # Extra wait for JavaScript-heavy content
        await asyncio.sleep(3)

        # Take screenshot
        await page.screenshot({'path': screenshot_path, 'fullPage': True})

        # Verify screenshot was saved
        if os.path.exists(screenshot_path):
            size = os.path.getsize(screenshot_path) / 1024
            logger.info(f"Screenshot saved: {screenshot_path} ({size:.1f} KB)")
            return True
        else:
            logger.error(f"Screenshot file doesn't exist after capture")
            return False

    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if browser:
            await browser.close()


def take_screenshot(url, save_path, cookies=None):
    """Wrapper to run the async screenshot function."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_take_screenshot(url, save_path, cookies))
        return result
    except Exception as e:
        logger.error(f"Screenshot wrapper failed: {str(e)}")
        return False

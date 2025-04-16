import asyncio
import os
from pyppeteer import launch
from logger import setup_logger

# Fix Chromium revision to a working one
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1263111'

logger = setup_logger("screenshot")
_browser = None  # Global browser instance


async def get_browser():
    """Get or create a persistent browser instance."""
    global _browser
    try:
        # Check if browser exists and is usable by testing a simple command
        if _browser is not None:
            try:
                # Try to get browser version as a check
                await _browser.version()
                return _browser
            except Exception:
                # If error occurs, browser is not usable
                _browser = None

        # Create new browser if needed
        _browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
        )
        return _browser
    except Exception as e:
        logger.error(f"Browser creation error: {str(e)}")
        # Always return a fresh browser instance as fallback
        return await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )


async def _take_screenshot(url, save_path, cookies=None):
    """Take a screenshot with detailed error handling and logging."""
    logger.info(f"Taking screenshot of: {url}")

    # Ensure directory exists
    os.makedirs(save_path, exist_ok=True)
    screenshot_path = os.path.join(save_path, 'screenshot.png')

    # Verify directory is writable
    if not os.access(save_path, os.W_OK):
        logger.error(f"Directory is not writable: {save_path}")
        return False

    try:
        browser = await get_browser()
        page = await browser.newPage()

        # Set viewport size
        await page.setViewport({'width': 1920, 'height': 1080})

        # Apply session cookies before navigation
        if cookies:
            logger.info(f"Applying {len(cookies)} cookies to browser")
            await page.setCookie(*cookies)

        # Navigate with longer timeout and wait until network is idle
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})

        # Wait for JavaScript rendering
        await asyncio.sleep(5)

        # Take screenshot
        await page.screenshot({'path': screenshot_path, 'fullPage': True})

        # Verify screenshot was saved
        if os.path.exists(screenshot_path):
            size = os.path.getsize(screenshot_path) / 1024
            logger.info(f"Screenshot saved: {screenshot_path} ({size:.1f} KB)")
            await page.close()
            return True
        else:
            logger.error(f"Screenshot file doesn't exist after capture")
            await page.close()
            return False

    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


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

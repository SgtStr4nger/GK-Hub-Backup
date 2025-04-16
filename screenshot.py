import asyncio
import os
from pyppeteer import launch
from logger import setup_logger
import traceback

# Fix Chromium revision to one that exists
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1263111'

logger = setup_logger("screenshot")
_browser = None


async def get_browser():
    """Get or create a persistent browser instance."""
    global _browser
    if _browser is None or not _browser.isConnected():
        _browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
        )
    return _browser


async def _take_screenshot(url, save_path, cookies=None):
    """Take a screenshot with detailed error handling and logging."""
    logger.info(f"Starting screenshot for URL: {url}")
    logger.info(f"Target save path: {os.path.abspath(save_path)}")

    # Ensure directory exists
    save_path = os.path.abspath(save_path)
    os.makedirs(save_path, exist_ok=True)

    screenshot_path = os.path.join(save_path, 'screenshot.png')
    logger.info(f"Full screenshot path: {screenshot_path}")

    # Verify directory is writable
    if not os.access(save_path, os.W_OK):
        logger.error(f"Directory is not writable: {save_path}")
        return False

    try:
        browser = await get_browser()
        page = await browser.newPage()

        # Set viewport size (match typical desktop)
        await page.setViewport({'width': 1920, 'height': 1080})

        # Apply session cookies before navigation
        if cookies:
            logger.info(f"Applying {len(cookies)} cookies to browser")
            await page.setCookie(*cookies)

        # Navigate with longer timeout and wait until network is idle
        logger.info(f"Navigating to {url}")
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})

        # Wait for content to render (adjust selectors for the GK-Hub portal)
        try:
            # Try to wait for common elements on GK-Hub (based on image)
            selectors = ['.navbar', 'h1', '.container', '.row']
            for selector in selectors:
                try:
                    await page.waitForSelector(selector, {'timeout': 5000})
                    logger.debug(f"Found selector: {selector}")
                except:
                    pass
        except Exception as e:
            logger.warning(f"Selector wait failed: {str(e)}")

        # Additional wait for JavaScript rendering
        logger.info("Waiting for JavaScript to finish rendering...")
        await asyncio.sleep(5)

        # Take screenshot
        logger.info(f"Taking screenshot and saving to {screenshot_path}")
        await page.screenshot({'path': screenshot_path, 'fullPage': True})

        # Verify screenshot was saved
        if os.path.exists(screenshot_path):
            size = os.path.getsize(screenshot_path)
            logger.info(f"Screenshot saved successfully: {size} bytes")
            await page.close()
            return True
        else:
            logger.error(f"Screenshot file doesn't exist after capture attempt")

            # Fallback method
            logger.info("Trying fallback screenshot method...")
            await page.screenshot({'path': screenshot_path})

            if os.path.exists(screenshot_path):
                logger.info("Fallback screenshot method succeeded")
                await page.close()
                return True

            logger.error("All screenshot methods failed")
            await page.close()
            return False

    except Exception as e:
        logger.error(f"Screenshot process error: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def take_screenshot(url, save_path, cookies=None):
    """Wrapper function to run the async screenshot function."""
    try:
        # Create new event loop for thread safety
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_take_screenshot(url, save_path, cookies))
        return result
    except Exception as e:
        logger.error(f"Screenshot wrapper failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def verify_installation():
    """Verify Chromium installation is working."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def check_browser():
            browser = await launch(headless=True)
            version = await browser.version()
            logger.info(f"Chrome version: {version}")
            await browser.close()
            return True

        return loop.run_until_complete(check_browser())
    except Exception as e:
        logger.error(f"Chrome installation verification failed: {str(e)}")
        return False

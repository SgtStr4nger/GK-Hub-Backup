import asyncio
import os
import json
from pyppeteer import launch
from logger import setup_logger

logger = setup_logger("screenshot")


async def _take_screenshot(url, save_path, cookies=None):
    browser = await launch(
        headless=True,
        executablePath="C:/Program Files/Google/Chrome/Application/chrome.exe",  # Adjust path to your Chrome
        args=['--no-sandbox']
    )
    page = await browser.newPage()

    try:
        # Apply session cookies before navigating
        if cookies:
            logger.info(f"Applying {len(cookies)} cookies to screenshot browser")
            await page.setCookie(*cookies)

        # Navigate with longer timeout and network idle
        await page.setViewport({'width': 1920, 'height': 1080})
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})

        # Take screenshot
        screenshot_path = os.path.join(save_path, 'screenshot.png')
        await page.screenshot({'path': screenshot_path, 'fullPage': True})
        logger.info(f"Screenshot saved to {screenshot_path}")
        return True
    except Exception as e:
        logger.error(f"Screenshot failed for {url}: {str(e)}")
        return False
    finally:
        await browser.close()


def take_screenshot(url, save_path, cookies=None):
    """Take a screenshot of a URL with an authenticated session."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_take_screenshot(url, save_path, cookies))
        return result
    except Exception as e:
        logger.error(f"Screenshot wrapper failed for {url}: {str(e)}")
        return False


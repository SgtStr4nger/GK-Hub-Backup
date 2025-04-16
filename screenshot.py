import asyncio
import os
from pyppeteer import launch
from logger import setup_logger

logger = setup_logger("screenshot")


async def _take_screenshot(url, save_path):
    browser = await launch(
        headless=True,
        executablePath="C:/Program Files/Google/Chrome/Application/chrome.exe",  # Adjust path to your Chrome
        args=['--no-sandbox']
    )
    page = await browser.newPage()
    try:
        # Set viewport size for consistent screenshots
        await page.setViewport({'width': 1920, 'height': 1080})

        # Navigate with robust wait conditions
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})

        # Add extra waiting for JavaScript rendering
        await asyncio.sleep(2)

        # Ensure screenshot folder exists
        screenshot_file = os.path.join(save_path, 'screenshot.png')
        os.makedirs(os.path.dirname(screenshot_file), exist_ok=True)

        # Take full page screenshot
        await page.screenshot({
            'path': screenshot_file,
            'fullPage': True
        })

        logger.info(f"Screenshot saved to {screenshot_file}")
        return True
    except Exception as e:
        logger.error(f"Screenshot failed for {url}: {str(e)}")
        return False
    finally:
        await browser.close()


def take_screenshot(url, save_path):
    """Wrapper function to run the async screenshot function"""
    try:
        # Create asyncio event loop and run the async function
        result = asyncio.get_event_loop().run_until_complete(_take_screenshot(url, save_path))
        return result
    except Exception as e:
        logger.error(f"Screenshot wrapper failed for {url}: {str(e)}")
        return False

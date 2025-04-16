import asyncio
from pyppeteer import launch
from logger import setup_logger
import os

logger = setup_logger("screenshot")

async def _take_screenshot(url, save_path):
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    try:
        await page.goto(url, waitUntil='networkidle2')
        await page.screenshot({
            'path': os.path.join(save_path, 'screenshot.png'),
            'fullPage': True
        })
        logger.debug(f"Screenshot saved for {url}")
    finally:
        await browser.close()

def take_screenshot(url, save_path):
    try:
        asyncio.run(_take_screenshot(url, save_path))
    except Exception as e:
        logger.error(f"Screenshot failed for {url}: {str(e)}")

import requests
import os
import logging
from auth import login
from crawler import ScreenshotCrawler, convert_cookies_for_pyppeteer
from logger import setup_logger
import config

# Disable noisy websocket debug messages
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Set up main logger
logger = setup_logger("main")


def main():
    """
    Main function to authenticate and start the crawler for GK-Hub portal.
    Handles the complete process of logging in and taking screenshots.
    """
    # Create output directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    logger.info(f"Starting GK-Hub backup - output to {config.output_dir}")

    with requests.Session() as session:
        # Set a proper user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GK-Hub-Backup/1.0'
        })

        # Authenticate
        logger.info("Authenticating to GK-Hub...")
        if not login(session, config.login_url, config.username, config.password):
            logger.error("Authentication failed. Please check credentials.")
            return

        logger.info("Authentication successful")

        # Initialize the crawler
        crawler = ScreenshotCrawler(
            session=session,
            base_url=config.base_url,
            output_dir=config.output_dir,
            max_pages=config.MAX_PAGES
        )

        # Start crawling
        logger.info(f"Starting crawler for {config.MAX_PAGES} pages")
        try:
            crawler.crawl()
            logger.info("Screenshot crawling completed successfully")
        except Exception as e:
            logger.error(f"Crawler error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("Process complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}")
        import traceback

        logger.critical(traceback.format_exc())
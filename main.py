import requests
from auth import login
from crawler import ScreenshotCrawler
import config
from logger import setup_logger

logger = setup_logger("main")


def main():
    with requests.Session() as session:
        # Authenticate
        if not login(session, config.login_url, config.username, config.password):
            logger.error("Authentication failed. Exiting.")
            return

        # Create and run crawler
        crawler = ScreenshotCrawler(
            session=session,
            base_url=config.base_url,
            output_dir=config.output_dir,
            max_pages=config.MAX_PAGES
        )
        crawler.crawl()

    logger.info("Screenshot crawling completed successfully")


if __name__ == "__main__":
    main()

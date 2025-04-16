from logger import setup_logger
from auth import login
from crawler import WebsiteCrawler
import requests
from tqdm import tqdm

import config

logger = setup_logger("main")


def main():
    with requests.Session() as session:
        success = login(session, config.login_url, config.username, config.password)
        if success:
            print("Login successful!")
        else:
            print("Login failed.")

        # Initialize progress bars
        with tqdm(desc="HTML Pages", unit="page") as html_pbar, \
                tqdm(desc="Screenshots", unit="shot") as screenshot_pbar, \
                tqdm(desc="Files Downloaded", unit="file") as file_pbar:
            # Create and run crawler
            crawler = WebsiteCrawler(
                session=session,
                base_url=config.base_url,
                output_dir=config.output_dir,
                max_pages=config.MAX_PAGES
            )
            crawler.crawl(html_pbar, screenshot_pbar, file_pbar)

    logger.info("Backup completed successfully")


if __name__ == "__main__":
    main()

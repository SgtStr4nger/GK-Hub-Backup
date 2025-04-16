import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from logger import setup_logger
from screenshot import take_selenium_screenshot

logger = setup_logger("crawler")


def convert_cookies_for_pyppeteer(session_cookies):
    """Convert requests session cookies to Pyppeteer format."""
    cookies = []
    for cookie in session_cookies:
        cookie_dict = {
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path,
            'secure': cookie.secure
        }
        # Omit expires field to avoid format errors
        cookies.append(cookie_dict)

    logger.debug(f"Converted {len(cookies)} cookies for Pyppeteer")
    return cookies


class ScreenshotCrawler:
    def __init__(self, session, base_url, output_dir, max_pages=5):
        self.session = session
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited = set()
        self.queue = []
        self.max_pages = max_pages
        self.processed_count = 0

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Initialized screenshot crawler for {base_url}")
        logger.info(f"Will save screenshots to {output_dir}")
        logger.info(f"Maximum pages to crawl: {max_pages}")

    def _create_directory_structure(self, url):
        """Create directory structure mirroring the website URL structure"""
        # Parse the URL to get the path component
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        # If there's no path, use 'index' for the homepage
        if not path_parts or path_parts[0] == '':
            path_parts = ['index']

        # Create the full path, including domain as the root folder
        full_path = os.path.join(self.output_dir, parsed.netloc, *path_parts)

        # Handle query parameters by appending them as a subfolder
        if parsed.query:
            # Replace special characters that are invalid in filenames
            query_folder = parsed.query.replace('=', '_').replace('&', '_')
            full_path = os.path.join(full_path, f"query_{query_folder}")

        # Create the directory recursively
        os.makedirs(full_path, exist_ok=True)

        logger.debug(f"Created directory structure: {full_path}")
        return full_path

    def _extract_links(self, soup, current_url):
        """Extract all links from the page that belong to the same domain"""
        links = set()
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            # Skip anchor links and javascript
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            # Create absolute URL
            full_url = urljoin(current_url, href)

            # Only include links to the same domain
            if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                links.add(full_url)

        return links

    def _process_page(self, url, screenshot_pbar):
        """Process a single page: take screenshot and extract links"""
        if url in self.visited:
            return

        logger.info(f"Processing page {self.processed_count + 1}/{self.max_pages}: {url}")
        self.visited.add(url)

        try:
            # Fetch page content
            response = self.session.get(url)
            response.raise_for_status()

            # Create directory structure based on URL path
            save_path = self._create_directory_structure(url)

            # Parse HTML to extract links
            soup = BeautifulSoup(response.text, 'html.parser')

            # Save HTML content
            with open(os.path.join(save_path, 'page.html'), 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Convert session cookies for Pyppeteer
            pyppeteer_cookies = convert_cookies_for_pyppeteer(self.session.cookies)

            # Take screenshot with authenticated cookies
            take_selenium_screenshot(url, save_path, self.session.cookies)
            screenshot_pbar.update(1)

            # Extract links for crawling
            new_links = self._extract_links(soup, url)
            # Add new links to the queue if they haven't been visited
            for link in new_links:
                if link not in self.visited:
                    self.queue.append(link)

        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def crawl(self):
        """Start crawling from the base URL"""
        self.queue.append(self.base_url)

        with tqdm(total=self.max_pages, desc="Screenshots", unit="page") as screenshot_pbar:
            while self.queue and self.processed_count < self.max_pages:
                current_url = self.queue.pop(0)
                if current_url not in self.visited:
                    self._process_page(current_url, screenshot_pbar)
                    self.processed_count += 1

            logger.info(f"Crawling completed. Took screenshots of {self.processed_count} pages.")

import os
import asyncio
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

# Import screenshot module
from screenshot import take_screenshot
from logger import setup_logger

logger = setup_logger("crawler")


class WebsiteCrawler:
    def __init__(self, session, base_url, output_dir, max_pages=None):

        self.session = session
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited = set()
        self.queue = []
        self.base_domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.processed_count = 0
        self.crawl_delay = 2

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Initialized crawler for {base_url} with output to {output_dir}")

    def _create_directory_structure(self, url):
        """Create directory structure mirroring the website URL structure"""
        parsed = urlparse(url)
        path = parsed.path.lstrip('/')

        # If path is empty, use 'index' for the homepage
        if not path:
            path = 'index'

        # Handle URL parameters by creating a subdirectory
        if parsed.query:
            path = os.path.join(path, f"query_{parsed.query.replace('=', '_').replace('&', '_')}")

        full_path = os.path.join(self.output_dir, self.base_domain, path)
        os.makedirs(full_path, exist_ok=True)

        # Create downloads directory
        downloads_dir = os.path.join(full_path, 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)

        return full_path

    def _extract_links(self, soup, current_url):
        """Extract all links from the page that belong to the same domain"""
        links = set()
        for tag in soup.find_all(['a', 'link'], href=True):
            href = tag['href']
            # Skip anchor links and javascript
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            # Create absolute URL
            full_url = urljoin(current_url, href)

            # Only include links to the same domain
            if urlparse(full_url).netloc == self.base_domain:
                links.add(full_url)

        return links

    def _download_file(self, url, save_path, file_pbar):
        """Download a file and save it to the specified path"""
        try:
            file_name = os.path.basename(url)
            full_path = os.path.join(save_path, file_name)

            # Skip if file already exists
            if os.path.exists(full_path):
                logger.debug(f"File already exists: {full_path}")
                return

            # Download the file with streaming
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_pbar.update(1)
            logger.debug(f"Downloaded {file_name} ({total_size / 1024:.1f} KB)")

        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")

    def _download_assets(self, soup, base_url, save_path, file_pbar):
        """Download all assets (CSS, JS, images, documents) from the page"""
        # Process CSS files
        for tag in soup.find_all('link', rel='stylesheet', href=True):
            url = urljoin(base_url, tag['href'])
            self._download_file(url, os.path.join(save_path, 'downloads'), file_pbar)

        # Process JS files
        for tag in soup.find_all('script', src=True):
            url = urljoin(base_url, tag['src'])
            self._download_file(url, os.path.join(save_path, 'downloads'), file_pbar)

        # Process images
        for tag in soup.find_all('img', src=True):
            url = urljoin(base_url, tag['src'])
            self._download_file(url, os.path.join(save_path, 'downloads'), file_pbar)

        # Process downloadable files
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if any(href.endswith(ext) for ext in
                   ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.mp4', '.mp3']):
                url = urljoin(base_url, href)
                self._download_file(url, os.path.join(save_path, 'downloads'), file_pbar)

    def _process_page(self, url, html_pbar, screenshot_pbar, file_pbar):
        """Process a single page: save HTML, take screenshot, download assets"""
        if url in self.visited:
            return

        logger.info(f"Processing page {self.processed_count + 1}: {url}")
        self.visited.add(url)

        try:
            # Fetch page content
            response = self.session.get(url)
            response.raise_for_status()

            # Create directory structure
            save_path = self._create_directory_structure(url)

            # Save HTML with proper encoding
            with open(os.path.join(save_path, 'page.html'), 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.debug(f"Saved HTML for {url}")
            html_pbar.update(1)

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Take screenshot - this calls the async function from screenshot.py
            try:
                screenshot_path = os.path.join(save_path, 'screenshot.png')
                take_screenshot(url, save_path)
                screenshot_pbar.update(1)
                logger.debug(f"Saved screenshot for {url}")
            except Exception as e:
                logger.error(f"Failed to take screenshot of {url}: {str(e)}")

            # Download assets
            self._download_assets(soup, url, save_path, file_pbar)

            # Extract links for crawling
            new_links = self._extract_links(soup, url)
            # Add new links to the queue if they haven't been visited
            for link in new_links:
                if link not in self.visited:
                    self.queue.append(link)

        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")

    def crawl(self, html_pbar, screenshot_pbar, file_pbar):
        """Start crawling from the base URL"""
        self.queue.append(self.base_url)

        while self.queue and (self.max_pages is None or self.processed_count < self.max_pages):
            current_url = self.queue.pop(0)
            if current_url not in self.visited:
                self._process_page(current_url, html_pbar, screenshot_pbar, file_pbar)
                self.processed_count += 1

                # Check if we've reached the maximum number of pages
                if self.max_pages and self.processed_count >= self.max_pages:
                    logger.info(f"Reached maximum page limit of {self.max_pages}")
                    break

        logger.info(f"Crawling completed. Processed {self.processed_count} pages.")

        # Print summary
        logger.info(f"Total pages processed: {self.processed_count}")
        logger.info(f"Total pages in queue: {len(self.queue)}")
        logger.info(f"Total unique pages visited: {len(self.visited)}")

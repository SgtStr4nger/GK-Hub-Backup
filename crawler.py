import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from logger import setup_logger
import requests

logger = setup_logger("crawler")


class WebsiteCrawler:
    def __init__(self, session, base_url, output_dir):
        self.session = session
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited = set()
        self.queue = []
        self.base_domain = urlparse(base_url).netloc

    def _create_directory_structure(self, url):
        parsed = urlparse(url)
        path = parsed.path.lstrip('/')
        full_path = os.path.join(self.output_dir, self.base_domain, path)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def _extract_links(self, soup, current_url):
        links = set()
        for tag in soup.find_all(['a', 'link'], href=True):
            href = tag['href']
            full_url = urljoin(current_url, href)
            if urlparse(full_url).netloc == self.base_domain:
                links.add(full_url)
        return links

    def _process_page(self, url, html_pbar, screenshot_pbar, file_pbar):
        if url in self.visited:
            return
        self.visited.add(url)

        try:
            # Fetch page content
            response = self.session.get(url)
            response.raise_for_status()

            # Create directory structure
            save_path = self._create_directory_structure(url)

            # Save HTML
            with open(os.path.join(save_path, 'page.html'), 'w', encoding='utf-8') as f:
                f.write(response.text)
            html_pbar.update(1)

            # Take screenshot
            take_screenshot(url, save_path)
            screenshot_pbar.update(1)

            # Process downloads
            soup = BeautifulSoup(response.text, 'html.parser')
            self._download_assets(soup, url, save_path, file_pbar)

            # Extract links for crawling
            new_links = self._extract_links(soup, url)
            self.queue.extend([link for link in new_links if link not in self.visited])

        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")

    def _download_assets(self, soup, base_url, save_path, file_pbar):
        for tag in soup.find_all(['a', 'img', 'script', 'link']):
            url = tag.get('href') or tag.get('src')
            if url and any(url.endswith(ext) for ext in ['.mp4', '.pptx', '.xlsx', '.pdf']):
                full_url = urljoin(base_url, url)
                download_file(self.session, full_url, os.path.join(save_path, 'downloads'), file_pbar)

    def crawl(self, html_pbar, screenshot_pbar, file_pbar):
        self.queue.append(self.base_url)
        while self.queue:
            current_url = self.queue.pop(0)
            self._process_page(current_url, html_pbar, screenshot_pbar, file_pbar)

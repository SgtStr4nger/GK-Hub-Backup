import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from logger import setup_logger

# Set up logging
logger = setup_logger("selenium_screenshot")

# Disable webdriver-manager logs
logging.getLogger('WDM').setLevel(logging.ERROR)


def take_selenium_screenshot(url, save_path, session_cookies):
    """
    Take a full-page screenshot using Selenium WebDriver with improved WebDriver Manager handling

    Args:
        url: URL to capture
        save_path: Directory to save screenshot
        session_cookies: Cookies from the authenticated requests session

    Returns:
        bool: True if screenshot was successful, False otherwise
    """
    logger.info(f"Taking Selenium screenshot of: {url}")

    # Ensure directory exists
    os.makedirs(save_path, exist_ok=True)
    screenshot_path = os.path.join(save_path, 'screenshot.png')

    # Configure Chrome options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")

    # Add user agent to match your crawler
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) GK-Hub-Backup/1.0")

    driver = None
    try:
        # Initialize WebDriver with improved version handling
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            logger.warning(f" ChromeDriver failed: {str(e)}")

        # First go to the domain root to set cookies
        domain_parts = url.split('/')
        domain_url = f"{domain_parts[0]}//{domain_parts[2]}"
        logger.info(f"Visiting domain for cookie setup: {domain_url}")
        driver.get(domain_url)

        # Set cookies from the authenticated session
        logger.info(f"Setting {len(session_cookies)} cookies")
        for cookie in session_cookies:
            # Convert cookies to the format Selenium expects
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'secure': cookie.secure
            }

            # Filter out attributes Selenium doesn't support
            cookie_attrs_to_remove = ['httpOnly', 'expiry', 'sameSite', 'expires']
            for attr in cookie_attrs_to_remove:
                if attr in cookie_dict and attr in cookie_dict:
                    del cookie_dict[attr]

            try:
                driver.add_cookie(cookie_dict)
            except Exception as e:
                logger.warning(f"Could not add cookie {cookie.name}: {str(e)}")

        # Navigate to target URL
        logger.info(f"Navigating to: {url}")
        driver.get(url)

        # Wait for the page to load
        logger.info("Waiting for page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for specific GK-Hub elements (based on the image)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Start')]"))
            )
            logger.info("Start found")
        except:
            logger.warning("Could not find start, continuing anyway")

        # FIX: Improved scrolling with actual delays to load lazy content
        logger.info("Scrolling to load all content...")
        driver.execute_script("""
            return new Promise((resolve) => {
                window.scrollTo(0, 0);
                var totalHeight = document.body.scrollHeight;
                var distance = 300;
                var currentPosition = 0;
                var timer = setInterval(() => {
                    window.scrollTo(0, currentPosition);
                    currentPosition += distance;

                    if(currentPosition >= totalHeight){
                        clearInterval(timer);
                        window.scrollTo(0, 0);
                        setTimeout(resolve, 500);  // Final delay before resolving
                    }
                }, 200);  // 200ms between scrolls
            });
        """)

        # Additional wait for lazy-loaded images after scrolling
        logger.info("Waiting for images to load...")
        time.sleep(3)  # Increased wait time for images


        # Get page dimensions
        width = driver.execute_script(
            "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);")
        height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);")
        logger.info(f"Page dimensions: {width}x{height} pixels")

        # Set window size to full page size
        driver.set_window_size(width, height)

        # Wait a bit after resizing the window
        time.sleep(1)

        # Take screenshot
        logger.info(f"Taking screenshot...")
        driver.save_screenshot(screenshot_path)

        if os.path.exists(screenshot_path):
            size_kb = os.path.getsize(screenshot_path) / 1024
            logger.info(f"Screenshot saved to {screenshot_path} ({size_kb:.1f} KB)")
            return True
        else:
            logger.error("Screenshot file wasn't created")
            return False

    except Exception as e:
        logger.error(f"Selenium screenshot error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        if driver:
            try:
                driver.quit()
                logger.debug("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {str(e)}")


def convert_requests_cookies_to_selenium(session_cookies):
    """
    Convert cookies from requests session to Selenium format.
    Use this if you need to convert cookies in a different format.

    Args:
        session_cookies: Cookies from requests.Session()

    Returns:
        list: Cookies in Selenium format
    """
    selenium_cookies = []
    for cookie in session_cookies:
        cookie_dict = {
            'name': cookie.name,
            'value': cookie.value,
            'path': cookie.path,
            'secure': cookie.secure
        }

        # Add domain if present
        if hasattr(cookie, 'domain') and cookie.domain:
            cookie_dict['domain'] = cookie.domain

        selenium_cookies.append(cookie_dict)

    return selenium_cookies
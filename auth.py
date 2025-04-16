import requests
from bs4 import BeautifulSoup
from logger import setup_logger

logger = setup_logger("auth")


def login(session, login_url, username, password):
    try:
        # Get login page
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.content, 'html.parser')

        # Extract CSRF token
        csrf_token = soup.find('input', {'name': '__RequestVerificationToken'})['value']
        language_id = soup.find('input', {'name': 'LanguageId'})['value']

        # Prepare payload with all required fields
        payload = {
            'Email': username,
            'Password': password,
            '__RequestVerificationToken': csrf_token,
            'LanguageId': language_id,
            'DeviceToken': '',
            'AppVersion': ''
        }

        # Perform login
        response = session.post(
            login_url,
            data=payload,
            allow_redirects=True
        )
        response.raise_for_status()

        logger.info(f"Login response status: {response.status_code}")
        logger.info(f"Final URL after login: {response.url}")

        # Basic check for success
        if 'logout' in response.text.lower() or (
                'name="Email"' not in response.text and 'name="Password"' not in response.text):
            logger.info("Login successful")
            return True
        else:
            logger.warning("Login response missing success indicator")
            return False

    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

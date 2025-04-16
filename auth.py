# auth.py
import requests
from bs4 import BeautifulSoup
from logger import setup_logger

logger = setup_logger("auth")


def login(session, login_url, username, password):
    try:
        # Get login page
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.content, 'html.parser')

        # Extract required fields
        csrf_token = soup.find('input', {'name': '__RequestVerificationToken'})['value']
        language_id = soup.find('input', {'name': 'LanguageId'})['value']

        # Prepare payload with ALL required fields
        payload = {
            'Email': username,  # Field name from HTML
            'Password': password,  # Field name from HTML
            '__RequestVerificationToken': csrf_token,
            'LanguageId': language_id,
            'DeviceToken': '',  # Required but empty
            'AppVersion': ''  # Required but empty
        }

        # Perform login
        response = session.post(
            login_url,
            data=payload,
            allow_redirects=True
        )
        response.raise_for_status()

        logger.info(f"Final URL after login: {response.url}")
        logger.debug(f"Response snippet: {response.text[:500]}")

        # Check for various success indicators
        if (
                'logout' in response.text.lower() or
                'dashboard' in response.text.lower() or
                ('name="Email"' not in response.text and 'name="Password"' not in response.text)
        ):
            logger.info("Login successful")
            return True

        # Check for common error messages
        if 'invalid' in response.text.lower() or 'error' in response.text.lower():
            logger.warning("Login failed: Invalid credentials or error message detected.")
            return False

        logger.warning("Login response missing success indicator")
        return False

    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

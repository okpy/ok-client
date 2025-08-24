import hashlib
import os
import pickle
import logging
import tempfile
import requests

# Set cache directory before importing googleapiclient to avoid path conflicts
os.environ['GOOGLE_API_PYTHON_CLIENT_DISCOVERY_CACHE_DIR'] = tempfile.gettempdir()

import google_auth_oauthlib.flow
from google.auth.transport.requests import Request

from client.utils.config import (REFRESH_FILE,
                                 create_config_directory)
from client.utils import network
from client.utils.oauth_config import CLIENT_CONFIG

log = logging.getLogger(__name__)

# OAuth scopes - email and openid (Google automatically adds openid)
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'openid']


def get_credentials(force=False, no_browser=False):
    """
    Handles the OAuth 2.0 flow for desktop applications.
    Returns Google credentials object or None if authentication fails.
    """
    creds = None
    create_config_directory()

    # Try to load existing credentials
    if not force and os.path.exists(REFRESH_FILE):
        try:
            with open(REFRESH_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            log.info("Failed to load cached credentials: {}".format(e))

    # If there are no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                log.info("Refreshing expired credentials...")
                creds.refresh(Request())
            except Exception as e:
                log.info("Failed to refresh credentials: {}".format(e))
                creds = None

        if not creds or not creds.valid:
            log.info("Starting new authentication flow...")
            try:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                    CLIENT_CONFIG, SCOPES, autogenerate_code_verifier=True)
                if no_browser:
                    creds = flow.run_console()
                else:
                    creds = flow.run_local_server(port=0)
            except Exception as e:
                log.info("Authentication flow failed: {}".format(e))
                return None

        # Save the credentials for next run
        if creds and creds.valid:
            try:
                with open(REFRESH_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                log.info("Saved credentials for future use")
            except Exception as e:
                log.warning("Could not save credentials: {}".format(e))

    return creds

def get_user_email_from_api(creds):
    """
    Uses the authenticated credentials to get the user's email address.
    """
    try:
        # Use direct HTTP request instead of discovery API to avoid cache issues

        # Get access token from credentials
        if not creds.valid:
            creds.refresh(Request())

        # Make direct API call to Google's userinfo endpoint
        headers = {'Authorization': f'Bearer {creds.token}'}
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)

        if response.status_code == 200:
            user_info = response.json()
            return user_info.get('email')
        else:
            log.error(f"API request failed with status {response.status_code}: {response.text}")
            return None

    except Exception as e:
        log.error("Failed to get user email from API: {}".format(e))
        return None

def authenticate(force=False, no_browser=False):
    """Returns Google OAuth credentials or None if authentication fails."""
    network.check_ssl()
    return get_credentials(force=force, no_browser=no_browser)

def get_student_email(args=None):
    """Attempts to get the student's email from Google OAuth. Returns the email, or None."""
    log.info("Attempting to get student email from Google")

    no_browser = bool(args and hasattr(args, 'no_browser') and args.no_browser)
    creds = authenticate(force=False, no_browser=no_browser)
    if not creds:
        return None
    try:
        return get_user_email_from_api(creds)
    except Exception as e:
        log.info("Failed to get email even though there are credentials: {}".format(e))
        return None

def get_identifier(args=None):
    """Obtain anonymized identifier."""
    student_email = get_student_email(args)
    if not student_email:
        return "Unknown"
    return hashlib.md5(student_email.encode()).hexdigest()

def test_auth():
    """Test function for developers to verify authentication works."""
    print("Testing Google OAuth authentication...")

    # First, check if we have cached tokens
    has_cached_token = os.path.exists(REFRESH_FILE)

    if has_cached_token:
        print("Found cached token, testing cached authentication...")
        try:
            email = get_student_email()
            if email:
                print("✅ Authentication successful using cached/refreshed token!")
                print("Your email:", email)

                # Now test force re-authentication
                print("\nTesting forced re-authentication...")
                creds = authenticate(force=True)
                if creds:
                    print("✅ Forced re-authentication also successful!")
                else:
                    print("❌ Forced re-authentication failed")
            else:
                print("❌ Authentication failed completely")
        except Exception as e:
            print("❌ Authentication error:", str(e))
    else:
        print("No cached token found, performing fresh authentication...")
        try:
            email = get_student_email()
            if email:
                print("✅ Authentication successful!")
                print("Your email:", email)
            else:
                print("❌ Authentication failed - no email returned")
        except Exception as e:
            print("❌ Authentication error:", str(e))

if __name__ == "__main__":
    test_auth()
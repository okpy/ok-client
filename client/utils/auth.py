import hashlib
import http.server
import os
import pickle
import requests
import time
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser

from client.exceptions import AuthenticationException
from client.utils.config import (CONFIG_DIRECTORY, REFRESH_FILE,
                                 create_config_directory)
from client.utils import network

import logging

log = logging.getLogger(__name__)

CLIENT_ID = 'ok-client'
# The client secret in an installed application isn't a secret.
# See: https://developers.google.com/accounts/docs/OAuth2InstalledApp
CLIENT_SECRET = 'EWKtcCp5nICeYgVyCPypjs3aLORqQ3H'
OAUTH_SCOPE = 'all'

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')

REFRESH_FILE = os.path.join(CONFIG_DIRECTORY, "auth_refresh")

REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 6165

TIMEOUT = 10

INFO_ENDPOINT = '/api/v3/user/'
AUTH_ENDPOINT =  '/oauth/authorize'
TOKEN_ENDPOINT = '/oauth/token'
ERROR_ENDPOINT = '/oauth/errors'

def pick_free_port(hostname=REDIRECT_HOST, port=0):
    """ Try to bind a port. Default=0 selects a free port. """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((hostname, port))  # port=0 finds an open port
    except OSError as e:
        log.warning("Could not bind to %s:%s %s", hostname, port, e)
        if port == 0:
            print('Unable to find an open port for authentication.')
            raise AuthenticationException(e)
        else:
            return pick_free_port(hostname, 0)
    addr, port = s.getsockname()
    s.close()
    return port

def _make_code_post(server, code, redirect_uri):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }
    response = requests.post(server + TOKEN_ENDPOINT, data=data, timeout=TIMEOUT)
    response.raise_for_status()
    info = response.json()
    return info['access_token'], info['refresh_token'], int(info['expires_in'])

def make_refresh_post(server, refresh_token):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    response = requests.post(server + TOKEN_ENDPOINT, data=data, timeout=TIMEOUT)
    response.raise_for_status()
    info = response.json()
    return info['access_token'], int(info['expires_in'])

def get_storage():
    create_config_directory()
    with open(REFRESH_FILE, 'rb') as fp:
        storage = pickle.load(fp)

    access_token = storage['access_token']
    expires_at = storage['expires_at']
    refresh_token = storage['refresh_token']

    return access_token, expires_at, refresh_token


def update_storage(access_token, expires_in, refresh_token):
    if not (access_token and expires_in and refresh_token):
        raise AuthenticationException(
            "Authentication failed and returned an empty token.")

    cur_time = int(time.time())
    create_config_directory()
    with open(REFRESH_FILE, 'wb') as fp:
        pickle.dump({
            'access_token': access_token,
            'expires_at': cur_time + expires_in,
            'refresh_token': refresh_token
        }, fp)

def authenticate(assignment, force=False):
    """Returns an OAuth token that can be passed to the server for
    identification. If FORCE is False, it will attempt to use a cached token
    or refresh the OAuth token. ARGS is the command-line arguments object.
    """
    server = assignment.server_url
    if not force:
        try:
            cur_time = int(time.time())
            access_token, expires_at, refresh_token = get_storage()
            if cur_time < expires_at - 10:
                return access_token
            access_token, expires_in = make_refresh_post(server, refresh_token)

            if not access_token and expires_in:
                raise AuthenticationException(
                    "Authentication failed and returned an empty token.")

            update_storage(access_token, expires_in, refresh_token)
            return access_token
        except IOError as _:
            print('Performing authentication')
        except AuthenticationException as e:
            raise e  # Let the main script handle this error
        except Exception as _:
            print('Performing authentication')

    network.check_ssl()

    print("Please enter your bCourses email.")
    email = input("bCourses email: ")

    host_name = REDIRECT_HOST
    try:
        port_number = pick_free_port(port=REDIRECT_PORT)
    except AuthenticationException as e:
        # Could not bind to REDIRECT_HOST:0, try localhost instead
        host_name = 'localhost'
        port_number = pick_free_port(host_name, 0)

    redirect_uri = "http://{0}:{1}/".format(host_name, port_number)
    log.info("Authentication server running on {}".format(redirect_uri))

    params = {
        'client_id': CLIENT_ID,
        'login_hint': email,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': OAUTH_SCOPE,
    }
    url = '{}{}?{}'.format(server, AUTH_ENDPOINT, urlencode(params))
    webbrowser.open_new(url)

    access_token = None
    refresh_token = None
    expires_in = None
    auth_error = None

    class CodeHandler(http.server.BaseHTTPRequestHandler):
        def send_redirect(self, location):
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()

        def send_failure(self, message):
            params = {
                'error': 'Authentication Failed',
                'error_description': message,
            }
            url = '{}{}?{}'.format(server, ERROR_ENDPOINT, urlencode(params))
            self.send_redirect(url)

        def do_GET(self):
            """Respond to the GET request made by the OAuth"""
            nonlocal access_token, refresh_token, expires_in, auth_error
            log.debug('Received GET request for %s', self.path)
            path = urlparse(self.path)
            qs = parse_qs(path.query)
            try:
                code = qs['code'][0]
                code_response = _make_code_post(server, code, redirect_uri)
                access_token, refresh_token, expires_in = code_response
            except KeyError:
                message = qs.get('error', ['Unknown'])[0]
                log.warning("No auth code provided {}".format(message))
                auth_error = message
            except Exception as e:  # TODO : Catch just SSL errors
                log.warning("Could not obtain token", exc_info=True)
                auth_error = str(e)

            if auth_error:
                self.send_failure(auth_error)
            else:
                self.send_redirect('{}/{}'.format(server, assignment.endpoint))

        def log_message(self, format, *args):
            return

    server_address = (host_name, port_number)

    try:
        httpd = http.server.HTTPServer(server_address, CodeHandler)
        httpd.handle_request()
    except OSError as e:
        log.warning("HTTP Server Err {}".format(server_address), exc_info=True)
        raise

    if not auth_error:
        update_storage(access_token, expires_in, refresh_token)
        return access_token
    else:
        print("Authentication error: {}".format(auth_error))
        return None

def get_student_email(assignment):
    """Attempts to get the student's email. Returns the email, or None."""
    log.info("Attempting to get student email")
    if assignment.cmd_args.local:
        return None
    access_token = authenticate(assignment, force=False)
    if not access_token:
        return None
    try:
        response = requests.get(
            assignment.server_url + INFO_ENDPOINT,
            params={'access_token': access_token},
            timeout=3)
        response.raise_for_status()
        return response.json()['data']['email']
    except IOError as e:
        return None

def get_identifier(assignment):
    """ Obtain anonmyzied identifier."""
    student_email = get_student_email(assignment)
    if not student_email:
        return "Unknown"
    return hashlib.md5(student_email.encode()).hexdigest()

#!/usr/bin/env python3

import http.server

import json
import hashlib
import os
import pickle
import time
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
import webbrowser

from sanction import Client

from client.exceptions import AuthenticationException
from client.utils.config import (CONFIG_DIRECTORY, REFRESH_FILE,
                                 create_config_directory)
from client.utils.html import (auth_html, partial_course_html,
                               partial_nocourse_html, red_css)

import logging

log = logging.getLogger(__name__)

CLIENT_ID = ('931757735585-vb3p8g53a442iktc4nkv5q8cbjrtuonv'
             '.apps.googleusercontent.com')

# The client secret in an installed application isn't a secret.
# See: https://developers.google.com/accounts/docs/OAuth2InstalledApp
CLIENT_SECRET = 'zGY9okExIBnompFTWcBmOZo4'

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')

REFRESH_FILE = os.path.join(CONFIG_DIRECTORY, "auth_refresh")

REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 6165

TIMEOUT = 10
SERVER = 'https://okpy.org'
INFO_ENDPOINT = "https://www.googleapis.com/oauth2/v1/userinfo?access_token={}"


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

def _make_code_post(code, redirect_uri):
    client = Client(
        token_endpoint='https://accounts.google.com/o/oauth2/token',
        resource_endpoint='https://www.googleapis.com/oauth2/v1',
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    params = {"redirect_uri": redirect_uri}
    client.request_token(code=code, **params)
    return client.access_token, client.refresh_token, client.expires_in


def make_refresh_post(refresh_token):
    client = Client(
        token_endpoint='https://accounts.google.com/o/oauth2/token',
        resource_endpoint='https://www.googleapis.com/oauth2/v1',
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    params = {"grant_type": "refresh_token"}
    client.request_token(refresh_token=refresh_token, **params)
    return client.access_token, client.expires_in

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


def check_ssl():
    try:
        import ssl
    except:
        log.warning('Error importing ssl', stack_info=True)
        raise Exception(
                'SSL Bindings are not installed. '
                'You can install python3 SSL bindings or run OK locally:\n'
                '\tpython3 ok --local')
    else:
        log.info('SSL bindings are available.')


def authenticate(force=False):
    """
    Returns an oauth token that can be passed to the server for identification.
    """
    if not force:
        try:
            cur_time = int(time.time())
            access_token, expires_at, refresh_token = get_storage()
            if cur_time < expires_at - 10:
                return access_token
            access_token, expires_in = make_refresh_post(refresh_token)

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

    check_ssl()

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

    c = Client(auth_endpoint='https://accounts.google.com/o/oauth2/auth',
               client_id=CLIENT_ID)
    url = c.auth_uri(scope="profile email", access_type='offline',
                     name='ok-server', redirect_uri=redirect_uri,
                     login_hint=email)

    webbrowser.open_new(url)

    done = False
    access_token = None
    refresh_token = None
    expires_in = None
    auth_error = None

    class CodeHandler(http.server.BaseHTTPRequestHandler):
        def send_failure(self, message):
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(failure_page(message), "utf-8"))

        def do_GET(self):
            """Respond to the GET request made by the OAuth"""
            nonlocal access_token, refresh_token, expires_in, auth_error, done

            path = urlparse(self.path)
            qs = parse_qs(path.query)
            try:
                code = qs['code'][0]
                code_response = _make_code_post(code, redirect_uri)
                access_token, refresh_token, expires_in = code_response
            except KeyError:
                message = qs.get('error', 'Unknown')
                log.warning("No auth code provided {}".format(message))
                auth_error = message
                done = True
                self.send_failure(message)
                return
            except Exception as e:  # TODO : Catch just SSL errors
                log.warning("Could not obtain token", exc_info=True)
                auth_error = e.message
                done = True
                self.send_failure(e.message)
                return

            done = True
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            actual_email = email

            try:
                email_resp = get_student_email(access_token)
                if email_resp:
                    actual_email = email_resp
            except Exception as e:  # TODO : Catch just SSL errors
                log.warning("Could not get email from token", exc_info=True)

            reponse = success_page(SERVER, actual_email, access_token)
            self.wfile.write(bytes(reponse, "utf-8"))

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


def success_page(server, email, access_token):
    """ Generate HTML for the auth page.
        Fetches courses and plug into templates.
    """
    API = server + '/api/v3/enrollment/{0}/?access_token={1}'.format(
        email, access_token)
    try:
        data = urlopen(API).read().decode("utf-8")
        log.debug("Enrollment API {} resp: {}".format(API, data))
        success_data = success_courses(email, data, server)
    except:
        log.debug("Enrollment for {} failed".format(email), exc_info=True)
        return success_auth(success_courses(email, '[]', server))
    return success_auth(success_data)


def failure_page(error):
    html = partial_nocourse_html
    title = 'Authentication Error'
    byline = 'Error: {}'.format(error)
    status = 'We could not authenticate you.'
    head = '<style>{0}</style>'.format(red_css)
    return auth_html.format(
        site=SERVER,
        status=status,
        courses=html,
        byline=byline,
        title=title,
        head=head)


def success_courses(email, response, server):
    """Generates HTML for individual courses"""
    response = json.loads(response)

    if response and response['data'].get('courses', []):
        courses = response['data']['courses']
        template_course = partial_course_html
        html = ''
        for course in courses:
            html += template_course.format(**course['course'])

        status = "Scroll for more: {0}".format(
            ', '.join(course['course']['display_name'] for course in courses))
        byline = '"{}" is currently enrolled in {}.'.format(
            email, pluralize(len(courses), ' course'))
        title = 'Ok!'
        head = ''
    else:
        html = partial_nocourse_html
        byline = 'The email "{}" is not enrolled. Is it correct?'.format(email)
        status = 'No courses found'
        title = 'Uh oh'
        head = '<style>{0}</style>'.format(red_css)
    return html, status, byline, title, head, server


def success_auth(data):
    """Generates finalized HTML"""
    return auth_html.format(
        site=data[5],
        status=data[1],
        courses=data[0],
        byline=data[2],
        title=data[3],
        head=data[4])

def get_file(relative_path, purpose):
    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, relative_path)
    return open(filename, purpose)

def get_contents(relative_path, purpose='r'):
    return get_file(relative_path, purpose).read()

def pluralize(num, string):
    return str(num)+string+('s' if num != 1 else '')

# Grabs the student's email through the access_token and returns it.
def get_student_email(access_token):
    log.info("Attempting to get student email")
    if access_token is None:
        return None
    try:
        request = urlopen(INFO_ENDPOINT.format(access_token), timeout=3)
        user_data = json.loads(request.read().decode("utf-8"))
        user_email = user_data["email"]
    except IOError as e:
        user_email = None
    return user_email

def get_identifier(token=None, email=None):
    """ Obtain anonmyzied identifier."""
    if not token:
        token = authenticate(False)
    if email:
        student_email = email
    else:
        student_email = get_student_email(token)
        if not student_email:
            return "Unknown"
    return hashlib.md5(student_email.encode()).hexdigest()

if __name__ == "__main__":
    print(authenticate())

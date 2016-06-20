#!/usr/bin/env python3

from client import exceptions

from .sanction import Client
from urllib.parse import urlparse, parse_qs
import http.server
import os
import pickle
import sys
import time
import webbrowser
from urllib.request import urlopen
import json
from .html import auth_html, partial_course_html, partial_nocourse_html, red_css

import logging

log = logging.getLogger(__name__)

OK_SERVER = 'https://ok.cs61a.org'

CLIENT_ID = \
    '931757735585-vb3p8g53a442iktc4nkv5q8cbjrtuonv.apps.googleusercontent.com'
# The client secret in an installed application isn't a secret.
# See: https://developers.google.com/accounts/docs/OAuth2InstalledApp
CLIENT_SECRET = 'zGY9okExIBnompFTWcBmOZo4'
REFRESH_FILE = '.ok_refresh'
REDIRECT_HOST = "localhost"
TIMEOUT = 10

def pick_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', 0)) # find an open port
    except OSError as e:
        print('Unable to find an open port for authentication.')
        raise exceptions.AuthenticationException(e)
    addr, port = s.getsockname()
    s.close()
    return port

REDIRECT_PORT = pick_free_port()
REDIRECT_URI = "http://%s:%u/" % (REDIRECT_HOST, REDIRECT_PORT)

def _make_code_post(code):
    client = Client(
        token_endpoint='https://accounts.google.com/o/oauth2/token',
        resource_endpoint='https://www.googleapis.com/oauth2/v1',
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    params = {"redirect_uri": REDIRECT_URI}
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
    with open(REFRESH_FILE, 'rb') as fp:
        storage = pickle.load(fp)
    return storage['access_token'], storage['expires_at'], storage['refresh_token']

def update_storage(access_token, expires_in, refresh_token):
    cur_time = int(time.time())
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
            update_storage(access_token, expires_in, refresh_token)
            return access_token
        except IOError as _:
            print('Performing authentication')
        except Exception as _:
            print('Performing authentication')

    check_ssl()

    print("Please enter your bCourses email.")
    email = input("bCourses email: ")

    c = Client(auth_endpoint='https://accounts.google.com/o/oauth2/auth',
               client_id=CLIENT_ID)
    url = c.auth_uri(scope="profile email", access_type='offline',
                     name='ok-server', redirect_uri=REDIRECT_URI,
                     login_hint=email)

    webbrowser.open_new(url)

    host_name = REDIRECT_HOST
    port_number = REDIRECT_PORT

    done = False
    access_token = None
    refresh_token = None
    expires_in = None

    class CodeHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            """Respond to the GET request made by the OAuth"""
            path = urlparse(self.path)
            nonlocal access_token, refresh_token, expires_in, done
            qs = parse_qs(path.query)
            code = qs['code'][0]
            access_token, refresh_token, expires_in = _make_code_post(code)

            done = True
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            reponse = success_page(OK_SERVER, email, access_token)
            self.wfile.write(bytes(reponse, "utf-8"))

        def log_message(self, format, *args):
            return

    server_address = (host_name, port_number)
    httpd = http.server.HTTPServer(server_address, CodeHandler)
    httpd.handle_request()

    update_storage(access_token, expires_in, refresh_token)
    return access_token


def success_page(server, email, access_token):
    """Generate HTML for the auth page - fetch courses and plug into templates"""
    API = server + '/api/v3/enrollment/{0}/?access_token={1}'.format(
        email, access_token)
    try:
        data = urlopen(API).read().decode("utf-8")
        success_data = success_courses(email, data, server)
    except:
        log.debug("Enrollment for {} failed".format(email), exc_info=True)
        return success_auth(success_courses(email, '[]', server))
    return success_auth(success_data)


def success_courses(email, response, server):
    """Generates HTML for individual courses"""
    response = json.loads(response)

    if response and response['data'].get('courses', []):
        courses = response['data']['courses']
        template_course = partial_course_html
        html = ''
        for course in courses:
            html += template_course.format(**course['course'])
        status = 'Enrolled in: '+', '.join([c['course']['display_name'] for c in courses])
        byline = '"%s" is currently enrolled in %s.' % (email, pluralize(len(courses), ' course'))
        title = 'Ok!'
        head = ''
    else:
        html = partial_nocourse_html
        byline = 'The email "%s" is not enrolled. Is it correct?' % email
        status = 'No courses found'
        title = 'Uh oh'
        head = '<style>%s</style>' % red_css
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

if __name__ == "__main__":
    print(authenticate())

#!/usr/bin/env python3

import http.server
import json
import os
import pickle
import sys
import time
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
import webbrowser

from client.exceptions import AuthenticationException
from client.utils.html import auth_html, partial_course_html, \
                              partial_nocourse_html, red_css
from client.utils.sanction import Client

import logging

log = logging.getLogger(__name__)

CLIENT_ID = \
    '931757735585-vb3p8g53a442iktc4nkv5q8cbjrtuonv.apps.googleusercontent.com'
# The client secret in an installed application isn't a secret.
# See: https://developers.google.com/accounts/docs/OAuth2InstalledApp
CLIENT_SECRET = 'zGY9okExIBnompFTWcBmOZo4'

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')
    
REFRESH_FILE = os.path.join(CONFIG_DIRECTORY, "auth_refresh")
REDIRECT_HOST = "localhost"
TIMEOUT = 10

SERVER = 'http://ok-server.appspot.com'


def pick_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', 0))  # find an open port
    except OSError as e:
        print('Unable to find an open port for authentication.')
        raise AuthenticationException(e)
    addr, port = s.getsockname()
    s.close()
    return port

REDIRECT_PORT = pick_free_port()
REDIRECT_URI = "http://{0}:{1}/".format(REDIRECT_HOST, REDIRECT_PORT)


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


def create_config_directory():
    if not os.path.exists(CONFIG_DIRECTORY):
        os.makedirs(CONFIG_DIRECTORY)


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
        def send_failure(self, message):
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(failure_page(message), "utf-8"))

        def do_GET(self):
            """Respond to the GET request made by the OAuth"""
            nonlocal access_token, refresh_token, expires_in, done

            path = urlparse(self.path)
            qs = parse_qs(path.query)

            try:
                code = qs['code'][0]
                access_token, refresh_token, expires_in = _make_code_post(code)
            except KeyError:
                message = qs.get('error', 'Unknown')
                log.warning("No auth code provided {}".format(message))
                done = True
                self.send_failure(message)
                return
            except Exception as e:  # TODO : Catch just SSL errors
                log.warning("Could not obtain token", exc_info=True)
                done = True
                self.send_failure(e.message)
                return

            done = True
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(success_page(SERVER, email), "utf-8"))

        def log_message(self, format, *args):
            return

    server_address = (host_name, port_number)
    httpd = http.server.HTTPServer(server_address, CodeHandler)
    httpd.handle_request()

    update_storage(access_token, expires_in, refresh_token)
    return access_token


def success_page(server, email):
    """Generate HTML for the auth page - fetch courses and plug into templates.
    """
    API = server + '/enrollment?email=%s' % email
    data = urlopen(API).read().decode("utf-8")
    return success_auth(success_courses(email, data, server))


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
    courses = json.loads(response)
    if len(courses) > 0:
        template_course = partial_course_html
        html = ''
        for course in courses:
            html += template_course.format(**course)

        status = "Scroll for more: {0}".format(
            ', '.join(course['display_name'] for course in courses))
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
    if access_token == None:
        return None
    try:
        user_dic = json.loads(urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token=" + \
            access_token, timeout = 1).read().decode("utf-8"))
        user_email = user_dic["email"]
    except IOError as e:
        user_email = None
    return user_email

if __name__ == "__main__":
    print(authenticate())

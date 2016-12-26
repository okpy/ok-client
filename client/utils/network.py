"""This module contains utilities for communicating with the ok server."""

from urllib import request, error
import json
import logging
import sys

log = logging.getLogger(__name__)

TIMEOUT = 15
SSL_ERROR_MESSAGE = """
ERROR: Your Python installation does not support SSL. You may need to
install OpenSSL and reinstall Python. In the meantime, you can run OK
locally, but you will not be able to back up or submit:
\tpython3 ok --local
""".strip()

def check_ssl():
    """Attempts to import SSL or raises an exception."""
    try:
        import ssl
    except:
        log.warning('Error importing SSL module', stack_info=True)
        print(SSL_ERROR_MESSAGE)
        sys.exit(1)
    else:
        log.info('SSL module is available')

def api_request(access_token, server, route, insecure=False, arguments={}):
    """Makes a request to the server API and returns the result."""
    try:
        prefix = "http" if insecure else "https"
        address = prefix + "://" + server + '/api/v3'
        address += route if route.startswith('/') else '/' + route
        address += "?access_token={0}".format(
            access_token)
        for arg in arguments:
            address += "&{0}={1}".format(arg, arguments[arg])
        log.info('Requesting data from %s', address)
        req = request.Request(address)
        arguments = []
        response = request.urlopen(req, None, TIMEOUT)
        return json.loads(response.read().decode('utf-8'))
    except error.HTTPError as ex:
        log.warning('Error while requesting from server: %s', str(ex))
        response = ex.read().decode('utf-8')
        response_json = json.loads(response)
        log.warning('Server error message: %s', response_json['message'])
        if ex.code == 401:
            print("Only members of the course staff can access this feature.")
            return
        return response_json

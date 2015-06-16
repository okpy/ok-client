"""This module contains utilities for communicating with the ok server."""

from urllib import request, error
import json
import time
import datetime
import socket

TIMEOUT = 500
RETRY_LIMIT = 5
            
def api_request(access_token, server, route, version, log, 
        insecure=False, arguments={}):
    """Makes a request to the server API and returns the result."""
    try:
        prefix = "http" if insecure else "https"
        address = prefix + "://" + server + '/api/v1'
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
        try:
            if ex.code == 401:
                print("Only members of the course staff can export submissions.")
                return
            if ex.code == 403:
                if software_update(response_json['data']['download_link'], log):
                    raise SoftwareUpdated
            return response_json
        except Exception as e:
            raise e
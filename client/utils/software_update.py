import json
import logging
import os
import urllib.error
import urllib.request
from socket import error as socket_error

log = logging.getLogger(__name__)

VERSION_ENDPOINT = 'https://{server}/api/v1/version'
SHORT_TIMEOUT = 3  # seconds

def check_version(server, version, filename, timeout=SHORT_TIMEOUT):
    """Check for the latest version of OK and update accordingly."""

    address = VERSION_ENDPOINT.format(server=server)

    print('Checking for software updates...')
    log.info('Existing OK version: %s', version)
    log.info('Checking latest version from %s', address)

    try:
        request = urllib.request.Request(address)
        response = urllib.request.urlopen(request, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, socket_error) as e:
        print('Network error when checking for updates.')
        log.warning('Network error when checking version from %s: %s', address,
                    str(e), stack_info=True)
        return False

    response_json = json.loads(response.read().decode('utf-8'))
    if not _validate_api_response(response_json):
        print('Error while checking updates: malformed server response')
        log.info('Malformed response from %s: %s', address,
                 json.dumps(response_json))
        return False

    current_version = response_json['data']['results'][0]['current_version']
    if current_version == version:
        print('OK is up to date')
        return True

    download_link = response_json['data']['results'][0]['current_download_link']
    log.info('Downloading version %s from %s', current_version, download_link)

    try:
        request = urllib.request.Request(download_link)
        response = urllib.request.urlopen(request, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, socket_error) as e:
        print('Error when downloading new version of OK')
        log.warning('Error when downloading new version of OK: %s', str(e),
                    stack_info=True)
        return False

    log.info('Writing new version to %s', filename)

    zip_binary = response.read()
    try:
        _write_zip(filename, zip_binary)
    except IOError as e:
        print('Error when downloading new version of OK')
        log.warning('Error writing to %s: %s', filename, str(e))
        return False
    else:
        print('Updated to version: {}'.format(current_version))
        log.info('Successfully wrote to %s', filename)
        return True

def _validate_api_response(data):
    return isinstance(data, dict) and \
           'data' in data and \
           isinstance(data['data'], dict) and \
           'results' in data['data'] and \
           isinstance(data['data']['results'], list) and \
           len(data['data']['results']) > 0 and \
           isinstance(data['data']['results'][0], dict) and \
           'current_version' in data['data']['results'][0] and \
           'current_download_link' in data['data']['results'][0]



def _write_zip(zip_name, zip_contents):
    with open(zip_name, 'wb') as f:
        f.write(zip_contents)
        os.fsync(f)

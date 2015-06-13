import client
import json
import logging
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

# TODO(sumukh): does software update require ssl?
VERSION_ENDPOINT = 'https://{server}/api/v1/version'

def check_version(server):
    """Check for the latest version of OK and update accordingly."""

    address = VERSION_ENDPOINT.format(server=server)
    log.info('Checking latest version from %s', address)

    request = urllib.request.Request(address)
    response = urllib.request.urlopen(request)
    response_json = json.loads(response.read().decode('utf-8'))

    current_version = response_json['data']['results'][0]['current_version']
    if current_version == client.__version__:
        log.info('OK is up to date')
        return

    download_link = response_json['data']['results'][0]['current_download_link']
    log.info('Downloading version %s from %s', current_version, download_link)

    try:
        request = urllib.request.Request(download_link)
        response = urllib.request.urlopen(request)
    except error.HTTPError as e:
        print('Error when downloading new version of OK')
        log.warning('Error when downloading new version of OK: %s', str(e),
                    stack_info=True)
        return

    log.info('Writing new version to %s', client.FILE_NAME)

    zip_binary = response.read()
    try:
        with open(client.FILE_NAME, 'wb') as f:
            f.write(zip_binary)
            os.fsync(f)
    except IOError as e:
        print('Error when downloading new version of OK')
        log.warning('Error writing to %s: %s', client.FILE_NAME, str(e))
    else:
        print('Update complete. New version: {}'.format(current_version))
        log.info('Successfully wrote to %s', client.FILE_NAME)


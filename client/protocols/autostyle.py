from client.protocols.common import models
from client.utils import auth
import client

import json
import logging
import urllib.error
import urllib.request
import webbrowser

log = logging.getLogger(__name__)

class AutoStyleProtocol(models.Protocol):

    # Timeouts are specified in seconds.
    SHORT_TIMEOUT = 2
    RETRY_LIMIT = 5
    API_ENDPOINT = '{prefix}://{server}'

    def run(self, messages):
        if not self.args.style:
            log.info("Autostyle not enabled.")
            return
        elif self.args.local:
            log.info("Autostyle requires network access.")
            return

        if not messages.get('analytics'):
            log.warning("Autostyle needs to be after analytics")
            return

        messages['analytics']['identifier'] = auth.get_identifier()

        # Send data to autostyle
        response_url = self.send_messages(messages, self.SHORT_TIMEOUT)
        # Parse response_url
        if response_url:
            print(response_url)
            webbrowser.open_new(response_url)
        else:
            log.info("Invalid response from autostyle")

    def send_messages(self, messages, timeout):
        """Send messages to server, along with user authentication."""

        data = {
            'assignment': self.assignment.endpoint,
            'messages': messages,
            'submit': self.args.submit
        }
        serialized_data = json.dumps(data).encode(encoding='utf-8')

        server = "localhost:5000/ok_launch/"
        address = self.API_ENDPOINT.format(server=server,
                prefix='http' if self.args.insecure else 'https')
        address_params = {
            'client_name': 'ok-client',
            'client_version': client.__version__,
        }
        address += '?'
        address += '&'.join('{}={}'.format(param, value)
                            for param, value in address_params.items())

        log.info('Sending messages to %s', address)
        try:
            request = urllib.request.Request(address)
            request.add_header("Content-Type", "application/json")

            response = urllib.request.urlopen(request, serialized_data, timeout)
            response_dict = json.loads(response.read().decode('utf-8'))
            return response_dict['url']
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.decoder.JSONDecodeError) as ex:
            log.warning('%s: %s', ex.__class__.__name__, str(ex))
        return

protocol = AutoStyleProtocol

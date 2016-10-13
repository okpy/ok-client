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
    SHORT_TIMEOUT = 10
    API_ENDPOINT = '{prefix}://{server}'
    ALLOW_QUESTIONS = ['flatten', 'add_up', 'permutations', 'deep_len']

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
        if not messages.get('grading'):
            log.warning("Autostyle needs to be after grading")
            return
        if not self.args.question:
            log.warning("Autostyle requires a specific question")
            return
        messages['autostyle'] = {}

        grading = messages['grading']

        if not self.args.question:
            log.info("-q flag was not specified")
            print("*" * 69)
            print("To use AutoStyle you must specify the -q flag!")
            print("*" * 69)
            return
        for question in self.args.question:
            if question in AutoStyleProtocol.ALLOW_QUESTIONS:
                # Ensure that all tests have passed
                results = grading.get(question)
                if not results:
                    log.warning("No grading info")
                    return
                elif results['failed'] or results['locked']:
                    log.warning("Has not passed all tests")
                    print("*" * 69)
                    print(
                        "To use AutoStyle you must have a correct solution for {0}!".format(question))
                    print("*" * 69)
                    return
            else:
                log.info("Not an autostyle question")
                print("*" * 69)
                print("Make sure the question you are using is an AutoStyle question!")
                print("*" * 69)
                return

        print("Once you begin you must finish the experiment in one sitting. This will take at most 2 hours.")
        confirm = input("Do you wish to continue to AutoStyle? (y/n): ")
        if confirm.lower().strip() != 'y':
            return

        messages['analytics']['identifier'] = auth.get_identifier()
        # Send data to autostyle
        response_url = self.send_messages(messages, self.SHORT_TIMEOUT)
        # Parse response_url
        if response_url:
            webbrowser.open_new(response_url)
        else:
            log.error("There was an error with AutoStyle. Please try again later!")

    def send_messages(self, messages, timeout):
        """Send messages to server, along with user authentication."""
        data = {
            'assignment': self.assignment.endpoint,
            'messages': messages,
            'submit': self.args.submit
        }
        serialized_data = json.dumps(data).encode(encoding='utf-8')
        server = 'codestyle.herokuapp.com/ok_launch/'
        address = self.API_ENDPOINT.format(server=server, prefix='http' if self.args.insecure else 'https')
        address_params = {
            'client_name': 'ok-client',
            'client_version': client.__version__,
        }
        address += '?'
        address += '&'.join('{}={}'.format(param, value) for param, value in address_params.items())

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

from client.protocols.common import models
from client.protocols.grading import grade
from client.utils import output

from client.utils import auth, format

import client

import json
import logging
import urllib.error
import urllib.request
import platform
import time

import webbrowser

log = logging.getLogger(__name__)

class CollaborateProtocol(models.Protocol):

    # Timeouts are specified in seconds.
    SHORT_TIMEOUT = 10
    API_ENDPOINT = '{prefix}://{server}'
    FIREBASE_CONFIG = {
        'apiKey': "AIzaSyAFJn-q5SbxJnJcPVFhjxd25DA5Jusmd74",
        'authDomain': "ok-server.firebaseapp.com",
        'databaseURL': "https://ok-server.firebaseio.com",
        'storageBucket': "ok-server.appspot.com"
    }

    def run(self, messages):
        if not self.args.collab:
            return
        elif self.args.local:
            log.info("Collaborate requires network access.")
            return

        if not messages.get('file_contents'):
            log.warning("Collaborate needs to be after file contents")
            return
        if not messages.get('analytics'):
            log.warning("Collaborate needs to be after analytics")
            return

        messages['collaborate'] = {}

        try:
            print("Starting collaboration mode.")
            self.start_firebase(messages)
        except (Exception, KeyboardInterrupt) as e:
            print("Exiting collaboration mode.")
            if hasattr(self, 'stream') and self.stream:
                self.stream.close()
            if hasattr(self, 'presence'):
                (self.fire_db.child("session{}".format(self.session_id))
                     .child('clients').child(self.presence['name'])
                    .remove(self.fire_user['idToken']))
            log.warning("Exception while waiting", exc_info=True)

    def start_firebase(self, messages):
        print("running")
        access_token = auth.authenticate(False)
        email = auth.get_student_email(access_token)
        identifier = auth.get_identifier(token=access_token)

        pyrebase = install_and_return('pyrebase')
        firebase = pyrebase.initialize_app(self.FIREBASE_CONFIG)
        self.fire_auth = firebase.auth()
        self.fire_db = firebase.database()

        data = {
            'access_token': access_token,
            'email': email,
            'identifier': identifier,
            'file_contents': messages.get('file_contents'),
            'analytics': messages.get('analytics'),
            'assignment': self.assignment.endpoint
        }

        # Send data to collaborate server
        response_data = self.send_messages(data, self.SHORT_TIMEOUT)
        print(response_data)
        self.session_id = response_data['session']
        # Login as the firebase user
        email, password = response_data.get('login_user'), response_data.get('password')
        self.fire_user = self.fire_auth.sign_in_with_email_and_password(email, password)

        self.stream = (self.fire_db.child("session{}".format(self.session_id))
                                   .child('chat').stream(self.stream_listener,
                                                         self.fire_user['idToken']))

        self.presence = (self.fire_db.child("session{}".format(self.session_id))
                             .child('clients').push({'computer': platform.node(),
                                                     'email': email},
                                                    self.fire_user['idToken']))

        # Parse response_url
        if response_data:
            webbrowser.open_new(response_data['url'])
        else:
            log.error("There was an error with the server. Please try again later!")
            return

        while True:
            data = input("[Collaboration Mode] Type in q to quit: ")
            time.sleep(1)
            if data.strip() == 'q':
                raise ValueError('Done with session')



    def send_messages(self, data, timeout):
        """Send messages to server, along with user authentication."""
        serialized_data = json.dumps(data).encode(encoding='utf-8')
        server = 'localhost:5000/collab/start'
        # address = self.API_ENDPOINT.format(server=server, prefix='http' if self.args.insecure else 'https')
        address = "http://" + server

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
            return response_dict
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.decoder.JSONDecodeError) as ex:
            message = '{}: {}'.format(ex.__class__.__name__, str(ex))
            log.warning(message)
            print(message)
        return

    def stream_listener(self, data):
        print(data)
        test_names = [t.name for t in self.assignment.specified_tests]
        (self.fire_db.child("session{}".format(self.session_id)).child('term')
             .push({"status": 'Running',
                    'text': "Running tests for: {}".format(test_names)},
                   self.fire_user['idToken']))
        grading_results = self.grade()
        (self.fire_db.child("session{}".format(self.session_id)).child('term')
             .push({"status": 'Done', 'text': str(grading_results['output']),
                    'grading': grading_results['grading']},
                   self.fire_user['idToken']))

    def grade(self, question=None):
        data = {}
        log_id = output.new_log()

        grade(self.assignment.specified_tests, data, verbose=self.args.verbose)
        printed_output = ''.join(output.get_log(log_id))

        output.remove_log(log_id)
        data['output'] = printed_output
        return data


protocol = CollaborateProtocol

def install_and_return(package):
    """Dynamically install a package through pip.
    Usage: install_and_import('requests')
    Source: http://stackoverflow.com/a/24773951/411514
    """
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        log.info("Installing {} via pip".format(package))
        print("Installing a dependency. Please wait")
        import pip
        pip.main(['install', package])
    finally:
        return importlib.import_module(package)

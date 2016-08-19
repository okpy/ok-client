from client.protocols.common import models
from client.protocols.grading import grade
from client.utils import output
from client.api import assignment

from client.utils import auth, format

import client

import os
import sys
import shutil

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

    FILE_TIME_FORMAT = '%m_%d_%H_%M_%S'
    TIME_FORMAT = '%m/%d %H:%M:%S'
    BACKUP_DIRECTORY = 'ok-collab'


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

        self.file_contents = messages.get('file_contents', {})
        self.collab_analytics = {'save': [], 'grade': []}
        messages['collaborate'] = self.collab_analytics

        self.collab_analytics['launch'] = time.strftime(self.TIME_FORMAT)
        try:
            print("Starting collaboration mode.")
            self.start_firebase(messages)
        except (Exception, KeyboardInterrupt, AttributeError) as e:
            print("Exiting collaboration mode.")
            self.collab_analytics['exit'] = time.strftime(self.TIME_FORMAT)

            if hasattr(self, 'stream') and self.stream:
                self.stream.close()
            if hasattr(self, 'presence'):
                (self.get_firebase()
                     .child('clients').child(self.presence['name'])
                    .remove(self.fire_user['idToken']))
            log.warning("Exception while waiting", exc_info=True)

    def start_firebase(self, messages):
        access_token = auth.authenticate(False)
        email = auth.get_student_email(access_token)
        identifier = auth.get_identifier(token=access_token)

        pyrebase = install_and_return('pyrebase')
        firebase = pyrebase.initialize_app(self.FIREBASE_CONFIG)
        self.fire_auth = firebase.auth()
        self.fire_db = firebase.database()

        self.user_email = email
        self.hostname = platform.node()

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

        self.session_id = response_data['session']
        self.login_user = response_data.get('login_user')

        # Login as the firebase user
        email, password = response_data.get('login_user'), response_data.get('password')
        try:
            self.fire_user = self.fire_auth.sign_in_with_email_and_password(email, password)
            self.fire_uid = self.fire_user['localId']

        except (ValueError, KeyError) as e:
            log.warning("Could not login", exc_info=True)
            print("Could not login to the collaboration server.")

        self.stream = (self.get_firebase()
                           .child('actions').stream(self.stream_listener,
                                                    self.fire_user['idToken']))

        self.presence = (self.get_firebase()
                             .child('clients').push({'computer': platform.node(),
                                                     'uid': self.fire_uid,
                                                     'email': email},
                                                    self.fire_user['idToken']))

        # Parse response_url
        if response_data:
            open_url = response_data['url']
            if 'access_token' not in open_url:
                open_url = open_url + "?access_token={}".format(access_token)
            webbrowser.open_new(open_url)
        else:
            log.error("There was an error with the server. Please try again later!")
            return

        # while True:
        #     data = input("[Collaboration Mode] Type exit to disconnect: ")
        #     if data.strip().lower() == 'exit':
        #         raise ValueError('Done with session')

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

    ############
    # Firebase #
    ############

    def get_firebase(self):
        return (self.fire_db.child('ok-sessions')
                            .child(self.fire_uid)
                            .child(self.session_id))

    def send_firebase(self, channel, data):
        return (self.get_firebase().child(channel)
                    .push(data, self.fire_user['idToken']))

    def stream_listener(self, message):
        data = message.get('data')
        if not data:
            logging.info("Irrelevant message logged while listening")
            return
        action = data.get('action')
        sender = data.get('user')
        log.debug('Recieved new {} message from {}'.format(action, sender))

        file_name = data.get('fileName')

        if action == "save":
            print("Saving {} locally (initiated by {})".format(file_name, data.get('user')))
            self.collab_analytics['save'].append(time.strftime(self.TIME_FORMAT))

            return self.save(data)
        elif action == "grade":
            self.collab_analytics['grade'].append(time.strftime(self.TIME_FORMAT))

            return self.run_tests(data)

    def run_tests(self, data):
        backup = self.save(data)

        # Perform reload of some modules for file change
        if self.assignment.reload:
            for module in self.assignment.reload:
                if module in sys.modules:
                    del sys.modules[module]

        if not backup:
            (self.get_firebase().child('term')
                 .push({"status": 'Failed',
                        "computer": self.hostname,
                        "time": time.strftime(self.TIME_FORMAT),
                        "email": self.user_email,
                        'text': "Unknown files. Could not run autograding\n"},
                       self.fire_user['idToken']))
            return
        test_names = [t.name for t in self.assignment.specified_tests]
        (self.get_firebase().child('term')
             .push({"status": 'Running',
                    "computer": self.hostname,
                    "time": time.strftime(self.TIME_FORMAT),
                    "email": self.user_email,
                    'text': "Running tests for: {}\n".format(test_names)},
                   self.fire_user['idToken']))

        grading_results = self.grade(self.assignment.specified_tests)
        (self.get_firebase().child('term')
             .push({"status": 'Done',
                    "computer": self.hostname,
                    "email": self.user_email,
                    "time": time.strftime(self.TIME_FORMAT),
                    'text': str(grading_results['output'])[:6000],
                    'grading': grading_results['grading']},
                   self.fire_user['idToken']))

        # Treat autograde attempts like a backup.
        # if backup and backup != data.get('fileName'):
        #   shutil.move(backup, data.get('fileName'))

    def save(self, data):
        file_name = data['fileName']
        file_name = file_name.strip()

        if file_name not in self.assignment.src or file_name.endswith('.ok'):
            logging.warning("Unknown filename {}".format(file_name))
            print("Unknown file - Not saving {}".format(file_name))
            return

        if not os.path.isfile(file_name):
            log.warning('File {} does not exist. Not backing up'.format(file_name))
            backup_dst = file_name
        else:
            # Backup the file
            log.debug("Backing up file")
            backup_dst = self.backup_file(file_name)
            print("Backed up file to {}".format(backup_dst))

        log.debug("Beginning overwriting file")
        contents = data['file']
        with open(file_name, 'w') as f:
            f.write(contents)
        log.debug("Done replacing file")

        # Update file contents for backup
        self.file_contents[file_name] = contents

        return backup_dst

    def backup_file(self, file_name):
        if not os.path.exists(self.BACKUP_DIRECTORY):
            os.makedirs(self.BACKUP_DIRECTORY)

        safe_file_name = file_name.replace('/', '').replace('.py', '')
        backup_name = '{}/{}-{}.txt'.format(self.BACKUP_DIRECTORY, safe_file_name,
                                            time.strftime(self.FILE_TIME_FORMAT))
        log.info("Backing up {} to {}".format(file_name, backup_name))
        shutil.copyfile(file_name, backup_name)
        return backup_name

    def grade(self, tests):
        data = {}
        print("Starting grading from external request")
        log_id = output.new_log()
        grade(tests, data, verbose=self.args.verbose)
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

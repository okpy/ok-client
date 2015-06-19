from client.protocols.common import models
from client.utils import auth
import client
import datetime
import json
import logging
import os
import pickle
import socket
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

class BackupProtocol(models.Protocol):

    TIMEOUT = 500
    RETRY_LIMIT = 5
    BACKUP_FILE = ".ok_messages"
    SUBMISSION_ENDPOINT = '{prefix}://{server}/api/v1/submission?'

    def run(self, messages):
        if self.args.local or self.args.export:
            return

        message_list = self.load_unsent_messages()
        message_list.append(messages)

        self.check_ssl()

        access_token = auth.authenticate(False)
        log.info('Authenticated with access token %s', access_token)

        response = self.send_all_messages(access_token, message_list)

        if isinstance(response, dict):
            print('Backup successful for user: '
                  '{0}'.format(response['data']['email']))
            if self.args.submit or self.args.backup:
                print('URL: https://ok-server.appspot.com/#/'
                      '{0}/submission/{1}'.format(response['data']['course'],
                                                  response['data']['key']))
            if self.args.backup:
                print('NOTE: this is only a backup. '
                      'To submit your assignment, use:\n'
                      '\tpython3 ok --submit')

        self.dump_unsent_messages(message_list)
        print()


    @classmethod
    def load_unsent_messages(cls):
        message_list = []
        try:
            with open(cls.BACKUP_FILE, 'rb') as fp:
                message_list = pickle.load(fp)
            log.info('Loaded %d backed up messages from %s',
                     len(message_list), cls.BACKUP_FILE)
        except (IOError, EOFError) as e:
            log.info('Error reading from ' + cls.BACKUP_FILE + \
                     ', assume nothing backed up')
        return message_list


    @classmethod
    def dump_unsent_messages(cls, message_list):
        with open(cls.BACKUP_FILE, 'wb') as f:
            log.info('Save %d unsent messages to %s', len(message_list),
                     cls.BACKUP_FILE)

            pickle.dump(message_list, f)
            os.fsync(f)


    def check_ssl(self):
        if self.args.insecure:
            return
        try:
            import ssl
        except:
            log.warning('Error importing ssl', stack_info=True)
            raise Exception(
                    'SSL Bindings are not installed. '
                    'You can install python3 SSL bindings or run OK locally:\n'
                    '\tpython3 ok --local')


    def send_all_messages(self, access_token, message_list):
        action = 'Submitting' if self.args.submit else 'Backing up'
        num_messages = len(message_list)

        send_all = self.args.submit or self.args.backup
        retries = self.RETRY_LIMIT
        stop_time = datetime.datetime.now() + datetime.timedelta(milliseconds=self.TIMEOUT)

        first_response = None
        error_msg = ''

        while retries > 0 and message_list and \
                (send_all or datetime.datetime.now() < stop_time):
            log.info('Sending messages...%d left', len(message_list))

            print('{action}... {percent}% complete'.format(action=action,
                percent=100 - round(len(message_list) * 100 / num_messages, 2)),
                end='\r')

            # message_list is assumed to be ordered in chronological order.
            # We want to send the most recent message first, and send older
            # messages after.
            message = message_list[-1]

            try:
                response = self.send_messages(access_token, message)
            except socket.timeout as ex:
                log.warning("socket.timeout: %s", str(ex))
                retries -= 1
                error_msg = 'Connection timed out. ' + \
                            'Please check your network connection.'
            except (urllib.error.URLError, urllib.error.HTTPError) as ex:
                response_json = json.loads(ex.read().decode('utf-8'))

                log.warning('%s: %s', ex.__class__.__name__, str(ex))
                log.warning('%s error message: %s', ex.__class__.__name__,
                            response_json['message'])

                if ex.code == 403 and 'download_link' in response_json['data']:
                    retries = 0
                    error_msg = 'Aborting because OK may need to be updated.'
                else:
                    retries -= 1
                    error_msg = response_json['message']
            else:
                if not first_response:
                    first_response = response

                message_list.pop()

        if retries <= 0:
            print()     # Preserve progress bar.
            print('Error while', action.lower() + ':', error_msg)
        elif not send_all and datetime.datetime.now() > stop_time:
            print()     # Preserve progress bar.
            print('Could not back up: '
                  'Connection to server timed out after {} milliseconds'.format(self.TIMEOUT))
        else:
            print('{action}... 100% complete'.format(action=action))
            return first_response


    def send_messages(self, access_token, messages):
        """Send messages to server, along with user authentication."""

        data = {
            'assignment': self.assignment.endpoint,
            'messages': messages,
        }
        serialized_data = json.dumps(data).encode(encoding='utf-8')

        address = self.SUBMISSION_ENDPOINT.format(server=self.args.server,
                prefix='http' if self.args.insecure else 'https')
        address_params = {
            'access_token': access_token,
            'client_version': client.__version__,
        }
        address += '&'.join('{}={}'.format(param, value)
                            for param, value in address_params.items())

        log.info('Sending messages to %s', address)

        request = urllib.request.Request(address)
        request.add_header("Content-Type", "application/json")

        response = urllib.request.urlopen(request, serialized_data, self.TIMEOUT)
        return json.loads(response.read().decode('utf-8'))

protocol = BackupProtocol

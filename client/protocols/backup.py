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

    # Timeouts are specified in seconds.
    SHORT_TIMEOUT = 2

    RETRY_LIMIT = 5
    BACKUP_FILE = ".ok_messages"
    SUBMISSION_ENDPOINT = '{prefix}://{server}/api/v1/submission?'

    def run(self, messages):
        if self.args.local or self.args.export or self.args.restore:
            return

        message_list = self.load_unsent_messages()
        message_list.append(messages)

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


    def send_all_messages(self, access_token, message_list):
        action = 'Submit' if self.args.submit else 'Back up'
        num_messages = len(message_list)

        send_all = self.args.submit or self.args.backup
        if send_all:
            timeout = None
            stop_time = datetime.datetime.max
        else:
            timeout = self.SHORT_TIMEOUT
            stop_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
            log.info('Setting timeout to %d seconds', timeout)
        retries = self.RETRY_LIMIT

        first_response = None
        error_msg = ''

        while retries > 0 and message_list and datetime.datetime.now() < stop_time:
            log.info('Sending messages...%d left', len(message_list))

            print('{action}... {percent}% complete'.format(action=action,
                percent=100 - round(len(message_list) * 100 / num_messages, 2)),
                end='\r')

            # message_list is assumed to be ordered in chronological order.
            # We want to send the most recent message first, and send older
            # messages after.
            message = message_list[-1]

            try:
                response = self.send_messages(access_token, message, timeout)
            except socket.timeout as ex:
                log.warning("socket.timeout: %s", str(ex))
                retries -= 1
                error_msg = 'Connection timed out after {} seconds. '.format(timeout) + \
                            'Please check your network connection.'
            except (urllib.error.URLError, urllib.error.HTTPError) as ex:
                log.warning('%s: %s', ex.__class__.__name__, str(ex))
                if not hasattr(ex, 'read'):
                    error_msg = 'Please check your network connection'
                    continue

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

        if not message_list:
            print('{action}... 100% complete'.format(action=action))
            return first_response
        elif not send_all:
            # Do not display any error messages if --backup or --submit are not
            # used.
            print()
        elif not error_msg:
            # No errors occurred, but could not complete request within TIMEOUT.
            print()     # Preserve progress bar.
            print('Could not {} within {} seconds.'.format(action.lower(), timeout))
        else:
            # If not all messages could be backed up successfully.
            print()     # Preserve progress bar.
            print('Could not', action.lower() + ':', error_msg)


    def send_messages(self, access_token, messages, timeout):
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

        response = urllib.request.urlopen(request, serialized_data, timeout)
        return json.loads(response.read().decode('utf-8'))

protocol = BackupProtocol

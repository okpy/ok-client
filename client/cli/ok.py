"""The ok.py script runs tests, checks for updates, and saves your work.

Common uses:
  python3 ok.py          Run unlocked tests (and save your work).
  python3 ok.py -u       Unlock new tests interactively.
  python3 ok.py -h       Display full help documentation.

This script will search the current directory for test files. Make sure that
ok.py appears in the same directory as the assignment you wish to test.
Otherwise, use -t to specify a test file manually.
"""

# TODO(denero) Add mechanism for removing DEVELOPER INSTRUCTIONS.
DEVELOPER_INSTRUCTIONS = """

This multi-line string contains instructions for developers. It is removed
when the client is distributed to students.

This file is responsible for coordinating all communication with the ok-server.
Students should never need to modify this file.

Local and remote interactions are encapsulated as protocols.
Contributors should do the following to add a protocol to this autograder:

    1- Extend the Protocol class and implement on_start and on_interact.
    2- Add the classname of your protocol to the "protocols" list.
    3- If your protocol needs command line arguments, change parse_input.

A standard protocol lifecycle has only one round-trip communication with the
server, processed by the on_start method. If other interactions are required
outside of this lifecycle, the send_to_server function can be used to send and
receive information from the server outside of the default times. Such
communications should be limited to the body of an on_interact method.
"""
from client import exceptions as ex
from client.cli.common import assignment
from client.utils import auth
from client.utils import network
from client.utils import output
from datetime import datetime
from urllib import error
import argparse
import client
import logging
import os
import pickle
import sys

LOGGING_FORMAT = '%(levelname)s | pid %(process)d | %(filename)s:%(lineno)d | %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
log = logging.getLogger('client')   # Get top-level logger

CLIENT_ROOT = os.path.dirname(client.__file__)
BACKUP_FILE = ".ok_messages"

##########################
# Command-line Interface #
##########################

def parse_input():
    """Parses command line input."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # Protocol paramters
    parser.add_argument('-q', '--question', type=str, action='append',
                        help="focus on specific questions")
    parser.add_argument('-u', '--unlock', action='store_true',
                        help="unlock tests interactively")
    parser.add_argument('-i', '--interactive', action='store_true',
                        help="toggle interactive mode")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="print more output")
    parser.add_argument('--submit', action='store_true',
                        help="wait for server response without timeout")
    parser.add_argument('--lock', action='store_true',
                        help="partial path to directory to lock")
    parser.add_argument('--score', action='store_true',
                        help="Scores the assignment")
    parser.add_argument('--config', type=str,
                        help="Specify a configuration file")
    parser.add_argument('--timeout', type=int, default=10,
                        help="set the timeout duration for running tests")

    # Debug information
    parser.add_argument('--version', action='store_true',
                        help="Prints the version number and quits")
    parser.add_argument('--tests', action='store_true',
                        help="display a list of all available tests")
    parser.add_argument('--debug', action='store_true',
                        help="show debug statements")

    # Server parameters
    parser.add_argument('--local', action='store_true',
                        help="disable any network activity")
    parser.add_argument('--server', type=str,
                        default='ok-server.appspot.com',
                        help="server address")
    parser.add_argument('--authenticate', action='store_true',
                        help="authenticate, ignoring previous authentication")
    parser.add_argument('--insecure', action='store_true',
                        help="uses http instead of https")

    return parser.parse_args()

def main():
    """Run all relevant aspects of ok.py."""
    args = parse_input()

    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)
    log.debug(args)

    if args.version:
        print("okpy=={}".format(client.__version__))
        exit(0)

    # Instantiating assignment
    try:
        assign = assignment.load_config(args.config, args)
    except (ex.LoadingException, ex.SerializeException) as e:
        log.warning('Assignment could not instantiate', exc_info=True)
        print('Error: ' + str(e).strip())
        exit(1)

    # Load backup files
    msg_list = []
    try:
        with open(BACKUP_FILE, 'rb') as fp:
            msg_list = pickle.load(fp)
            log.info('Loaded %d backed up messages from %s',
                     len(msg_list), BACKUP_FILE)
    except (IOError, EOFError) as e:
        log.info('Error reading from ' + BACKUP_FILE \
                + ', assume nothing backed up')
    except KeyboardInterrupt:
        log.warning('Backup messages were not loaded due to KeyboardInterrupt')


    try:
        # Load tests and protocols
        assign.load()

        if args.tests:
            print('Available tests:')
            for name in assign.test_map:
                print('    ' + name)
            exit(0)

        # Run protocol.on_start
        start_messages = dict()
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.on_start()'.format(name))
            start_messages[name] = proto.on_start()
        # TODO(albert): doesn't AnalyticsProtocol store the timestamp?
        start_messages['timestamp'] = str(datetime.now())
        msg_list.append(start_messages)

        # Run protocol.on_interact
        interact_msg = {}
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.on_interact()'.format(name))
            interact_msg[name] = proto.on_interact()
        # TODO(albert): doesn't AnalyticsProtocol store the timestamp?
        interact_msg['timestamp'] = str(datetime.now())
        msg_list.append(interact_msg)
    except ex.LoadingException as e:
        log.warning('Assignment could not load', exc_info=True)
        print('Error loading assignment')
    except KeyboardInterrupt:
        log.info('Quitting protocols')
        assign.dump_tests()
    else:
        assign.dump_tests()

    if args.local:
        return

    # Send request to server
    try:
        # TODO(denero) Print server responses.

        # Check if ssl is available
        if not args.insecure:
            try:
                import ssl
            except:
                log.warning('Error importing ssl', stack_info=True)
                sys.exit("SSL Bindings are not installed. You can install python3 SSL bindings or \nrun ok locally with python3 ok --local")

        try:
            access_token = auth.authenticate(args.authenticate)
            log.info('Authenticated with access token %s', access_token)

            print("Backing up your work...")
            response = network.dump_to_server(access_token, msg_list,
                               assign.endpoint, args.server, args.insecure,
                               client.__version__, log, send_all=args.submit)

            if isinstance(response, dict):
                print("Backup successful for user: {0}".format(response['data']['email']))
                print("URL: https://ok-server.appspot.com/#/{0}/submission/{1}".format(response['data']['course'], response['data']['key']))
            else:
                print('Unable to complete backup.')
                log.warning('network.dump_to_server returned {}'.format(response))

        except error.URLError as e:
            log.warning('on_start messages not sent to server: %s', str(e))

        with open(BACKUP_FILE, 'wb') as fp:
            log.info('Save %d unsent messages to %s', len(msg_list),
                     BACKUP_FILE)

            pickle.dump(msg_list, fp)
            os.fsync(fp)

        if len(msg_list) == 0:
            print("Backup successful.")
    except KeyboardInterrupt:
        print("Quitting ok.")

if __name__ == '__main__':
    main()

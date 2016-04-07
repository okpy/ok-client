"""This file is responsible for coordinating all of OK's protocols."""

from client import exceptions as ex
from client.api import assignment
from client.cli.common import messages
from client.utils import auth
from client.utils import output
from client.utils import software_update
from datetime import datetime
import argparse
import client
import logging
import os
import sys
import struct

LOGGING_FORMAT = '%(levelname)s  | %(filename)s:%(lineno)d | %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
log = logging.getLogger('client')   # Get top-level logger

CLIENT_ROOT = os.path.dirname(client.__file__)

##########################
# Command-line Interface #
##########################

def parse_input(command_input=None):
    """Parses command line input."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # Protocol parameters
    parser.add_argument('-q', '--question', type=str, action='append',
                        help="focus on specific questions")
    parser.add_argument('-u', '--unlock', action='store_true',
                        help="unlock tests interactively")
    parser.add_argument('-i', '--interactive', action='store_true',
                        help="toggle interactive mode")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="print more output")
    parser.add_argument('--all', action='store_true',
                        help="run tests for all questions in config file")
    parser.add_argument('--submit', action='store_true',
                        help="Submit assignment")
    parser.add_argument('--backup', action='store_true',
                        help="Backup assignment reliably")
    parser.add_argument('--restore', action='store_true',
                        help="Restore assignment from an earlier backup")
    parser.add_argument('--lock', action='store_true',
                        help="partial path to directory to lock")
    parser.add_argument('--score', action='store_true',
                        help="Scores the assignment")
    parser.add_argument('--score-out', type=argparse.FileType('w'),
                        default=sys.stdout, help="file to write scores to")
    parser.add_argument('--config', type=str,
                        help="Specify a configuration file")
    parser.add_argument('--timeout', type=int, default=10,
                        help="set the timeout duration for running tests")

    # Guidance and hinting
    parser.add_argument('--guidance', action='store_true',
                        help="display guidance messages")
    parser.add_argument('--no-hints', action='store_true',
                        help="do not prompt for hints")

    # Submission Export
    parser.add_argument('--export', action='store_true',
                        help="Downloads all submissions for the current assignment")
    parser.add_argument('--latest', action='store_true',
                        help="When used with --export, downloads latest submissions instead of final submissions")

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
    parser.add_argument('--no-update', action='store_true',
                        help="turns off software updating")
    parser.add_argument('--update', action='store_true',
                        help="checks and performs software update then exits")

    if command_input is None:
        return parser.parse_args()
    else:
        return parser.parse_args(command_input)

def main():
    """Run all relevant aspects of ok.py."""
    args = parse_input()

    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)

    # Checking user's Python bit version
    bit_v = (8 * struct.calcsize("P"))
    log.debug("Python bit version: {}".format(bit_v))

    log.debug(args)

    if args.version:
        print("okpy=={}".format(client.__version__))
        exit(0)
    elif args.update:
        print("Current version: {}".format(client.__version__))
        did_update = software_update.check_version(
                args.server, client.__version__, client.FILE_NAME, timeout=10)
        exit(not did_update) # exit with error if ok failed to update

    assign = None
    try:
        if args.authenticate:
            auth.authenticate(True)

        # Instantiating assignment
        assign = assignment.load_assignment(args.config, args)

        if args.tests:
            print('Available tests:')
            for name in assign.test_map:
                print('    ' + name)
            exit(0)

        msgs = messages.Messages()
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.run()'.format(name))
            proto.run(msgs)

        msgs['timestamp'] = str(datetime.now())

    except ex.LoadingException as e:
        log.warning('Assignment could not load', exc_info=True)
        print('Error loading assignment: ' + str(e))
    except ex.AuthenticationException as e:
        log.warning('Authentication exception occurred', exc_info=True)
        print('Authentication error: {0}'.format(e))
    except ex.OkException as e:
        log.warning('General OK exception occurred', exc_info=True)
        print('Error: ' + str(e))
    except KeyboardInterrupt:
        log.info('KeyboardInterrupt received.')
    finally:
        if not args.no_update:
            try:
                software_update.check_version(args.server, client.__version__,
                                              client.FILE_NAME)
            except KeyboardInterrupt:
                pass

        if assign:
            assign.dump_tests()


if __name__ == '__main__':
    main()

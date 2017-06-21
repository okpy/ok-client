"""ok is an autograder that you can use to run tests, back up your work, and
submit assignments.

You can run all tests with

    python3 ok

There are several "options" you can give ok to modify its behavior. These
options generally have both a short form (preceded by a single dash, like -q)
or a long form (preceded by two dashes, like --question). This is similar to how
many other command line applications accept options. These options can be mixed
and matched in any order. The options are listed in full below, but we'll
describe some of the more common ones here.

To test a specific question, use the -q (or --question) option with the name of
the question:

    python3 ok -q foo
    python3 ok -q 12

By default, only tests that fail will appear. If you want to see the results
from all tests, you can use the -v (or --verbose) option:

    python3 ok -q foo -v

To start an interactive interpreter after a failed test for debugging, use the
-i (or --interactive) option:

    python3 ok -q foo -i

By default, after each test run ok will attempt to back up your work to the
server. To run the tests without any network access, use the --local option:

    python3 ok -q foo --local

To submit the assignment after you're done, use the --submit option:

    python3 ok --submit

Finally, to log out and log in under a different email, use --authenticate:

    python3 ok --authenticate

Visit https://okpy.org to view your backups and submissions.
"""

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
        prog='python3 ok',
        description=__doc__,
        usage='%(prog)s [--help] [options]',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    testing = parser.add_argument_group('running tests')
    testing.add_argument('-q', '--question', type=str, action='append',
                        help="run tests for a specific question")
    testing.add_argument('--suite', type=int, default=None,
                        help="run cases from a specific suite")
    testing.add_argument('--case', type=int, action='append',
                        help="run specific cases")
    testing.add_argument('-u', '--unlock', action='store_true',
                        help="unlock tests interactively")
    testing.add_argument('-i', '--interactive', action='store_true',
                        help="start the Python interpreter after a failed test")
    testing.add_argument('-v', '--verbose', action='store_true',
                        help="show all tests, not just passing tests")
    testing.add_argument('--all', action='store_true',
                        help="run tests for all questions in config file")
    testing.add_argument('--submit', action='store_true',
                        help="submit the assignment")
    testing.add_argument('--backup', action='store_true',
                        help="attempt to reliably backup your work")
    testing.add_argument('--revise', action='store_true',
                        help="submit composition revision")
    testing.add_argument('--timeout', type=int, default=10,
                        help="set the timeout duration (in seconds) for running tests")

    # Experiments
    experiment = parser.add_argument_group('experiment options')
    experiment.add_argument('--no-experiments', action='store_true',
                        help="do not run experimental features")
    experiment.add_argument('--hint', action='store_true',
                        help="give a hint (if available)")
    experiment.add_argument('--style', action='store_true',
                        help="run AutoStyle feedback system")
    experiment.add_argument('--collab', action='store_true',
                        help="launch collaborative programming environment")

    # Debug information
    debug = parser.add_argument_group('debugging options')
    debug.add_argument('--version', action='store_true',
                        help="print the version number and exit")
    debug.add_argument('--tests', action='store_true',
                        help="display a list of all available tests")
    debug.add_argument('--debug', action='store_true',
                        help="show debugging output")

    # Grading
    grading = parser.add_argument_group('grading options')
    grading.add_argument('--lock', action='store_true',
                        help="lock the tests in a directory")
    grading.add_argument('--score', action='store_true',
                        help="score the assignment")
    grading.add_argument('--score-out', type=argparse.FileType('w'),
                        default=sys.stdout, help="write scores to a file")
    grading.add_argument('--config', type=str,
                        help="use a specific configuration file")

    # Server parameters
    server = parser.add_argument_group('server options')
    server.add_argument('--local', action='store_true',
                        help="disable any network activity")
    server.add_argument('--server', type=str,
                        default='okpy.org',
                        help="set the server address")
    server.add_argument('--authenticate', action='store_true',
                        help="authenticate, ignoring previous authentication")
    server.add_argument('--no-browser', action='store_true',
                        help="do not use a web browser for authentication")
    server.add_argument('--get-token', action='store_true',
                        help="get ok access token")
    server.add_argument('--insecure', action='store_true',
                        help="use http instead of https")
    server.add_argument('--no-update', action='store_true',
                        help="do not check for ok updates")
    server.add_argument('--update', action='store_true',
                        help="update ok and exit")

    return parser.parse_args(command_input)

def main():
    """Run all relevant aspects of ok.py."""
    args = parse_input()

    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)
    log.debug(args)

    # Checking user's Python bit version
    bit_v = (8 * struct.calcsize("P"))
    log.debug("Python {} ({}bit)".format(sys.version, bit_v))

    if args.version:
        print("okpy=={}".format(client.__version__))
        exit(0)
    elif args.update:
        print("Current version: {}".format(client.__version__))
        did_update = software_update.check_version(
                args.server, client.__version__, client.FILE_NAME, timeout=10)
        exit(not did_update)  # exit with error if ok failed to update

    assign = None
    try:
        if args.get_token:
            access_token = auth.authenticate(args, force=True)
            print("Token: {}".format(access_token))
            exit(not access_token)  # exit with error if no access_token

        # Instantiating assignment
        assign = assignment.load_assignment(args.config, args)

        if args.authenticate:
            # Authenticate and check for success
            if not assign.authenticate(force=True):
                exit(1)

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
    except ex.EarlyExit as e:
        log.warning('OK exited early (non-error)')
        print(str(e))
    except ex.OkException as e:
        log.warning('General OK exception occurred', exc_info=True)
        print('Error: ' + str(e))
    except KeyboardInterrupt:
        log.info('KeyboardInterrupt received.')
    finally:
        if not args.no_update and not args.local:
            try:
                software_update.check_version(args.server, client.__version__,
                                              client.FILE_NAME)
            except KeyboardInterrupt:
                pass

        if assign:
            assign.dump_tests()


if __name__ == '__main__':
    main()

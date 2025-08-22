"""ok run tests and provides AI-generated help.

You can run all tests with

    python3 ok

There are several options you can give ok to modify its behavior. These
options generally have both a short form (preceded by a single dash, like -q)
or a long form (preceded by two dashes, like --question). This is similar to how
many other command line applications accept options. These options can be mixed
and matched in any order. The options are listed in full below, but we'll
describe some of the more common ones here.

To run a specific test, use -k:

    python3 ok -k test_name

You must authenticate as a Berkeley student to receive AI-generated help.

    python3 ok --authenticate
"""

from client import exceptions as ex
from client.utils import auth
from client.utils.printer import print_error
from client.utils.pytest import run_pytest
from client.protocols.help import HelpProtocol
from client.protocols.followup import FollowupProtocol
import argparse
import client
import logging
import os
import yaml

# TODO: Fix config_utils import in FollowupProtocol when config system is updated

LOGGING_FORMAT = '%(levelname)s  | %(filename)s:%(lineno)d | %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
log = logging.getLogger('client')   # Get top-level logger

CLIENT_ROOT = os.path.dirname(client.__file__)
PROTOCOLS = [HelpProtocol, FollowupProtocol]
GRADER_YAML = 'grader.yaml'

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


    # Experiments
    experiment = parser.add_argument_group('AI help options')
    experiment.add_argument('--get-help', action='store_true',
                        help="receive 61A-bot feedback on your code")
    experiment.add_argument('--consent', action='store_true',
                        help="get 61A-bot research consent")

    # Debug information
    debug = parser.add_argument_group('ok developer debugging options')
    debug.add_argument('--version', action='store_true',
                        help="print the version number and exit")
    debug.add_argument('--debug', action='store_true',
                        help="show debugging output")

    # Server parameters
    server = parser.add_argument_group('server options')
    server.add_argument('--local', action='store_true',
                        help="disable any network activity")
    server.add_argument('--authenticate', action='store_true',
                        help="authenticate, ignoring previous authentication")
    server.add_argument('--no-browser', action='store_true',
                        help="do not use a web browser for authentication")
    server.add_argument('--get-token', action='store_true',
                        help="get ok access token")
    server.add_argument('--insecure', action='store_true',
                        help="use http instead of https")
    server.add_argument('--server', type=str,
                        default='okpy.org',
                        help="set the server address")

    args, unknown_args = parser.parse_known_args(command_input)
    return args, unknown_args

def main():
    """Run pytest and provide AI help."""
    args, pytest_args = parse_input()
    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)
    log.debug(args)

    test_result = run_pytest(pytest_args)
    if test_result.has_failed_test():
        run_ai_help(args, test_result, log)



def run_ai_help(args, test_result, log):
    access_token = None
    try:
        if args.get_token:
            if args.nointeract:
                print_error("Cannot pass in --get-token and --nointeract, the only way to get a token is by interaction")
                exit(1)
            access_token = auth.authenticate(args, force=True)
            print_error("Token: {}".format(access_token))
            exit(not access_token)  # exit with error if no access_token

        force_authenticate = args.authenticate
        retry = True
        while retry:
            retry = False
            if force_authenticate:
                if args.nointeract:
                    print_error("Cannot pass in --authenticate and --nointeract")
                    exit(1)
                # Authenticate and check for success
                access_token = auth.authenticate(args, endpoint='', force=True)
                if not access_token:
                    exit(1)

            try:
                with open(GRADER_YAML, 'r') as f:
                    assignment = yaml.safe_load(f)
                email = auth.get_student_email(args)  # This uses the access token from authentication
                for proto_class in PROTOCOLS:
                    log.info('Execute {}.run()'.format(proto_class.__name__))
                    proto_instance = proto_class(args, assignment)
                    proto_instance.run(assignment, email, test_result)
            except ex.AuthenticationException as e:
                if not force_authenticate:
                    force_authenticate = True
                    retry = True
                elif not args.no_browser:
                    args.no_browser = True
                    retry = True
                if retry:
                    msg = "without a browser" if args.no_browser else "with a browser"
                    log.warning('Authentication exception occurred; will retry {0}'.format(msg), exc_info=True)
                    print_error('Authentication error; will try to re-authenticate {0}...'.format(msg))
                else:
                    raise  # outer handler will be called

    except ex.AuthenticationException as e:
        log.warning('Authentication exception occurred', exc_info=True)
        print_error('Authentication error: {0}'.format(e))
    except ex.EarlyExit as e:
        log.warning('OK exited early (non-error)')
        print_error(str(e))
    except ex.OkException as e:
        log.warning('General OK exception occurred', exc_info=True)
        print_error('Error: ' + str(e))
    except KeyboardInterrupt:
        log.info('KeyboardInterrupt received.')


if __name__ == '__main__':
    main()

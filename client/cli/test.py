from client import exceptions as ex
from client.cli.common import assignment
from client.cli.common import messages
from client.protocols import grading
from client.protocols import scoring
import argparse
import client
import logging
import os.path

LOGGING_FORMAT = '%(levelname)s | pid %(process)d | %(filename)s:%(lineno)d | %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
log = logging.getLogger('client')   # Get top-level logger

CLIENT_ROOT = os.path.dirname(client.__file__)

def parse_input():
    """Parses command line input."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-q', '--question', type=str, action='append',
                        help="focus on specific questions")
    parser.add_argument('-u', '--unlock', action='store_true',
                        help="unlock tests interactively")
    parser.add_argument('-i', '--interactive', action='store_true',
                        help="toggle interactive mode")
    parser.add_argument('-c', '--config', type=str,
                        help="Specify a configuration file")
    parser.add_argument('-s', '--score', action='store_true',
                        help="Score the assignment")
    parser.add_argument('--timeout', type=int, default=10,
                        help="Specify a timeout limit")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Specify verbose mode")
    parser.add_argument('--debug', action='store_true',
                        help="show debug statements")
    parser.add_argument('--export', action='store_true',
                        help="This is a nop. Used for compatibility with OK.")
    return parser.parse_args()

def main():
    """Run the LockingProtocol."""
    args = parse_input()

    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)
    log.debug(args)

    try:
        assign = assignment.load_config(args.config, args)
        assign.load()

        msgs = messages.Messages()

        grading.protocol(args, assign).run(msgs)
        scoring.protocol(args, assign).run(msgs)
    except (ex.LoadingException, ex.SerializeException) as e:
        log.warning('Assignment could not instantiate', exc_info=True)
        print('Error: ' + str(e).strip())
        exit(1)
    except (KeyboardInterrupt, EOFError):
        log.info('Quitting...')

if __name__ == '__main__':
    main()

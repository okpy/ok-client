from client.protocols import grading
from client.protocols import scoring
from client.cli.common import assignment
import argparse
import client
import os.path

CLIENT_ROOT = os.path.dirname(client.__file__)

def parse_input():
    """Parses command line input."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--config', type=str,
                        help="Specify a configuration file")
    parser.add_argument('-s', '--score', action='store_true',
                        help="Score the assignment")
    parser.add_argument('--timeout', type=int, default=10,
                        help="Specify a timeout limit")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Specify verbose mode")
    return parser.parse_args()

def main():
    """Run the LockingProtocol."""
    args = parse_input()
    args.question = []
    args.interactive = False

    assign = assignment.load_config(args.config, args)
    assign.load()

    grading.protocol(args, assign).on_interact()
    scoring.protocol(args, assign).on_interact()

if __name__ == '__main__':
    main()

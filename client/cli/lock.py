from client.protocols import lock
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
    parser.add_argument('--config', type=str,
                        default=os.path.join(CLIENT_ROOT, 'config.json'),
                        help="Specifies the configuration file")
    return parser.parse_args()

def main():
    """Run the LockingProtocol."""
    args = parse_input()
    args.lock = True
    args.question = []
    args.timeout = 0
    args.verbose = False
    args.interactive = False

    assign = assignment.load_config(args.config, args)

    protocol = lock.protocol(args, assign)
    protocol.on_start()

    assign.dump_tests()

if __name__ == '__main__':
    main()

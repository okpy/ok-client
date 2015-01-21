from client.sources.common import core
from client.utils import format
import client
import collections
import glob
import importlib
import json
import logging
import os
import zipfile

log = logging.getLogger(__name__)

def load_config(filepath, args):
    config = get_config(filepath)
    log.info('Loaded config from {}'.format(filepath))
    if not isinstance(config, dict):
        # TODO(albert): raise a more appropriate error
        raise TypeError('Config should be a dictionary')
    return Assignment(args, **config)

def get_config(filepath):
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            return json.load(f, object_pairs_hook=collections.OrderedDict)
    elif os.path.exists('ok'):
        # Assume using zipped version of OK, and assume there exists a
        # config.json file in the zip archive
        archive = zipfile.ZipFile('ok')
        config = archive.read('client/config.json').decode('utf-8')
        return json.loads(config)

class Assignment(core.Serializable):
    name = core.String()
    endpoint = core.String()
    src = core.List(type=str, optional=True)
    tests = core.Dict(keys=str, values=str, ordered=True)
    protocols = core.List(type=str)

    _TESTS_PACKAGE = 'client.sources'
    _PROTOCOL_PACKAGE = 'client.protocols'

    def __init__(self, cmd_args, **fields):
        self.cmd_args = cmd_args
        self.test_map = collections.OrderedDict()
        self.protocol_map = collections.OrderedDict()
        self.specified_tests = []

    def post_instantiation(self):
        self._print_header()
        self._load_tests()
        self._load_protocols()
        self._resolve_specified_tests()

    def _load_tests(self):
        """Loads all tests specified by test_map.

        PARAMETERS:
        test_map -- dict; file pattern -> serialize module. Every file that
                    that matches the UNIX style file pattern will be loaded
                    by the module.load method.
        """
        log.info('Loading tests')
        for file_pattern, source in self.tests.items():
            # Separate filepath and parameter
            if ':' in file_pattern:
                file_pattern, parameter = file_pattern.split(':', maxsplit=1)
            else:
                parameter = ''

            for file in glob.glob(file_pattern):
                # TODO(albert): add error handling
                module = importlib.import_module(self._TESTS_PACKAGE + '.' + source)
                self.test_map[file] = module.load(file, parameter, self.cmd_args)
                log.info('Loaded {}'.format(file))

    def dump_tests(self):
        """Dumps all tests, as determined by their .dump() method.

        PARAMETERS:
        tests -- dict; file -> Test. Each Test object has a .dump method
                 that takes a filename and serializes the test object.
        """
        log.info('Dumping tests')
        for file, test in self.test_map.items():
            # TODO(albert): add error handling
            test.dump(file)
            log.info('Dumped {} to {}'.format(test.name, file))

    def _resolve_specified_tests(self):
        """For each of the questions specified on the command line,
        find the best test corresponding that question.

        The best match is found by finding the test filepath that has the
        smallest edit distance with the specified question.

        Questions are preserved in the order that they are specified on the
        command line. If no questions are specified, use the entire set of
        tests.
        """
        if not self.cmd_args.question:
            log.info('Using all tests (no questions specified)')
            self.specified_tests = list(self.test_map.values())
            return
        elif not self.test_map:
            log.info('No tests loaded')
            return
        for question in self.cmd_args.question:
            matches = {}
            for test in self.test_map:
                # TODO(albert): change to subsequence matching. edit distance
                # will always return a match, even if the input resembles no
                # such test.
                score = _edit_distance(test.lower(), question.lower())
                matches.setdefault(score, []).append(test)
            best_score = min(matches)

            if len(matches[best_score]) > 1:
                print('Ambiguous question specified: {}'.format(question))
                print('Did you mean one of the following?')
                for test in matches[best_score]:
                    print('    {}'.format(test))
                # TODO(albert): raise an appropriate error
                raise TypeError

            best_match = matches[best_score][0]
            log.info('Matched {} to {}'.format(question, best_match))
            if best_match not in self.specified_tests:
                self.specified_tests.append(self.test_map[best_match])

    def _load_protocols(self):
        log.info('Loading protocols')
        for proto in self.protocols:
            # TODO(albert): add error handling
            module = importlib.import_module(self._PROTOCOL_PACKAGE + '.' + proto)
            # TODO(albert): determine all arguments to a protocol
            self.protocol_map[proto] = module.protocol(self.cmd_args, self)
            log.info('Loaded protocol "{}"'.format(proto))

    def _print_header(self):
        format.print_line('=')
        print('Assignment: {}'.format(self.name))
        print('OK, version {}'.format(client.__version__))
        format.print_line('=')
        print()

def _edit_distance(s1, s2):
    """Calculates the minimum edit distance between two strings.

    The costs are as follows:
    - match: 0
    - mismatch: 2
    - indel: 1

    PARAMETERS:
    s1 -- str; the first string to compare
    s2 -- str; the second string to compare

    RETURNS:
    int; the minimum edit distance between s1 and s2
    """
    m, n = len(s1), len(s2)
    subst_cost = lambda x, y: 0 if x == y else 2    # Penalize mismatches.

    cost = [[0 for _ in range(n + 1)] for _ in range(m + 1)]
    for col in range(1, n + 1):
        cost[0][col] = cost[0][col - 1] + 1
    for row in range(1, m + 1):
        cost[row][0] = cost[row - 1][0] + 1

    for col in range(1, n + 1):
        for row in range(1, m + 1):
            cost[row][col] = min(
                cost[row - 1][col] + 1,
                cost[row][col - 1] + 1,
                cost[row - 1][col - 1] + subst_cost(s1[row-1], s2[col-1])
            )
    return cost[m][n]


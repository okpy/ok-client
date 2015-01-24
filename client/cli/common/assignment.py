from client import exceptions as ex
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
        raise ex.LoadingException('Config should be a dictionary')
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

            files = glob.glob(file_pattern)
            if not files:
                error_msg = 'No tests found for pattern: {}'.format(file_pattern)
                print(error_msg)
                raise ex.LoadingException(error_msg)

            for file in files:
                try:
                    module = importlib.import_module(self._TESTS_PACKAGE + '.' + source)
                except ImportError:
                    raise ex.LoadingException('Invalid test source: {}'.format(source))

                test_name = file
                if parameter:
                    test_name += ':' + parameter
                self.test_map[test_name] = module.load(file, parameter, self.cmd_args)
                log.info('Loaded {}'.format(test_name))

    def dump_tests(self):
        """Dumps all tests, as determined by their .dump() method.

        PARAMETERS:
        tests -- dict; file -> Test. Each Test object has a .dump method
                 that takes a filename and serializes the test object.
        """
        log.info('Dumping tests')
        for file, test in self.test_map.items():
            try:
                test.dump(file)
            except ex.SerializeException as e:
                log.info('Unable to dump {} to {}: {}'.format(test.name, file,
                         str(e)))
            else:
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
            matches = []
            for test in self.test_map:
                if _has_subsequence(test.lower(), question.lower()):
                    matches.append(test)

            if len(matches) > 1:
                print('Did you mean one of the following?')
                for test in matches:
                    print('    {}'.format(test))
                raise ex.LoadingException('Ambiguous test specified: {}'.format(question))

            elif not matches:
                print('Did you mean one of the following?')
                for test in self.test_map:
                    print('    {}'.format(test))
                raise ex.LoadingException('Invalid test specified: {}'.format(question))

            match = matches[0]
            log.info('Matched {} to {}'.format(question, match))
            if match not in self.specified_tests:
                self.specified_tests.append(self.test_map[match])

    def _load_protocols(self):
        log.info('Loading protocols')
        for proto in self.protocols:
            try:
                module = importlib.import_module(self._PROTOCOL_PACKAGE + '.' + proto)
            except ImportError:
                raise ex.LoadingException('Invalid protocol: {}'.format(proto))

            self.protocol_map[proto] = module.protocol(self.cmd_args, self)
            log.info('Loaded protocol "{}"'.format(proto))

    def _print_header(self):
        format.print_line('=')
        print('Assignment: {}'.format(self.name))
        print('OK, version {}'.format(client.__version__))
        format.print_line('=')
        print()

def _has_subsequence(string, pattern):
    """Returns true if the pattern is a subsequence of string."""
    string_index, pattern_index = 0, 0
    while string_index < len(string) and pattern_index < len(pattern):
        if string[string_index] == pattern[pattern_index]:
            string_index += 1
            pattern_index += 1
        else:
            string_index += 1
    return pattern_index == len(pattern)


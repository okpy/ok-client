from client import exceptions as ex
from client.sources.common import core
from client.utils import format
from client.protocols.grading import grade
import client
import collections
import glob
import importlib
import json
import logging
import os
import textwrap

log = logging.getLogger(__name__)

CONFIG_EXTENSION = '*.ok'

def load_assignment(filepath=None, cmd_args=None):
    config = _get_config(filepath)
    if not isinstance(config, dict):
        raise ex.LoadingException('Config should be a dictionary')
    if cmd_args is None:
        cmd_args = _MockNamespace()
    return Assignment(cmd_args, **config)

def _get_config(config):
    if config is None:
        configs = glob.glob(CONFIG_EXTENSION)
        if len(configs) > 1:
            raise ex.LoadingException('\n'.join([
                'Multiple .ok files found:',
                '    ' + ' '.join(configs),
                "Please specify a particular assignment's config file with",
                '    python3 ok --config <config file>'
            ]))
        elif not configs:
            raise ex.LoadingException('No .ok configuration file found')
        config = configs[0]
    elif not os.path.isfile(config):
        raise ex.LoadingException(
                'Could not find config file: {}'.format(config))

    try:
        with open(config, 'r') as f:
            result = json.load(f, object_pairs_hook=collections.OrderedDict)
    except IOError:
        raise ex.LoadingException('Error loading config: {}'.format(config))
    except ValueError:
        raise ex.LoadingException(
            '{0} is a malformed .ok configuration file. '
            'Please re-download {0}.'.format(config))
    else:
        log.info('Loaded config from {}'.format(config))
        return result


class Assignment(core.Serializable):
    name = core.String()
    endpoint = core.String()
    src = core.List(type=str, optional=True)
    tests = core.Dict(keys=str, values=str, ordered=True)
    default_tests = core.List(type=str, optional=True)
    protocols = core.List(type=str)

    ####################
    # Programmatic API #
    ####################

    def grade(self, question, env=None, skip_locked_cases=False):
        """Runs tests for a particular question. The setup and teardown will
        always be executed.

        question -- str; a question name (as would be entered at the command
                    line
        env      -- dict; an environment in which to execute the tests. If
                    None, uses the environment of __main__. The original
                    dictionary is never modified; each test is given a
                    duplicate of env.
        skip_locked_cases -- bool; if False, locked cases will be tested

        Returns: dict; maps question names (str) -> results (dict). The
        results dictionary contains the following fields:
        - "passed": int (number of test cases passed)
        - "failed": int (number of test cases failed)
        - "locked": int (number of test cases locked)
        """
        if env is None:
            import __main__
            env = __main__.__dict__
        messages = {}
        tests = self._resolve_specified_tests([question], all_tests=False)
        for test in tests:
            try:
                for suite in test.suites:
                    suite.skip_locked_cases = skip_locked_cases
                    suite.console.skip_locked_cases = skip_locked_cases
                    suite.console.hash_key = self.name
            except AttributeError:
                pass
        test_name = tests[0].name
        grade(tests, messages, env)
        return messages['grading'][test_name]

    ############
    # Internal #
    ############

    _TESTS_PACKAGE = 'client.sources'
    _PROTOCOL_PACKAGE = 'client.protocols'

    def __init__(self, args, **fields):
        self.cmd_args = args
        self.test_map = collections.OrderedDict()
        self.protocol_map = collections.OrderedDict()

    def post_instantiation(self):
        self._print_header()
        self._load_tests()
        self._load_protocols()
        self.specified_tests = self._resolve_specified_tests(
            self.cmd_args.question, self.cmd_args.all)

    def _load_tests(self):
        """Loads all tests specified by test_map."""
        log.info('Loading tests')
        for file_pattern, source in self.tests.items():
            # Separate filepath and parameter
            if ':' in file_pattern:
                file_pattern, parameter = file_pattern.split(':', 1)
            else:
                parameter = ''

            for file in sorted(glob.glob(file_pattern)):
                try:
                    module = importlib.import_module(self._TESTS_PACKAGE + '.' + source)
                except ImportError:
                    raise ex.LoadingException('Invalid test source: {}'.format(source))

                test_name = file
                if parameter:
                    test_name += ':' + parameter
                self.test_map.update(module.load(file, parameter, self))
                log.info('Loaded {}'.format(test_name))

        if not self.test_map:
            raise ex.LoadingException('No tests loaded')

    def dump_tests(self):
        """Dumps all tests, as determined by their .dump() method.

        PARAMETERS:
        tests -- dict; file -> Test. Each Test object has a .dump method
                 that takes a filename and serializes the test object.
        """
        log.info('Dumping tests')
        for test in self.test_map.values():
            try:
                test.dump()
            except ex.SerializeException as e:
                log.warning('Unable to dump {}: {}'.format(test.name, str(e)))
            else:
                log.info('Dumped {}'.format(test.name))

    def _resolve_specified_tests(self, questions, all_tests=False):
        """For each of the questions specified on the command line,
        find the test corresponding that question.

        Questions are preserved in the order that they are specified on the
        command line. If no questions are specified, use the entire set of
        tests.
        """
        if not questions and not all_tests \
                and self.default_tests != core.NoValue \
                and len(self.default_tests) > 0:
            log.info('Using default tests (no questions specified): '
                     '{}'.format(self.default_tests))
            return [self.test_map[test] for test in self.default_tests]
        elif not questions:
            log.info('Using all tests (no questions specified and no default tests)')
            return list(self.test_map.values())
        elif not self.test_map:
            log.info('No tests loaded')
            return []

        specified_tests = []
        for question in questions:
            if question not in self.test_map:
                print('Test "{}" not found.'.format(question))
                print('Did you mean one of the following? '
                      '(Names are case sensitive)')
                for test in self.test_map:
                    print('    {}'.format(test))
                raise ex.LoadingException('Invalid test specified: {}'.format(question))

            log.info('Adding {} to specified tests'.format(question))
            if question not in specified_tests:
                specified_tests.append(self.test_map[question])
        return specified_tests

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

class _MockNamespace(object):
    """A mock object that is meant to be a substitute for an argparse.Namespace
    object. This object contains the minimal set of fields necessary for an
    Assignment to be created.

    Do NOT use this for any command-line related work. This object should only
    be used for the programmatic API. This implies that if an Assignment is
    created with a MockNamespace, any functionality not specified in the
    programmatic API will not work.

    Design note: In an ideal world, this object wouldn't even exist and the
    Assignment and Protocol classes shouldn't take in an argparse.Namespace
    object. Instead, the Assignment class should be part of the API and should
    not be tied to command-line usage only. Making changes to this effect would
    take a substantial rewrite, so I'm putting it off for now.
    """
    def __init__(self):
        from client.cli.ok import parse_input
        self.args = parse_input([])

    def __getattr__(self, attr):
        return getattr(self.args, attr)

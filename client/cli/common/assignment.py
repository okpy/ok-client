from client.sources.common import core
import glob
import importlib
import json
import collections

def load_config(filepath, args):
    with open(filepath, 'r') as f:
        config = json.load(f)
    if not isinstance(config, dict):
        # TODO(albert): raise an error
        pass
    return Assignment(cmd_args, **config)

class Assignment(core.Serializable):
    name = core.String()
    endpoint = core.String()
    src = core.List(type=str, optional=True)
    tests = core.Dict(keys=str, values=str)
    protocols = core.List(type=str)

    _TESTS_PACKAGE = 'client.sources'
    _PROTOCOL_PACKAGE = 'client.protocols'

    def __init__(self, cmd_args, **fields):
        self.cmd_args = cmd_args
        self.test_map = {}
        self.protocol_map = collections.OrderedDict()

    def post_instantiation(self):
        self.load_tests()
        self.load_protocols()

    def load_tests(self):
        """Loads all tests specified by test_map.

        PARAMETERS:
        test_map -- dict; file pattern -> serialize module. Every file that
                    that matches the UNIX style file pattern will be loaded
                    by the module.load method.
        """
        for file_pattern, source in self.tests.items():
            for file in glob.glob(file_pattern):
                # TODO(albert): add error handling
                module = importlib.import_module(source, self._TESTS_PACKAGE)
                self.test_map[file] = module.load(file)

    def dump_tests(self):
        """Dumps all tests, as determined by their .dump() method.

        PARAMETERS:
        tests -- dict; file -> Test. Each Test object has a .dump method
                 that takes a filename and serializes the test object.
        """
        for file, test in self.test_map.items():
            # TODO(albert): add error handling
            test.dump(file)

    def load_protocols(self):
        for proto in self.protocols:
            # TODO(albert): add error handling
            module = importlib.import_module(proto, self._PROTOCOL_PACKAGE)
            # TODO(albert): determine all arguments to a protocol
            self.protocol_map[proto] = module.Protocol(self.cmd_args, self)



import glob

def load_tests(test_map):
    """Loads all tests specified by test_map.

    PARAMETERS:
    test_map -- dict; file pattern -> serialize module. Every file that
                that matches the UNIX style file pattern will be loaded
                by the module.load method.

    RETURNS:
    dict; file -> Test
    """
    tests = {}
    for file_pattern, module in test_map.items():
        for file in glob.glob(file_pattern):
            # TODO(albert): add error handling
            tests[file] = eval(module + '.load(file)')
    return tests

def dump_tests(tests):
    """Dumps all tests, as determined by their .dump() method.

    PARAMETERS:
    tests -- dict; file -> Test. Each Test object has a .dump method
             that takes a filename and serializes the test object.
    """
    for file, test in tests.items():
        # TODO(albert): add error handling
        test.dump(file)

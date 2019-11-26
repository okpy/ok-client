from client import exceptions as ex
from client.api import assignment
from client.sources.common import core
import collections
import mock
import unittest

class LoadAssignmentTest(unittest.TestCase):
    VALID_CONFIG = """
    {
        "name": "Homework 1",
        "endpoint": "https://okpy.org/path/to/endpoint",
        "src": [
            "hw1.py"
        ],
        "tests": {
            "hw1.py": "doctest"
        },
        "default_tests": [
            "square"
        ],
        "protocols": [
            "restore",
            "export",
            "file_contents",
            "analytics",
            "unlock",
            "lock",
            "grading",
            "scoring",
            "backup"
        ]
    }
    """

    def setUp(self):
        self.is_file_patcher = mock.patch('os.path.isfile')
        self.mock_is_file = self.is_file_patcher.start()
        self.mock_is_file.return_value = True

        self.glob_patcher = mock.patch('glob.glob')
        self.mock_glob = self.glob_patcher.start()

        self.import_module_patcher = mock.patch('importlib.import_module')
        self.mock_import_module = self.import_module_patcher.start()

    def tearDown(self):
        self.is_file_patcher.stop()
        self.glob_patcher.stop()
        self.import_module_patcher.stop()

    def testFailOnNonexistentConfig(self):
        self.mock_is_file.return_value = False
        with self.assertRaises(ex.LoadingException) as cm:
            assignment.load_assignment('does_not_exist.ok')
        self.assertEquals(
                'Could not find config file: does_not_exist.ok',
                str(cm.exception))

    def testFailOnMultipleFoundConfigs(self):
        self.mock_glob.return_value = ['1.ok', '2.ok']
        with self.assertRaises(ex.LoadingException) as cm:
            assignment.load_assignment()
        self.assertEquals(
                '\n'.join([
                    'Multiple .ok files found:',
                    '    1.ok 2.ok',
                    "Please specify a particular assignment's config file with",
                    '    python3 ok --config <config file>'
                ]),
                str(cm.exception))

    def testFailOnCorruptedConfig(self):
        corrupted_config = '{not valid json}'
        mock_open = mock.mock_open(read_data=corrupted_config)
        with mock.patch('builtins.open', mock_open):
            with self.assertRaises(ex.LoadingException) as cm:
                assignment.load_assignment('corrupted.ok')
        self.assertEquals(
                'corrupted.ok is a malformed .ok configuration file. '
                'Please re-download corrupted.ok.',
                str(cm.exception))

    def testSpecificConfig(self):
        mock_open = mock.mock_open(read_data=self.VALID_CONFIG)
        with mock.patch('builtins.open', mock_open):
            with mock.patch('client.api.assignment.Assignment') as mock_assign:
                assign = assignment.load_assignment('some_config.ok')
        # Verify config file was actually opened.
        mock_open.assert_called_with('some_config.ok', 'r')
        mock_open().read.assert_called_once_with()

    def testSearchForConfigInFilesystem(self):
        self.mock_glob.return_value = ['some_config.ok']
        mock_open = mock.mock_open(read_data=self.VALID_CONFIG)
        with mock.patch('builtins.open', mock_open):
            with mock.patch('client.api.assignment.Assignment') as mock_assign:
                assign = assignment.load_assignment()
        # Verify config file was actually opened.
        mock_open.assert_called_with('some_config.ok', 'r')
        mock_open().read.assert_called_once_with()

class AssignmentTest(unittest.TestCase):
    NAME = 'Assignment'
    ENDPOINT = 'endpoint'
    SRC = ['file1', 'file2']

    PATTERN1 = 'pattern1'
    PATTERN2 = 'pattern2'
    PARAMETER = 'param'
    PATTERN_WITH_PARAM = PATTERN1 + ':' + PARAMETER

    SOURCE1 = 'source1'
    SOURCE2 = 'source2'

    FILE1 = 'tests/q1.py'
    FILE2 = 'tests/q2.py'
    FILES = [FILE1, FILE2]
    QUESTION1 = FILE1
    QUESTION2 = FILE2
    AMBIGUOUS_QUESTION = 'q'
    INVALID_QUESTION = 'x'

    PROTOCOL = 'protocol'

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.question = []
        self.cmd_args.all = False
        self.mockSource1 = mock.Mock()
        self.mockProtocol1 = mock.Mock()
        self.mockTest = mock.Mock()

        self.patcherFindFiles = mock.patch('glob.glob')
        self.addCleanup(self.patcherFindFiles.stop)
        self.mockFindFiles = self.patcherFindFiles.start()

        self.patcherLoadModule = mock.patch('importlib.import_module')
        self.addCleanup(self.patcherLoadModule.stop)
        self.mockImportModule = self.patcherLoadModule.start()

        self.mockModule = mock.Mock()
        self.mockModule.load.return_value = {
            self.FILE1: self.mockTest
        }
        self.mockImportModule.return_value = self.mockModule

    def makeAssignment(self, tests=None, protocols=None, default_tests=None):
        if tests is None:
            tests = {self.PATTERN1: self.SOURCE1}
        if protocols is None:
            protocols = [self.PROTOCOL]
        if default_tests is None:
            default_tests = core.NoValue
        assign = assignment.Assignment(self.cmd_args, name=self.NAME,
                                       endpoint=self.ENDPOINT, src=self.SRC,
                                       tests=tests, protocols=protocols,
                                       default_tests=default_tests)
        return assign

    def testConstructor_noTestSources(self):
        self.assertEqual(collections.OrderedDict(), self.makeAssignment().test_map)

    def testConstructor_sourceWithNoMatches(self):
        def selective_pattern_match(pattern):
            if pattern == self.PATTERN1:
                return []
            elif pattern == self.PATTERN2:
                return [self.FILE1]
        self.mockFindFiles.side_effect = selective_pattern_match

        assign = self.makeAssignment(tests=collections.OrderedDict((
            (self.PATTERN1, self.SOURCE1),
            (self.PATTERN2, self.SOURCE2),
        )))

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
        )), assign.test_map)

    def testConstructor_noTestsLoaded(self):
        self.mockFindFiles.return_value = []

        self.assertEqual(collections.OrderedDict(), self.makeAssignment().test_map)

    def testConstructor_invalidSource(self):
        self.mockFindFiles.return_value = [self.FILE1]
        self.mockImportModule.side_effect = ImportError

        self.assertRaises(ex.LoadingException, self.makeAssignment)

    def testConstructor_parameterInTestPattern(self):
        self.mockFindFiles.return_value = [self.FILE1]
        assign = self.makeAssignment(tests=collections.OrderedDict((
            (self.PATTERN_WITH_PARAM, self.SOURCE1),
        )))

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
        )), assign.test_map)

    def testConstructor_specifiedTest_ambiguousTest(self):
        self.cmd_args.question = [self.AMBIGUOUS_QUESTION]
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        self.assertRaises(ex.LoadingException, self.makeAssignment)

    def testConstructor_specifiedTest_invalidTest(self):
        self.cmd_args.question = [self.INVALID_QUESTION]
        self.mockFindFiles.return_value = self.FILES
        self.assertRaises(ex.LoadingException, self.makeAssignment)

    def testConstructor_specifiedTest_match(self):
        self.cmd_args.question = [self.QUESTION1]
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest], assign.specified_tests)

    def testConstructor_specifiedTest_multipleQuestions(self):
        self.cmd_args.question = [self.QUESTION1, self.QUESTION2]
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest, self.mockTest], assign.specified_tests)

    def testConstructor_specifiedTest_noSpecifiedTests(self):
        self.cmd_args.question = []
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest, self.mockTest], assign.specified_tests)

    def testConstructor_specifiedTest_multipleQuestions(self):
        """Specified questions should override default tests."""
        self.cmd_args.question = [self.QUESTION1, self.QUESTION2]
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        default_tests = [self.QUESTION1]
        assign = self.makeAssignment(default_tests=default_tests)

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest, self.mockTest], assign.specified_tests)

    def testConstructor_defaultTests(self):
        self.cmd_args.question = []
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        default_tests = [self.QUESTION1]
        assign = self.makeAssignment(default_tests=default_tests)

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest], assign.specified_tests)

    def testConstructor_questionDoesNotExist(self):
        self.cmd_args.question = []
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))

        try:
            self.makeAssignment(default_tests=[self.QUESTION1, "question_that_does_not_exist"])
        except ex.LoadingException as e:
            self.assertIn("Required question(s) missing: question_that_does_not_exist", str(e))

        try:
            self.makeAssignment(default_tests=["question_that_does_not_exist"])
        except ex.LoadingException as e:
            self.assertIn("Required question(s) missing: question_that_does_not_exist", str(e))

        try:
            self.makeAssignment(default_tests=["question_that_does_not_exist", "another_nonexistent_question"])
        except ex.LoadingException as e:
            self.assertIn("Required question(s) missing: another_nonexistent_question, question_that_does_not_exist", str(e))

    def testConstructor_allTests_noSpecifiedTests(self):
        self.cmd_args.question = []
        self.cmd_args.all = True
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest, self.mockTest], assign.specified_tests)

    def testConstructor_allTests_specifiedTtests(self):
        self.cmd_args.question = [self.QUESTION1]
        self.cmd_args.all = True
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest], assign.specified_tests)

    def testConstructor_allTests_overrideDefaultTests(self):
        self.cmd_args.question = []
        self.cmd_args.all = True
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        default_tests = [self.QUESTION1]
        assign = self.makeAssignment(default_tests=default_tests)

        self.assertEqual(collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest),
        )), assign.test_map)
        self.assertEqual([self.mockTest, self.mockTest], assign.specified_tests)

    def testConstructor_invalidProtocol(self):
        def import_module(module):
            if self.PROTOCOL in module:
                raise ImportError
            else:
                result = mock.Mock()
                result.load.return_value = {
                    self.FILE1: self.mockTest
                }
                return result
        self.mockImportModule.side_effect = import_module
        self.mockFindFiles.return_value = [self.FILE1]

        self.assertRaises(ImportError, self.makeAssignment)

    def testConstructor_noProtocols(self):
        self.mockFindFiles.return_value = [self.FILE1]

        try:
            self.makeAssignment(protocols=[])
        except ex.LoadingException:
            self.fail('It is ok for no protocols to be specified')

    def testDumpTests(self):
        self.mockFindFiles.return_value = self.FILES
        self.mockModule.load.return_value = collections.OrderedDict((
            (self.FILE1, self.mockTest),
            (self.FILE2, self.mockTest)
        ))
        assign = self.makeAssignment()

        assign.dump_tests()
        self.mockTest.dump.assert_has_calls([
            mock.call(),
            mock.call(),
        ])

    def testDumpTests_serializeError(self):
        self.mockFindFiles.return_value = self.FILES
        assign = self.makeAssignment()
        self.mockTest.dump.side_effect = ex.SerializeException

        try:
            assign.dump_tests()
        except ex.SerializeException:
            self.fail('If one test fails to dump, continue dumping the rest.')

class AssignmentGradeTest(unittest.TestCase):
    CONFIG = """
    {
        "name": "Homework 1",
        "endpoint": "",
        "tests": {
            "q1.py": "ok_test"
        },
        "protocols": []
    }
    """
    def setUp(self):
        self.is_file_patcher = mock.patch('os.path.isfile')
        self.mock_is_file = self.is_file_patcher.start()
        self.mock_is_file.return_value = True

        self.glob_patcher = mock.patch('glob.glob')
        self.mock_glob = self.glob_patcher.start()

        self.load_module_patcher = mock.patch('client.sources.common.importing.load_module')
        self.mock_load_module = self.load_module_patcher.start()

    def tearDown(self):
        self.is_file_patcher.stop()
        self.glob_patcher.stop()
        self.load_module_patcher.stop()

    def testGrade_noSuchTest(self):
        assign = self.makeAssignmentWithTestCode('')
        with self.assertRaises(ex.LoadingException) as cm:
            assign.grade('no_such_test')
        self.assertEqual('Invalid test specified: no_such_test', str(cm.exception))

    def testGrade_userSuppliedEnvironment(self):
        assign = self.makeAssignmentWithTestCode("""
        >>> square(4)
        16
        """)

        # This should fail because square isn't defined in the empty environment.
        results = assign.grade('q1', env={})
        self.assertEqual(0, results['passed'])
        self.assertEqual(1, results['failed'])

        # This should pass now that square is defined.
        results = assign.grade('q1', env={
            'square': lambda x: x * x
        })
        self.assertEqual(1, results['passed'])
        self.assertEqual(0, results['failed'])

    def testGrade_defaultEnvironmentIsGlobal(self):
        assign = self.makeAssignmentWithTestCode("""
        >>> square(4)
        16
        """)

        # This should fail because square isn't defined in the empty environment.
        results = assign.grade('q1')
        self.assertEqual(0, results['passed'])
        self.assertEqual(1, results['failed'])

        import __main__
        __main__.square = lambda x: x * x

        # This should pass now that square is defined.
        results = assign.grade('q1')
        self.assertEqual(1, results['passed'])
        self.assertEqual(0, results['failed'])

    def makeAssignmentWithTestCode(self, test_code):
        self.mock_glob.return_value = ['q1.py']
        self.mock_load_module.return_value.test = {
            'name': 'Homework 1',
            'points': 1,
            'suites': [
                {
                    'type': 'doctest',
                    'cases': [
                        { 'code': test_code }
                    ]
                }
            ]
        }
        with mock.patch('builtins.open', mock.mock_open(read_data=self.CONFIG)):
            return assignment.load_assignment('some_config.ok')

from client import exceptions as ex
from client.cli.common import assignment
import collections
import mock
import unittest

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
    QUESTION1 = 'q1'
    QUESTION2 = 'tests2'
    AMBIGUOUS_QUESTION = 'q'
    INVALID_QUESTION = 'x'

    PROTOCOL = 'protocol'

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.question = []
        self.mockSource1 = mock.Mock()
        self.mockProtocol1 = mock.Mock()

        self.mockFindFiles = mock.Mock()
        self.mockImportModule = mock.Mock()
        self.mockTest = mock.Mock()

        self.mockModule = mock.Mock()
        self.mockModule.load.return_value = {
            self.FILE1: self.mockTest
        }
        self.mockImportModule.return_value = self.mockModule

    def makeAssignment(self, tests=None, protocols=None):
        if tests is None:
            tests = {self.PATTERN1: self.SOURCE1}
        if protocols is None:
            protocols = [self.PROTOCOL]
        assign = assignment.Assignment(self.cmd_args, name=self.NAME,
                                           endpoint=self.ENDPOINT, src=self.SRC,
                                           tests=tests, protocols=protocols)
        assign._import_module = self.mockImportModule
        assign._find_files = self.mockFindFiles
        assign.load()
        return assign

    def testConstructor_noTestSources(self):
        self.assertRaises(ex.LoadingException, self.makeAssignment,
                          tests={})

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

        self.assertRaises(ex.LoadingException, self.makeAssignment)

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

        self.assertRaises(ex.LoadingException, self.makeAssignment)

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
            mock.call(self.FILE1),
            mock.call(self.FILE2)
        ])

    def testDumpTests_serializeError(self):
        self.mockFindFiles.return_value = self.FILES
        assign = self.makeAssignment()
        self.mockTest.dump.side_effect = ex.SerializeException

        try:
            assign.dump_tests()
        except ex.SerializeException:
            self.fail('If one test fails to dump, continue dumping the rest.')

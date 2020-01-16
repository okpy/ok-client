from client.sources.doctest import models
from client.utils import output
import sys
import unittest

class DoctestTest(unittest.TestCase):
    NAME = 'doctest'
    POINTS = 1
    FILE = 'operator'

    def setUp(self):
        self.old_stdout = sys.stdout
        self.old_logger = output._logger
        sys.stdout = output._logger = output._OutputLogger()
        output.on()

    def tearDown(self):
        sys.stdout = self.old_stdout
        output._logger = self.old_logger

    def makeDoctest(self, docstring, verbose=False, interactive=False):
        return models.Doctest(self.FILE, verbose, interactive, name=self.NAME,
                              points=self.POINTS, docstring=docstring)

    def testConstructor_standardDoctest(self):
        try:
            self.makeDoctest("""
            >>> 2 + 3
            5
            """)
        except TypeError:
            self.fail()

    def testConstructor_noDoctest(self):
        try:
            self.makeDoctest("""
            This is just a docstring
            """)
        except TypeError:
            self.fail()

    def testConstructor_lineBreakInDoctest(self):
        try:
            self.makeDoctest("""
            >>> 4 + 5
            9

            >>> 1 + 2
            3
            """)
        except TypeError:
            self.fail()

    def testConstructor_validIndentationInconsistencies(self):
        try:
            self.makeDoctest("""
                >>> 4 + 5
                9

            >>> 1 + 2
            3
            """)
        except TypeError:
            self.fail()

    def testConstructor_indentationInOutput(self):
        test = self.makeDoctest("""
        >>> print('1\\n  2')
        1
          2
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testConstructor_printThenReturn(self):
        test = self.makeDoctest("""
        >>> def foo():
        ...     print('hi')
        ...     return 1
        >>> foo()
        hi
        1
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testConstructor_debugThenReturn(self):
        test = self.makeDoctest("""
        >>> def foo():
        ...     print('DEBUG: hi')
        ...     print('Not a debug line, even though it contains "DEBUG:"')
        ...     print("Starts a line, ", end="")
        ...     print("DEBUG: this is not a debug line")
        ...     print("DEBUG: This, however is a debug line")
        ...     print("DEBUG with just a space is fine")
        ...     print("DEBUG_must have a colon or a space to be ignored")
        ...     print("debug lowercase is ignored")
        ...     return 1
        >>> foo()
        Not a debug line, even though it contains "DEBUG:"
        Starts a line, DEBUG: this is not a debug line
        DEBUG_must have a colon or a space to be ignored
        1
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testConstructor_printNoEndCharThenReturn(self):
        test = self.makeDoctest("""
        >>> def foo():
        ...     print('hi', end='')
        ...     return 1
        >>> foo()
        hi1
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testConstructor_invalidIndentationInconsistencies(self):
        # TODO(albert): test not passing
        pass
        # self.assertRaises(TypeError, self.makeDoctest, """
        #     >>> 4 + 5
        #     9
        #         >>> 1 + 2
        #         3
        #     """)
        # self.assertRaises(TypeError, self.makeDoctest, """
        #         >>> 4 + 5
        #         9
        #     >>> 1 + 2
        #     3
        #     """)

    def testRun_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testRun_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run(None))

    def testRun_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run(None))

    def testRun_solitaryPS1(self):
        test = self.makeDoctest("""
        >>> 1 + 2
        3
        >>>
        >>> 1
        1
        """)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run(None))

    def testRun_solitaryPS2(self):
        test = self.makeDoctest("""
        >>> def f():
        ...     return 4
        ...
        >>> f()
        4
        """)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run(None))


    def testScore_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """)
        self.assertEqual(1, test.score())

    def testScore_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """)
        self.assertEqual(0, test.score())

    def testScore_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """)
        self.assertEqual(0, test.score())

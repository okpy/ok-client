"""Tests the DoctestCase model."""

# from client import exceptions
# from client.models import core
# from client.models import doctest_case
# from client.protocols import unlock
# from client.utils import formatting
# from client.utils import output

from client.models import core
from client.sources.common import doctest_case
from client.utils import output
import mock
import sys
import textwrap
import unittest

class PythonConsoleTest(unittest.TestCase):
    def setUp(self):
        self.logger = output.OutputLogger()

    def createConsole(self, verbose=True, interactive=False, timeout=None):
        self.console = doctest_case.PythonConsole(
                self.logger, verbose, interactive, timeout)

    def calls_interpret(self, success, code, setup='', teardown=''):
        self.createConsole()
        self.console.load(code, setup, teardown)
        result = self.console.interpret()
        self.assertEqual(success, result)

    def testPass_equals(self):
        self.calls_interpret(True,
            """
            >>> 3 + 4
            7
            """)

    def testPass_expectException(self):
        self.calls_interpret(True,
            """
            >>> 1 / 0
            ZeroDivisionError
            """)

    def testPass_multilineSinglePrompt(self):
        self.calls_interpret(True,
            """
            >>> x = 5
            >>> x + 4
            9
            """)

    def testPass_multiplePrompts(self):
        self.calls_interpret(True,
            """
            >>> x = 5
            >>> x + 4
            9
            >>> 5 + x
            10
            """)

    def testPass_multilineWithIndentation(self):
        self.calls_interpret(True,
            """
            >>> def square(x):
            ...     return x * x
            >>> square(4)
            16
            """)

    def testPass_setup(self):
        self.calls_interpret(True,
            """
            >>> def square(x):
            ...     return x * x
            >>> square(x)
            9
            >>> square(y)
            1
            """,
            setup="""
            >>> x = 3
            >>> y = 1
            """)

    def testPass_teardown(self):
        # TODO(albert)
        pass

    def testError_notEqualError(self):
        self.calls_interpret(False,
            """
            >>> 2 + 4
            7
            """)

    def testError_expectedException(self):
        self.calls_interpret(False,
            """
            >>> 1 + 2
            ZeroDivisionError
            """)

    def testError_wrongException(self):
        self.calls_interpret(False,
            """
            >>> 1 / 0
            TypeError
            """)

    def testError_runtimeError(self):
        self.calls_interpret(False,
            """
            >>> f = lambda: f()
            >>> f()
            4
            """)

    def testError_timeoutError(self):
        # TODO(albert): test timeout errors without actually waiting
        # for timeouts.
        pass

    def testError_teardown(self):
        # TODO(albert):
        pass

# class OnGradeTest(unittest.TestCase):
#     ASSIGN_NAME = 'dummy'
#
#     def setUp(self):
#         # This logger captures output and is used by the unittest,
#         # it is wired to stdout.
#         self.log = []
#         self.capture = sys.stdout = output.OutputLogger()
#         self.capture.register_log(self.log)
#         self.capture.on = mock.Mock()
#         self.capture.off = mock.Mock()
#
#         # This logger is used by on_grade.
#         self.logger = output.OutputLogger()
#
#         self.case_map = {'doctest': doctest_case.DoctestCase}
#         self.makeAssignment()
#         self.makeTest()
#
#     def tearDown(self):
#         self.stdout = sys.__stdout__
#
#     def makeAssignment(self, hidden_params=None, params=None):
#         json = {
#             'name': self.ASSIGN_NAME,
#             'version': '1.0',
#         }
#         if hidden_params:
#             json['hidden_params'] = hidden_params
#         if params:
#             json['params'] = params
#         self.assignment = core.Assignment.deserialize(json, self.case_map)
#         return self.assignment
#
#     def makeTest(self, hidden_params=None, params=None):
#         json = {
#             'names': ['q1'],
#             'points': 1,
#         }
#         if hidden_params:
#             json['hidden_params'] = hidden_params
#         if params:
#             json['params'] = params
#         self.test = core.Test.deserialize(json, self.assignment, self.case_map)
#         return self.test
#
#     def makeTestCase(self, case_json):
#         case_json['type'] = doctest_case.DoctestCase.type
#         if 'locked' not in case_json:
#             case_json['locked'] = False
#         return doctest_case.DoctestCase.deserialize(case_json,
#                 self.assignment, self.test)
#
#     def calls_onGrade(self, case_json, errors=False, verbose=False,
#             interact=False):
#         case = self.makeTestCase(case_json)
#         error = case.on_grade(self.logger, verbose, interact, 10)
#         if errors:
#             self.assertTrue(error)
#         else:
#             self.assertFalse(error)
#
#     def assertCorrectLog(self, expected_log):
#         expected_log = '\n'.join(expected_log).strip('\n')
#         log = ''.join(self.capture.log).strip('\n')
#         self.assertEqual(expected_log, log)
#
#     def testOutput_singleLine(self):
#         self.calls_onGrade({
#             'test': """
#             >>> 1 + 2
#             3
#             """
#         })
#         self.assertCorrectLog([
#             '>>> 1 + 2',
#             '3'
#         ])
#
#     def testOutput_multiLineIndentNoNewline(self):
#         self.calls_onGrade({
#             'test': """
#             >>> def square(x):
#             ...     return x * x
#             >>> square(4)
#             16
#             """,
#         })
#         self.assertCorrectLog([
#             '>>> def square(x):',
#             '...     return x * x',
#             '>>> square(4)',
#             '16',
#         ])
#
#     def testOutput_multiLineIndentWithNewLine(self):
#         self.calls_onGrade({
#             'test': """
#             >>> def square(x):
#             ...     return x * x
#
#             >>> square(4)
#             16
#             """,
#         })
#         self.assertCorrectLog([
#             '>>> def square(x):',
#             '...     return x * x',
#             '>>> square(4)',
#             '16',
#         ])
#
#     def testOutput_forLoop(self):
#         self.calls_onGrade({
#             'test': """
#             >>> for i in range(3):
#             ...     print(i)
#             >>> 3 + 4
#             7
#             """
#         })
#         self.assertCorrectLog([
#             '>>> for i in range(3):',
#             '...     print(i)',
#             '0',
#             '1',
#             '2',
#             '>>> 3 + 4',
#             '7',
#         ])
#
#     def testOutput_errorNotEqual(self):
#         self.calls_onGrade({
#             'test': """
#             >>> 3 + 4
#             1
#             """,
#         }, errors=True)
#         self.assertCorrectLog([
#             '>>> 3 + 4',
#             '7',
#             '# Error: expected 1 got 7'
#         ])
#
#     def testOutput_errorOnNonPrompt(self):
#         self.calls_onGrade({
#             'test': """
#             >>> x = 1 / 0
#             >>> 3 + 4
#             7
#             """,
#         }, errors=True)
#         self.assertCorrectLog([
#             '>>> x = 1 / 0',
#             'ZeroDivisionError: division by zero'
#         ])
#
#     def testOutput_errorOnPromptWithException(self):
#         self.calls_onGrade({
#             'test': """
#             >>> 1 / 0
#             1
#             """,
#         }, errors=True)
#         self.assertCorrectLog([
#             '>>> 1 / 0',
#             'ZeroDivisionError: division by zero',
#             '# Error: expected 1 got ZeroDivisionError'
#         ])
#
class UnlockTest(unittest.TestCase):
    def setUp(self):
        self.console = mock.Mock(spec=doctest_case.PythonConsole)
        self.mock_answer = ['mock']
        self.interact_fn = mock.Mock(return_value=self.mock_answer)

    def makeCase(self, code):
        return doctest_case.DoctestCase(self.console, code=code)

    def calls_unlock(self, code, expect, errors=False):
        case = self.makeCase(code)
        if errors:
            self.assertRaises(unlock.UnlockException, case.unlock, self.interact_fn)
            return
        case.unlock(self.interact_fn)
        self.assertFalse(case.locked)

        answers = [line for line in case.lines
                        if isinstance(line, doctest_case._Answer)]
        self.assertEqual(expect, [answer.output for answer in answers])
        self.assertEqual([False] * len(answers),
                         [answer.locked for answer in answers])

    def testUnlockAll(self):
        self.calls_unlock(
            """
            >>> 3 + 4
            <hash>
            # locked
            >>> 3 + 1
            <hash>
            # locked
            >>> 1 / 0
            <hash>
            # locked
            """,
            [self.mock_answer] * 3)

    def testNoLockedAnswers(self):
        self.calls_unlock(
            """
            >>> 3 + 4
            7
            >>> 'foo'
            'foo'
            """,
            [['7'],
             ["'foo'"]])

    def testPartiallyLockedAnswers(self):
        self.calls_unlock(
            """
            >>> 3 + 4
            7
            >>> 'foo'
            <hash>
            # locked
            """,
            [['7'],
             self.mock_answer])

class OnLockTest(unittest.TestCase):
    ANSWER = 42

    def setUp(self):
        self.console = mock.Mock(spec=doctest_case.PythonConsole)
        self.hash_fn = mock.Mock(return_value=self.ANSWER)

    def makeCase(self, code):
        return doctest_case.DoctestCase(self.console, code=code)

    def calls_lock(self, code, expect):
        case = self.makeCase(code)
        case.lock(self.hash_fn)
        self.assertTrue(case.locked)

        answers = [line for line in case.lines
                        if isinstance(line, doctest_case._Answer)]
        self.assertEqual(expect,
                         [answer.output for answer in answers])
        self.assertEqual([True] * len(answers),
                         [answer.locked for answer in answers])

    def testLockAll(self):
        self.calls_lock(
            """
            >>> 3 + 4
            7
            >>> 3 + 1
            4
            >>> 1 / 0
            ZeroDivisionError
            """,
            [[self.ANSWER],
             [self.ANSWER],
             [self.ANSWER]])

    def testLockNone(self):
        self.calls_lock(
            """
            >>> 3 + 4
            7
            # locked
            >>> 'foo'
            'foo'
            # locked
            """,
            [['7'],
             ["'foo'"]])

    def testPartiallyLockedAnswers(self):
        self.calls_lock(
            """
            >>> 3 + 4
            7
            >>> 9
            9
            # locked
            """,
            [[self.ANSWER],
             ['9']])


class ToJsonTest(unittest.TestCase):
    def setUp(self):
        self.console = mock.Mock(spec=doctest_case.PythonConsole)
        self.interact_fn = mock.Mock(side_effect=lambda x, y: x)

    def makeCase(self, **fields):
        return doctest_case.DoctestCase(self.console, **fields)

    def testUnlocked(self):
        case = self.makeCase(
            code="""
            >>> square(-2)
            1
            >>> square(-2)
            2
            # locked
            >>> square(-2)
            3
            # locked
            # choice: 0
            # choice: 2
            # choice: 5
            """)
        expect = textwrap.dedent("""
            >>> square(-2)
            1
            >>> square(-2)
            2
            >>> square(-2)
            3
            """)
        case.unlock(self.interact_fn)
        result = case.to_json()

        self.assertIn('code', result)
        self.assertEqual(expect, result['code'])



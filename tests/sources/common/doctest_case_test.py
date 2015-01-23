from client.sources.common import doctest_case
import mock
import textwrap
import unittest

class PythonConsoleTest(unittest.TestCase):
    def createConsole(self, verbose=True, interactive=False, timeout=None):
        self.console = doctest_case.PythonConsole(
                verbose, interactive, timeout)

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

class DoctestCaseTest(unittest.TestCase):
    def setUp(self):
        self.console = doctest_case.PythonConsole(False, False)

    def makeCase(self, code, setup='', teardown=''):
        return doctest_case.DoctestCase(self.console, setup, teardown, code=code)

    def testConstructor_basicCase(self):
        try:
            self.makeCase("""
            >>> 4 + 2
            6
            """)
        except TypeError:
            self.fail()

    def testConstructor_missingCode(self):
        self.assertRaises(TypeError, doctest_case.DoctestCase, self.console)

    def testConstructor_setupAndTeardown(self):
        try:
            self.makeCase("""
            >>> 4 + 2
            6
            """,
            setup="""
            >>> import hi
            """,
            teardown="""
            >>> print('hi')
            """)
        except TypeError:
            self.fail()

    def testRun_success(self):
        case = self.makeCase("""
        >>> 2 + 2
        4
        """)
        self.assertTrue(case.run())

    def testRun_fail(self):
        case = self.makeCase("""
        >>> 2 + 2
        5
        """)
        self.assertFalse(case.run())

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

class LockTest:
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


class ToJsonTest:
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



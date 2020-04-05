from client import exceptions as ex
from client.sources.common import interpreter
import mock
import textwrap
import unittest

class CodeCaseTest(unittest.TestCase):
    def setUp(self):
        self.console = mock.Mock(interpreter.Console)
        self.console.PS1 = '> '
        self.console.PS2 = '. '
        self.console.normalize = lambda x: x

    def makeCase(self, code, setup='', teardown=''):
        return interpreter.CodeCase(self.console, setup, teardown, code=code)

    def testConstructor_basicCase(self):
        try:
            self.makeCase("""
            > 4 + 2
            6
            """)
        except TypeError:
            self.fail()

    def testConstructor_missingCode(self):
        self.assertRaises(ex.SerializeException, interpreter.CodeCase,
                          self.console)

    def testConstructor_setupAndTeardown(self):
        try:
            self.makeCase("""
            > 4 + 2
            6
            """,
            setup="""
            > setup code
            """,
            teardown="""
            > teardown code
            """)
        except TypeError:
            self.fail()

    def testRun_success(self):
        case = self.makeCase("""
        > 2 + 2
        4
        """)
        self.console.interpret.return_value = True
        self.assertTrue(case.run())

    def testRun_debug_success(self):
        case = self.makeCase("""
        > print("DEBUG: ignore this line")
        """)
        self.console.interpret.return_value = True
        self.assertTrue(case.run())

    def testRun_fail(self):
        case = self.makeCase("""
        >>> 2 + 2
        5
        """)
        self.console.interpret.return_value = False
        self.assertFalse(case.run())

class UnlockTest(unittest.TestCase):
    CASE_ID = 'Test 1 > Suite 1 > Case 1'
    UNIQUE_ID_PREFIX = 'assignment\ntest'

    def setUp(self):
        self.console = mock.Mock(interpreter.Console)
        self.console.PS1 = '> '
        self.console.PS2 = '. '
        self.console.normalize = lambda x: x

        self.mock_answer = ['mock']
        self.interact_fn = mock.Mock(return_value=self.mock_answer)

    def makeCase(self, code):
        return interpreter.CodeCase(self.console, code=code)

    def calls_unlock(self, code, expect, errors=False):
        case = self.makeCase(code)
        if errors:
            self.assertRaises(unlock.UnlockException, case.unlock, self.CASE_ID,
                              self.interact_fn)
            return
        case.unlock(self.UNIQUE_ID_PREFIX, self.CASE_ID, self.interact_fn)
        self.assertFalse(case.locked)

        answers = [line for line in case.lines
                        if isinstance(line, interpreter.CodeAnswer)]
        self.assertEqual(expect, [answer.output for answer in answers])
        self.assertEqual([False] * len(answers),
                         [answer.locked for answer in answers])

    def testUnlockAll(self):
        self.calls_unlock(
            """
            > 3 + 4
            <hash>
            # locked
            > 3 + 1
            <hash>
            # locked
            > 1 / 0
            <hash>
            # locked
            """,
            [self.mock_answer] * 3)

    def testNoLockedAnswers(self):
        self.calls_unlock(
            """
            > 3 + 4
            7
            > 'foo'
            'foo'
            """,
            [['7'],
             ["'foo'"]])

    def testPartiallyLockedAnswers(self):
        self.calls_unlock(
            """
            > 3 + 4
            7
            > 'foo'
            <hash>
            # locked
            """,
            [['7'],
             self.mock_answer])

class LockTest:
    ANSWER = 42

    def setUp(self):
        self.console = mock.Mock(interpreter.Console)
        self.console.PS1 = '> '
        self.console.PS2 = '. '
        self.console.normalize = lambda x: x

        self.hash_fn = mock.Mock(return_value=self.ANSWER)

    def makeCase(self, code):
        return interpreter.CodeCase(self.console, code=code)

    def calls_lock(self, code, expect):
        case = self.makeCase(code)
        case.lock(self.hash_fn)
        self.assertTrue(case.locked)

        answers = [line for line in case.lines
                        if isinstance(line, interpreter.CodeAnswer)]
        self.assertEqual(expect,
                         [answer.output for answer in answers])
        self.assertEqual([True] * len(answers),
                         [answer.locked for answer in answers])

    def testLockAll(self):
        self.calls_lock(
            """
            > 3 + 4
            7
            > 3 + 1
            4
            > 1 / 0
            ZeroDivisionError
            """,
            [[self.ANSWER],
             [self.ANSWER],
             [self.ANSWER]])

    def testLockNone(self):
        self.calls_lock(
            """
            > 3 + 4
            7
            # locked
            > 'foo'
            'foo'
            # locked
            """,
            [['7'],
             ["'foo'"]])

    def testPartiallyLockedAnswers(self):
        self.calls_lock(
            """
            > 3 + 4
            7
            > 9
            9
            # locked
            """,
            [[self.ANSWER],
             ['9']])


class ToJsonTest:
    CASE_ID = 'Test 1 > Suite 1 > Case 1'
    UNIQUE_ID_PREFIX = 'Assignment\nTest'

    def setUp(self):
        self.console = mock.Mock(interpreter.Console)
        self.console.normalize = lambda x: x
        self.interact_fn = mock.Mock(side_effect=lambda x, y: x)

    def makeCase(self, **fields):
        return interpreter.CodeCase(self.console, **fields)

    def testUnlocked(self):
        case = self.makeCase(
            code="""
            > square(-2)
            1
            > square(-2)
            2
            # locked
            > square(-2)
            3
            # locked
            # choice: 0
            # choice: 2
            # choice: 5
            """)
        expect = textwrap.dedent("""
            > square(-2)
            1
            > square(-2)
            2
            > square(-2)
            3
            """)
        case.unlock(self.UNIQUE_ID_PREFIX, self.CASE_ID, self.interact_fn)
        result = case.to_json()

        self.assertIn('code', result)
        self.assertEqual(expect, result['code'])



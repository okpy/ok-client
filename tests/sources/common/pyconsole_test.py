from client.sources.common import interpreter
from client.sources.common import pyconsole
from client.utils import locking
import client
import unittest

class PythonConsoleTest(unittest.TestCase):
    def createConsole(self, verbose=True, interactive=False, timeout=None):
        return pyconsole.PythonConsole(
                verbose, interactive, timeout)

    def calls_interpret(self, success, code, setup='', teardown='', skip_locked_cases=True, hash_key=None):
        self.console = self.createConsole()
        self.console.skip_locked_cases = skip_locked_cases
        self.console.hash_key = hash_key
        lines = interpreter.CodeCase.split_code(code, self.console.PS1,
                                                self.console.PS2)
        self.console.load(lines, setup, teardown)
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
        self.calls_interpret(True,
            """
            >>> def square(x):
            ...     return x * x
            >>> square(3)
            9
            >>> square(1)
            1
            """,
            teardown="""
            >>> import client
            >>> client.foo = 1
            """)
        self.assertEqual(1, client.foo)

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
        self.calls_interpret(False,
            """
            >>> 1 / 0
            """,
            teardown="""
            >>> import client
            >>> client.foo = 2
            """)
        self.assertEqual(2, client.foo)

    def testError_setUpFails(self):
        self.calls_interpret(False,
            """
            >>> client.foo = 4
            """,
            setup="""
            >>> import client
            >>> client.foo = 3
            >>> 1 / 0
            """,
            teardown="""
            >>> client.foo = 5
            """)
        self.assertEqual(3, client.foo)

    def testError_tearDownFails(self):
        self.calls_interpret(False,
            """
            >>> x = 3
            """,
            teardown="""
            >>> 1 / 0
            """)
            
    
        
    def testPass_locked(self):
        key = "testKey"
        hashedAnswer = locking.lock(key, "4")
        self.calls_interpret(True, """
        >>> 2 + 2
        %s
        """ % hashedAnswer, skip_locked_cases=False, hash_key=key)
        
    def testError_locked(self):
        key = "testKey"
        hashedAnswer = locking.lock(key, "5")
        self.calls_interpret(False, """
        >>> 2 + 2
        %s
        """ % hashedAnswer, skip_locked_cases=False, hash_key=key)
        
    def testError_skipLocked(self):
        key = "testKey"
        hashedAnswer = locking.lock(key, "4")
        self.calls_interpret(False, """
        >>> 2 + 2
        %s
        """ % hashedAnswer)

from client import exceptions
from client.sources.common import interpreter
from client.sources.ok_test import doctest
from client.utils import output
from client.utils import timer
import importlib
import textwrap
import traceback

class SchemeConsole(interpreter.Console):
    PS1 = 'scm> '
    PS2 = '.... '

    MODULE = 'scheme'

    def __init__(self, verbose, interactive, timeout=None):
        """Loads the Scheme module from the current working directory
        before calling the superclass constructor.
        """
        self._import_scheme()
        super().__init__(verbose, interactive, timeout)

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        super().load(code, setup, teardown)
        self._import_scheme()
        self._frame = self.scheme.create_global_frame()

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        pass

    def evaluate(self, code):
        if not code.strip():
            # scheme.scheme_read can't handle empty strings.
            return None, None
        log_id = output.new_log()
        try:
            exp = self.scheme.read_line(code)
            result = timer.timed(self.timeout, self.scheme.scheme_eval,
                                 (exp, self._frame))
        except RuntimeError as e:
            stacktrace_length = 15
            stacktrace = traceback.format_exc().strip().split('\n')
            print('Traceback (most recent call last):\n  ...')
            print('\n'.join(stacktrace[-stacktrace_length:]))
            raise interpreter.ConsoleException(e)
        except exceptions.Timeout as e:
            print('# Error: evaluation exceeded {} seconds.'.format(e.timeout))
            raise interpreter.ConsoleException(e)
        except Exception as e:
            stacktrace = traceback.format_exc()
            token = '<module>\n'
            index = stacktrace.rfind(token) + len(token)
            stacktrace = stacktrace[index:].rstrip('\n')
            if '\n' in stacktrace:
                print('Traceback (most recent call last):')
            print(stacktrace)
            raise interpreter.ConsoleException(e)
        else:
            printed_output = ''.join(output.get_log(log_id))
            return result, printed_output
        finally:
            output.remove_log(log_id)


    def _import_scheme(self):
        try:
            self.scheme = importlib.import_module(self.MODULE)
        except ImportError as e:
            raise e

class SchemeSuite(doctest.DoctestSuite):
    console_type = SchemeConsole


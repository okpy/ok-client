from contextlib import contextmanager

from lark import Lark, LarkError, UnexpectedEOF

from client import exceptions
from client.sources.common import interpreter
from client.sources.ok_test import doctest
from client.utils import output
from client.utils import timer
from client.utils import debug

import traceback

class LarkConsole(interpreter.Console):
    PS1 = 'lark> '
    PS2 = '....> '

    _output_fn = str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser = None

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        try:
            with self._lark_execution_guard():
                self._parser = Lark("\n".join(self._setup), start="start", import_paths=["."])
                assert not self._teardown, "Lark tests do not support teardown"
                pass
        except interpreter.ConsoleException:
            return False

        return self._interpret_lines(self._code, compare_all=True)

    def evaluate(self, code):
        if not code:
            return None, ''
        log_id = output.new_log()
        with self._lark_execution_guard():
            result = timer.timed(self.timeout, self._parser.parse, [], dict(text=code))
            printed_output = ''.join(output.get_log(log_id))
            return self.normalize(result.pretty()), debug.remove_debug(printed_output)

    @contextmanager
    def _lark_execution_guard(self):
        log_id = output.new_log()
        try:
            yield
        except exceptions.Timeout as e:
            print('# Error: evaluation exceeded {} seconds.'.format(e.timeout))
            raise interpreter.ConsoleException(e)
        except (LarkError, UnexpectedEOF) as e:
            print('# Error: {}'.format(e))
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
        finally:
            output.remove_log(log_id)

    @staticmethod
    def normalize(response):
        return "\n".join(
            line.rstrip() for line in response.replace("\t", "  ").split("\n")
        )

class LarkSuite(doctest.DoctestSuite):
    console_type = LarkConsole

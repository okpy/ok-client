"""Case for doctest-style Python tests."""

from client import exceptions
from client.sources.common import core
from client.sources.common import interpreter
from client.sources.common import models
from client.utils import output
from client.utils import timer
import code
import re
import textwrap
import traceback

class DoctestCase(interpreter.InterpreterCase):
    """TestCase for doctest-style Python tests."""

    code = core.String()

    PS1 = '>>> '
    PS2 = '... '

    def __init__(self, console, setup='', teardown='', **fields):
        """Constructor.

        PARAMETERS:
        input_str -- str; the input string, which will be dedented and
                     split along newlines.
        outputs   -- list of TestCaseAnswers
        test      -- Test or None; the test to which this test case
                     belongs.
        frame     -- dict; the environment in which the test case will
                     be executed.
        teardown  -- str; the teardown code. This code will be executed
                     regardless of errors.
        status    -- keyword arguments; statuses for the test case.
        """
        assert isinstance(console, PythonConsole), 'Improper console: {}'.format(console)
        super().__init__(console, **fields)
        self.setup = setup
        self.teardown = teardown

    def post_instantiation(self):
        self.code = textwrap.dedent(self.code)
        self.setup = textwrap.dedent(self.setup)
        self.teardown = textwrap.dedent(self.teardown)

        self.lines = _split_code(self.code, self.PS1, self.PS2)

    def preprocess(self):
        self.console.load(self.code, setup=self.setup, teardown=self.teardown)

    def lock(self, hash_fn):
        assert self.locked != False, 'called lock when self.lock = False'
        for line in self.lines:
            if isinstance(line, _Answer) and not line.locked:
                line.output = [hash_fn(output) for output in line.output]
                line.locked = True
        self.locked = True
        self._sync_code()

    def unlock(self, interact):
        """Unlocks the DoctestCase.

        PARAMETERS:
        interact -- function; handles user interaction during the unlocking
                    phase.
        """
        try:
            for line in self.lines:
                if isinstance(line, str) and line:
                    print(line)
                elif isinstance(line, _Answer):
                    if not line.locked:
                        print('\n'.join(line.output))
                        continue
                    line.output = interact(line.output, line.choices)
                    line.locked = False
            self.locked = False
        finally:
            self._sync_code()

    def _sync_code(self):
        new_code = []
        for line in self.lines:
            if isinstance(line, _Answer):
                new_code.append(line.dump())
            else:
                new_code.append(line)
        self.code = '\n'.join(new_code)

class _Answer(object):
    status_re = re.compile(r'^#\s*(.+?):\s*(.*)\s*$')
    locked_re = re.compile(r'^#\s*locked\s*$')

    def __init__(self, output=None, choices=None, explanation='', locked=False):
        self.output = output or []
        self.choices = choices or []
        self.locked = locked
        self.explanation = explanation

    def dump(self):
        result = list(self.output)
        if self.locked:
            result.append('# locked')
            if self.choices:
                for choice in self.choices:
                    result.append('# choice: ' + choice)
        if self.explanation:
            result.append('# explanation: ' + self.explanation)
        return '\n'.join(result)

    def update(self, line):
        if self.locked_re.match(line):
            self.locked = True
            return
        match = self.status_re.match(line)
        if not match:
            self.output.append(line)
        elif match.group(1) == 'locked':
            self.locked = True
        elif match.group(1) == 'explanation':
            self.explanation = match.group(2)
        elif match.group(1) == 'choice':
            self.choices.append(match.group(2))

class PythonConsole(interpreter.Console):
    PS1 = DoctestCase.PS1
    PS2 = DoctestCase.PS2

    def __init__(self, verbose, interactive, timeout=None):
        super().__init__(verbose, interactive, timeout)
        self.load('')   # Initialize empty code.

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        self._frame = {}
        self._setup = textwrap.dedent(setup).split('\n')
        self._code = _split_code(code, self.PS1, self.PS2)
        self._teardown = textwrap.dedent(teardown).split('\n')

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        # If the setup fails, do not proceed with the rest of the test
        if not self._interpret_lines(self._setup):
            return False

        success = self._interpret_lines(self._code, compare=True)
        success &= self._interpret_lines(self._teardown)
        return success

    def _interpret_lines(self, lines, compare=False):
        """Interprets the set of lines.

        RETURNS:
        bool; True if successful, False otherwise.
        """
        self.clear_history()

        current = []
        for line in lines + ['']:
            if isinstance(line, str):
                if current and (line.startswith(self.PS1) or not line):
                    # Previous prompt ends when PS1 or a blank line occurs
                    try:
                        self._evaluate('\n'.join(current))
                    except PythonConsoleException:
                        return False
                    current = []
                if line:
                    print(line)
                line = self._strip_prompt(line)
                self.add_history(line)
                current.append(line)
            elif isinstance(line, _Answer):
                assert len(current) > 0, 'Answer without a prompt'
                try:
                    self._compare('\n'.join(line.output), '\n'.join(current))
                except PythonConsoleException:
                    return False
                current = []
        return True

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        console = code.InteractiveConsole(self._frame)
        console.interact('# Interactive console. Type exit() to quit')

    def _compare(self, expected, code):
        try:
            value, output = self._evaluate(code)
        except PythonConsoleException as e:
            actual = e.exception.__class__.__name__
        else:
            if value is not None:
                print(repr(value))
                actual = (output + '\n' + repr(value)).strip()
            else:
                actual = output.strip()

        expected = expected.strip()
        if expected != actual:
            print()
            print('# Error: expected')
            print('\n'.join('#     {}'.format(line)
                            for line in expected.split('\n')))
            print('# but got')
            print('\n'.join('#     {}'.format(line)
                            for line in actual.split('\n')))
            raise PythonConsoleException

    def _evaluate(self, code, frame=None):
        if frame is None:
            frame = self._frame
        log_id = output.new_log()
        try:
            try:
                result = timer.timed(self.timeout, eval, (code, frame))
            except SyntaxError:
                timer.timed(self.timeout, exec, (code, frame))
                result = None
        except RuntimeError as e:
            stacktrace_length = 15
            stacktrace = traceback.format_exc().strip().split('\n')
            print('Traceback (most recent call last):\n  ...')
            print('\n'.join(stacktrace[-stacktrace_length:]))
            raise PythonConsoleException(e)
        except exceptions.Timeout as e:
            print('# Error: evaluation exceeded {} seconds.'.format(e.timeout))
            raise PythonConsoleException(e)
        except Exception as e:
            stacktrace = traceback.format_exc()
            token = '<module>\n'
            index = stacktrace.rfind(token) + len(token)
            stacktrace = stacktrace[index:].rstrip('\n')
            if '\n' in stacktrace:
                print('Traceback (most recent call last):')
            print(stacktrace)
            raise PythonConsoleException(e)
        else:
            printed_output = ''.join(output.get_log(log_id))
            return result, printed_output
        finally:
            output.remove_log(log_id)

    def _strip_prompt(self, line):
        if line.startswith(self.PS1):
            return line[len(self.PS1):]
        elif line.startswith(self.PS2):
            return line[len(self.PS2):]
        return line

class PythonConsoleException(Exception):
    def __init__(self, exception=None):
        self.exception = exception


def _split_code(code, PS1, PS2):
    processed_lines = []
    for line in textwrap.dedent(code).split('\n'):
        if not line or line.startswith(PS1) or line.startswith(PS2):
            processed_lines.append(line)
            continue

        assert len(processed_lines) > 0, 'code improperly formated: {}'.format(code)
        if not isinstance(processed_lines[-1], _Answer):
            processed_lines.append(_Answer())
        processed_lines[-1].update(line)
    return processed_lines


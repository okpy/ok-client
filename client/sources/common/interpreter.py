"""Case for generic interpreter-style tests."""

from client.sources.common import core
from client.sources.common import models
from client.utils import locking
import re
import textwrap

class CodeCase(models.Case):
    """TestCase for doctest-style Python tests."""

    code = core.String()

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
        super().__init__(**fields)
        self.console = console
        self.setup = setup
        self.teardown = teardown

    def post_instantiation(self):
        self.code = textwrap.dedent(self.code)
        self.setup = textwrap.dedent(self.setup)
        self.teardown = textwrap.dedent(self.teardown)

        self.lines = self.split_code(self.code, self.console.PS1, self.console.PS2)

    def run(self):
        """Implements the GradedTestCase interface."""
        self.console.load(self.lines, setup=self.setup, teardown=self.teardown)
        return self.console.interpret()

    def lock(self, hash_fn):
        assert self.locked != False, 'called lock when self.lock = False'
        for line in self.lines:
            if isinstance(line, CodeAnswer) and not line.locked:
                line.output = [hash_fn(output) for output in line.output]
                line.locked = True
        self.locked = True
        self._sync_code()

    def unlock(self, unique_id_prefix, case_id, interact):
        """Unlocks the CodeCase.

        PARAMETERS:
        unique_id_prefix -- string; a prefix of a unique identifier for this
                            Case, for purposes of analytics.
        case_id          -- string; an identifier for this Case, for purposes of
                            analytics.
        interact         -- function; handles user interaction during the unlocking
                            phase.
        """
        print(self.setup.strip())
        prompt_num = 0
        current_prompt = []
        try:
            for line in self.lines:
                if isinstance(line, str) and line:
                    print(line)
                    current_prompt.append(line)
                elif isinstance(line, CodeAnswer):
                    prompt_num += 1
                    if not line.locked:
                        print('\n'.join(line.output))
                        continue

                    unique_id = self._construct_unique_id(unique_id_prefix, self.lines)
                    line.output = interact(unique_id,
                                           case_id + ' >  Prompt {}'.format(prompt_num),
                                           '\n'.join(current_prompt),
                                           line.output, line.choices)
                    line.locked = False
                    current_prompt = []
            self.locked = False
        finally:
            self._sync_code()

    @classmethod
    def split_code(cls, code, PS1, PS2):
        """Splits the given string of code based on the provided PS1 and PS2
        symbols.

        PARAMETERS:
        code -- str; lines of interpretable code, using PS1 and PS2 prompts
        PS1  -- str; first-level prompt symbol
        PS2  -- str; second-level prompt symbol

        RETURN:
        list; a processed sequence of lines corresponding to the input code.
        """
        processed_lines = []
        for line in textwrap.dedent(code).split('\n'):
            if not line or line.startswith(PS1) or line.startswith(PS2):
                processed_lines.append(line)
                continue

            assert len(processed_lines) > 0, 'code improperly formated: {}'.format(code)
            if not isinstance(processed_lines[-1], CodeAnswer):
                processed_lines.append(CodeAnswer())
            processed_lines[-1].update(line)
        return processed_lines

    def _sync_code(self):
        """Syncs the current state of self.lines with self.code, the
        serializable string representing the set of code.
        """
        new_code = []
        for line in self.lines:
            if isinstance(line, CodeAnswer):
                new_code.append(line.dump())
            else:
                new_code.append(line)
        self.code = '\n'.join(new_code)

    def _construct_unique_id(self, id_prefix, lines):
        """Constructs a unique ID for a particular prompt in this case,
        based on the id_prefix and the lines in the prompt.
        """
        text = []
        for line in lines:
            if isinstance(line, str):
                text.append(line)
            elif isinstance(line, CodeAnswer):
                text.append(line.dump())
        return id_prefix + '\n' + '\n'.join(text)


class Console(object):
    PS1 = '> '
    PS2 = '. '

    _output_fn = repr

    ####################
    # Public interface #
    ####################

    def __init__(self, verbose, interactive, timeout=None):
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout
        self.skip_locked_cases = True
        self.load('')   # Initialize empty code.

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.

        PARAMETERS:
        code     -- list; processed lines of code. Elements in the list are
                    either strings (input) or CodeAnswer objects (output)
        setup    -- str; raw setup code
        teardown -- str; raw teardown code
        """
        self._setup = textwrap.dedent(setup).split('\n')
        self._code = code
        self._teardown = textwrap.dedent(teardown).split('\n')

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        if not self._interpret_lines(self._setup):
            return False

        success = self._interpret_lines(self._code, compare_all=True)
        success &= self._interpret_lines(self._teardown)
        return success

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        pass

    def evaluate(self, code):
        """Evaluates the given code.

        PARAMETERS:
        code -- str

        RETURNS:
        (result, output), where
        result -- the evaluated result of the code
        output -- str; any output that was printed to stdout
        """
        raise NotImplementedError

    ############################
    # Interpretation utilities #
    ############################

    def _interpret_lines(self, lines, compare_all=False):
        """Interprets the set of lines.

        PARAMTERS:
        lines       -- list of str; lines of code
        compare_all -- bool; if True, check for no output for lines that are not
                       followed by a CodeAnswer

        RETURNS:
        bool; True if successful, False otherwise.
        """
        current = []
        for line in lines + ['']:
            if isinstance(line, str):
                if current and (line.startswith(self.PS1) or not line):
                    # Previous prompt ends when PS1 or a blank line occurs
                    try:
                        if compare_all:
                            self._compare('', '\n'.join(current))
                        else:
                            self.evaluate('\n'.join(current))
                    except ConsoleException:
                        return False
                    current = []
                if line:
                    print(line)
                line = self._strip_prompt(line)
                current.append(line)
            elif isinstance(line, CodeAnswer):
                assert len(current) > 0, 'Answer without a prompt'
                try:
                    self._compare('\n'.join(line.output), '\n'.join(current))
                except ConsoleException:
                    return False
                current = []
        return True

    def _compare(self, expected, code):
        try:
            value, printed = self.evaluate(code)
        except ConsoleException as e:
            actual = e.exception_type
        else:
            if value is not None:
                print(self._output_fn(value))
                actual = (printed + self._output_fn(value)).strip()
            else:
                actual = printed.strip()

        expected = expected.strip()
        
        if not self.skip_locked_cases and expected != actual:
            actual = locking.lock(self.hash_key, actual)
            if expected != actual:
                print()
                print("# Error: expected and actual results do not match")
                raise ConsoleException
        elif expected != actual:
            print()
            print('# Error: expected')
            print('\n'.join('#     {}'.format(line)
                            for line in expected.split('\n')))
            print('# but got')
            print('\n'.join('#     {}'.format(line)
                            for line in actual.split('\n')))
            raise ConsoleException

    def _strip_prompt(self, line):
        if line.startswith(self.PS1):
            return line[len(self.PS1):]
        elif line.startswith(self.PS2):
            return line[len(self.PS2):]
        return line


class CodeAnswer(object):
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


class ConsoleException(Exception):
    def __init__(self, exception=None, exception_type=''):
        self.exception = exception
        if not exception or exception_type:
            self.exception_type = exception_type
        else:
            self.exception_type = exception.__class__.__name__


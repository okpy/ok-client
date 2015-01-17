"""Case for generic interpreter-style tests."""

from client.sources.common import models

# TODO(albert): come up with a better cross-platform readline solution.
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

class InterpreterCase(models.Case):
    """TestCase for doctest-style Python tests."""

    def __init__(self, console, **fields):
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

    def run(self):
        """Implements the GradedTestCase interface."""
        self.preprocess()
        success = self.console.interpret()
        self.postprocess()
        return success

    def preprocess(self):
        pass

    def postprocess(self):
        pass

class Console(object):
    def __init__(self, verbose, interactive, timeout=None):
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def load(self, code, setup=None, teardown=None):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        pass

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        raise NotImplementedError

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        pass

    ######################
    # History management #
    ######################

    def add_history(self, line):
        if HAS_READLINE:
            readline.add_history(line)

    def clear_history(self):
        if HAS_READLINE:
            readline.clear_history()

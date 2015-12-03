"""Console for interpreting sqlite."""

from client import exceptions
from client.sources.common import core, interpreter
from client.sources.ok_test import doctest
from client.utils import format
from client.utils import timer
import importlib
import os
import re
import subprocess

class SqliteConsole(interpreter.Console):
    PS1 = 'sqlite> '
    PS2 = '   ...> '

    MODULE = 'sqlite3'
    VERSION = (3, 8, 3)

    ordered = False # will be set by SqliteSuite.__init__

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.

        Loads the sqlite3 module before loading any code.
        """
        super().load(code, setup, teardown)

    def interpret(self):
        """Interprets the code in this Console.

        Due to inconsistencies with sqlite3 and Python's bindings, the following
        process is used to interpret code:

        1. If the Python sqlite3 module has an up-to-date binding (compared to
           self.VERSION), interpret line-by-line with full output validation.
        2. Otherwise, if there is an executable called "sqlite3" (in the current
           directory is okay), pipe the test case into sqlite3 and display
           expected and actual output. No output validation is available;
           students have to verify their solutions manually.
        3. Otherwise, report an error.
        """
        if self._import_sqlite():
            self._conn = self.sqlite3.connect(':memory:', check_same_thread=False)
            return super().interpret()
        env = dict(os.environ,
                   PATH=os.getcwd() + os.pathsep + os.environ["PATH"])
        if self._has_sqlite_cli(env):
            test, expected, actual = self._use_sqlite_cli(env)
            print(format.indent(test, 'sqlite> '))  # TODO: show test with prompt
            print(actual)
            try:
                self._diff_output(expected, actual)
                return True
            except interpreter.ConsoleException:
                return False
        else:
            print("ERROR: could not run sqlite3.")
            print("Tests will not pass, but you can still submit your assignment.")
            print("Please download the newest version of sqlite3 into this folder")
            print("to run tests.")
            return False

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        # TODO(albert)

    def evaluate(self, code):
        if not code.strip():
            return
        code = re.sub(r'(\A|\n)\s*--.*?\n', '', code, re.M)
        if code.startswith('.'):
            try:
                self.evaluate_dot(code)
            except interpreter.ConsoleException as e:
                print('Error: {}'.format(e))
                raise
            except self.sqlite3.Error as e:
                print('Error: {}'.format(e))
                raise interpreter.ConsoleException(e, exception_type='Error')
            return
        try:
            cursor = timer.timed(self.timeout, self._conn.execute, (code,))
        except exceptions.Timeout as e:
            print('Error: evaluation exceeded {} seconds.'.format(e.timeout))
            raise interpreter.ConsoleException(e)
        except self.sqlite3.Error as e:
            print('Error: {}'.format(e))
            raise interpreter.ConsoleException(e, exception_type='Error')
        else:
            return cursor

    def _compare(self, expected, code):
        if not code.strip():
            return
        try:
            cursor = self.evaluate(code)
        except interpreter.ConsoleException as e:
            actual = str(e.exception_type)
        else:
            actual = self.format_rows(cursor)
        self._diff_output(expected, actual)

    def _diff_output(self, expected, actual):
        """Raises an interpreter.ConsoleException if expected and actual output
        don't match.

        PARAMETERS:
        expected -- str; may be multiple lines
        actual   -- str; may be multiple lines
        """
        expected = expected.split('\n')
        actual = actual.split('\n')

        if self.ordered:
            correct = expected == actual
        else:
            correct = sorted(expected) == sorted(actual)

        if not correct:
            print()
            error_msg = '# Error: expected'
            if self.ordered:
                error_msg += ' ordered output'
            print(error_msg)
            print('\n'.join('#     {}'.format(line)
                            for line in expected))
            print('# but got')
            print('\n'.join('#     {}'.format(line)
                            for line in actual))
            raise interpreter.ConsoleException

    def _import_sqlite(self):
        """Attempts to import the sqlite3 Python module.

        RETURNS:
        bool; True if able to import the sqlite3 module and the binding version
        is at least self.VERSION; False otherwise.
        """
        return False # Hotfix to prevent segfaults (See Issue 140)
        # try:
        #     self.sqlite3 = importlib.import_module(self.MODULE)
        # except ImportError:
        #     return False
        # return self.sqlite3.sqlite_version_info >= self.VERSION

    def _has_sqlite_cli(self, env):
        """Checks if the command "sqlite3" is executable with the given
        shell environment variables.

        PARAMETERS:
        env -- mapping; represents shell environment variables. Primarily, this
               allows modifications to PATH to check the current directory first.

        RETURNS:
        bool; True if "sqlite3" is executable and the version is at least
        self.VERSION; False otherwise.
        """
        # Modify PATH in subprocess to check current directory first for sqlite3
        # executable.
        try:
            version = subprocess.check_output(["sqlite3", "--version"],
                                              env=env).decode()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        version = version.split(' ')[0].split('.')
        version_info = tuple(int(num) for num in version)
        return version_info >= self.VERSION

    def _use_sqlite_cli(self, env):
        """Pipes the test case into the "sqlite3" executable.

        The method _has_sqlite_cli MUST be called before this method is called.

        PARAMETERS:
        env -- mapping; represents shell environment variables. Primarily, this
               allows modifications to PATH to check the current directory first.

        RETURNS:
        (test, expected, result), where
        test     -- str; test input that is piped into sqlite3
        expected -- str; the expected output, for display purposes
        result   -- str; the actual output form piping input into sqlite3
        """
        test = []
        expected = []
        for line in self._setup + self._code + self._teardown:
            if isinstance(line, interpreter.CodeAnswer):
                expected.extend(line.output)
            elif line.startswith(self.PS1):
                test.append(line[len(self.PS1):])
            elif line.startswith(self.PS2):
                test.append(line[len(self.PS2):])
        test = '\n'.join(test)
        process = subprocess.Popen(["sqlite3"],
                                    universal_newlines=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=env)
        result, error = process.communicate(test)
        return test, '\n'.join(expected), (error + '\n' + result).strip()

    def format_rows(self, cursor):
        """Print rows from the given sqlite cursor, formatted with pipes "|".

        RETURNS:
        str; sqlite output (formatted as strings with pipes "|" to delimit columns)
        """
        rows = []
        for row in cursor:
            row = '|'.join(map(str, row))
            rows.append(row)
            print(row)
        return '\n'.join(rows)

    def evaluate_dot(self, code):
        """Performs dot-command expansion on the given code.

        PARAMETERS:
        code -- str

        RETURNS:
        bool; True if the evaluation was successful.
        """
        if code.startswith('.read'):
            contents = self.evaluate_read(code)
            for i, segment in enumerate(re.split(r'(?:\n|\A)(\..*?)(?:\n|\Z)', contents)):
                if i % 2 == 0:
                    self._conn.executescript(segment)
                else:
                    self.evaluate_dot(segment)
        elif code.startswith('.open'):
            srcfile = self.evaluate_open(code)
            self._conn.close()
            self._conn = self.sqlite3.connect(srcfile, check_same_thread=False)
        return True

    def evaluate_read(self, line):
        """Subroutine for evaluating a .read command."""
        filename = line.replace('.read', '').strip()
        if ' ' in filename:
            raise interpreter.ConsoleException(
                Exception('Invalid usage of .read'), exception_type='Error')
        if not os.path.exists(filename):
            raise interpreter.ConsoleException(
                Exception('No such file: {}'.format(filename)),
                exception_type='Error')
        with open(filename, 'r') as f:
            contents = f.read()
        return re.sub(r'^\.read\s+.*$',
                      lambda m: self.evaluate_read(m.group(0)),
                      contents, flags=re.M)

    def evaluate_open(self, line):
        """Subroutine for evaluating a .open command."""
        filename = line.replace('.open', '').strip()
        if ' ' in filename:
            raise interpreter.ConsoleException(
                Exception('Invalid usage of .open'), exception_type='Error')
        if not os.path.exists(filename):
            raise interpreter.ConsoleException(
                Exception('No such file: {}'.format(filename)),
                exception_type='Error')
        return filename

class SqliteSuite(doctest.DoctestSuite):
    console_type = SqliteConsole
    # TODO: Ordered should be a property of cases, not entire suites.
    ordered = core.Boolean(default=False)

    def __init__(self, verbose, interactive, timeout=None, **fields):
        super().__init__(verbose, interactive, timeout, **fields)
        self.console.ordered = fields.get('ordered', False)

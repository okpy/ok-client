"""Console for interpreting sqlite."""

from client import exceptions
from client.sources.common import interpreter
from client.sources.ok_test import doctest
from client.utils import timer
import importlib

class SqliteConsole(interpreter.Console):
    PS1 = 'sqlite> '
    PS2 = '   ...> '

    MODULE = 'sqlite3'
    _output_fn = str

    def __init__(self, verbose, interactive, timeout=None):
        """Loads the Scheme module from the current working directory
        before calling the superclass constructor.
        """
        super().__init__(verbose, interactive, timeout)

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        self.sqlite3 = self.import_sqlite()
        super().load(code, setup, teardown)
        self._conn = self.sqlite3.connect(':memory:', check_same_thread=False)

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        # TODO(albert)

    def evaluate(self, code):
        if code.startswith('.'):
            if not self.evaluate_dot(code):
                raise interpreter.ConsoleException(None)
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
        try:
            cursor = self.evaluate(code)
        except interpreter.ConsoleException as e:
            actual = [e.exception_type]
        else:
            actual = self.format_rows(cursor)

        if expected != 'Error':
            expected = set(expected.split('\n'))
        if expected != actual:
            print()
            print('# Error: expected')
            print('\n'.join('#     {}'.format(line)
                            for line in expected))
            print('# but got')
            print('\n'.join('#     {}'.format(line)
                            for line in actual))
            raise interpreter.ConsoleException

    def import_sqlite(self):
        try:
            sqlite = importlib.import_module(self.MODULE)
        except ImportError:
            print('Could not import sqlite3. Make sure you have installed sqlite3')
            raise e
        # TODO(albert): check version
        return sqlite

    def format_rows(self, cursor):
        """Print rows from the given sqlite cursor, formatted with pipes "|".

        RETURNS:
        set; set of rows (formatted as strings with pipes "|" to delimit columns)
        """
        rows = set()
        for row in cursor:
            row = '|'.join(row)
            rows.add(row)
            print(row)
        return rows

    def evaluate_dot(self, code):
        """Performs dot-command expansion on the given code.

        PARAMETERS:
        code -- str

        RETURNS:
        bool; True if the evaluation was successful.
        """
        if code.startswith('.read'):
            return self._interpret_lines(self.evaluate_read(code), quiet=True)

    def evaluate_read(self, line):
        """Subroutine for evaluating a .read command."""
        filename = line.replace('.read', '').strip()
        if ' ' in filename:
            # TODO(albert): handle invalid usage
            pass
        with open(filename, 'r') as f:
            # TODO(albert): handle non-existent file
            return f.read().split('\n')

class SqliteSuite(doctest.DoctestSuite):
    console_type = SqliteConsole


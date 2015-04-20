"""Console for interpreting sqlite."""

from client import exceptions
from client.sources.common import interpreter
from client.sources.ok_test import doctest
from client.utils import timer
import importlib
import os
import re

class SqliteConsole(interpreter.Console):
    PS1 = 'sqlite> '
    PS2 = '   ...> '

    MODULE = 'sqlite3'
    VERSION = (3, 8, 3)

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.

        Loads the sqlite3 module before loading any code.
        """
        self.sqlite3 = self._import_sqlite()
        super().load(code, setup, teardown)
        self._conn = self.sqlite3.connect(':memory:', check_same_thread=False)

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

    def _import_sqlite(self):
        try:
            sqlite = importlib.import_module(self.MODULE)
        except ImportError:
            print()
            raise exceptions.ProtocolException(
                    'Could not import sqlite3. '
                    'Make sure you have installed sqlite3')
        if sqlite.sqlite_version_info < self.VERSION:
            raise exceptions.ProtocolException(
            'You are running an outdated version of sqlite3:\n'
            '    {}\n'
            'Please install sqlite version {} '
            'or newer'.format(sqlite.sqlite_version,
                              '.'.join(map(str, self.VERSION))))
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
            if not self._interpret_lines(self.evaluate_read(code), quiet=True):
                raise interpreter.ConsoleException

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
            return f.read().split('\n')

class SqliteSuite(doctest.DoctestSuite):
    console_type = SqliteConsole


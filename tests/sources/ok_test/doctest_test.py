from client import exceptions as ex
from client.sources.ok_test import doctest
import unittest

class DoctestSuiteTest(unittest.TestCase):
    TEST_NAME = 'test name'
    SUITE_NUMBER = 'suite number'

    def makeSuite(self, cases, setup='', teardown=''):
        return doctest.DoctestSuite(False, False, cases=cases, setup=setup,
                                    teardown=teardown, type='doctest')

    def testConstructor_noCases(self):
        try:
            self.makeSuite([])
        except TypeError:
            self.fail()

    def callsRun(self, test, passed, failed, locked):
        self.assertEqual({
            'passed': passed,
            'locked': locked,
            'failed': failed,
        }, test.run(self.TEST_NAME, self.SUITE_NUMBER, None))

    def testConstructor_basicCases(self):
        try:
            self.makeSuite([
                {
                    'code': """
                    >>> 4 + 5
                    9
                    """
                },
                {
                    'code': """
                    >>> 11 + 0
                    11
                    >>> 'hi'
                    'hi'
                    """
                },
            ])
        except TypeError:
            self.fail()

    def testConstructor_setup(self):
        try:
            self.makeSuite([
                {
                    'code': """
                    >>> 11 + 0
                    11
                    >>> 'hi'
                    'hi'
                    """
                },
            ], setup="""
            >>> import assign
            """)
        except TypeError:
            self.fail()

    def testConstructor_teardown(self):
        try:
            self.makeSuite([
                {
                    'code': """
                    >>> 11 + 0
                    11
                    >>> 'hi'
                    'hi'
                    """
                },
            ], teardown="""
            >>> assign = assign.teardown()
            """)
        except TypeError:
            self.fail()

    def testConstructor_improperlyFormattedTestCase(self):
        self.assertRaises(ex.SerializeException, self.makeSuite,
            [
                {
                    'foo': "Not a valid case",
                },
            ])

    def testRun_noCases(self):
        test = self.makeSuite([])
        self.callsRun(test, 0, 0, 0)

    def testRun_failedCases(self):
        test = self.makeSuite([
            {
                'code': """
                >>> 4 + 5
                9
                """
            },
            {
                'code': """
                >>> 2 + 2
                5
                """
            },
        ])
        self.callsRun(test, 1, 1, 0)

    def testRun_passedCases(self):
        test = self.makeSuite([
            {
                'code': """
                >>> 4 + 5
                9
                """
            },
            {
                'code': """
                >>> 2 + 2
                4
                """
            },
        ])
        self.callsRun(test, 2, 0, 0)

    def testRun_lockedCases(self):
        test = self.makeSuite([
            {
                'code': """
                >>> 4 + 5
                9
                # locked
                """,
                'locked': True
            },
            {
                'code': """
                >>> 2 + 2
                4
                """
            },
        ])
        self.callsRun(test, 0, 0, 2)


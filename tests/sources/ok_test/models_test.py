from client import exceptions as ex
from client.api import assignment
from client.sources.ok_test import models
from client.sources.common import core
import mock
import unittest

class OkTest(unittest.TestCase):
    ASSIGNMENT = 'assignment'
    NAME = 'ok test'
    POINTS = 10
    FILE = 'file'

    def setUp(self):
        self.assignment = mock.Mock(spec=assignment.Assignment)

        self.mockSuite1 = mock.Mock(spec=models.Suite)
        self.mockCase1 = mock.Mock()
        self.mockSuite1.return_value.cases = [
            self.mockCase1
        ]

        self.mockSuite2 = mock.Mock(spec=models.Suite)
        self.mockCase2 = mock.Mock()
        self.mockSuite2.return_value.cases = [
            self.mockCase2
        ]

        self.suite_map = {
            'mock1': self.mockSuite1,
            'mock2': self.mockSuite2,
        }

        self.interact = mock.Mock()
        self.hash_fn = mock.Mock()

    def makeTest(self, name=NAME, points=POINTS, file=FILE, **fields):
        return models.OkTest(file, self.suite_map, self.ASSIGNMENT, self.assignment, True, False,
                             name=name, points=points, **fields)

    def callsRun(self, passed, failed, locked):
        test = self.makeTest(suites=[
            {'type': 'mock1'},
            {'type': 'mock2'}
        ])

        self.assertEqual({
            'passed': passed,
            'failed': failed,
            'locked': locked,
        }, test.run(None))
        self.mockSuite1.return_value.run.assert_called_with(self.NAME, 1, None)
        self.mockSuite2.return_value.run.assert_called_with(self.NAME, 2, None)

    def callsScore(self, score):
        test = self.makeTest(suites=[
            {'type': 'mock1'},
            {'type': 'mock2'}
        ])

        self.assertEqual(score, test.score())
        self.mockSuite1.return_value.run.assert_called_with(self.NAME, 1, None)
        self.mockSuite2.return_value.run.assert_called_with(self.NAME, 2, None)

    def testConstructor_noSuites(self):
        try:
            self.makeTest(suites=[])
        except TypeError:
            self.fail()

    def testConstructor_singleSuiteTypes(self):
        try:
            self.makeTest(suites=[
                {
                    'type': 'mock1',
                    'foo': 'bar'
                },
                {
                    'type': 'mock1',
                    'foo': 'garply'
                }
            ])
        except TypeError:
            self.fail()

        self.assertEqual(2, self.mockSuite1.call_count)

    def testConstructor_multipleSuiteTypes(self):
        try:
            self.makeTest(suites=[
                {
                    'type': 'mock1',
                    'foo': 'bar'
                },
                {
                    'type': 'mock2',
                    'foo': 'garply'
                }
            ])
        except TypeError:
            self.fail()

        self.assertEqual(1, self.mockSuite1.call_count)
        self.assertEqual(1, self.mockSuite2.call_count)

    def testConstructor_unknownSuiteType(self):
        self.assertRaises(ex.SerializeException, self.makeTest, suites=[
            {
                'type': 'mock1',
                'foo': 'bar'
            },
            {
                'type': 'unknown suite',
                'foo': 'garply'
            }
        ])

    def testConstructor_improperlyFormattedSuite(self):
        self.assertRaises(ex.SerializeException, self.makeTest, suites=[
            {
                'foo': 'bar'
            },
        ])

    def testRun_noSuites(self):
        test = self.makeTest(suites=[])
        self.assertEqual({
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }, test.run(None))

    def testRun_correctResults(self):
        self.mockSuite1.return_value.run.return_value = {
            'passed': 2,
            'failed': 1,
            'locked': 0,
        }
        self.mockSuite2.return_value.run.return_value = {
            'passed': 0,
            'failed': 2,
            'locked': 1,
        }
        self.callsRun(2, 3, 1)

    def testScore_noSuites(self):
        test = self.makeTest(suites=[])
        self.assertEqual(0, test.score())

    def testScore_allPassed(self):
        self.mockSuite1.return_value.run.return_value = {
            'passed': 2,
            'failed': 0,
            'locked': 0,
        }
        self.mockSuite2.return_value.run.return_value = {
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }
        self.callsScore(self.POINTS)

    def testScore_partialPass(self):
        self.mockSuite1.return_value.run.return_value = {
            'passed': 2,
            'failed': 1,
            'locked': 0,
        }
        self.mockSuite2.return_value.run.return_value = {
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }
        self.callsScore(self.POINTS * (1/2))

    def testScore_locked(self):
        self.mockSuite1.return_value.run.return_value = {
            'passed': 2,
            'failed': 1,
            'locked': 1,
        }
        self.mockSuite2.return_value.run.return_value = {
            'passed': 1,
            'failed': 0,
            'locked': 3,
        }
        self.callsScore(0)

    def testUnlock_noSuites(self):
        test = self.makeTest(suites=[])

        try:
            test.unlock(self.interact)
        except (KeyboardInterrupt, EOFError):
            self.fail()

    def testUnlock_multipleSuites(self):
        self.mockCase1.locked = True
        self.mockCase2.locked = True
        test = self.makeTest(suites=[
            {'type': 'mock1'},
            {'type': 'mock2'},
        ])

        try:
            test.unlock(self.interact)
        except (KeyboardInterrupt, EOFError):
            self.fail()
        self.assertEqual(1, self.mockCase1.unlock.call_count)
        self.assertEqual(1, self.mockCase2.unlock.call_count)

    def testUnlock_multipleSuites_caseAlreadyUnlocked(self):
        self.mockCase1.locked = False
        self.mockCase2.locked = True
        test = self.makeTest(suites=[
            {'type': 'mock1'},
            {'type': 'mock2'},
        ])

        try:
            test.unlock(self.interact)
        except (KeyboardInterrupt, EOFError):
            self.fail()
        self.assertEqual(0, self.mockCase1.unlock.call_count)
        self.assertEqual(1, self.mockCase2.unlock.call_count)

    def testLock_noSuites(self):
        test = self.makeTest(suites=[])

        try:
            test.lock(self.hash_fn)
        except Exception as e:
            self.fail(e)

    def testLock_multipleSuites(self):
        self.mockCase1.locked = core.NoValue
        self.mockCase1.hidden = False
        self.mockCase2.locked = True
        self.mockCase2.hidden = False
        test = self.makeTest(suites=[
            {'type': 'mock1'},
            {'type': 'mock2'},
        ])

        try:
            test.lock(self.hash_fn)
        except Exception as e:
            self.fail(e)
        self.assertEqual(1, self.mockCase1.lock.call_count)
        self.assertEqual(0, self.mockCase2.lock.call_count)

    def testLock_emptySuite(self):
        self.mockSuite1.return_value.cases = []
        test = self.makeTest(suites=[
            {'type': 'mock1'},
        ])

        try:
            test.lock(self.hash_fn)
        except Exception as e:
            self.fail(e)
        self.assertEqual(0, len(test.suites))

    def testLock_allCasesHidden(self):
        self.mockCase1.locked = core.NoValue
        self.mockCase1.hidden = True
        test = self.makeTest(suites=[
            {'type': 'mock1'},
        ])

        try:
            test.lock(self.hash_fn)
        except Exception as e:
            self.fail(e)
        self.assertEqual(0, len(self.mockSuite1.return_value.cases))
        self.assertEqual(0, len(test.suites))

    def testLock_someCasesHidden(self):
        self.mockCase1.locked = core.NoValue
        self.mockCase1.hidden = True
        self.mockCase2.locked = core.NoValue
        self.mockCase2.hidden = False
        self.mockSuite1.return_value.cases = [
            self.mockCase1,
            self.mockCase2
        ]
        test = self.makeTest(suites=[
            {'type': 'mock1'},
        ])

        try:
            test.lock(self.hash_fn)
        except Exception as e:
            self.fail(e)
        self.assertEqual(1, len(self.mockSuite1.return_value.cases))
        self.assertEqual(1, len(test.suites))

    def testDump(self):
        # TODO(albert)
        pass

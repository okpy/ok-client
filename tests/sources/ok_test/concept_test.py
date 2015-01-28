from client import exceptions as ex
from client.sources.ok_test import concept
import unittest

class ConceptSuiteTest(unittest.TestCase):
    TEST_NAME = 'A'
    SUITE_NUMBER = 0

    def makeTest(self, cases):
        return concept.ConceptSuite(False, False, type='concept', cases=cases)

    def testConstructor_noCases(self):
        try:
            self.makeTest([])
        except TypeError:
            self.fail()

    def testConstructor_validTestCase(self):
        try:
            self.makeTest([
                {
                    'question': 'Question 1',
                    'answer': 'Answer',
                },
                {
                    'question': 'Question 1',
                    'answer': 'Answer',
                },
            ])
        except TypeError:
            self.fail()

    def testConstructor_missingQuestion(self):
        self.assertRaises(ex.SerializeException, self.makeTest, [
                {
                    'answer': 'Answer',
                },
                {
                    'question': 'Question 1',
                    'answer': 'Answer',
                },
            ])

    def testConstructor_missingAnswer(self):
        self.assertRaises(ex.SerializeException, self.makeTest, [
                {
                    'question': 'Question 1',
                    'answer': 'Answer',
                },
                {
                    'question': 'Question 1',
                },
            ])

    def testRun_noCases(self):
        test = self.makeTest([])
        self.assertEqual({
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }, test.run(self.TEST_NAME, self.SUITE_NUMBER))

    def testRun_lockedCases(self):
        test = self.makeTest([
            {
                'question': 'Question 1',
                'answer': 'Answer',
                'locked': True,
            },
            {
                'question': 'Question 1',
                'answer': 'Answer',
            },
        ])
        self.assertEqual({
            'passed': 0,
            'failed': 0,
            'locked': 2,    # Can't continue if preceding test is locked.
        }, test.run(self.TEST_NAME, self.SUITE_NUMBER))

    def testRun_noLockedCases(self):
        test = self.makeTest([
            {
                'question': 'Question 1',
                'answer': 'Answer',
            },
            {
                'question': 'Question 1',
                'answer': 'Answer',
            },
        ])
        self.assertEqual({
            'passed': 2,
            'failed': 0,
            'locked': 0,
        }, test.run(self.TEST_NAME, self.SUITE_NUMBER))


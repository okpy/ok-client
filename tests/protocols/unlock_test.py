"""Tests the UnlockProtocol."""

from client.protocols import unlock
from client.sources.common import models
import mock
import unittest

class UnlockProtocolTest(unittest.TestCase):
    TEST = 'Test 1'

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.export = False
        self.assignment = mock.Mock()
        self.proto = unlock.protocol(self.cmd_args, self.assignment)

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        messages = {}
        try:
            self.proto.run(messages)
        except (KeyboardInterrupt, EOFError):
            self.fail('UnlockProtocol.run should abort gracefully')

        self.assertIn('unlock', messages)
        self.assertIsInstance(messages['unlock'], dict)

    def testOnInteract_withTests(self):
        self.assignment.specified_tests = [mock.Mock(spec=models.Test)]
        messages = {}
        try:
            self.proto.run(messages)
        except (KeyboardInterrupt, EOFError):
            self.fail('UnlockProtocol.run should abort gracefully')

        self.assertIn('unlock', messages)
        self.assertIsInstance(messages['unlock'], dict)

class InteractTest(unittest.TestCase):
    TEST = 'Test 0'
    QUESTION = 'Question 0'
    SHORT_ANSWER = ['42']
    LONG_ANSWER = ['3.1', '41', '59']
    INCORRECT_ANSWERS = ['a', 'b', 'c']
    CHOICES = SHORT_ANSWER + INCORRECT_ANSWERS

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.Mock()
        self.proto = unlock.protocol(self.cmd_args, self.assignment)
        self.proto.current_test = self.TEST

        self.proto._verify = self.mockVerify
        self.proto._input = self.mockInput

        self.input_choices = []
        self.choice_number = 0

    def mockInput(self, prompt):
        self.choice_number += 1
        return self.input_choices[self.choice_number - 1]

    def mockVerify(self, guess, locked):
        return guess == locked

    def checkNumberOfAttempts(self, number_of_attempts):
        self.assertIn(self.TEST, self.proto.analytics)
        self.assertEqual(number_of_attempts, len(self.proto.analytics[self.TEST]))

    def checkDictField(self, dictionary, field, expected_value):
        self.assertIn(field, dictionary)
        self.assertEqual(expected_value, dictionary[field])

    def testInputExitPattern(self):
        self.input_choices = [self.proto.EXIT_INPUTS[0]]
        self.assertRaises((KeyboardInterrupt, EOFError), self.proto.interact,
                          self.QUESTION, self.SHORT_ANSWER)

    def testRaiseError(self):
        self.proto._input = mock.Mock(side_effect=KeyboardInterrupt)
        self.assertRaises((KeyboardInterrupt, EOFError), self.proto.interact,
                          self.QUESTION, self.SHORT_ANSWER)

    def testSingleLine_immediatelyCorrect(self):
        self.input_choices = list(self.SHORT_ANSWER)
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.QUESTION, self.SHORT_ANSWER))

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[self.TEST][0]

        self.checkDictField(attempt, 'question', self.QUESTION)
        self.checkDictField(attempt, 'answer', self.SHORT_ANSWER)
        self.checkDictField(attempt, 'correct', True)

    def testSingleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.INCORRECT_ANSWERS + self.SHORT_ANSWER
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.QUESTION, self.SHORT_ANSWER))

        self.checkNumberOfAttempts(1 + len(self.INCORRECT_ANSWERS))
        for attempt_number, attempt in enumerate(self.proto.analytics[self.TEST]):
            self.checkDictField(attempt, 'question', self.QUESTION)
            if attempt_number < len(self.INCORRECT_ANSWERS):
                self.checkDictField(attempt, 'answer', [self.INCORRECT_ANSWERS[attempt_number]])
                self.checkDictField(attempt, 'correct', False)
            else:
                self.checkDictField(attempt, 'answer', self.SHORT_ANSWER)
                self.checkDictField(attempt, 'correct', True)

    def testMultipleLine_immediatelyCorrect(self):
        self.input_choices = list(self.LONG_ANSWER)
        self.assertEqual(self.LONG_ANSWER,
                         self.proto.interact(self.QUESTION, self.LONG_ANSWER))

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[self.TEST][0]

        self.checkDictField(attempt, 'question', self.QUESTION)
        self.checkDictField(attempt, 'answer', self.LONG_ANSWER)
        self.checkDictField(attempt, 'correct', True)

    def testMultipleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.LONG_ANSWER[:1] + self.INCORRECT_ANSWERS + \
                             self.LONG_ANSWER
        self.assertEqual(self.LONG_ANSWER,
                         self.proto.interact(self.QUESTION, self.LONG_ANSWER))

        print(self.proto.analytics[self.TEST])
        self.checkNumberOfAttempts(1 + len(self.INCORRECT_ANSWERS))
        for attempt_number, attempt in enumerate(self.proto.analytics[self.TEST]):
            self.checkDictField(attempt, 'question', self.QUESTION)

            if attempt_number == 0:
                self.checkDictField(attempt, 'answer', [self.LONG_ANSWER[0], self.INCORRECT_ANSWERS[0]])
                self.checkDictField(attempt, 'correct', False)
            elif attempt_number < len(self.INCORRECT_ANSWERS):
                self.checkDictField(attempt, 'answer', [self.INCORRECT_ANSWERS[attempt_number]])
                self.checkDictField(attempt, 'correct', False)
            else:
                self.checkDictField(attempt, 'answer', self.LONG_ANSWER)
                self.checkDictField(attempt, 'correct', True)

    def testMultipleChoice_immediatelyCorrect(self):
        self.input_choices = ['0']
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.QUESTION, self.SHORT_ANSWER, self.CHOICES,
                                             randomize=False))

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[self.TEST][0]

        self.checkDictField(attempt, 'question', self.QUESTION)
        self.checkDictField(attempt, 'answer', self.SHORT_ANSWER)
        self.checkDictField(attempt, 'correct', True)

    def testMultipleChoice_multipleFailsBeforeSuccess(self):
        self.input_choices = ['1', '2', '0']
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.QUESTION, self.SHORT_ANSWER,
                                             self.CHOICES, randomize=False))

        self.checkNumberOfAttempts(len(self.input_choices))
        for attempt_number, attempt in enumerate(self.proto.analytics[self.TEST]):
            self.checkDictField(attempt, 'question', self.QUESTION)
            choice = self.input_choices[attempt_number]

            if attempt_number < len(self.input_choices) - 1:
                self.checkDictField(attempt, 'answer', [self.CHOICES[int(choice)]])
                self.checkDictField(attempt, 'correct', False)
            else:
                self.checkDictField(attempt, 'answer', self.SHORT_ANSWER)
                self.checkDictField(attempt, 'correct', True)

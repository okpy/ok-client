"""Tests the UnlockProtocol."""

from client.protocols import unlock
from client.sources.common import models
import mock
import unittest

class UnlockProtocolTest(unittest.TestCase):
    TEST = 'Test 1'

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.Mock()
        self.assignment.is_test = True
        self.proto = unlock.protocol(self.cmd_args, self.assignment)

    def testOnInteract_noTests(self):
        self.assignment.specified_tests = []
        messages = {}
        try:
            self.proto.run(messages)
        except (KeyboardInterrupt, EOFError):
            self.fail('UnlockProtocol.run should abort gracefully')

        self.assertIn('unlock', messages)
        self.assertIsInstance(messages['unlock'], list)

    def testOnInteract_withTests(self):
        self.assignment.specified_tests = [mock.Mock(spec=models.Test)]
        messages = {}
        try:
            self.proto.run(messages)
        except (KeyboardInterrupt, EOFError):
            self.fail('UnlockProtocol.run should abort gracefully')

        self.assertIn('unlock', messages)
        self.assertIsInstance(messages['unlock'], list)

class InteractTest(unittest.TestCase):
    TEST = 'Test 0'
    CASE_ID = TEST + ' > Suite 1 > Case 1'
    UNIQUE_ID = 'string containing\nunique id'
    PROMPT = 'question prompt text'
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
        self.assertEqual(number_of_attempts, len(self.proto.analytics))

    def checkDictField(self, dictionary, field, expected_value):
        self.assertIn(field, dictionary)
        self.assertEqual(expected_value, dictionary[field])

    def callsInteractError(self, expected_error, answer, choices=None, unique_id=None,
            case_id=None, prompt=None, randomize=True):
        if not unique_id:
            unique_id = self.UNIQUE_ID
        if not case_id:
            case_id = self.CASE_ID
        if not prompt:
            prompt = self.PROMPT
        if not choices:
            choices = None

        self.assertRaises(expected_error, self.proto.interact,
                          unique_id, case_id, prompt, answer)

    def callsInteract(self, expected, answer, choices=None, unique_id=None,
                case_id=None, prompt=None, randomize=True):
        if not unique_id:
            unique_id = self.UNIQUE_ID
        if not case_id:
            case_id = self.CASE_ID
        if not prompt:
            prompt = self.PROMPT
        if not choices:
            choices = None

        self.assertEqual(expected, self.proto.interact(unique_id, case_id,
                         prompt, answer, choices=choices, randomize=randomize))

    def validateRecord(self, record, answer, correct, prompt=None,
                       unique_id=None, case_id=None):
        if not unique_id:
            unique_id = self.UNIQUE_ID
        if not case_id:
            case_id = self.CASE_ID
        if not prompt:
            prompt = self.PROMPT

        self.checkDictField(record, 'prompt', prompt)
        self.checkDictField(record, 'answer', answer)
        self.checkDictField(record, 'correct', correct)
        self.checkDictField(record, 'id', unique_id)
        self.checkDictField(record, 'case_id', case_id)

        self.assertIn('question timestamp', record)
        self.assertIsInstance(record['question timestamp'], int)

        self.assertIn('answer timestamp', record)
        self.assertIsInstance(record['answer timestamp'], int)

    def testInputExitPattern(self):
        self.input_choices = [self.proto.EXIT_INPUTS[0]]
        self.callsInteractError((KeyboardInterrupt, EOFError), self.SHORT_ANSWER)

    def testRaiseError(self):
        self.proto._input = mock.Mock(side_effect=KeyboardInterrupt)
        self.callsInteractError((KeyboardInterrupt, EOFError), self.SHORT_ANSWER)

    def testSingleLine_immediatelyCorrect(self):
        self.input_choices = list(self.SHORT_ANSWER)
        self.callsInteract(self.SHORT_ANSWER, self.SHORT_ANSWER)

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[0]

        self.validateRecord(attempt, answer=self.SHORT_ANSWER, correct=True)

    def testSingleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.INCORRECT_ANSWERS + self.SHORT_ANSWER
        self.callsInteract(self.SHORT_ANSWER, self.SHORT_ANSWER)

        self.checkNumberOfAttempts(1 + len(self.INCORRECT_ANSWERS))
        for attempt_number, attempt in enumerate(self.proto.analytics):
            if attempt_number < len(self.INCORRECT_ANSWERS):
                self.validateRecord(attempt,
                                    answer=[self.INCORRECT_ANSWERS[attempt_number]],
                                    correct=False)
            else:
                self.validateRecord(attempt,
                                    answer=self.SHORT_ANSWER,
                                    correct=True)

    def testMultipleLine_immediatelyCorrect(self):
        self.input_choices = list(self.LONG_ANSWER)
        self.callsInteract(self.LONG_ANSWER, self.LONG_ANSWER)

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[0]

        self.validateRecord(attempt, answer=self.LONG_ANSWER, correct=True)

    def testMultipleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.LONG_ANSWER[:1] + self.INCORRECT_ANSWERS + \
                             self.LONG_ANSWER
        self.callsInteract(self.LONG_ANSWER, self.LONG_ANSWER)

        self.checkNumberOfAttempts(1 + len(self.INCORRECT_ANSWERS))
        for attempt_number, attempt in enumerate(self.proto.analytics):
            if attempt_number == 0:
                self.validateRecord(attempt,
                    answer=[self.LONG_ANSWER[0], self.INCORRECT_ANSWERS[0]],
                    correct=False)
            elif attempt_number < len(self.INCORRECT_ANSWERS):
                self.validateRecord(attempt,
                    answer=[self.INCORRECT_ANSWERS[attempt_number]],
                    correct=False)
            else:
                self.validateRecord(attempt, answer=self.LONG_ANSWER, correct=True)

    def testMultipleChoice_immediatelyCorrect(self):
        self.input_choices = ['0']
        self.callsInteract(self.SHORT_ANSWER, self.SHORT_ANSWER,
                           choices=self.CHOICES, randomize=False)

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[0]

        self.validateRecord(attempt, answer=self.SHORT_ANSWER, correct=True)

    def testMultipleChoice_multipleFailsBeforeSuccess(self):
        self.input_choices = ['1', '2', '0']
        self.callsInteract(self.SHORT_ANSWER, self.SHORT_ANSWER,
                           choices=self.CHOICES, randomize=False)

        self.checkNumberOfAttempts(len(self.input_choices))
        for attempt_number, attempt in enumerate(self.proto.analytics):
            choice = self.input_choices[attempt_number]
            if attempt_number < len(self.input_choices) - 1:
                self.validateRecord(attempt, answer=[self.CHOICES[int(choice)]],
                        correct=False)
            else:
                self.validateRecord(attempt, answer=self.SHORT_ANSWER, correct=True)

    EVAL_ANSWER = ['[1, 2, 3, 4]']
    CORRECT_EVAL = ['[1,2,3,4]']
    INCORRECT_EVALS = ['[4,3,2,1]', '{1,2,3,4}', '[1,2,3,8/2]']

    def testEvaluatedInput_immediatelyCorrect(self):
        self.input_choices = list(self.CORRECT_EVAL)
        self.callsInteract(self.EVAL_ANSWER, self.EVAL_ANSWER)

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[0]

        self.validateRecord(attempt, answer=self.EVAL_ANSWER, correct=True)

    def testEvaluatedInput_multipleFailsBeforeSuccess(self):
        self.input_choices = self.INCORRECT_EVALS + self.CORRECT_EVAL
        self.callsInteract(self.EVAL_ANSWER, self.EVAL_ANSWER)

        self.checkNumberOfAttempts(1 + len(self.INCORRECT_EVALS))
        for attempt_number, attempt in enumerate(self.proto.analytics):
            if attempt_number < len(self.INCORRECT_EVALS):
                self.validateRecord(attempt, answer=[self.INCORRECT_EVALS[attempt_number]],
                                    correct=False)
            else:
                self.validateRecord(attempt, answer=self.EVAL_ANSWER, correct=True)

    def testSpecialInputs_correct(self):
        # list of (answer, student_input)
        inputs = [
            ('Error', 'error'),
            ('Nothing', 'noThing'),
            ('Infinite Loop', 'infinite Loop'),
            ('Foo', 'Foo'),
            ('error', 'error'),
        ]
        for answer, student_input in inputs:
            self.choice_number = 0
            self.proto.analytics = []
            self.input_choices = [student_input]
            self.callsInteract([answer], [answer])
            self.checkNumberOfAttempts(1)
            self.validateRecord(self.proto.analytics[0], answer=[answer], correct=True)

    def testSpecialInputs_incorrect(self):
        # list of (answer, student_input)
        inputs = [
            ('Foo', 'foo'),  # not special
            ('error', 'Error'),  # must be lowercase
        ]
        for answer, student_input in inputs:
            self.choice_number = 0
            self.proto.analytics = []
            self.input_choices = [student_input, answer]
            self.callsInteract([answer], [answer])
            self.checkNumberOfAttempts(2)
            self.validateRecord(self.proto.analytics[0], answer=[student_input], correct=False)
            self.validateRecord(self.proto.analytics[1], answer=[answer], correct=True)

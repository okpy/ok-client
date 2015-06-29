"""Tests the UnlockProtocol."""

from client.protocols import unlock
from client.sources.common import models
import mock
import unittest

class UnlockProtocolTest(unittest.TestCase):
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
    SHORT_ANSWER = ['42']
    LONG_ANSWER = ['3.1', '41', '59']
    INCORRECT_ANSWERS = ['a', 'b', 'c']
    CORRECT_EVAL = ['2 + (2**3)*5']
    INCORRECT_EVALS = ['1 + 43', '2**3', 'raise Exception("test")']
    CHOICES = SHORT_ANSWER + INCORRECT_ANSWERS

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.Mock()
        self.proto = unlock.protocol(self.cmd_args, self.assignment)
        self.proto._verify = self.mockVerify
        self.proto._input = self.mockInput

        self.input_choices = []

    def mockInput(self, prompt):
        return self.input_choices.pop(0)

    def mockVerify(self, guess, locked):
        return guess == locked

    def testInputExitPattern(self):
        self.input_choices = [self.proto.EXIT_INPUTS[0]]
        self.assertRaises((KeyboardInterrupt, EOFError), self.proto.interact,
                          self.SHORT_ANSWER)

    def testRaiseError(self):
        self.proto._input = mock.Mock(side_effect=KeyboardInterrupt)
        self.assertRaises((KeyboardInterrupt, EOFError), self.proto.interact,
                          self.SHORT_ANSWER)

    def testSingleLine_immediatelyCorrect(self):
        self.input_choices = list(self.SHORT_ANSWER)
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.SHORT_ANSWER))

    def testSingleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.INCORRECT_ANSWERS + self.SHORT_ANSWER
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.SHORT_ANSWER))

    def testMultipleLine_immediatelyCorrect(self):
        self.input_choices = list(self.LONG_ANSWER)
        self.assertEqual(self.LONG_ANSWER,
                         self.proto.interact(self.LONG_ANSWER))

    def testMultipleLine_multipleFailsBeforeSuccess(self):
        self.input_choices = self.LONG_ANSWER[0:] + self.INCORRECT_ANSWERS + \
                             self.LONG_ANSWER
        self.assertEqual(self.LONG_ANSWER,
                         self.proto.interact(self.LONG_ANSWER))

    def testMultipleChoice_immediatelyCorrect(self):
        self.input_choices = ['0']
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.SHORT_ANSWER, self.CHOICES,
                                             randomize=False))

    def testMultipleChoice_multipleFailsBeforeSuccess(self):
        self.input_choices = ['1', '2', '0']
        self.assertEqual(self.SHORT_ANSWER,
                         self.proto.interact(self.SHORT_ANSWER, self.CHOICES,
                                             randomize=False))
                                             
    def testEvaluatedInput_immediatelyCorrect(self):
        self.input_choices = list(self.CORRECT_EVAL)
        self.assertEqual(self.SHORT_ANSWER, 
                         self.proto.interact(self.SHORT_ANSWER))
                         
    def testEvaluatedInput_multipleFailsBeforeSuccess(self):
        self.input_choices = self.INCORRECT_EVALS + self.CORRECT_EVAL
        self.assertEqual(self.SHORT_ANSWER, 
                         self.proto.interact(self.SHORT_ANSWER))


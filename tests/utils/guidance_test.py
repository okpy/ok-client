from client.protocols import unlock
from client.utils import guidance
from client.sources.common import models
from client.utils import assess_id_util
import mock
import unittest
import os


class GuidanceProtocolTest(unittest.TestCase):
    GUIDANCE_DIRECTORY = "demo/guidance_test/"
    MISUCOUNT_FILE = "tests/misUcount.json"
    TEST = "Test"
    CASE_ID = TEST + ' > Suite 1 > Case 1 > Prompt 1'
    # TODO @ok-guidance: Update test input and expected output for new guidance format.
    UNIQUE_ID = "\nTest\n\n>>> 1 + 1 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n>>> 2 + 2 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n"
    PROMPT = ">>> 1 + 1 # OK will accept 'black' as right answer"

    ANSWER = ["'black'"]
    ANSWERMSG = [["-- OK! --"]]
    INPUT0 = [['1','3'],['0','4'],['1','-2']]
    TG0MSG = [[[],[]],[[],[]],[[],[]]]

    INPUT1 = [['1','3'],['1','1'],['1','4'],['1','5']]
    TG1MSG = [[[],"KI: Try using your fingers to add"],[[],[],[]],[[],[],[]],[[],[],[]]]

    INPUT2 = [['1','3'],['0','4'],['1','0','100'],['4','-2','0']]
    TG2MSG = [[[],"Reteach: Addition"],[[],"Reteach: Addition"],[[],[],"Reteach: Addition"],[[],[],"Reteach: AdditionReteach: Negation"]]

    ALLINPUTS = [INPUT0,INPUT1,INPUT2]
    ALLMSG = [TG0MSG,TG1MSG,TG2MSG]

    @classmethod
    def remove_misucount_file(cls):
        try:
            os.remove(cls.GUIDANCE_DIRECTORY + cls.MISUCOUNT_FILE)
        except:
            pass

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.Mock(endpoint="cal/cs61a/sp16/test")
        self.proto = unlock.protocol(self.cmd_args, self.assignment)
        self.proto.guidance_util = guidance.Guidance(self.GUIDANCE_DIRECTORY,
                                                     self.assignment)
        self.proto.guidance_util.set_tg = self.mockSet_TG
        self.proto.current_test = self.TEST
        self.proto._verify = self.mockVerify
        self.proto._input = self.mockInput

        self.input_choices = []
        self.choice_number = 0

    def mockSet_TG(self):
        return 1

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
                         prompt, answer, normalizer=lambda x: x, choices=choices, randomize=randomize))

    def validateRecord(self, record, answer, correct, prompt=None,
                       unique_id=None, case_id=None, guidance_msg=None):
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
        self.checkDictField(record, 'printed msg',guidance_msg)

        self.assertIn('question timestamp', record)
        self.assertIsInstance(record['question timestamp'], int)

        self.assertIn('answer timestamp', record)
        self.assertIsInstance(record['answer timestamp'], int)

    def testSingleLine_immediatelyCorrect(self):
        self.input_choices = self.ANSWER
        self.callsInteract(self.ANSWER, self.ANSWER)

        self.checkNumberOfAttempts(1)
        attempt = self.proto.analytics[0]

        self.validateRecord(attempt, answer=self.ANSWER, correct=True,guidance_msg = self.ANSWERMSG[0])

    def testAllTreatmentGroups(self):
        for tg in range(0,3):
            cur_input = self.ALLINPUTS[tg]
            cur_expect_msg = self.ALLMSG[tg]
            GuidanceProtocolTest.remove_misucount_file()
            for x in range(0,len(cur_input)):
                self.setUp()
                self.proto.guidance_util.tg_id = tg
                self.input_choices = cur_input[x] + self.ANSWER
                self.callsInteract(self.ANSWER, self.ANSWER)

                self.checkNumberOfAttempts(len(self.input_choices))
                attempt = self.proto.analytics[0]
                # for attempt_number, attempt in enumerate(self.proto.analytics):
                #     if attempt_number < len(cur_input[x]):
                #         self.validateRecord(attempt,
                #                             answer=[cur_input[x][attempt_number]],
                #                             correct=False,guidance_msg=cur_expect_msg[x][attempt_number])
                #     else:
                #         self.validateRecord(attempt,
                #                             answer=self.ANSWER,
                #                             correct=True,guidance_msg=self.ANSWERMSG[0])
                GuidanceProtocolTest.remove_misucount_file()

from client.protocols import unlock
from client.protocols import guidance
from client.sources.common import models
import mock
import unittest
import os


class GuidanceProtocolTest(unittest.TestCase):
	GUIDANCE_DIRECTORY = "demo/guidance_test/"
	MISUCOUNT_FILE = "tests/misUcount.json"
	TEST = "Test"
	CASE_ID = TEST + ' > Suite 1 > Case 1 > Prompt 1'
	UNIQUE_ID = "\nTest\n\n>>> 1 + 1 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n>>> 2 + 2 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n"
	PROMPT = ">>> 1 + 1 # OK will accept 'black' as right answer"
	
	ANSWER = ["'black'"]
	ANSWERMSG = ["-- OK! --"]
	INPUT0 = [['1','3'],['0','4'],['1','-2']]
	TG0MSG = [["",""],["",""],["",""]]

	INPUT1 = [['1','3'],['1','1'],['1','4'],['1','5']]
	TG1MSG = [["","KI: Try using your fingers to add"],["","",""],["","",""],["","",""]]

	INPUT2 = [['1','3'],['0','4'],['1','0','100'],['4','-2','0']]
	TG2MSG = [["","Reteach: Addition"],["","Reteach: Addition"],["","","Reteach: Addition"],["","","Reteach: AdditionReteach: Negation"]]
	def setUp(self):
		self.cmd_args = mock.Mock()
		self.assignment = mock.Mock()
		self.proto = unlock.protocol(self.cmd_args, self.assignment)
		self.proto.current_test = self.TEST
		self.proto._verify = self.mockVerify
		self.proto._input = self.mockInput
		self.proto.printed_msg = ""

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
		self.checkDictField(record,'printed msg',guidance_msg)

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

	def testTreatmentGroup0(self):
		for x in range(0,len(self.INPUT0)):
			self.setUp()
			self.proto.guidance_proto = guidance.protocol(self.GUIDANCE_DIRECTORY,debug = 0)

			try:
				os.remove(self.GUIDANCE_DIRECTORY + self.MISUCOUNT_FILE)
			except:
				pass
			self.input_choices = self.INPUT0[x] + self.ANSWER
			self.callsInteract(self.ANSWER, self.ANSWER)

			self.checkNumberOfAttempts(len(self.input_choices))
			attempt = self.proto.analytics[0]
			for attempt_number, attempt in enumerate(self.proto.analytics):
				if attempt_number < len(self.INPUT0[x]):
					self.validateRecord(attempt,
										answer=[self.INPUT0[x][attempt_number]],
										correct=False,guidance_msg=self.TG0MSG[x][attempt_number])
				else:
					self.validateRecord(attempt,
										answer=self.ANSWER,
										correct=True,guidance_msg=self.ANSWERMSG[0])
	def testTreatmentGroup1(self):
		for x in range(0,len(self.INPUT1)):
			self.setUp()
			self.proto.guidance_proto = guidance.protocol(self.GUIDANCE_DIRECTORY,debug =1)

			try:
				os.remove(self.GUIDANCE_DIRECTORY + self.MISUCOUNT_FILE)
			except:
				pass
			self.input_choices = self.INPUT1[x] + self.ANSWER
			self.callsInteract(self.ANSWER, self.ANSWER)

			self.checkNumberOfAttempts(len(self.input_choices))
			attempt = self.proto.analytics[0]
			for attempt_number, attempt in enumerate(self.proto.analytics):
				if attempt_number < len(self.INPUT1[x]):
					self.validateRecord(attempt,
										answer=[self.INPUT1[x][attempt_number]],
										correct=False,guidance_msg=self.TG1MSG[x][attempt_number])
				else:
					self.validateRecord(attempt,
										answer=self.ANSWER,
										correct=True,guidance_msg=self.ANSWERMSG[0])
	def testTreatmentGroup2(self):
		for x in range(0,len(self.INPUT2)):
			self.setUp()
			self.proto.guidance_proto = guidance.protocol(self.GUIDANCE_DIRECTORY,debug =2)
			try:
				os.remove(self.GUIDANCE_DIRECTORY + self.MISUCOUNT_FILE)
			except:
				pass
			self.input_choices = self.INPUT2[x] + self.ANSWER
			self.callsInteract(self.ANSWER, self.ANSWER)

			self.checkNumberOfAttempts(len(self.input_choices))
			attempt = self.proto.analytics[0]
			for attempt_number, attempt in enumerate(self.proto.analytics):
				if attempt_number < len(self.INPUT2[x]):
					self.validateRecord(attempt,
										answer=[self.INPUT2[x][attempt_number]],
										correct=False,guidance_msg=self.TG2MSG[x][attempt_number])
				else:
					self.validateRecord(attempt,
										answer=self.ANSWER,
										correct=True,guidance_msg=self.ANSWERMSG[0])
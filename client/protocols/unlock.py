"""Implements the UnlockProtocol, which unlocks all specified tests
associated with an assignment.

The UnlockTestCase interface can be implemented by TestCases that are
compatible with the UnlockProtocol.
"""

from client.protocols.common import models
from client.utils import format
from client.utils import locking, auth
from datetime import datetime
import logging
import random
import string
from urllib.request import urlopen
import json
import os
import sys

log = logging.getLogger(__name__)
countDir = "countDir"
TGSERVER = "http://127.0.0.1:5000/"

try:
    with open("tests/.ok_guidance","r") as f:
        json_dict_file = json.load(f)
        f.close()
    error = False
except:
    error = True

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

class UnlockProtocol(models.Protocol):
    """Unlocking protocol that wraps that mechanism."""

    PROMPT = '? '       # Prompt that is used for user input.
    EXIT_INPUTS = (     # Valid user inputs for aborting the session.
        'exit()',
        'quit()',
    )

    def __init__(self, cmd_args, assignment):
        super().__init__(cmd_args, assignment)
        self.hash_key = assignment.name
        self.analytics = []

    def run(self, messages):
        """Responsible for unlocking each test.

        The unlocking process can be aborted by raising a KeyboardInterrupt or
        an EOFError.

        RETURNS:
        dict; mapping of test name (str) -> JSON-serializable object. It is up
        to each test to determine what information is significant for analytics.
        """
        if self.args.export or not self.args.unlock:
            return
        access_token = auth.authenticate(False)
        format.print_line('~')
        print('Unlocking tests')
        print()

        print('At each "{}", type what you would expect the output to be.'.format(
              self.PROMPT))
        print('Type {} to quit'.format(self.EXIT_INPUTS[0]))
        print()

        for test in self.assignment.specified_tests:
            log.info('Unlocking test {}'.format(test.name))
            self.current_test = test.name

            try:
                test.unlock(self.interact)
            except (KeyboardInterrupt, EOFError):
                try:
                    # TODO(albert): When you use Ctrl+C in Windows, it
                    # throws two exceptions, so you need to catch both
                    # of them. Find a cleaner fix for this.
                    print()
                    print('-- Exiting unlocker --')
                except (KeyboardInterrupt, EOFError):
                    pass
                print()
                break
        messages['unlock'] = self.analytics

    def interact(self, unique_id, case_id, question_prompt, answer, choices=None, randomize=True):
        """Reads student input for unlocking tests until the student
        answers correctly.

        PARAMETERS:
        unique_id       -- str; the ID that is recorded with this unlocking
                           attempt.
        case_id         -- str; the ID that is recorded with this unlocking
                           attempt.
        question_prompt -- str; the question prompt
        answer          -- list; a list of locked lines in a test case answer.
        choices         -- list or None; a list of choices. If None or an
                           empty list, signifies the question is not multiple
                           choice.
        randomize       -- bool; if True, randomizes the choices on first
                           invocation.

        DESCRIPTION:
        Continually prompt the student for an answer to an unlocking
        question until one of the folliwng happens:

            1. The student supplies the correct answer, in which case
               the supplied answer is returned
            2. The student aborts abnormally (either by typing 'exit()'
               or using Ctrl-C/D. In this case, return None

        Correctness is determined by the verify method.

        RETURNS:
        list; the correct solution (that the student supplied). Each element
        in the list is a line of the correct output.
        """
        access_token = auth.authenticate(False)

        if randomize and choices:
            choices = random.sample(choices, len(choices))

        correct = False
        while not correct:
            if choices:
                assert len(answer) == 1, 'Choices must have 1 line of output'
                choice_map = self._display_choices(choices)

            question_timestamp = datetime.now()
            input_lines = []

            for line_number, line in enumerate(answer):
                if len(answer) == 1:
                    prompt = self.PROMPT
                else:
                    prompt = '(line {}){}'.format(line_number + 1, self.PROMPT)

                student_input = format.normalize(self._input(prompt))
                self._add_history(student_input)
                if student_input in self.EXIT_INPUTS:
                    raise EOFError

                if choices and student_input in choice_map:
                    student_input = choice_map[student_input]

                input_lines.append(student_input)
                if not self._verify(student_input, line):
                    # Try to evaluate student answer as Python expression and
                    # use the result as the answer.
                    try:
                        eval_input = repr(eval(student_input, {}, {}))
                        if not self._verify(eval_input, answer[line_number]):
                            break
                        # Replace student_input with evaluated input.
                        input_lines[-1] = eval_input
                    except Exception as e:
                        # Incorrect answer.
                        break

            else:
                correct = True
            tg_id = -1
            msg_id = -1
            spen_dict = {}

            if not correct and error:
                print("-- Not quite. Try again! --")

            elif not correct:
                spen_dict, tg_id = self.error_handling(unique_id,input_lines,access_token)

            else:
                print("-- OK! --")

            self.analytics.append({
                'id': unique_id,
                'case_id': case_id,
                'question timestamp': self.unix_time(question_timestamp),
                'answer timestamp': self.unix_time(datetime.now()),
                'prompt': question_prompt,
                'answer': input_lines,
                'correct': correct,
                'treatment group id': tg_id,
                'misU count': spen_dict,
            })

            """:if not correct:
                print("-- Not quite. Try again! --")

            else:
                print("-- OK! --")"""
            print()
        return input_lines

    ###################
    # Private Methods #
    ###################

    # Displaying the correct messages depending on students' wrong answers and treatment group ID
    def error_handling(self, unique_id, input_lines,access_token):

        shorten_unique_id = unique_id[unique_id.index('\n')+1:]

        # Try to get th info dictionary for this question
        wa_2_dict_info = json_dict_file['dictAssessId2WA2DictInfo'].get(shorten_unique_id)

        if not wa_2_dict_info: # get returns None if wa_2_dict_info doesn't have shorten_unique_id in dictionary
            print ("-- Not quite. Try again! --")
            return ({}, -1)

        dict_info = wa_2_dict_info.get(repr(input_lines))

        # If this wrong answer is not in the JSON file, display default message
        if not dict_info:            
            print ("-- Not quite. Try again! --")
            return ({}, -1)

        # Checks to see the student currently has a treatment group number. If not, calls helper function in auth.py
        if not os.path.isfile("tests/tg.ok_tg"):
            cur_email = auth.get_student_email(access_token)
            if not cur_email:
                print ("--Not quite. Try again! --")
                return ({}, -1)
            lab_assignment = "".join(("".join(self.hash_key.split())).split(":"))
            try:
                data = json.loads(urlopen(TGSERVER + cur_email +"/"+lab_assignment+ "/unlock_tg",timeout =1).read().decode("utf-8"))
            except IOError as e:
                data = {"tg":-1}
            fd = open("tests/tg.ok_tg","w")
            fd.write(str(data["tg"]))
            fd.close()

        tg_file = open("tests/tg.ok_tg", 'r')
        tg_id = int(tg_file.read())

        if tg_id == -1: 
            # If tg_id == -1, some errors happen when trying to access server
            print ("-- Not quite. Try again! --")
            return ({}, -1)

        #Get the string that corresponds to this treatment group ID
        lambda_string = json_dict_file['dictTg2Func'].get(str(tg_id))

        if not lambda_string:
            print ("-- Not quite. Try again! --")
            return ({}, -1)

        lambda_info_misu = eval(lambda_string)

        lst_mis_u = dict_info.get('lstMisU')

        # No list of misunderstandings for this wrong answer, default message
        if not lst_mis_u:
            print ("-- Not quite. Try again! --")
            return ({}, -1)

        spen_dict = self.update_misUcounts(self.hash_key, lst_mis_u, repr(input_lines),shorten_unique_id)

        thresold = json_dict_file['wrongAnsThresh']

        """
        Update Spenser's count file by each misunderstanding in lst_mis_u
        Get the updated counts from Spenser as a dictionary: mis_u -> counts.
        Called that dictionary spen_dict
        """

        msg_id_set = set()

        # If the count is higher than the thresold, we need to display the message
        for mis_u in spen_dict:
            if spen_dict[mis_u] >= thresold:
                # Print each associated unique message for each miunderstanding
                msg_id = lambda_info_misu(dict_info, mis_u)
                msg_id_set.add(msg_id)

        if len(msg_id_set) == 0 or None in msg_id_set:
            # if student is in control group, just print the default message
            print ("-- Not quite. Try again! --")
            return (spen_dict, tg_id)

        for mid in msg_id_set:
            msg = json_dict_file['dictId2Msg'][str(mid)]
            print("-- " + msg + " --")

        return (spen_dict, tg_id)

    # Looks at the locally saved file for number of misU and returns the current count
    def update_misUcounts(self, hashkey, misU, wrongAnswer, shorten_unique_id):
        if not os.path.isdir("tests/" + countDir):
            os.makedirs("tests/" + countDir)

        #Creates a new folder inside tests that stores the number of misU per assignment
        count_file_path = "tests/" + countDir +"/" + "misUcount" + ".json"
        if os.path.isfile(count_file_path):
            with open(count_file_path,'r') as f:
                jsonDic = json.load(f)
                answerDict = jsonDic["answerDict"]
                countData = jsonDic["countData"] 
                f.close()
        else:
            countData = {}
            answerDict = {}
        newjsonDic = {}

        # Checks to see if the question is already stored and whether the student's answer is there
        # It does not update misU count if same answer was seen before
        if shorten_unique_id in answerDict and wrongAnswer in answerDict[shorten_unique_id]:
            return countData
        if not shorten_unique_id in answerDict:
            answerDict[shorten_unique_id] = []

        # Updates misU count
        for x in misU: 
            if x in countData:
                countData[x] += 1
            else:
                countData[x] = 1

        # Stores the updated count back into the same file and overrides it
        answerDict[shorten_unique_id].append(wrongAnswer)
        newjsonDic["countData"] = countData
        newjsonDic["answerDict"] = answerDict
        with open(count_file_path,"w") as f:
            json.dump(newjsonDic,f)
            f.close()

        # Returns a dictionary containing how many times each misU has been seen.
        return countData

    def _verify(self, guess, locked):
        return locking.lock(self.hash_key, guess) == locked

    def _input(self, prompt):
        """Retrieves user input from stdin."""
        return input(prompt)

    def _display_choices(self, choices):
        """Prints a mapping of numbers to choices and returns the
        mapping as a dictionary.
        """
        print("Choose the number of the correct choice:")
        choice_map = {}
        for i, choice in enumerate(choices):
            i = str(i)
            print('{}) {}'.format(i, format.indent(choice,
                                                   ' ' * (len(i) + 2)).strip()))
            choice = format.normalize(choice)
            choice_map[i] = choice
        return choice_map

    def _add_history(self, line):
        """Adds the given line to readline history, only if the line
        is non-empty.
        """
        if line and HAS_READLINE:
            readline.add_history(line)

    def unix_time(self, dt):
        """Returns the number of seconds since the UNIX epoch for the given
        datetime (dt).

        PARAMETERS:
        dt -- datetime
        """
        epoch = datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return int(delta.total_seconds())

protocol = UnlockProtocol

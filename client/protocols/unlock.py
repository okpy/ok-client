"""Implements the UnlockProtocol, which unlocks all specified tests
associated with an assignment.

The UnlockTestCase interface can be implemented by TestCases that are
compatible with the UnlockProtocol.
"""

from client.protocols.common import models
from client.utils import auth
from client.utils import format
from client.utils import guidance
from client.utils import locking
from datetime import datetime
import ast
import logging
import random

log = logging.getLogger(__name__)

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
        self.access_token = None
        self.guidance_util = guidance.Guidance("", assignment=assignment)

    def run(self, messages):
        """Responsible for unlocking each test.

        The unlocking process can be aborted by raising a KeyboardInterrupt or
        an EOFError.

        RETURNS:
        dict; mapping of test name (str) -> JSON-serializable object. It is up
        to each test to determine what information is significant for analytics.
        """
        if not self.args.unlock:
            return
        if not self.args.local:
            self.access_token = auth.authenticate(False)

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
                        eval_input = repr(ast.literal_eval(student_input))
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
            misU_count_dict = {}

            if not correct:
                misU_count_dict, tg_id, printed_msg = self.guidance_util.show_guidance_msg(unique_id,input_lines,
                    self.access_token, self.hash_key)

            else:
                print("-- OK! --")
                printed_msg = ["-- OK! --"]

            self.analytics.append({
                'id': unique_id,
                'case_id': case_id,
                'question timestamp': self.unix_time(question_timestamp),
                'answer timestamp': self.unix_time(datetime.now()),
                'prompt': question_prompt,
                'answer': input_lines,
                'correct': correct,
                'treatment group id': tg_id,
                'misU count': misU_count_dict,
                'printed msg': printed_msg
            })
            print()
        return input_lines

    ###################
    # Private Methods #
    ###################

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

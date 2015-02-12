"""Implements the UnlockProtocol, which unlocks all specified tests
associated with an assignment.

The UnlockTestCase interface can be implemented by TestCases that are
compatible with the UnlockProtocol.
"""

from client.protocols.common import models
from client.utils import format
import hmac
import logging
import random
import string

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

    def on_interact(self):
        """Responsible for unlocking each test.

        The unlocking process can be aborted by raising a KeyboardInterrupt or
        an EOFError.

        RETURNS:
        dict; mapping of test name (str) -> JSON-serializable object. It is up
        to each test to determine what information is significant for analytics.
        """
        if not self.args.unlock:
            return

        format.print_line('~')
        print('Unlocking tests')
        print()

        print('At each "{}", type what you would expect the output to be.'.format(
              self.PROMPT))
        print('Type {} to quit'.format(self.EXIT_INPUTS[0]))
        print()

        analytics = {}
        for test in self.assignment.specified_tests:
            log.info('Unlocking test {}'.format(test.name))
            try:
                analytics[test.name] = test.unlock(self.interact)
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
        return analytics

    def interact(self, answer, choices=None, randomize=True):
        """Reads student input for unlocking tests until the student
        answers correctly.

        PARAMETERS:
        answer    -- list; a list of locked lines in a test case answer.
        choices   -- list or None; a list of choices. If None or an
                     empty list, signifies the question is not multiple
                     choice.

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
        # attempts = 0
        if randomize and choices:
            choices = random.sample(choices, len(choices))
        correct = False
        while not correct:
            # attempts += 1
            if choices:
                assert len(answer) == 1, 'Choices must have 1 line of output'
                choice_map = self._display_choices(choices)

            input_lines = []
            for i in range(len(answer)):
                if len(answer) == 1:
                    prompt = self.PROMPT
                else:
                    prompt = '(line {}){}'.format(i + 1, self.PROMPT)

                student_input = format.normalize(self._input(prompt))
                self._add_history(student_input)
                if student_input in self.EXIT_INPUTS:
                    raise EOFError

                if choices and student_input in choice_map:
                    student_input = choice_map[student_input]

                if not self._verify(student_input, answer[i]):
                    break
                else:
                    input_lines.append(student_input)
            else:
                correct = True


            # TODO(albert): record analytis
            # Performt his before the function exits?
            # self._analytics[self._analytics['current']].append((attempts, correct))

            # if input_lines.lower() in self.EXIT_INPUTS:
            #     attempts -= 1
            #     self._analytics[self._analytics['current']].append((attempts, correct))
            #     return

            if not correct:
                print("-- Not quite. Try again! --")
            else:
                print("-- OK! --")
            print()
        # self._analytics[self._analytics['current']].append((attempts, correct))
        return input_lines

    ###################
    # Private Methods #
    ###################

    def _verify(self, guess, locked):
        return hmac.new(self.hash_key.encode('utf-8'),
                        guess.encode('utf-8')).hexdigest() == locked

    def _input(self, prompt):
        """Retrieves user input from stdin."""
        return input(prompt)

    def _display_choices(self, choices):
        """Prints a mapping of numbers to choices and returns the
        mapping as a dictionary.
        """
        print("Choose the number of the correct choice:")
        choice_map = {}
        # TODO(albert): consider using letters as choices instead of numbers.
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

protocol = UnlockProtocol

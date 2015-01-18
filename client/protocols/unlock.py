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

    name = 'unlock'

    PROMPT = '? '       # Prompt that is used for user input.
    EXIT_INPUTS = (     # Valid user inputs for aborting the session.
        'exit()',
        'quit()',
    )

    def __init__(self, cmd_args, assignment):
        super().__init__(cmd_args, assignment)
        self.hash_key = assignment.name

    def on_interact(self):
        """
        Responsible for unlocking each test.
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

        for test in self.assignment.specified_tests:
            log.info('Unlocking test {}'.format(test.name))
            try:
                test.unlock(self._interact)
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
        return self.analytics

    ###################
    # Private Methods #
    ###################

    def _interact(self, answer, choices=None):
        """Reads student input for unlocking tests until the student
        answers correctly.

        PARAMETERS:
        answer    -- str; a locked test case answer.
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
        str  -- the correct solution (that the student supplied)
        """
        # attempts = 0
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
                if student_input in self.EXIT_INPUTS:
                    raise EOFError
                input_lines.append(student_input)
                self._add_history(input_lines[-1])

                if choices and student_input in choice_map:
                    student_input = choice_map[student_input]

                if not self._verify(student_input, answer[i]):
                    break
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
        for i, choice in enumerate(random.sample(choices, len(choices))):
            print('    {}) {}'.format(i, choice))
            i = str(i)
            choice = format.normalize(choice)
            choice_map[i] = choice
        return choice_map

    def _add_history(self, line):
        """Adds the given line to readline history, only if the line
        is non-empty.
        """
        if line and HAS_READLINE:
            readline.add_history(line)

def unlock(test, logger, hash_key, analytics=None):
    """Unlocks TestCases for a given Test.

    PARAMETERS:
    test   -- Test; the test to unlock.
    logger -- OutputLogger.
    hash_key -- string; hash_key to be used to unlock.
    analytics -- dict; dictionary used to store analytics for this protocol

    DESCRIPTION:
    This function incrementally unlocks all TestCases in a specified
    Test. Students must answer in the order that TestCases are
    written. Once a TestCase is unlocked, it will remain unlocked.

    RETURN:
    int, bool; the number of cases that are newly unlocked for this Test
    after going through an unlocking session and whether the student wanted
    to exit the unlocker or not.
    """
    if analytics is None:
        analytics = {}
    console = UnlockConsole(logger, hash_key, analytics)
    cases = 0
    cases_unlocked = 0
    analytics[test.name] = []
    analytics['current'] = test.name
    for suite in test['suites']:
        for case in suite:
            cases += 1
            if not isinstance(case, UnlockTestCase) \
                    or not case['locked']:
                continue
            formatting.underline('Case {}'.format(cases), line='-')
            if console.run(case):   # Abort unlocking.
                return cases_unlocked, True
            cases_unlocked += 1
    print("You are done unlocking tests for this question!")
    del analytics['current']
    return cases_unlocked, False

protocol = UnlockProtocol

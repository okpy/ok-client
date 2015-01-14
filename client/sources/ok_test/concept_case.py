"""Case for conceptual tests.

ConceptCases are designed to be natural language tests that help
students understand high-level understanding. As such, these test cases
focus mainly on unlocking.
"""

from client.sources.common import core
from client.sources.common import models

class ConceptCase(models.LockableCase):
    question = core.String()
    answer = core.String()
    choices = core.List(type=str, optional=True)

    def run(self, logger):
        """Runs the test conceptual test case.

        RETURNS:
        bool; True if the test case passes, False otherwise.
        """
        # TODO(albert): print question and answer if verbose
        # print('Q: ' + self['question'])
        # print('A: ' + self['answer'])
        # print()
        return True

    def lock(self, hash_fn):
        if self.choices is not core.NoValue:
            # TODO(albert): ask Soumya why join is used
            self.answer = hash_fn("".join(self.answer))
        else:
            self.answer = hash_fn(self.answer)
        self.locked = True

    def unlock(self, interact):
        """Unlocks the conceptual test case."""
        if self.locked == core.NoValue:
            # TODO(albert): determine best initial setting.
            self.locked = False
        if self.locked:
            # TODO(albert): perhaps move ctrl-c handling here
            # TODO(albert): print question
            # print('Q: ' + self['question'])
            # print()
            answer = interact(self.answer, self.choices)
            if answer != self.answer:
                # Answer was presumably unlocked
                self.locked = False
                self.answer = answer

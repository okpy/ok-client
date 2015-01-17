"""Case for conceptual tests.

ConceptCases are designed to be natural language tests that help
students understand high-level understanding. As such, these test cases
focus mainly on unlocking.
"""

from client.sources.common import models as common_models
from client.sources.ok_test import models as ok_models
from client.sources.common import core

class ConceptSuite(ok_models.Suite):
    scored = core.Boolean(default=False)
    cases = core.List()

    def post_instantiation(self):
        for i, case in enumerate(self.cases):
            if not isinstance(case, dict):
                # TODO(albert): raise an appropriate error
                raise TypeError
            self.cases[i] = ConceptCase(**case)

    def run(self):
        for case in self.cases:
            # TODO(albert): print some informative output
            case.run()
        return True

class ConceptCase(common_models.Case):
    question = core.String()
    answer = core.String()
    choices = core.List(type=str, optional=True)

    def run(self):
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


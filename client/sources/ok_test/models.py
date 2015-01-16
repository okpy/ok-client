from client.sources.common import core
from client.sources.common import models
from client.utils import formatting

##########
# Models #
##########

class OkTest(models.Test):
    suites = core.List()
    description = core.String(optional=True)

    def __init__(self, suite_map, **fields):
        super().__init__(**fields)
        self.suite_map = suite_map

    def post_instantiation(self):
        for i, suite in enumerate(self.suites):
            if not isinstance(suite, dict) or 'type' not in suite:
                # TODO(albert): raise an appropriate error
                raise TypeError
            self.suites[i] = self.suite_map[suite['type']](**suite)

    def run(self):
        """Runs the suites associated with this OK test."""
        # formatting.underline('Running tests for ' + test.name)
        # print()
        # if test.description:
        #     print(test.description)

        # cases_tested = Counter()
        for suite in self.suites:
            success = suite.run()
            if not success:
                break

        # TODO(albert): Print results to stdout
        # if test.num_locked > 0:
        #     print('-- There are still {} locked test cases.'.format(
        #         test.num_locked) + ' Use the -u flag to unlock them. --')
        # print('-- {} cases passed ({}%) for {} --'.format(
        #     passed, round(100 * passed / total, 2), test.name))
        # print()

    def score(self):
        # TODO(albert): call self.run and assign score based on returned
        # analytics
        pass

    def dump(self, file):
        # TODO(albert): add log messages
        # TODO(albert): writing causes an error halfway, the tests
        # directory may be left in a corrupted state.
        # TODO(albert): might need to delete obsolete test files too.
        # TODO(albert): verify that test_json is serializable into json.
        json = formatting.json_triple_quotes(self.to_json())
        with open(file, 'w') as f:
            f.write('test = ' + json)

class Suite(core.Serializable):
    type = core.String()
    scored = core.Boolean(default=True)

    def run(self):
        """Subclasses should override this method to run tests.

        RETURNS:
        bool; True if all cases pass successfully, False otherwise.
        """
        raise NotImplementedError

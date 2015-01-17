from client.sources.common import core
from client.sources.common import models
from client.utils import formatting

##########
# Models #
##########

class OkTest(models.Test):
    suites = core.List()
    description = core.String(optional=True)

    def __init__(self, suite_map, verbose, interactive, timeout=None, **fields):
        super().__init__(**fields)
        self.suite_map = suite_map
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def post_instantiation(self):
        for i, suite in enumerate(self.suites):
            if not isinstance(suite, dict) or 'type' not in suite:
                # TODO(albert): raise an appropriate error
                raise TypeError
            self.suites[i] = self.suite_map[suite['type']](
                    self.verbose, self.interactive, self.timeout, **suite)

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
        passed, total = 0, 0
        for suite in self.suites:
            if not suite.scored:
                continue
            total += 1
            success = suite.run()
            if success:
                passed += 1
        if total > 0:
            score = passed * self.points / total
        else:
            score = 0
        return score

    def unlock(self, interact):
        # formatting.underline('Unlocking tests for {}'.format(test.name))
        # print()

        for suite in self.suites:
            for case in suite.cases:
                if case.locked != True:
                    continue

                # formatting.underline('Case {}'.format(cases), line='-')

                case.unlock(interact)
        # print("You are done unlocking tests for this question!")
        # print()

    def lock(self, hash_fn):
        # formatting.underline('Locking Test ' + test.name, line='-')

        num_cases = 0
        for suite in self.suites:
            for case in list(suite.cases):
                if case.hidden:
                    suite.cases.remove(case)
                    print('* Case {}: removed hidden test'.format(num_cases))
                elif case.locked == core.NoValue:
                    case.lock(hash_fn)
                    print('* Case {}: locked test'.format(num_cases))
                elif case.locked == False:
                    pass
                    print('* Case {}: never lock'.format(num_cases))
                elif case.locked == True:
                    pass
                    print('* Case {}: already locked'.format(num_cases))
                num_cases += 1  # 1-indexed

    def dump(self, file):
        # TODO(albert): add log messages
        # TODO(albert): writing causes an error halfway, the tests
        # directory may be left in a corrupted state.
        # TODO(albert): might need to delete obsolete test files too.
        # TODO(albert): verify that test_json is serializable into json.
        json = formatting.prettyjson(self.to_json())
        with open(file, 'w') as f:
            f.write('test = ' + json)

class Suite(core.Serializable):
    type = core.String()
    scored = core.Boolean(default=True)

    def __init__(self, verbose, interactive, timeout=None, **fields):
        super().__init__(**fields)
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def run(self):
        """Subclasses should override this method to run tests.

        RETURNS:
        bool; True if all cases pass successfully, False otherwise.
        """
        raise NotImplementedError

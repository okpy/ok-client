from client.sources.common import core
from client.sources.common import models
from client.utils import format
from client.utils import output

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
        passed, failed, locked = 0, 0, 0
        for i, suite in enumerate(self.suites):
            results = suite.run(self.name, i + 1)

            passed += results['passed']
            failed += results['failed']
            locked += results['locked']

        self._print_breakdown('cases', passed, failed, locked)
        if locked > 0:
            print()
            print('There are still unlocked tests! '
                  'Use the -u option to unlock them')

        if type(self.description) == str and self.description:
            print()
            print(self.description)
        print()

    def _print_breakdown(self, type, passed, failed, locked=None):
        format.print_line('-')
        print(self.name)
        print('    Passed: {}'.format(passed))
        print('    Failed: {}'.format(failed))
        if locked is not None:
            print('    Locked: {}'.format(locked))

        # Print [oook.....] progress bar
        total = passed + failed + (0 if locked is None else locked)
        percent = round(100 * passed / total, 1) if total != 0 else 0.0
        print('[{}k{}] {}% of {} passed'.format(
            'o' * int(percent // 10),
            '.' * int(10 - (percent // 10)),
            percent,
            type))

    def score(self):
        passed, total = 0, 0
        for i, suite in enumerate(self.suites):
            if not suite.scored:
                continue

            total += 1
            results = suite.run(self.name, i + 1)

            if results['locked'] == 0 and results['failed'] == 0:
                passed += 1
        if total > 0:
            score = passed * self.points / total
        else:
            score = 0.0

        self._print_breakdown('suites', passed, total - passed)
        print()
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
        format.print_line('-')
        print(self.name)

        for suite_num, suite in enumerate(list(self.suites)):
            for case_num, case in enumerate(list(suite.cases)):
                message = '* Suite {} > Case {}: '.format(suite_num, case_num)
                if case.hidden:
                    suite.cases.remove(case)
                    print(message + 'removing hidden case')
                elif case.locked == core.NoValue:
                    case.lock(hash_fn)
                    print(message + 'locking')
                elif case.locked == False:
                    print(message + 'leaving unlocked')
                elif case.locked == True:
                    print(message + 'already unlocked')
        print()

    def dump(self, file):
        # TODO(albert): add log messages
        # TODO(albert): writing causes an error halfway, the tests
        # directory may be left in a corrupted state.
        # TODO(albert): might need to delete obsolete test files too.
        # TODO(albert): verify that test_json is serializable into json.
        json = format.prettyjson(self.to_json())
        with open(file, 'w') as f:
            f.write('test = ' + json)

class Suite(core.Serializable):
    type = core.String()
    scored = core.Boolean(default=True)

    def __init__(self, verbose, interactive, timeout=None,
                 **fields):
        super().__init__(**fields)
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def run(self, test_name, suite_number):
        """Subclasses should override this method to run tests.

        RETURNS:
        dict; results of the following form:
        {
            'passed': int,
            'failed': int,
            'locked': int,
        }
        """
        raise NotImplementedError

    def _run_case(self, test_name, suite_number, case, case_number):
        """A wrapper for case.run().

        Prints informative output and also captures output of the test case
        and returns it as a log. The output is suppressed -- it is up to the
        calling function to decide whether or not to print the log.
        """
        output.off()    # Delay printing until case status is determined.
        log_id = output.new_log()

        format.print_line('-')
        print('{} > Suite {} > Case {}'.format(test_name, suite_number,
                                               case_number))
        print()

        success = case.run()
        if success:
            print('-- OK! --')

        output.on()
        output_log = output.get_log(log_id)
        output.remove_log(log_id)

        return success, output_log


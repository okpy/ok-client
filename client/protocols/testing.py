from client.protocols.common import models
from client.exceptions import EarlyExit
from client.utils.storage import contains, get, store
from client.utils import format
import doctest
import os

###########################
#    Testing Mechanism    #
###########################
CURR_DIR = os.getcwd()

class TestingProtocol(models.Protocol):
    """A Protocol that keeps track of the tests in mytest.rst.
    """
    def __init__(self, args, assignment):
        super().__init__(args, assignment)

    def test(self, verbose=False, testloc=CURR_DIR):
        test_results = {}
        count = 0
        for file in sorted(os.listdir(testloc)):
            if file.endswith('.rst'):
                if verbose and test_results:
                    format.print_line('%')
                ABS_PATH = os.path.join(testloc, file)
                res = doctest.testfile(ABS_PATH, module_relative=False, verbose=verbose, optionflags=doctest.FAIL_FAST, report=False)
                failed = res.failed
                attempted = res.attempted
                passed = attempted - failed
                format.print_progress_bar( '{} summary'.format(file), passed, failed, 0,
                              verbose=verbose)
                test_results['Test {}'.format(count)] =  {'name': file, 'failed' : failed, 'passed' : passed, 'attempted' : attempted}
                count += 1
        return test_results

    def run(self, messages, testloc=CURR_DIR):
        if self.args.score or self.args.unlock:
            return
        analytics = self.test(self.args.verbose, testloc)
        messages['testing'] = analytics





protocol = TestingProtocol

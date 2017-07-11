from client.protocols.common import models
from client.exceptions import EarlyExit
from client.utils.storage import contains, get, store
from client.utils import format
import doctest
import os

###########################
#    Testing Mechanism    #
###########################

TESTFILE = 'mytests.rst'
CURR_DIR = os.getcwd()
ABS_PATH = os.path.join(CURR_DIR, TESTFILE)

class TestingProtocol(models.Protocol):
    """A Protocol that keeps track of the tests in mytest.rst.
    """
    def __init__(self, args, assignment):
        super().__init__(args, assignment)

    def test(self, verbose=False):
        res = doctest.testfile(ABS_PATH, module_relative=False, 
            verbose=verbose, optionflags=doctest.FAIL_FAST, report=False)
        failed = res.failed
        attempted = res.attempted
        passed = attempted - failed
        format.print_progress_bar('MyTest summary', passed, failed, 0,
                              verbose=verbose)

    def run(self, messages):
        self.test(self.args.verbose)





protocol = TestingProtocol
"""Implements the TraceProtocol, which traces code and
provides a Python Tutor visualization.
"""

import logging

from client.protocols.common import models
from client.sources.doctest import models as doctest_models

from client.utils import format
from client.pythontutor import generate_trace
log = logging.getLogger(__name__)

class TraceProtocol(models.Protocol):
    """ Trace a specific test and render a JSON. """

    def run(self, messages, env=None):
        """Run gradeable tests and print results and return analytics.
        """
        if not self.args.trace:
            return
        tests = self.assignment.specified_tests
        if not self.args.question:
            with format.block('*'):
                print("Could not trace: Please specify a question to trace.")
                print("Example: python3 ok --trace -q <name>")
            return

        test = tests[0]
        # TODO: Check for appropriate instance types
        data = test.get_code()
        if not data:
            with format.block('*'):
                print("This test is not traceable.")
            return

        if isinstance(test, doctest_models.Doctest):
            # Directly handle case (for doctests)
            question = self.args.question[0]
            if question not in data:
                with format.block('*'):
                    eligible_questions = ','.join([str(i) for i in data.keys()])
                    print("The following doctests can be traced: {}".format(eligible_questions))
                    usage_base = "Usage: python3 ok -q {} --trace"
                    usage_base.format(eligible_questions[0])
                    return
            suite = [data[question]]
        elif hasattr(test, 'suites'):
            # Handle ok_tests
            if self.args.suite:
                eligible_suite_nums = ','.join([str(i) for i in data.keys()])
                with format.block('*'):
                    print("Please specify a specific suite to test.")
                    print("The following suites can be traced: {}".format(eligible_suite_nums))
                    usage_base = "Usage: python3 ok -q {} --suite {} --trace"
                    usage_base.format(self.args.question[0], eligible_suite_nums[0])
                return
            if self.args.suite not in data:
                with format.block('*'):
                    print("Suite {} is not traceable.".format(self.args.suite))
                return

            suite = data[self.args.suite] # only trace this one suite
            case_arg = self.args.case
            if case_arg:
                case_num = case_arg[0]-1
                if not (case_arg[0]-1 not in range(len(suite))):
                    with format.block('*'):
                        print("You can specify a specific case to test.")
                        print("Cases: 1-{}".format(len(suite)))
                        usage_base = "Usage: python3 ok -q {} --suite {} --case 1 --trace"
                        print(usage_base.format(self.args.question[0], self.args.suite))
                        return
                suite = [suite[case_arg[0]-1]]
        else:
            pass

        # Setup and teardown are shared among cases within a suite.
        setup, test_script, _ = suite_to_code(suite)
        data = generate_trace.run_logger(test_script, setup, {})
        print(data)

        # Call Python Tutor with the approriate values

def suite_to_code(suite):
    code_lines = []
    for ind, case in enumerate(suite):
        setup = case['setup']
        teardown = case['teardown']

        case_intro = "# --- Begin Case --- #"
        code = '\n'.join(case['code'])

        # Only grab the code, since the setup/teardown is shared
        lines = "{}\n{}".format(case_intro, code)
        code_lines.append(lines)
    return setup, '\n'.join(code_lines), teardown

protocol = TraceProtocol

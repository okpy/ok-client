from client.protocols.common import models
from client.utils import format
from doctest import DocTest, DocTestParser, DocTestRunner, FAIL_FAST, Example
import os
import re
import sys
import importlib

CURR_DIR = os.getcwd()

###########################
#    Testing Mechanism    #
###########################

class TestingProtocol(models.Protocol):
    """A Protocol that keeps track of the tests in mytest.rst.
    """
    def __init__(self, args, assignment):
        super().__init__(args, assignment)

    def test(self, good_env={}, suite=None, case=None, verbose=False, testloc=CURR_DIR):
        #remember to catch the lookup error
        parser = DocTestParser()
        runner = DocTestRunner(verbose=verbose, optionflags= FAIL_FAST)
        file = "mytests.rst"
        data = {}
        test_results = {}
        ABS_PATH = os.path.join(testloc, file)
        with open(ABS_PATH, "r") as testfile:
            data_str=testfile.read()
        data_suites = re.findall("(Suite[^\n]*([0-9]+))((?:(?!Suite)(.|\n))*)", data_str)
        num_suites = len(data_suites)
        num_cases = 0
        try:
            for curr_suite in data_suites:
                case_data = {}
                cases = re.findall("(Case[^\n]*([0-9]+))((?:(?!Case)(.|\n))*)", curr_suite[2])
                num_cases += len(cases)
                for curr_case in cases:
                    case_data[curr_case[1]] = curr_case[2]
                data[curr_suite[1]] = case_data
            if suite:
                name = "Suite " + str(suite)
                if case:
                    parsed_examples = parser.parse(data[str(suite)][str(case[0])], file)
                    examples = [i for i in parsed_examples if isinstance(i, Example)]
                else:
                    examples = []
                    for itemcase in sorted(data[str(suite)].keys()):
                        parsed_temp_examples = parser.parse(data[str(suite)][itemcase], file)
                        examples.extend([i for i in parsed_temp_examples if isinstance(i, Example)])
                dtest = DocTest(examples, good_env, name, file, examples[0].lineno, None)
            else:
                name = file
                examples = []
                for sui in sorted(data.keys()):
                    for itemcase in sorted(data[sui].keys()):
                        parsed_temp_examples = parser.parse(data[sui][itemcase], file)
                        examples.extend([i for i in parsed_temp_examples if isinstance(i, Example)])
                dtest = DocTest(examples, good_env, name, file, examples[0].lineno, None)

            res = runner.run(dtest)
            failed = res.failed
            attempted = res.attempted
            passed = attempted - failed
            format.print_progress_bar( '{} summary'.format(name), passed, failed, 0,
                          verbose=verbose)
            test_results['Test 0'] =  {'name': file, 'suites_total' : num_suites, 
            'cases_total': num_cases, 'failed' : failed, 'passed' : passed, 'attempted' : attempted}
        except KeyError:
            sys.exit(('python3 ok: error: ' 
                        'Suite/Case number must be valid.'))
        #print(test_results)
        return test_results


    def run(self, messages, testloc=CURR_DIR):
        self.good_env = {}
        default = dict(globals())
        sys.path.insert(0, testloc)
        #Not sure if line above is needed...
        #Insert config.ok parser to get the mod_list? example is 'hw1', 'hw1_extra'
        mod_list = ["hw1"]
        for mod in mod_list:
            temp_mod = importlib.import_module(mod)
            module_dict = temp_mod.__dict__
            try:
                to_import = temp_mod.__all__
            except AttributeError:
                to_import = [name for name in module_dict if not name.startswith('_')]
            globals().update({name: module_dict[name] for name in to_import})
        diff = globals().keys() - default.keys() - {'default'}
        self.good_env = { key: globals()[key] for key in diff}
        for key in set(globals().keys()):
            if key not in default and key != "default":
                del globals()[key]
        if self.args.score or self.args.unlock:
            return
        analytics = self.test(self.good_env, self.args.suite, self.args.case, self.args.verbose, testloc)
        messages['testing'] = analytics

protocol = TestingProtocol


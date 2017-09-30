from client.protocols.common import models
from client.utils import format
from doctest import DocTest, DocTestParser, DocTestRunner, FAIL_FAST, Example
from client.exceptions import EarlyExit
import os
import re
import sys
import importlib
import collections
from coverage import coverage
import signal
###########################
#    Testing Mechanism    #
###########################

# Must get current dir for Travis to pass, among other reasons
CURR_DIR = os.getcwd()

# Users will generally name their test file the following name.
# If changing default name, change in ok.py args parse as well
DEFAULT_TST_FILE = "mytests.rst"

def timeout(seconds_before_timeout):
    """www.saltycrane.com/blog/2010/04/using-python-timeout-decorator-uploading-s3/"""
    def decorate(f):
        def handler(signum, frame):
            raise EarlyExit("Test examples timed out!")
        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result
        new_f.__name__ = f.__name__
        return new_f
    return decorate

class TestingProtocol(models.Protocol):
    """A Protocol that executes doctests as lists of Example objects, supports
    suite/case specificity, alternate file testing, and provides users with
    details such as cases passed and test coverage.
    """
    def __init__(self, args, assignment):
        super().__init__(args, assignment)
        # The environment in which the doctests are run (global vars)
        self.good_env = {}
        self.verb = self.args.verbose
        # Initialize the doctest module objects that will do the testing/parse
        self.parser = DocTestParser()
        self.runner = DocTestRunner(verbose=self.verb, optionflags=FAIL_FAST)
        self.lines_exec = 0
        self.lines_total = 0


    def test(self, good_env={}, suite=None, case=None):
        test_results = {}
        # all examples to be run will be put in exs
        exs = collections.OrderedDict()
        # use regex to get raw strings organized into suite/case
        self.get_data()
        try:
            if suite:
                exs = self.get_suite_examples(suite, case)
            elif case:
                # No support for cases without their suite
                raise EarlyExit('python3 ok: error: ' 
                    'Please specify suite for given case ({}).'.format(case[0]))
            else:
                exs = self.get_all_examples()
            # gets analytics to be returned
            test_results[self.tstfile_name] =  self.analyze(suite, case, exs)
        except KeyError as e:
            raise EarlyExit('python3 ok: error: ' 
                    'Suite/Case label must be valid.'
                    '(Suites: {}, Cases: {})'.format(self.num_suites, self.num_cases))
        return test_results

    def analyze(self, suite, case, examples):
        failed, attempted = self.run_examples(examples)
        self.postcov.stop()
        passed = attempted - failed
        format.print_test_progress_bar( '{} summary'.format(self.tstfile_name),
                                        passed, failed, verbose=self.verb)
        # only support test coverage stats when running everything
        if not suite:
            self.print_coverage()
            if self.args.coverage:
                if self.lines_exec == self.lines_total:
                    print("Maximum coverage achieved! Great work!")
                else:
                    self.give_suggestions()

        return {'suites_total' : self.num_suites, 'cases_total': self.num_cases,
                'exs_failed' : failed, 'exs_passed' : passed, 'attempted' : attempted,
                'actual_cov' : self.lines_exec, 'total_cov' : self.lines_total}

    def give_suggestions(self):
        print("Consider adding tests for the following:")
        for file in self.clean_src:
            file += '.py'
            cov_stats_post = self.postcov.analysis2(file)
            cov_stats_pre = self.precov.analysis2(file)
            missing_post = cov_stats_post[3]
            missing_pre = cov_stats_pre[3]
            missing = [i for i in missing_post if i in missing_pre]
            if missing:
                print('   File: {}'.format(file))
                missing_string = '      Line(s): ' + ','.join(map(str, missing))
                print(missing_string)



    def get_suite_examples(self, suite, case):
        # suite/case specified, so only parse relevant text into Examples
        exs = collections.OrderedDict()
        case_ex = collections.OrderedDict()
        # get the shared lines that should impact all the cases in the suite.
        shrd_txt = self.shared_case_data[suite]
        if shrd_txt:
            parse_shared = self.parser.parse(shrd_txt.group(0), self.tstfile_name)
            shrd_ex = [i for i in parse_shared if isinstance(i, Example)]
            if shrd_ex:
                case_ex['shared'] = shrd_ex
        if case:
            if str(case[0]) not in self.data[suite]:
                 raise KeyError
            parsed_temp_examples = self.parser.parse(self.data[suite][case[0]], self.tstfile_name)
            case_examples = [i for i in parsed_temp_examples if isinstance(i, Example)]
            case_ex[str(case[0])] = case_examples
        else:
            for itemcase in self.data[suite].keys():
                parsed_temp_examples = self.parser.parse(self.data[suite][itemcase], self.tstfile_name)
                case_examples = [i for i in parsed_temp_examples if isinstance(i, Example)]
                case_ex[itemcase] = case_examples
        exs[suite] = case_ex
        return exs


    def get_all_examples(self):
        # no suite/case flag, so parses all text into Example objects
        exs = collections.OrderedDict()
        for sui in self.data.keys():
            case_ex = collections.OrderedDict()
            # get the shared lines that should impact all the cases in the suite.
            shrd_txt = self.shared_case_data[sui]
            if shrd_txt:
                parse_shared = self.parser.parse(shrd_txt.group(0), self.tstfile_name)
                shrd_ex = [i for i in parse_shared if isinstance(i, Example)]
                if shrd_ex:
                    case_ex['shared'] = shrd_ex
            for itemcase in self.data[sui].keys():
                parsed_temp_examples = self.parser.parse(self.data[sui][itemcase], self.tstfile_name)
                case_examples = [i for i in parsed_temp_examples if isinstance(i, Example)]
                case_ex[itemcase] = case_examples
            exs[sui] = case_ex
        return exs

    # catch inf loops/ recur err
    @timeout(10)
    def run_examples(self, exs):
        # runs the Example objects, keeps track of right/wrong etc
        total_failed = 0
        total_attempted = 0
        case = 'shared'
        for sui in exs.keys():
            if not total_failed:
                final_env = dict(self.good_env)
                if 'shared' in exs[sui].keys():
                    dtest = DocTest(exs[sui]['shared'], self.good_env, 'shared', None, None, None)
                    result = self.runner.run(dtest, clear_globs=False)
                    # take the env from shared dtest and save it for other exs
                    final_env = dict(self.good_env, **dtest.globs)
                    total_failed += result.failed
                    total_attempted += result.attempted
            for case in exs[sui].keys():
                if case != 'shared':    
                    if not total_failed:
                        example_name = "Suite {}, Case {}".format(sui, case)
                        dtest = DocTest(exs[sui][case], final_env, example_name, None, None, None)
                        result = self.runner.run(dtest)
                        total_failed += result.failed
                        total_attempted += result.attempted
        return total_failed, total_attempted

    def get_data(self):
        # organizes data into suite/case strings to feed to the parser module
        self.tstfile_name, data_str = self.get_tstfile(self.testloc)
        self.data = collections.OrderedDict()
        self.shared_case_data = collections.OrderedDict()
        # chunk the file into suites
        data_suites = re.findall("(Suite\s*([\d\w]+))((?:(?!Suite)(.|\n))*)", data_str)
        self.num_suites = len(data_suites)
        self.num_cases = 0
        for curr_suite in data_suites:
                case_data = collections.OrderedDict()
                # chunk the suite into cases
                cases = re.findall("(Case\s*([\d\w]+))((?:(?!Case)(.|\n))*)", curr_suite[2])
                self.num_cases += len(cases)
                self.shared_case_data[str(curr_suite[1])] = re.match("((?:(?!Case)(.|\n))*)", curr_suite[2])
                for curr_case in cases:
                    case_data[curr_case[1]] = curr_case[2]
                self.data[curr_suite[1]] = case_data

    def get_tstfile(self, location):
        # return file, file as a string
        PATH = os.path.join(location, self.args.testing)
        name = self.args.testing
        if not name.endswith('.rst'):
            raise EarlyExit('python3 ok: error: '
                        'Only .rst files are supported at this time.')
        try:
            with open(PATH, "r") as testfile:
                data_str=testfile.read()
        except FileNotFoundError as e:
            raise EarlyExit('python3 ok: error: '
                    '{} test file ({}) cannot be found.'.format(
                    'Default' if DEFAULT_TST_FILE==name else 'Specified', name))
        return name, data_str


    def print_coverage(self):
        # prints the coverage summary by diffing the two coverage trackers
        lines, post_exec = self.get_coverage(self.postcov)
        lines, default_exec = self.get_coverage(self.precov)
        self.lines_total = lines - default_exec
        self.lines_exec = post_exec
        format.print_coverage_bar( 'Coverage summary', 
            self.lines_exec, self.lines_total,verbose=self.verb)

    def get_coverage(self, cov):
        # returns executable lines, executed_lines
        lines_run = 0
        total_lines = 0
        for file in self.clean_src:
            file_cov = cov.analysis2(file + '.py')
            lines = len(file_cov[1])
            lines_not_run = len(file_cov[3])
            total_lines += lines
            lines_run += lines - lines_not_run
        return total_lines, lines_run

    def execute_imports(self):
        # imports py modules into good_env
        # imports must be direct, no using exec(), for coverage to track lines
        default = dict(globals())
        sys.path.insert(0, self.testloc)
        for mod in self.clean_src:
            temp_mod = importlib.import_module(mod)
            module_dict = temp_mod.__dict__
            try:
                to_import = temp_mod.__all__
            except AttributeError:
                to_import = [name for name in module_dict if not name.startswith('_')]
            globals().update({name: module_dict[name] for name in to_import})
        diff = globals().keys() - default.keys() - {'default'}
        self.good_env = {}
        #self.good_env = { key: globals()[key] for key in diff} (Uncomment for autoimport)
        for key in set(globals().keys()):
            if key not in default and key != "default":
                del globals()[key]

    def run(self, messages, testloc=CURR_DIR):
        if self.args.score or self.args.unlock or not self.args.testing:
            return
        # Note: All (and only) .py files given in the src will be tracked and
        # contribute to coverage statistics
        self.clean_src = [i[:-3] for i in self.assignment.src if i.endswith('.py')]
        # Since importing boosts coverage, we make an additional precov to know
        # how much to subtract to get to the true coverage
        self.precov = coverage(source = [os.path.join(testloc, file + '.py') for file in self.clean_src])
        self.postcov = coverage(source = [os.path.join(testloc, file + '.py') for file in self.clean_src])
        self.testloc = testloc
        self.postcov.start()
        self.precov.start()
        self.execute_imports()
        # we stop precov tracker here so we can later subract out the influence
        # of executing imports (aka runs function definitions)
        self.precov.stop()
        analytics = self.test(self.good_env, self.args.suite, self.args.case)
        messages['testing'] = analytics

protocol = TestingProtocol


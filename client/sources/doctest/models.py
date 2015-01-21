from client.sources.common import core
from client.sources.common import models
from client.sources.common import doctest_case
from client.sources.common import importing
from client.utils import format
from client.utils import output
import re
import textwrap

##########
# Models #
##########

class Doctest(models.Test):
    docstring = core.String()

    PS1 = '>>> '
    PS2 = '... '

    SETUP = PS1 + 'from {} import *'
    prompt_re = re.compile(r'(\s*)({}|{})'.format(PS1, '\.\.\. '))

    def __init__(self, file, verbose, interactive, timeout=None, **fields):
        super().__init__(**fields)
        self.file = file
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

        self.console = doctest_case.PythonConsole(self.verbose, self.interactive,
                                                  self.timeout)

    def post_instantiation(self):
        # TODO(albert): often, the first line of a docstring is at the beginning
        # of the string. Dedenting will have no effect.
        self.docstring = textwrap.dedent(self.docstring)
        code = []
        prompt_on = False
        leading_space = ''
        for line in self.docstring.split('\n'):
            prompt_match = self.prompt_re.match(line)
            if prompt_match:
                if prompt_on and not line.startswith(leading_space):
                    # TODO(albert): raise appropriate error
                    raise TypeError('Inconsistent tabs for doctest')
                elif not prompt_on:
                    prompt_on = True
                    leading_space = prompt_match.group(1)
                code.append(line.lstrip())
            elif not line.strip():
                prompt_on = False
                leading_space = ''
            elif prompt_on:
                if not line.startswith(leading_space):
                    # TODO(albert): raise appropriate error
                    raise TypeError('Inconsistent tabs for doctest')
                code.append(line.lstrip())
        module = self.SETUP.format(importing.path_to_module_string(self.file))
        self.case = doctest_case.DoctestCase(self.console, module,
                                             code='\n'.join(code))

    def run(self):
        """Runs the suites associated with this doctest."""
        format.print_line('-')
        print('Doctests for {}'.format(self.name))
        print()
        self.case.run()

    def score(self):
        format.print_line('-')
        print('Doctests for {}'.format(self.name))
        print()
        success = self.case.run()
        score = 1.0 if success else 0.0

        print('Score: {}/1'.format(score))
        print()
        return score


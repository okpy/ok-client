"""

Extension for Jupyter Notebook

- prepares makefile dependencies
- convert .ipynb notebooks into .py files
- cache and update python files accordingly

"""
from io import StringIO
import sys

from client.protocols.grading import GradingProtocol
from . import Extension, extension
import json
import os
import subprocess


MAKEFILE_TEMPLATE = """\
{name}.py: {name}.ipynb
	ok --extension notebook --extargs '{args}'
"""


def shell(f):
	""" Wraps all shell commands, prints command first """
	def helper(*args, **kwargs):
		print('[Notebook] %s' % str(args[1:]))
		return f(*args, **kwargs)
	helper.__name__ = f.__name__
	return helper


@extension
class NotebookExt(Extension):

	cache_dir = 'cache'
	tests = []
	results = {}
	files = {}
	
	######################
	# OBLIGATORY METHODS #
	######################

	def setup(self, assign=None):
		""" setup dependencies, and cache code blocks """
		if self.args.nb:
			self.terminate_after_setup = True
			self.extract_book(self.args.nb)
		elif assign:
			self.tests = assign.default_tests
		else:
			self.setup_makefile()
			self.call('make', 'all', '--quiet')
			self.bind(GradingProtocol, 'run', self.run)
		return self
	
	def run(self, func, obj, messages):
		""" feed test data back to IPython """
		try:
			test, self.tests = self.tests[0], self.tests[1:]
			print('[Notebook] Processing OK test "%s"' % test)
			output = self.capture_output(func, obj, messages)
			self.inject(test, messages['grading'], output)
		except IndexError:
			print('[Notebook] Whoa, rogue test. Not sure what to do with this output: %s' % messages)
		return self
		
	def teardown(self, assign):
		return self
	
	##################
	# HELPER METHODS #
	##################
	
	@shell
	def call(self, *cmd):
		""" Shell command """
		return subprocess.call(cmd)
		
	@shell
	def return_output(self, *cmd):
		""" Get output of shell command """
		return subprocess.check_output(cmd)

	def capture_output(self, func, *args, **kwargs):
		""" Capture output of invoking python function, list of lines """
		class Capturing(list):
			# http://stackoverflow.com/a/16571630/4855984
			def __enter__(self):
				self._stdout = sys.stdout
				sys.stdout = self._stringio = StringIO()
				return self
			
			def __exit__(self, *args):
				self.extend(self._stringio.getvalue().splitlines())
				sys.stdout = self._stdout
				
		with Capturing() as output:
			func(*args, **kwargs)
			
		return output

	def setup_makefile(self):
		""" Setup makefile, mapping python files to notebooks """
		print('[Notebook] Generating makefile dependencies.')
		self.books = books = [
			f.split('.')[0] for f in os.listdir('.')
			if f.endswith('.ipynb')]
		deps = '\n'.join([MAKEFILE_TEMPLATE.format(
			name=f, args=str({"nb": f})) for f in books])
		all = ' '.join(['%s.py' % f for f in books])
		content = 'all: %s\n\n%s' % (all, deps)
		open('makefile', 'w').write(content)
		
	def extract_book(self, name):
		""" Extract python script from IPython source """
		book = '%s.ipynb' % name
		py = '%s.py' % name
		print('[Notebook] Extracting {book} from {py} ...'.format(**locals()))
		cells = json.loads(open(book, 'r').read())['cells']
		self.files[book] = cells
		scripts = [self.extract_lines(cell['source']) 
		           for cell in cells if cell['cell_type'] == 'code']
		script = '\n\n'.join(scripts)
		open(py, 'w').write(script)
		print('[Notebook] Extraction to {py} successful.'.format(py=py))
		
	def extract_lines(self, lines):
		""" Extracts code segment from IPython source block """
		return ''.join([line for line in lines if line[0] != '%'])
	
	def inject(self, test, grade, output):
		""" Inject the test results back into the file. """
		self.results[test] = {
			'grading': grade,
			'output': output
		}


Extension = NotebookExt
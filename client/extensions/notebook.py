"""

Extension for Jupyter Notebook

- prepares makefile dependencies
- convert .ipynb notebooks into .py files
- cache and update python files accordingly

"""
from io import StringIO
import sys
from client.exceptions import OkException

from client.protocols.grading import GradingProtocol
from . import Extension, extension
import json
import os
import subprocess


MAKEFILE_TEMPLATE = """\
{name}.py: {name}.ipynb
	ok --extension notebook --extargs "{args}"
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
	methods = {}
	
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
			print('[Notebook] Whoa, rogue test. Not sure what to do with\
this output: %s' % messages)
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
		data = json.loads(open(book, 'r').read())
		self.files[book], cells = data, data['cells']
		scripts = [self.extract_lines(cell['source'])
		           for cell in cells if cell['cell_type'] == 'code']
		script = '\n\n'.join(scripts)
		open(py, 'w').write(script)
		print('[Notebook] Extraction to {py} successful.'.format(py=py))
		
	def extract_lines(self, lines):
		""" Extracts code segment from IPython source block """
		return ''.join(self.exclude_lines(lines))
	
	def exclude_lines(self, lines):
		""" Filters out specific lines """
		if lines[0].startswith('## ok'):
			return [line for line in lines if line[0] != '%']
		return []
	
	def inject(self, test, grade, output):
		""" Inject the test results back into the file. """
		output_data = {
			"name": "stdout",
			"output_type": "stream",
			"text": [l+'\n' for l in output]
		}
		data = self.get_data_with_method(test)
		filename, cell = data['filename'], data['cell']
		cell['outputs'].append(output_data)
		cell['metadata']['collapsed'] = False
		open(filename, 'w').write(json.dumps(data['file']))
		
	def get_data_with_method(self, method):
		""" Returns filename, cell for method """
		try:
			if method not in self.methods:
				self.reload_methods()
			return self.methods[method]
		except KeyError:
			raise OkException('Cannot find method "%s". This shouldn\'t \
happen. Please create a new issue at \
https://github.com/Cal-CS-61A-Staff/ok-client.' % method)

	def reload_methods(self):
		""" Refresh methods dictionary with all Notebooks """
		print('[Notebook] Examining all notebooks...')
		books = [f for f in os.listdir('.') if f.endswith('.ipynb')]
		self.books, methods = [f.split('.')[0] for f in books], []
		files = {book: json.loads(open(book).read()) for book in books}
		for filename, file in files.items():
			print('[Notebook] Examining "%s"' % filename)
			for cell in file['cells']:
				methods += self.extract_methods(filename, file, self.exclude_lines(cell['source']), cell)
		print('[Notebook] Found %d test cases: %s' % (len(methods), str(methods)))

	def extract_methods(self, filename, file, lines, cell):
		""" Extract all methods from cell text """
		import re
		template = re.compile('(def|class) (.+?)(\(|:)')
		methods = []
		for line in lines:
			match = template.findall(line)
			if len(match) > 0:
				methods.append(match[0][1])
		if 'outputs' in cell:
			cell['outputs'] = []
		for method in methods:
			self.methods[method] = {
				'cell': cell,
			    'file': file,
			    'filename': filename
			}
		return methods

Extension = NotebookExt
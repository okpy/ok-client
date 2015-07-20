"""

Extension for Jupyter Notebook

- prepares makefile dependencies
- convert .ipynb notebooks into .py files
- cache and update python files accordingly

"""

from . import Extension, extension
import json
import os
import subprocess


MAKEFILE_TEMPLATE = """\
{name}.py: {name}.ipynb
	@echo "[Notebook] Extracting {name}.py from {name}.ipynb"
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
	
	######################
	# OBLIGATORY METHODS #
	######################

	def setup(self, assign):
		""" setup dependencies, and cache code blocks """
		if self.args.nb:
			self.terminate_after_setup = True
			self.extract_book(self.args.nb)
		else:
			self.setup_makefile()
			self.call('make', 'all', '--quiet')
		return self
	
	def run(self, assign):
		""" feed test data back to IPython """
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

	def setup_makefile(self):
		""" Setup makefile, mapping python files to notebooks """
		print('[Notebook] Generating makefile dependencies.')
		books = [f.split('.')[0] for f in os.listdir('.') 
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
		cells = json.loads(open(book, 'r').read())['cells']
		scripts = [self.extract_lines(cell['source']) 
		           for cell in cells if cell['cell_type'] == 'code']
		script = '\n'.join(scripts)
		open(py, 'w').write(script)
		
	def extract_lines(self, lines):
		""" Extracts code segment from IPython source block """
		return '\n'.join([line for line in lines if line[0] != '%'])

Extension = NotebookExt
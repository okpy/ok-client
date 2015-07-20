"""

Extension for Jupyter Notebook

- prepares makefile dependencies
- convert .ipynb notebooks into .py files
- cache and update python files accordingly

"""

from . import Extension, extension
import os
import subprocess


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
		else:
			self.setup_makefile()
			self.call('make', 'all')
		return self
	
	def run(self, assign):
		""" feed test data back to IPython """
		return self
		
	def teardown(self, assign):
		return self
	
	##################
	# HELPER METHODS #
	##################
	
	def call(self, *cmd):
		""" Shell command """
		print('[Notebook] %s' % str(cmd))
		print(subprocess.call(cmd))

	def setup_makefile(self):
		""" Setup makefile, mapping python files to notebooks """
		print('[Notebook] Generating makefile dependencies.')
		template = """\
{name}.py: {name}.ipynb
	ok --extension notebook --extargs '{args}'
		"""
		books = [f.split('.')[0] for f in os.listdir('.') if f.endswith('.ipynb')]
		deps = [template.format(name=f, args=str({"nb": f})) for f in books]
		all = ['%s.py' % f for f in books]
		content = 'all: %s\n\n' % ' '.join(all)
		content += '\n'.join(deps)
		open('makefile', 'w').write(content)

Extension = NotebookExt
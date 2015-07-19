"""

Extension for Jupyter Notebook

- prepares makefile dependencies
- convert .ipynb notebooks into .py files
- cache and update python files accordingly

"""

from . import Extension, extension


@extension
class NotebookExt(Extension):
	
	terminate_after_load = True
	cache_dir = 'cache'
	
	######################
	# OBLIGATORY METHODS #
	######################
	
	def parse_args(self, parser):
		""" add custom notebook args """
	
	def setup(self, assign):
		""" setup dependencies, and cache code blocks """
	
	def run(self, assign):
		""" feed test data back to IPython """
		
	def teardown(self, assign):
		pass
	
	##################
	# HELPER METHODS #
	##################
	
	
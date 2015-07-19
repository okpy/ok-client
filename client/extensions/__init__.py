"""

Extensions Manager

"""

import importlib


def load(ext):
	""" Loads the extension """
	module = importlib.import_module(ext)
	return module.Extension()


def extension(cls):
	""" wrapper for all Extensions """
	def Extension(*args, **kwargs):
		return cls(*args, **kwargs)
	return Extension


class Extension:
	""" Base class for all extensions """
	
	_args = None
	terminate_after_load = False
	terminate_after_run = False
	
	def parse_args(self, parser):
		""" optionally add custom args and parse the results """
		return parser.parse_args()
	
	def setup(self, assign):
		""" setup extension """
		raise NotImplementedError()
		
	def run(self, assign):
		""" tell the Extension to do its thing """
		raise NotImplementedError()
	
	def teardown(self, assign):
		""" teardown extension """
		raise NotImplementedError()
"""

Extensions Manager

"""

import importlib
import os


def load(ext, extargs):
	""" Loads the extension """
	module = importlib.import_module('client.extensions.%s' % ext)
	return module.Extension(extargs)


def extension(cls):
	""" wrapper for all Extensions """
	def Extension(*args, **kwargs):
		return cls(*args, **kwargs)
	return Extension


class Namespace:
	
	vars = {}
	
	def __setattr__(self, key, value):
		self.vars[key] = value
		
	def __getattr__(self, key):
		if key not in self.vars:
			return None
		return self.vars[key]


class Extension:
	""" Base class for all extensions """
	
	_args = None
	terminate_after_setup = False
	terminate_after_run = False
	
	def __init__(self, args):
		self.args = Namespace()
		[setattr(self.args, k, v) for k, v in (args or {}).items()]
	
	def setup(self, assign):
		""" setup extension """
		raise NotImplementedError()
		
	def run(self, assign):
		""" tell the Extension to do its thing """
		raise NotImplementedError()
	
	def teardown(self, assign):
		""" teardown extension """
		raise NotImplementedError()
"""

Extensions Manager

"""

import importlib


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
	""" container for all args passed via --extargs"""
	
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
		""" Setup and save namespace """
		self.args = Namespace()
		[setattr(self.args, k, v) for k, v in (args or {}).items()]
	
	def setup(self, *args):
		""" setup extension """
		raise NotImplementedError()
	
	def teardown(self, *args):
		""" teardown extension """
		raise NotImplementedError()

	@staticmethod
	def bind(obj, method_old_name, method_new):
		""" Bind an extension function to an existing function """
		print('[Notebook] Binding function "%s" to "%s"' % (method_new.__name__, method_old_name))
		method_old = getattr(obj, method_old_name)
		
		def replacement(*args, **kwargs):
			return method_new(method_old, *args, **kwargs)
		replacement.__name__ = method_old_name
		setattr(obj, method_old_name, replacement)
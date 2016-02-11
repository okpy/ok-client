import imp
import importlib
import os
import sys

def load_module(filepath):
    module_name = path_to_module_string(filepath)
    module = importlib.import_module(module_name)
    return reload_module(module)

def path_to_module_string(filepath):
    filepath = filepath.replace('.py', '')
    module_components = []
    while filepath:
        filepath, component = os.path.split(filepath)
        module_components.insert(0, component)
    return '.'.join(module_components)

def reload_module(module):
    """Use the correct module to reload an imported module. Since Python 3.4,
    imp.reload has been deprecated in favor of importlib.reload.
    """
    if sys.version_info >= (3, 4, 0):
        importlib.reload(module)
    else:
        imp.reload(module)
    return module

""" This module is used to reload all loaded modules from rollover to in case updates have been 
made. Having this as a separate modules removes unecessary clotter from the real code. 

.. codeauthor:: Knut Andreas Meyer
"""

import sys
import importlib

def execute():
    modules = [m for m in sys.modules.values()]
    for module in modules:
        if not hasattr(module, '__file__'):
            continue
        try:
            if 'rollover' in module.__file__:
                importlib.reload(module)
        except AttributeError:
            pass    # Seems like not all items in sys.modules.values() contain __file__
                    # This is ok, as those containing 'rollover' will. 
        except NameError:
            pass    # Reload only works for python 2 without loading modules
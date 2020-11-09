""" This module is used to reload all loaded modules from rollover to in case updates have been 
made. Having this as a separate modules removes unecessary clotter from the real code. 

.. codeauthor:: Knut Andreas Meyer
"""

import sys

for module in sys.modules.values():
    try:
        if 'rollover' in module.__file__:
            reload(module)
    except AttributeError:
        pass

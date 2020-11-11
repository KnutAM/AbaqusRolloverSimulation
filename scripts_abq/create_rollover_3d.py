"""Create a 3d rollover simulation

The dictionary described by the rollover settings .json file with name
rollover.utils.naming_mod.rollover_settings_file should contain keywords 

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
import sys

from abaqusConstants import *
import interaction

# Reload modules (tmp while developing)
for module in sys.modules.values():
    try:
        if 'rollover' in module.__file__:
            reload(module)
    except AttributeError:
        pass    # Seems like not all items in sys.modules.values() contain __file__
                # This is ok, as those containing 'rollover' will. 
    except NameError:
        pass    # Reload only works for python 2 without loading modules


# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.utils import abaqus_python_tools as apt
from rollover.three_d.rail import include as rail_include
from rollover.three_d.wheel import include as wheel_include
from rollover.three_d.utils import contact
from rollover.three_d.utils import loading

def main():
    # Read in rollover parameters
    param = json_io.read(names.rollover_settings_file)
    
    # Create the model
    rollover_model = apt.create_model(names.model)
    # rollover_model = mdb.models[names.model]
    # Include the rail part
    rail_include.from_file(rollover_model, **param['rail'])
    
    # Include the wheel part
    wheel_stiffness = wheel_include.from_folder(rollover_model, **param['wheel'])
                  
    # Setup contact
    contact.setup(rollover_model, **param['contact'])
    
    # Setup loading steps
    loading.setup(rollover_model, **param['loading'])
    
    # Add wheel uel to input file
    wheel_include.add_wheel_super_element_to_inp(rollover_model, wheel_stiffness)
    
    mdb.saveAs(pathName=names.model)
    
        
if __name__ == '__main__':
    main()

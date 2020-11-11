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
    
    if not check_input(param):
        return
    
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
    
       
def check_input(param):
    
    def get_arguments(function, num_first=0):
        all_arguments = function.__code__.co_varnames[num_first:]
        num_defaults = len(function.__defaults__)
        num_mandatory = len(all_arguments) - num_defaults
        
        mandatory_arguments = [arg for i, arg in enumerate(all_arguments) if i<num_mandatory]
        
        return all_arguments, mandatory_arguments

    def check_param(param, function, num_first=0):
        failed = False
        name = function.__name__
        all, mandatory = get_arguments(function, num_first)
        for marg in mandatory:
            if marg not in param:
                print('Function "' + name + '" requires argument "' + marg + '"')
                failed = True
        for par in param:
            if par not in all:
                print('Function ' + name + ' does not have argument "' + par + '"')
                failed = True
        
        return failed
        
    rail_ok = check_param(param['rail'], rail_include.from_file, num_first=1)
    wheel_ok = check_param(param['wheel'], wheel_include.from_folder, num_first=1)
    contact_ok = check_param(param['contact'], contact.setup, num_first=1)
    loading_ok = check_param(param['loading'], loading.setup, num_first=1)
    
    if not all([rail_ok, wheel_ok, contact_ok, loading_ok]):
        return False
    else:
        return True
        
    
if __name__ == '__main__':
    main()

"""Create a 3d rollover simulation

The dictionary described by the rollover settings .json file with name
rollover.utils.naming_mod.rollover_settings_file should contain keywords 

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function

# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.utils import abaqus_python_tools as apt
from rollover.three_d.rail import include as rail_include
# from rollover.three_d.wheel import include as wheel_include


def main():
    # Read in rollover parameters
    rollover_param = json_io.read(names.rollover_settings_file)
    
    # Create the model
    rollover_model = apt.create_model(names.model)
    
    # Include the rail part
    rail_include.from_file(rollover_model, rollover_param['rail_model_file'], 
                           rollover_param['shadow_extents'])
    
    # Include the wheel part
    
    
if __name__ == '__main__':
    main()

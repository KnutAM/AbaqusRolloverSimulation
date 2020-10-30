"""Running this abaqus script generates a meshed cross-section of a 
3d-wheel. It will read the parameters from 'wheel_section_param.json' 
and output the resulting mesh to 'wheel_section_mesh.npz'. 

The dictionary described by the 'wheel_section_param.json' file should
contain the keywords according to 
:py:func:`rollover.three_d.wheel.create_2d_section_mesh.get_2d_mesh`

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
import sys
import json
import numpy as np

# Abaqus imports 
from abaqusConstants import *
import part

# Project library imports
from rollover.three_d.wheel import create_wheel_mod as wheel
import rollover.utils.abaqus_python_tools as apt
import rollover.utils.naming_mod as names
from rollover.utils import json_io

# Reload is only convenient during development. Should be removed later.
if sys.version_info.major == 3:
    if sys.version_info.minor < 4:
        from imp import reload
    else:
        from importlib import reload
reload(wheel)


def main():
    apt.setup_log_file()
    # Read in wheel section parameters
    wheel_param = json_io.read('wheel_settings.json')
    
    # Setup the wheel model and part
    wheel_model = apt.create_model('WHEEL_SUBSTRUCTURE')
    wheel_part = wheel_model.Part(name=names.wheel_part, dimensionality=THREE_D, 
                                  type=DEFORMABLE_BODY)
    
    # Create the 2d section mesh
    possible_section_param = list(wheel.generate_2d_mesh.__code__.co_varnames)
    possible_section_param.remove('wheel_model')
    wheel_section_param = {key: wheel_param[key] for key in wheel_param 
                           if key in possible_section_param}
    section_bb = wheel.generate_2d_mesh(wheel_model, **wheel_section_param)
    
    # Revolve 2d mesh to obtain 3d mesh
    wheel.generate_3d_mesh(wheel_model, wheel_param['mesh_sizes'])
    
    # Create retained node set
    wheel.create_retained_set(wheel_part, wheel_param['wheel_angles'])
    
    # Create inner node set
    wheel.create_inner_set(wheel_part, section_bb)
    
    job = wheel.setup_substructure_simulation(wheel_model)
    
        
    
if __name__ == '__main__':
    main()

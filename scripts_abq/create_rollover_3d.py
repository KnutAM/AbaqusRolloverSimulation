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

def main():
    # Read in rollover parameters
    rollover_param = json_io.read(names.rollover_settings_file)
    
    # Create the model
    rollover_model = apt.create_model(names.model)
    # rollover_model = mdb.models[names.model]
    # Include the rail part
    rail_include.from_file(rollover_model, rollover_param['rail_model_file'], 
                           rollover_param['shadow_extents'])
    
    # Include the wheel part
    wheel_include.from_folder(rollover_model, rollover_param['wheel_folder'],
                              rollover_param['wheel_translation'])
                              
    test(rollover_model)
    
    # Add wheel uel to input file
    wheel_include.add_wheel_super_element_to_inp(rollover_model, wheel_stiffness=210.e3)
    
    
def test(the_model):
    assy = the_model.rootAssembly
    rail_inst = assy.instances[names.rail_inst]
    wheel_inst = assy.instances[names.wheel_inst]
    
    the_model.StaticStep(name='Step-1', previous='Initial')
    the_model.DisplacementBC(name='BC-1', createStepName='Initial', 
                             region=rail_inst.sets[names.rail_bottom_nodes],
                             u1=0.0, u2=0.0, u3=UNSET)
    
    the_model.DisplacementBC(name='BC-2', createStepName='Step-1', 
                             region=wheel_inst.sets[names.wheel_rp_set], 
                             u1=0.0, u2=-0.2, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)
    
    int_prop = the_model.ContactProperty('IntProp-1')
    int_prop.NormalBehavior(pressureOverclosure=LINEAR, contactStiffness=1000000.0, 
                            constraintEnforcementMethod=DEFAULT)
                            
    the_model.SurfaceToSurfaceContactStd(name='Int-1', createStepName='Initial', 
                                         master=rail_inst.surfaces[names.rail_contact_surf],
                                         slave=wheel_inst.surfaces[names.wheel_contact_surf], 
                                         sliding=FINITE, interactionProperty='IntProp-1')
    
if __name__ == '__main__':
    main()

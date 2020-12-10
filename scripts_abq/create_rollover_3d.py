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


# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.utils import abaqus_python_tools as apt
from rollover.utils import general as gen_tools
from rollover.three_d.rail import include as rail_include
from rollover.three_d.wheel import include as wheel_include
from rollover.three_d.utils import contact
from rollover.three_d.utils import loading
from rollover.three_d.utils import odb_output
from rollover.three_d.utils import fil_output

def main():
    # Read in rollover parameters
    param = json_io.read(names.rollover_settings_file)
    
    if not check_input(param):
        return
    
    # Create the model
    rollover_model = apt.create_model(names.model)
    # rollover_model = mdb.models[names.model]
    print('model created')
    # Include the rail part
    num_nodes, num_elems = rail_include.from_file(rollover_model, **param['rail'])
    print('rail included')
    # Include the wheel part
    wheel_stiffness = wheel_include.from_folder(rollover_model, 
                                                start_labels=(num_nodes+1, num_elems+1),
                                                **param['wheel'])
    print('wheel included')
    # Setup contact
    contact.setup(rollover_model, **param['contact'])
    print('contact setup')
    # Setup loading steps
    num_cycles = loading.setup(rollover_model, **param['loading'])
    print('loading setup')
    # Add odb field output if not standard
    if 'field_output' in param:
        odb_output.add(rollover_model, param['field_output'], num_cycles)
    print('field output setup')
    # Add wheel uel to input file
    wheel_include.add_wheel_super_element_to_inp(rollover_model, wheel_stiffness, 
                                                 param['wheel']['folder'],
                                                 param['wheel']['translation'])
                                                 
    print('wheel included in input')
    # Add results file output
    fil_output.add(rollover_model, num_cycles)
    print('fil output added')
    write_rp_coord(param['wheel']['translation'], [0.0, 0.0, 0.0])
    
    mdb.saveAs(pathName=names.model)
    
    # Create job after saving cae file, because job will not have sufficient options to run from 
    # cae, in particular user subroutine path.
    write_input_file()


def write_input_file():
    the_job = mdb.Job(name=names.job, model=names.model)
    the_job.writeInput(consistencyChecking=OFF)
    

def write_rp_coord(wheel_rp_coord, rail_rp_coord):
    with open(names.rp_coord_file, 'w') as fid:
        fid.write(('%25.15e'*3 + '\n') % tuple(wheel_rp_coord))
        fid.write(('%25.15e'*3 + '\n') % tuple(rail_rp_coord))
    
       
def check_input(param):
    
    def check_param(params, function, num_first=0):
        failed = False
        name = function.__name__
        all_arg, man_arg = gen_tools.get_arguments(function, num_first)
        for marg in man_arg:
            if marg not in params:
                print('Function "' + name + '" requires argument "' + marg + '"')
                failed = True
        for param in params:
            if param not in all_arg:
                print('Function ' + name + ' does not have argument "' + param + '"')
                failed = True
        
        return failed
        
    
    not_ok_list = []
    not_ok_list.append(check_param(param['rail'], rail_include.from_file, num_first=1))
    not_ok_list.append(check_param(param['wheel'], wheel_include.from_folder, num_first=1))
    not_ok_list.append(check_param(param['contact'], contact.setup, num_first=1))
    not_ok_list.append(check_param(param['loading'], loading.setup, num_first=1))
    
    if any(not_ok_list):
        return False
    else:
        return True
        
    
if __name__ == '__main__':
    main()

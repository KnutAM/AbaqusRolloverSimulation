import sys
import os
import numpy as np
import inspect



def create_uel(stiffness_matrix, coords):
    this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
    
    base_file = this_path + '/uel_base_file.f90'
    with open(base_file, 'r') as fid:
        uel_base_str = fid.read()
    
    stiffness_str = get_stiffness_str(stiffness_matrix)
    
    uel_base_str_split = uel_base_str.split('    !<ke_to_be_defined_by_python_script>')
    uel_str = uel_base_str_split[0] + stiffness_str + uel_base_str_split[1]
    with open('uel.for', 'w') as fid:
        fid.write(uel_str)
        
    np.save('uel_coords.npy', coords)


def get_stiffness_str(ke):
    the_str = ''
    for i in range(ke.shape[0]):
        for j in range(ke.shape[1]):
            the_str = the_str + '    ke(%u,%u) = %23.15e\n' % (i+1,j+1,ke[i,j])
    
    return the_str
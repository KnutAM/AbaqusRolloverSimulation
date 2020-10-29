"""Running this python script will create a super wheel element. 

This script takes one input argument: The filepath for a json settings 
file that contain at least the mandatory inputs to 
:py:func:`rollover.three_d.wheel.create_2d_section_mesh.get_2d_mesh`

Note that in the json format booleans are given as true/false, None as 
null, and strings must have double quotes ("). File paths on Windows 
should either have escaped backslashes or replace backslashes with 
forward slashes. 

.. codeauthor:: Knut Andreas Meyer
"""
# System imports
from __future__ import print_function
import os, sys
import uuid
import json
import numpy as np


def main(settings_file):
    settings = get_settings(settings_file)
    
    section_mesh = get_section_mesh(settings)
    '''
    three_d_mesh = get_three_d_mesh(settings, section_mesh)
    
    abq_input = get_input_str(settings, three_d_mesh)
    
    ke = get_stiffness_matrix(abq_input)
    
    save_uel(settings, ke, three_d_mesh)
    '''
    
def get_settings(settings_file):
    with open(settings_file, 'r') as fid:
        return json.load(fid)
    
    
def get_section_mesh(settings):
    
    # Determine required paths
    rollover_repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_abq_path = rollover_repo_path + '/scripts_abq'
    
    # Setup temporary directory to run Abaqus in
    tmpdir = str(uuid.uuid4())
    os.mkdir(tmpdir)
    os.chdir(tmpdir)
    
    # Add required files and run Abaqus
    create_abaqus_env_file(rollover_repo_path)
    section_param = {key: settings[key] for key in settings if key in 
                     ['wheel_profile', 'mesh_sizes', 'wheel_contact_pos', 'partition_line', 
                     'fine_mesh_edge_bb', 'quadratic_order']}
    with open('wheel_section_param.json', 'w') as fid:
        json.dump(section_param, fid, indent=4)
    
    os.system('abaqus cae noGUI=' + script_abq_path + '/wheel_section_mesh.py')
    
    # Read results
    section_mesh = {}
    with np.load('wheel_section_mesh.npz', allow_pickle=False) as npz:
        for key in npz:
            print(key)
            section_mesh[key] = npz[key]
    
    return section_mesh
    
    
def create_abaqus_env_file(append_directory):
    with open('abaqus_v6.env', 'w') as fid:
        fid.write('import sys\n'
                  + 'if not "' + append_directory + '" in sys.path:\n'
                  + '    sys.path.append("' + append_directory + '")\n')
    
   
def get_three_d_mesh(settings, section_mesh):
    """ Convert the 2d section mesh to a revolved 3d wheel. 
    """
    # Determine element order
    num_tri_elems = 0
    num_quad_elems = 0
    if len(section_mesh['TRI_elements']) > 0:
        element_order = 1 if section_mesh['TRI_elements'].shape[1] == 3 else 2
        num_tri_elems = section_mesh['TRI_elements'].shape[0]
    elif len(section_mesh['QUAD_elements']) > 0:
        element_order = 1 if section_mesh['QUAD_elements'].shape[1] == 4 else 2
        num_quad_elems = section_mesh['QUAD_elements'].shape[0]
    else:
        raise ValueError('No elements defined in section_mesh')
        
    coords_2d = section_mesh['node_coords']
    num_nodes_in_sect = coords_2d.shape[0]
    fine_mesh_size = settings['mesh_sizes'][0]/element_order
    
    # Get largest radius as maximum absolute y-value
    outer_radius = np.max(np.abs(coords_2d[:,1]))
    
    # Calculate number of angles
    num_angles = element_order * np.ceil(2 * outer_radius * np.pi / fine_mesh_size)
    angles = np.linspace(0, 2 * np.pi, num_angles + 1)[:-1]
    
    # Calculate the nodal positions
    num_nodes = num_angles * num_nodes_in_sect
    coords = np.zeros((num_nodes, 3))
    x0 = coords_2d[:,0]
    # y-axis is radius direction, ensure that radius is positive
    r0 = np.abs(coords_2d[:,1])
    
    for iang, angle in enumerate(angles):
        sect_num = np.arange(num_nodes_in_sect)
        node_nums = get_node_num(sect_num, iang, num_nodes_in_sect, num_angles)
        # Calculate coordinates for rotation about x-axis.
        # angle=0 imply negative y-direction
        coords[node_nums, 0] = x0                     # x
        coords[node_nums, 1] = -r0 * np.cos(angle)    # y
        coords[node_nums, 2] = -r0 * np.sin(angle)    # z
    
    # Get elements
    num_wedge_elems = num_tri_elems * num_angles / element_order
    iwedge = 0
    for iang, _ in enumerate(angles):
        for tri_elem in section['TRI_elements']:
            
        
    
    
    num_hex_elems = num_quad_elems * num_angles / element_order
        
    
def get_node_num(sect_num, ang_num, num_in_sect, num_angs):
    """Given a node number in the section, and the angle number, return 
    the global node number. The node number is calculated as 
    sect_num + ang_num*num_in_sect. Kept as separate function for 
    clarity and possibility to change convention if desired. 
    
    :param sect_num: Node number in the section mesh
    :type sect_num: int, np.array
    
    :param ang_num: Which angle number in the 360 revolution, starting 
                    at 0
    :type ang_num: int, np.array
    
    :param num_in_sect: Number of nodes in the section
    :type num_in_sect: int, np.array
    
    :param num_angs: Number of angles in the 360 revolution
    :type num_angs: int, np.array
    
    :returns: The node number in the 3d mesh
    :rtype: int, np.array

    """
    
    # Support ang_num >= num_angs to facilitate getting connectivity in 
    # the angular direction
    if isinstance(ang_num, np.ndarray):
        ang_num[ang_num >= num_angs] = ang_num[ang_num >= num_angs] - num_angs
    else:
        if ang_num >= num_angs:
            ang_num -= num_angs
            
    return sect_num + ang_num*num_in_sect    
    
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise IOError('The filepath to the *.json input file must be given as input')
    
    main(settings_file = sys.argv[1])

from __future__ import print_function
import numpy as np
import os, inspect, sys, json, shutil
from datetime import datetime


this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not this_path in sys.path:
    sys.path.append(this_path)
    
import wheel_mesh_tb

default_wheel_settings = {'mesh_size': 6.0,
                          'outer_diameter': 400.0,
                          'inner_diameter': 200.0,
                          'output_directory': this_path + '/../../super_wheels'
                          }

# Set default rolling_angle such that max rolling length (incl. slip) is 40 mm
default_wheel_settings['rolling_angle'] = 40.0/(default_wheel_settings['outer_diameter']/2.0)
# Set default contact_angle such that max contact size is 20 mm
default_wheel_settings['contact_angle'] = (default_wheel_settings['rolling_angle'] +
                                           20.0/(default_wheel_settings['outer_diameter']/2.0))

def set_default_options(wheel_settings):
    for key in default_wheel_settings:
        if not key in wheel_settings:
            wheel_settings[key] = default_wheel_settings[key]
    

def create_super_element(**kwargs):
    wheel_settings = {}
    for key, value in kwargs.items():
        if key in default_wheel_settings:
            wheel_settings[key] = value
        else:
            print('WARNING: the key ' + key + ' is not understood and will be ignored')
            
    set_default_options(wheel_settings)
    # Setup names and directories
    job_name = 'super_wheel_sim'
    tempdir = 'temporary_super_wheel_simulation_directory'
    od, id, ms = [wheel_settings[key] for key in ['outer_diameter', 'inner_diameter', 'mesh_size']]
    save_dir = (wheel_settings['output_directory'] + 
                'OD%u_ID%u_M%02up%03u' % (od, id, int(ms), 1000*int(ms-int(ms))) )
    
    # Setup temporary folder to run simulation in 
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)
    os.mkdir(tempdir)
    
    # Run abaqus substructure simulation
    os.chdir(tempdir)
    create_input_file_2d(job_name + '.inp', wheel_settings)
    cmd = 'abaqus' + ' job=' + job_name + ' ask_delete=OFF' + ' interactive'
    os.system(cmd)
    # Postprocess results
    Kred, coords = get_stiffness_from_substructure_mtx_file(job_name)
    os.chdir('..')
    
    # Save results
    create_uel(Kred, coords)
    save_wheel_data_to_json(wheel_settings)
    
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        
    for file in ['uel.for', 'uel_coords.npy', 'uel_info.json']:
        os.rename(file, save_dir + '/' + file)
    
    # Clean up temporary directory
    shutil.rmtree(tempdir)
    
    
def save_wheel_data_to_json(wheel_settings):
    with open('uel_info.json', 'w') as fid:
        json.dump(wheel_settings, fid, indent=4)
    
    
def clean_files(job_name):
    all_files_in_cwd = [f for f in os.listdir('.') if os.path.isfile(f)]
    for file in all_files_in_cwd:
        if job_name in file:
            os.remove(file)
            
    try:
        os.remove('uel_coords_tmp.npy')
    except FileNotFoundError:
        pass
    
    
def delete_all_old_files(job_name):
    clean_files(job_name)
    for file in ['uel.for', 'uel.f', 'uel_coords.npy', 'uel_info.json']:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
            

def create_input_file_2d(filename, wheel_settings):
    elem_and_nods = get_nodes_and_elements(wheel_settings)
    nodes, elem_nods, inner_node_nrs, contact_node_nrs = elem_and_nods
    write_input_file(filename, wheel_settings, nodes, elem_nods, inner_node_nrs, contact_node_nrs)


def get_nodes_and_elements(wheel_settings):
    mesh_size = wheel_settings['mesh_size']
    outer_dia = wheel_settings['outer_diameter']
    inner_dia = wheel_settings['inner_diameter']
    contact_angle = wheel_settings['contact_angle']
    rolling_angle = wheel_settings['rolling_angle']
    
    # Calculate number of elements around circumference. Multiple of 4 to ensure symmetry.
    nel_circumf = 4*int(outer_dia*np.pi/(4.0*mesh_size))
    angles = np.linspace(0, 2*np.pi, nel_circumf + 1)[:-1]  # Remove last element that is duplicated
    radii, nel_radial = wheel_mesh_tb.get_radial_node_pos(inner_dia, outer_dia, mesh_size)
    nel = nel_circumf*nel_radial
    nnod = nel_circumf*(nel_radial+1)
    nodes = np.zeros((nnod,2))
    elem_nods = np.zeros((nel,4), dtype=np.int)
    
    for ir, r in zip(range(nel_radial+1), radii):
        for ic, a in zip(range(nel_circumf), angles):
            x = r*np.cos(a)
            y = r*np.sin(a)
            node_nr = wheel_mesh_tb.get_node_nr(ir, ic, nel_radial, nel_circumf)
            nodes[node_nr, :] = np.array([x, y])
    
    for ir in range(nel_radial):
        for ic in range(nel_circumf):
            enodes = wheel_mesh_tb.get_elem_node_nrs(ir, ic, nel_radial, nel_circumf)
            eind = wheel_mesh_tb.get_elem_nr(ir, ic, nel_radial, nel_circumf)
            elem_nods[eind, :] = np.array(enodes)
    
    
    
    inner_node_nrs = [wheel_mesh_tb.get_node_nr(nel_radial, ic, nel_radial, nel_circumf)
                   for ic in range(nel_circumf)]
    contact_node_nrs = []
    for ic in range(nel_circumf):
        node_nr = wheel_mesh_tb.get_node_nr(0, ic, nel_radial, nel_circumf)
        coords = nodes[node_nr, :]
        angle = get_angle_to_minus_y(coords)
        if np.abs(angle - rolling_angle/2.0) <= contact_angle/2.0:
            contact_node_nrs.append(node_nr)

    contact_node_coords = np.transpose([nodes[node_nr, :] for node_nr in contact_node_nrs])
    np.save('uel_coords_tmp.npy', contact_node_coords)

    return nodes, elem_nods, inner_node_nrs, contact_node_nrs
    
    
def get_angle_to_minus_y(coords):
    return np.arctan2(-coords[0], -coords[1])
    
def write_input_file(filename, info, nodes, elem_nods, inner_node_nrs, contact_node_nrs):
    nu = 0.3    # Poissons ratio
    
    with open(filename, 'w') as inp:
        #Name of current file
        this_file = os.path.basename(os.path.abspath(inspect.getfile(lambda: None)))
        inp.write('*Heading\n')
        inp.write('** Input file to create superelement for wheel automatically generated by \n' + 
                  '** ' + this_file + '\n')
        inp.write('** Input file created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
        for key in info:
            inp.write('** ' + key + ' = ' + str(info[key]) + '\n')
        inp.write('*Preprint, echo=NO, model=NO, history=NO, contact=NO\n')
        
        # Wheel nodes
        inp.write('*Node\n')
        for nind, row in enumerate(nodes):
            inp.write('%10.0f' % (nind+1))
            for coord in row:
                inp.write(', %25.15e' % coord)
            inp.write('\n')
        
        # Wheel elements
        inp.write('*Element, type=CPS4R\n')
        for eind, row in enumerate(elem_nods):
            inp.write('%10.0f' % (eind + 1))
            for nind in row:
                inp.write(', %10.0f' % (nind + 1))
            inp.write('\n')
            
        # Reference node
        inp.write('*Node\n')
        inp.write('%10.0f, 0.0, 0.0, 0.0\n' % (nodes.shape[0] + 1))
        inp.write('*Nset, nset=RP\n')
        inp.write('%10.0f,\n' % (nodes.shape[0] + 1))
        
        # Inner circle node set
        inp.write('*Nset, nset=SUPER_WHEEL_INNER_CIRCLE, generate\n')
        inp.write('%10.0f, %10.0f, 1\n' % (np.min(inner_node_nrs)+1, np.max(inner_node_nrs)+1))
        
        # Contact node set
        inp.write('*Nset, nset=SUPER_WHEEL_CONTACT_NODES\n')
        contact_node_str = ''
        num_on_line = 0
        for cn_ind in contact_node_nrs:
            contact_node_str = contact_node_str + '%0.0f, ' % (cn_ind+1)
            num_on_line = num_on_line + 1
            if num_on_line >= 16:
                contact_node_str = contact_node_str + '\n'
                num_on_line = 0
                
        inp.write(contact_node_str[:-2] + '\n')
        
        # All elements set
        inp.write('*Elset, elset=AllElements, generate\n')
        inp.write('%10.0f, %10.0f, %10.0f\n' % (1, elem_nods.shape[0], 1))
        
        # Section
        inp.write('*Solid Section, elset=AllElements, material=Elastic\n,\n')
        
        # Constraints
        inp.write('*System\n')
        inp.write('*Rigid Body, ref node=RP, tie nset=SUPER_WHEEL_INNER_CIRCLE\n')
        
        # Materials
        inp.write('*Material, name=Elastic\n')
        inp.write('*Elastic\n')
        inp.write('1.0, %0.5f\n' % nu)
        
        # Step definition
        inp.write('*Step, name=Step-1, nlgeom=NO\n')
        inp.write('*Substructure Generate, overwrite, type=Z1, recovery matrix=YES\n')
        inp.write('*Damping Controls, structural=COMBINED, viscous=COMBINED\n')
        inp.write('*Retained Nodal Dofs\n')
        inp.write('SUPER_WHEEL_CONTACT_NODES, 1, 2\n')
        inp.write('RP, 1, 2\n')
        inp.write('RP, 6, 6\n')
        inp.write('*SUBSTRUCTURE MATRIX OUTPUT, STIFFNESS=YES, OUTPUT FILE=USER DEFINED,' + 
                  ' FILE NAME=' + filename.split('.')[0] + '\n')
        inp.write('*End Step\n')
        
        
def get_stiffness_from_substructure_mtx_file(filename):
    with open(filename + '.mtx', 'r') as mtx:
        mtx_str = mtx.read()

    mat_str = mtx_str.split('*MATRIX,TYPE=STIFFNESS')[-1].strip(',').strip('\n')
    mat_vec = []
    for entry in mat_str.split():
        ent = entry.strip(',').strip('\n')
        try:
            mat_vec.append(float(ent))
        except ValueError:
            pass

    mat_vec = np.array(mat_vec)
    ndof = -0.5+np.sqrt(0.25+mat_vec.size*2)
    if np.abs(ndof-int(ndof)) < 1.e-10:
        ndof = int(ndof)
    else:
        print('Error reading matrix from ' + filename + '.mtx')
        return None
    
    kmat = np.zeros((ndof,ndof))
    k = 0
    for i in range(ndof):
        for j in range(i+1):
            kmat[i,j] = mat_vec[k]
            kmat[j,i] = kmat[i,j]
            k = k + 1
    
    # Reorder matrix (this is a bit risky, as we don't check with the input file)
    # A check with the input file could be made later in combination with reading the 
    # ELEMENT NODES part of the <filename>.mtx file.
    re_order = [ndof-3,ndof-2,ndof-1]
    for i in range(ndof-3):
        re_order.append(i)
    
    re_order = np.array(re_order, dtype=np.int)
    kmat = kmat[np.ix_(re_order, re_order)]
    coords = np.load('uel_coords_tmp.npy')
    
    print('Checking stiffness matrix:')
    check_stiffness_matrix(kmat, coords)
    
    return kmat, coords
    
    
def check_stiffness_matrix(kmat, coords):
    kcheck = kmat[3:,3:]
    check_rbm_x = np.abs(kmat[:, 0] + np.sum(kmat[:, 3::2], axis=1))
    check_rbm_y = np.abs(kmat[:, 1] + np.sum(kmat[:, 4::2], axis=1))
    ndof = kmat.shape[0]
    unit_ur = np.zeros((ndof))
    unit_ur[2] = 1.0
    rx = coords[0, :]
    ry = coords[1, :]
    unit_ur[3::2] = -ry # x-displacement for pure (unit) rotation
    unit_ur[4::2] = rx  # y-displacement for pure (unit) rotation
    check_rbm_rot = np.dot(kmat, unit_ur)
    cond = np.linalg.cond(kcheck)
    symnorm = np.linalg.norm(np.transpose(kmat)-kmat)/np.linalg.norm(kmat)
    stiffness_ok = (cond < 1.e4)    # Nodal output typically single precision
    if cond > 1.e12:
        print('stiffness NOT OK, check for errors')
    elif cond > 1.e4:
        print('stiffness matrix badly conditioned, consider double precision for nodal output')
    
    # Put check to a non-conservative level (1e-4) to avoid output. But this seems rather high.
    # However, in the fortran uel code, the forces are calculated by considering displacements
    # relative the central node, hence the rbm are small and should not pose a numerical problem. 
    if any(np.array([np.max(check_rbm_x), np.max(check_rbm_y), np.max(check_rbm_rot)]) > 1.e-3):
        print('stiffness matrix sensitive to rbm')
        for n, v in enumerate(check_rbm_x):
            print('K*u [' + str(n) + '] for ux=1: %10.3e' % v)
        for n, v in enumerate(check_rbm_y):
            print('K*u [' + str(n) + '] for uy=1: %10.3e' % v)
        for n, v in enumerate(check_rbm_rot):
            print('K*u [' + str(n) + '] for ur=1: %10.3e' % v)
        
    print('determinant  = %10.3e' % np.linalg.det(kcheck))
    print('condition nr = %10.3e' % cond)
    print('|K-K^T|/|K|  = %10.3e' % symnorm)
    print('max rbm x effect = %10.3e' % np.max(check_rbm_x))
    print('max rbm y effect = %10.3e' % np.max(check_rbm_y))
    print('max rbm rot effect = %10.3e' % np.max(check_rbm_rot))
    
    
def create_uel(stiffness_matrix, coords):
    # Need to save this first as loadmod.get_preposition_motion require this file to exist.
    np.save('uel_coords.npy', coords)
    
    this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
    
    base_file = this_path + '/uel_base_file.f90'
    with open(base_file, 'r') as fid:
        uel_str = fid.read()
    
    # Rotate stiffness and coordinates to account for rotation during prepositioning
    # rotation_angle, translation_vector = get_preposition_motion()
    # krot = rotate_stiffness(stiffness_matrix, rotation_angle)
    # coords_rot = rotate_and_translate_coordinates(coords, rotation_angle, translation_vector)
    
    stiffness_str = get_stiffness_str(stiffness_matrix)
    uel_str = uel_str.split('    !<ke_to_be_defined_by_python_script>')
    uel_str = uel_str[0] + stiffness_str + uel_str[1]
    
    coord_str = get_coord_str(coords)
    uel_str = uel_str.split('    !<coords_to_be_defined_by_python_script>')
    uel_str = uel_str[0] + coord_str + uel_str[1]
    
    with open('uel.for', 'w') as fid:
        fid.write(uel_str)


def get_stiffness_str(ke):
    the_str = ''
    for i in range(ke.shape[0]):
        for j in range(ke.shape[1]):
            the_str = the_str + '    ke(%u,%u) = %23.15e\n' % (i+1,j+1,ke[i,j])
    
    return the_str
    

def get_coord_str(coords):
    the_str = '    allocate(coords(%u, %u))\n' % (coords.shape[0], coords.shape[1])
    for n, coord in enumerate(np.transpose(coords)):
        for i, c in enumerate(coord):
            the_str = the_str + '    coords(%u,%u) = %23.15e\n' % (i+1, n+1, c)
    
    return the_str
    
if __name__ == '__main__':
    create_super_element()
    
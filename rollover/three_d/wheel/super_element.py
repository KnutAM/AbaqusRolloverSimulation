"""Analyze the results from a wheel substructure and create the 
necessary data structures to setup the user element implementation

.. codeauthor:: Knut Andreas Meyer
"""

# Python imports
from __future__ import print_function
import numpy as np

# Abaqus imports
from abaqusConstants import *

# Project imports
import rollover.utils.abaqus_python_tools as apt
import rollover.utils.naming_mod as names

def get_uel_mesh(rp_coord_file='rp_coord.txt', 
                 contact_node_base_file='contact_node', 
                 section_contact_node_base_file='section_contact_node', 
                 mtx_file='ke'):
    """Determine the mesh from the substructure simulation
    
    :returns: ?
    :rtype: ?

    """
    
    ke_raw = get_stiffness(mtx_file)
    rp_nr, contact_node_labels = get_mtx_nodes(mtx_file)
    ke = reorder_stiffness(ke_raw, rp_nr)
    # rp_coord = get_rp_coord(rp_coord_file)
    coords = get_node_coords(contact_node_base_file, contact_node_labels)
    
    elements = get_element_connectivity(coords)
    
    return coords, elements
    
    
def get_stiffness(mtx_file):
    """Extracts the stiffness from the mtx file "`mtx_file`.mtx".
    
    :returns: The stiffness matrix
    :rtype: np.array

    """
    
    with open(mtx_file + '.mtx', 'r') as mtx:
        mtx_str = mtx.read()

    mat_str = mtx_str.split('*MATRIX,TYPE=STIFFNESS')[-1].split('*')[0].strip(',').strip('\n')
    mat_vec = []
    for entry in mat_str.split():
        ent = entry.strip(',').strip('\n')
        try:
            mat_vec.append(float(ent))
        except ValueError as e:
            if len(ent) == 0:
                pass
            else:
                print('Cannot convert "' + ent + '" to a float')
                raise e

    mat_vec = np.array(mat_vec)
    ndof = -0.5+np.sqrt(0.25+mat_vec.size*2)
    if np.abs(ndof-int(ndof)) < 1.e-10:
        ndof = int(ndof)
    else:
        print('Error reading matrix from ' + mtx_file + '.mtx')
        return None
    
    kmat = np.zeros((ndof,ndof))
    k = 0
    for i in range(ndof):
        for j in range(i+1):
            kmat[i,j] = mat_vec[k]
            kmat[j,i] = kmat[i,j]
            k = k + 1
            
    return kmat


def get_mtx_nodes(mtx_file):
    """Extracts the node labels from the mtx file. Note, node numbers
    starts from zero, while node labels starts from 1. 
    
    :returns: List with items
    
              - Element node number for reference point node (int)
              - np.array of contact node labels corresponding to the 
                node labels in `contact_nodes.txt`
              
    :rtype: list

    """
    
    with open(mtx_file + '.mtx', 'r') as mtx:
        # Skip the introduction
        line = mtx.readline()
        while not line.startswith('** ELEMENT NODES'):
            line = mtx.readline()
        
        # Read the element nodes category
        line = mtx.readline()
        node_str = ''
        while line.startswith('**'):
            node_str = node_str + line[2:]
            line = mtx.readline()
            
        node_inds = [int(n) for n in node_str.split(',')]
        
        # Read the node dofs to determine which node is the reference 
        # point
        node_dofs = []
        node_dofs_ind = 0
        while not line.startswith('*'):
            node_dofs.append([int(s) for s in line.split(',')])
            if len(node_dofs[-1]) == 7: # All disp and rotations
                rp_dof_ind = node_dofs_ind
            node_dofs_ind += 1
            line = mtx.readline()
        
        rp_node_nr = node_dofs[rp_dof_ind][0] - 1
        
        contact_nodes = [node_ind for i, node_ind in enumerate(node_inds) if i != rp_node_nr]
        
        return rp_node_nr, contact_nodes


def reorder_stiffness(ke_raw, rp_nr):
    """Reorder the stiffness such that the dofs related to the reference
    point comes first. The order of the remaining nodes is unaffacted.
    
    :param ke_raw: Unordered stiffness matrix
    :type ke_raw: np.array
    
    :param rp_nr: Node number in the element for the reference point
    :type rp_nr: int
    
    :returns: Ordered stiffness matrix
    :rtype: np.array

    """
    ndof_trans = 3
    ndof_rot = 3
    
    ndof = ke_raw.shape[0]
    nnods = (ndof - ndof_rot)/ndof_trans    # Number of nodes incl. rp
    print(ndof)
    print(nnods)
    # Add the dofs for the reference point first
    reorder = [ndof_trans*rp_nr + i for i in range(ndof_trans+ndof_rot)]
    
    # Then add all nodes that previously were before the rp
    for node_nr in range(rp_nr):
        for dof_nr in range(ndof_trans):
            reorder.append(node_nr*ndof_trans + dof_nr)
    
    # Finally add nodes that previously were after the rp
    for node_nr in range(rp_nr+1, nnods):
        for dof_nr in range(ndof_trans):
            reorder.append(ndof_rot + node_nr*ndof_trans + dof_nr)
    
    reorder = np.array(reorder, dtype=np.int)
    
    return ke_raw[np.ix_(reorder, reorder)]


def get_node_coords(base_file_name, contact_node_labels=None):
    """ {TEST} 
    
    """
    coords = np.load(base_file_name + '_coords.npy')
    labels = list(np.load(base_file_name + '_labels.npy'))
    
    if contact_node_labels is not None:
        sort_inds = np.array([labels.index(label) for label in contact_node_labels], dtype=np.int)
        coords = coords[sort_inds]
        
    return coords


def get_element_connectivity(coords):
    """ Knowing that the mesh is revolved around the x-axis and that 
    we only have coordinates of the contact nodes. Create the element
    connectivity (which nodes belong to which element) for the quoad
    mesh.
    
    """
    
    # Create an index matrix where the row goes along the section and
    # the column along the angular direction.
    index_matrix = get_mesh_inds(coords)
    elems = []
    for row1, row2 in zip(index_matrix[:-1], index_matrix[1:]):
        for inds in zip(row1[:-1], row1[1:], row2[1:], row2[:-1]):
            elems.append(inds)
    
    return elems
    
    
def get_mesh_inds(coords):
    TOL = 1.e-3
    
    # Get angle around the x-axis, measured from the negative y-axis
    angles = np.arctan2(-coords[:, 2], -coords[:, 1])
    print(angles)
    # Get radius and x-position
    radii = np.sqrt(coords[:, 1]**2 + coords[:, 2]**2)
    xcoords = coords[:, 0]
    
    ang_tol = TOL/np.max(radii)
    unique_angles = get_unique(angles, ang_tol)
    unique_xcoords = get_unique(xcoords, TOL)
    
    with open('tmp.txt', 'w') as fid:
        fid.write(('%10.4f'*len(unique_angles)) % tuple(unique_angles*180/np.pi) + '\n')
        fid.write(('%10.4f'*len(unique_xcoords)) % tuple(unique_xcoords) + '\n')
        fid.write('x-coordinates [mm]\n')
        for x in xcoords:
            fid.write('%10.4f' % x + '\n')
        fid.write('angles [deg]\n')
        for a in angles:
            print(a)
            fid.write('%10.4f' % (a*180/np.pi) + '\n')
            
    index_matrix = []
    for ang in unique_angles:
        index_matrix.append([])
        for xcoord in unique_xcoords:
            coord_index = find_coord(find_coords=(ang, xcoord), search_coords=(angles, xcoords),
                                     tol=[ang_tol, TOL])
            index_matrix[-1].append(coord_index)
    
    return np.array(index_matrix)
    
    
def get_unique(vector, tol=0):
    
    sorted = np.sort(vector)
    unique_vals = []
    current_vals = [sorted[0]]
    for v in sorted[1:]:
        if v > current_vals[0] + tol:
            unique_vals.append(np.average(current_vals))
            current_vals = [v]
        else:
            current_vals.append(v)
    unique_vals.append(np.average(current_vals))
    
    return np.array(unique_vals)


def find_coord(find_coords, search_coords, tol=0.0):
    """ Find the index for the coordinate in search_coords that matches
    the coordinate find_coords. 
    
    :param find_coords: Coordinates for the point to find
    :type find_coords: tuple[ float ]
    
    :param search_coords: Coordinate lists to be searched through for 
                          match. Length of tuple must match 
                          `find_coords`
    :type search_coords: tuple[ np.array ]
    
    :param tol: Tolerance for the found coordinate to be considered a 
                match. If tuple, the length must match `find_coords`
    :type tol: float / tuple[ float ]
    
    :returns: Index of the found coordinate
    :rtype: int
    
    """
    
    if isinstance(tol, float):
        tol_list = [tol for _ in find_coords]
    else:
        tol_list = tol[:]
    
    logical_array = [True for _ in search_coords[0]]
    for find_coord, search_coord, the_tol in zip(find_coords, search_coords, tol_list):
        logical_array *= np.abs(find_coord - search_coord) < the_tol
    
    indices = np.argwhere(logical_array).flatten()
    if indices.shape[0] > 1:
        print('Warning: find_coord found multiple coordinates. Taking the smallest')
        errors = np.abs(find_coords[0][indices] - search_coords[0][indices])/tol_list[0]
        for find_coord, search_coord, the_tol in zip(find_coords[1:], search_coords[1:], 
                                                     tol_list[1:]):
            errors += np.abs(find_coord[indices] - search_coord[indices])/the_tol
        index = indices[np.argmin(errors)]
    elif indices.shape[0] < 1:
        raise ValueError('Could not identify a matching coordinate, choose a larger tolerance or '
                         + 'check that a matching coordinate exists')
    else:
        index = indices[0]
        
    return index
    
    
def test_part(coords, element_connectivity):
    wheel_model = apt.create_model('WHEEL_TEST_IMP')
    wheel_part = wheel_model.Part(name=names.wheel_part, dimensionality=THREE_D, 
                                  type=DEFORMABLE_BODY)
    nodes = [wheel_part.Node(coordinates=coord) for coord in coords]
    elems = []
    for ec in element_connectivity:
        enodes = [nodes[i] for i in ec]
        elems.append(wheel_part.Element(nodes=enodes, elemShape=QUAD4))
    
    
""" This module is used to generate a 3d mesh based on a 2d section in
the xy-plane that is revolved around the x-axis. Note that only 
quadratic elements are supported. For linear elements, Abaqus' builtin
routine works reasonably well (although the node coordinate accuracy 
seem a bit low), see 
:py:func:`~rollover.three_d.wheel.substructure.generate_3d_mesh`

"""
from __future__ import print_function
import numpy as np


from rollover.utils import naming_mod as names

def generate(wheel_model, mesh_size):
    """ Based on a meshed 2d-profile of a wheel, generate a 3d-revolved
    mesh with angular spacing such that the elements on the outer radius 
    have a circumferential size of mesh_size.
    
    :param wheel_model: A model that contains a wheel part with a 2d 
                        section mesh
    :type wheel_model: Model object (Abaqus)
    
    :param mesh_size: The mesh size to decide the angular increments
    :type mesh_size: float
    
    :returns: The wheel part and the angles for the element end planes
    :type: tuple( Part object(Abaqus), np.array )
    
    """
    
    wheel_part = wheel_model.parts[names.wheel_part]
    # 1) Extract the 2d mesh
    mesh_2d = get_2d_mesh(wheel_part)
    
    # 2) Create the 3d-mesh
    mesh_3d = make_3d_mesh_quad(mesh_2d, mesh_size)
    
    # 3) Save the 3d-mesh to a part definition in an abaqus input file
    input_file = save_3d_mesh_to_inp(mesh_3d)
    
    # 4) Import the mesh. Delete the old part, and import the 3d mesh
    del wheel_model.parts[names.wheel_part]
    
    wheel_model.PartFromInputFile(inputFileName=input_file)
    wheel_part = wheel_model.parts[names.wheel_part]
    return wheel_part, mesh_3d['angles']
    

def get_2d_mesh(wheel_part):
    """ Based on the wheel part, determine the 2d mesh information
    
    :param wheel_part: The wheel part containing the 2d mesh
    :type wheel_part: Part object (Abaqus)
    
    :returns: Mesh specification with the following fields:
              
              - nodes: np.array with node coordinates
              - elements: dictionary with keys according to number of 
                nodes in element: N3,N4,N6,N8. Each item contains a list
                of list of node labels
              - edge_nodes: list of labels of nodes that belong to the 
                edges of the elements (and not the corners)
              - corner_nodes: list of labels of nodes that belong to the
                corners of the elements. 
    :rtype: dict
    
    """
    node_coords = np.array([n.coordinates for n in wheel_part.nodes])
    elements = {'N3': [], 'N4': [], 'N6': [], 'N8': []}
    edge_nodes = []
    corner_nodes = []
    for e in wheel_part.elements:
        enods = e.connectivity
        num_enods = len(enods)
        key = 'N' + str(num_enods)
        if key in elements:
            elements[key].append(enods)
        else:
            raise ValueError('Unknown element type with '
                             + str(num_enods) + ' nodes.\n'
                             + '- Element label: ' + e.label + '\n'
                             + '- Element nodes: ' + enods + '\n'
                             + '- Element type : ' + e.type + '\n')
        if num_enods > 4:   # 2nd order, second half of nodes on edges
            for n in enods[:num_enods/2]:
                if n not in corner_nodes:
                    corner_nodes.append(n)
            for n in enods[num_enods/2:]:
                if n not in edge_nodes:
                    edge_nodes.append(n)
        else:               # 1st order elements, all nodes at corners
            for n in enods:
                if n not in corner_nodes:
                    corner_nodes.append(n)
    
    the_mesh = {'nodes': node_coords, 'elements': elements,
                'edge_nodes': edge_nodes, 'corner_nodes': corner_nodes}
    
    return the_mesh
    

def make_3d_mesh_quad(mesh_2d, mesh_size):
    """ Revolve a 2d-mesh into a 3d-mesh 
    
    :param mesh_2d: Mesh specification with the following fields:
              
                    - nodes: np.array with node coordinates
                    - elements: dictionary with keys according to number 
                      of nodes in element: N3,N4,N6,N8. 
                      Each item contains a list of list of node labels
                    - edge_nodes: list of labels of nodes that belong to 
                      the edges of the elements (and not the corners)
                    - corner_nodes: list of labels of nodes that belong 
                      to the corners of the elements. 
    :type mesh_2d: dict
    
    :param mesh_size: The circumferential mesh size at largest radius
    :type mesh_size: float
    
    :returns: Mesh specification with the following fields:
              
              - nodes: np.array with node coordinates
              - elements: dictionary with keys according to number 
                of nodes in element: N15, N20. Each item contains a list
                of list of node labels
              - angles: np.array of angles for angular increments of 
                elements. 
    :rtype: dict
    
    """
    
    nodes_2d = mesh_2d['nodes']
    elems_2d = mesh_2d['elements']
    edge_node_num_2d = mesh_2d['edge_nodes']
    corner_node_num_2d = mesh_2d['corner_nodes']
    
    r_outer = np.max(np.abs(nodes_2d[:, 1]))
    num_angles = int(r_outer*2*np.pi/mesh_size)
    angles = np.linspace(0, 2*np.pi, num_angles+1)[:-1]
    delta_angle = angles[1]-angles[0]
    
    # Calculate size of mesh and allocate variables
    num_corner_nodes_2d = len(corner_node_num_2d)
    num_edge_nodes_2d = len(edge_node_num_2d)
    num_nodes_per_section = 2*num_corner_nodes_2d + num_edge_nodes_2d
    
    nodes = np.zeros((num_nodes_per_section*num_angles, 3), dtype=np.float)
    
    corner_node_num = np.zeros((num_corner_nodes_2d, num_angles), dtype=np.int)
    edge_ip_node_num = np.zeros((num_edge_nodes_2d, num_angles), dtype=np.int)
    edge_op_node_num = np.zeros((num_corner_nodes_2d, num_angles), dtype=np.int)
    
    edge_op_node_num[-1,-1] = -1    # Used the first iteration in the loop
    for i, ang in enumerate(angles):
        # Corner nodes
        corner_node_num[:, i] = edge_op_node_num[-1,i-1] + 1 + np.arange(num_corner_nodes_2d)
        for j, num in enumerate(corner_node_num[:,i]):
            coords_2d = nodes_2d[corner_node_num_2d[j], :]
            nodes[num, :] = rotate_coords(coords_2d, ang)
        # Edge nodes (in plane)
        edge_ip_node_num[:, i] = corner_node_num[-1,i] + 1 + np.arange(num_edge_nodes_2d)
        for j, num in enumerate(edge_ip_node_num[:,i]):
            coords_2d = nodes_2d[edge_node_num_2d[j], :]
            nodes[num, :] = rotate_coords(coords_2d, ang)
            
        # Edge nodes (out of plane, i.e. between angle increments, 
        # stemming from corner nodes in 2d)
        edge_op_node_num[:, i] = edge_ip_node_num[-1,i] + 1 + np.arange(num_corner_nodes_2d)
        for j, num in enumerate(edge_op_node_num[:,i]):
            coords_2d = nodes_2d[corner_node_num_2d[j], :]
            nodes[num, :] = rotate_coords(coords_2d, ang + delta_angle/2.0)

    angle_inds = np.arange(num_angles+1)
    angle_inds[-1] = 0
    hex20_elems = get_elements(elems_2d['N8'], angle_inds, corner_node_num_2d, 
                                 edge_node_num_2d, corner_node_num, edge_ip_node_num, 
                                 edge_op_node_num)
                                 
    wedge15_elems = get_elements(elems_2d['N6'], angle_inds, corner_node_num_2d, 
                                 edge_node_num_2d, corner_node_num, edge_ip_node_num, 
                                 edge_op_node_num)
    
    mesh_3d = {'nodes': nodes,
               'elements': {'N15': wedge15_elems, 'N20': hex20_elems},
               'angles': angles}
    
    return mesh_3d
    

def get_elements(elem_2d_con, angle_inds, corner_node_num_2d, edge_node_num_2d, 
                 corner_node_num, edge_ip_node_num, edge_op_node_num):
    """ Get the node lists of the revolved elements belonging to a given
    set of node lists of elements from the 2d mesh.
    
    :param elem_2d_con: list of list of 2d nodes for each element
    :type elem_2d_con: list[ list[ int ] ]
    
    :param angle_inds: indices of angles, counting 0, 1, 2, ..., N, 0
    :type angle_inds: np.array
    
    :param corner_node_num_2d: node numbers of corner nodes from 2d
    :type corner_node_num_2d: list[ int ]
    
    :param edge_node_num_2d: node numbers for edge nodes from 2d
    :type edge_node_num_2d: list[ int ]
    
    :param corner_node_num: array of node numbers for corner nodes in 
                            3d. First index refers to index in 
                            corner_node_num_2d and second index to 
                            angle_inds
    :type corner_node_num: np.array( int )
    
    :param edge_ip_node_num: array of node numbers for in-plane nodes in
                             3d. First index refers to index in 
                             edge_node_num_2d and second to angle_inds
    :type edge_ip_node_num: np.array( int )
    
    :param edge_op_node_num: array of node numbers for out-of-plane 
                             nodes in 3d. First index refers to index
                             in corner_node_num_2d and second to 
                             angle_inds. 
    :type edge_op_node_num: np.array( int )
    
    :returns: list of list containing element node labels for 3d mesh
    :rtype: np.array
    
    """
    elems = []
    n = len(elem_2d_con[0])/2
    
    for enodes in elem_2d_con:
        corner_rows = [corner_node_num_2d.index(node_num) for node_num in enodes[:n]]
        edge_rows = [edge_node_num_2d.index(node_num) for node_num in enodes[n:]]
        for i in range(len(angle_inds)-1):
            elems.append([])
            # Corner nodes
            for j in range(2):
                for cr in corner_rows:
                    elems[-1].append(corner_node_num[cr, angle_inds[i+(1-j)]])
            # Edge nodes in plane
            for j in range(2):
                for er in edge_rows:
                    elems[-1].append(edge_ip_node_num[er, angle_inds[i+(1-j)]])
            # Edge nodes between planes
            for cr in corner_rows:
                elems[-1].append(edge_op_node_num[cr, angle_inds[i]])
        
    return np.array(elems)
    

def rotate_coords(coords, angles):
    """ Rotate 2d coords in the xy-plane around the x-axis. 
    
    .. note::
        
        The function supports either a list of coordinates or a list of
        angles, not both at the same time
    
    :param coords: Coordinates in xy-plane to be rotated. Can also 
                   contain z-coordinate, but this is ignored. 
                   Can be either a single coordinate, or 2d array. In 
                   the latter case, the last index should give the axis,
                   i.e. size [N,2] or [N,3] where N is number of coords
    :type coords: np.array
    
    :param angles: List of angles to rotate a single coordinate with. 
    :type angles: float, int, list, np.array
    
    :returns: An array of rotated coordinates: [N, 3], where N is number
              of coordinates, i.e. N=max(len(angles), coords.shape[0])
    :rtype: np.array
    
    """
    if isinstance(angles, (float, int)):
        rot_ang = [angles]
    else:
        rot_ang = angles
        
    if len(coords.shape) == 1:
        coords_rotated = np.zeros((len(rot_ang), 3))
        coords_rotated[:,0] = coords[0]*np.ones((len(rot_ang)))
        coords_rotated[:,1] = coords[1]*np.cos(rot_ang)
        coords_rotated[:,2] = coords[1]*np.sin(rot_ang)
    elif len(rot_ang) == 1:
        coords_rotated = np.zeros((coords.shape[1], 3))
        coords_rotated[:,0] = coords[:, 0]
        coords_rotated[:,1] = coords[:, 1]*np.cos(rot_ang[0])
        coords_rotated[:,2] = coords[:, 1]*np.sin(rot_ang[0])
    else:
        raise ValueError('Cannot specify both multiple coordinates and angles')
        
    return coords_rotated
    

def save_3d_mesh_to_inp(mesh_3d):
    """ Given a specification of the 3d mesh, save this to an input file
    for use when generating substructure.
    
    :param mesh_3d: Mesh specification with the following fields:
              
                    - nodes: np.array with node coordinates
                    - elements: dictionary with keys according to number 
                      of nodes in element: N15, N20. Each item contains 
                      a list of list of node labels
                    - angles: np.array of angles for angular increments 
                      of elements. 
    :type mesh_3d: dict
    
    :returns: Relative path of input file
    :rtype: str
    
    """
    
    input_file = 'wheel_3d_mesh.inp'
    with open(input_file, 'w') as inp:
        inp.write('** Input file to save mesh (faster than creating mesh in abaqus cae)\n')
        inp.write('*Heading\n')
        inp.write('*Preprint, echo=NO, history=NO, contact=NO\n')
        inp.write('*Part, name=' + names.wheel_part + '\n')
        
        # Write node coordinates
        inp.write('*Node\n')
        for i, node in enumerate(mesh_3d['nodes']):
            inp.write(('{:7.0f}' + 3*', {:25.15e}' + '\n').format(i+1, *node))
        
        # Write element connectivity
        ecodes = {'N6': 'C3D6',     # Linear wedge elements
                  'N8': 'C3D8',     # Linear hex elements
                  'N15': 'C3D15',   # Quadratic wedge elements
                  'N20': 'C3D20',   # Quadratic hex elements
                  }
        enum = 1
        for etype in mesh_3d['elements']:
            ecode = ecodes[etype]
            elems = mesh_3d['elements'][etype]
            nnods = len(elems[0])
            inp.write('*Element, type=' + ecode + '\n')
            for i, elem in enumerate(elems):
                elem_nn = elem + 1  # Because abaqus numbering starts from 1
                inp.write(('{:7.0f}' + nnods*', {:7.0f}' + '\n').format(i+enum, *elem_nn))
            enum = enum + len(elems)
        inp.write('*End Part\n')
        
        # Unsure if assy required to import part?
        
    return input_file
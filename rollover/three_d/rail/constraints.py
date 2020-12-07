"""This module adds the linear constraints to enforce symmetry conditions on the rail
Constraints between points in the same position in the xy-plane are added by the following equations

.. math::

    u_x^{(\\mathrm{c})} &= u_x^{(\\mathrm{r})} 

    u_y^{(\\mathrm{c})} &= u_y^{(\\mathrm{r})}

    u_z^{(\\mathrm{c})} &= u_z^{(\\mathrm{r})} + 
    \\frac{(z^{(\\mathrm{c})} - z^{(\\mathrm{r})})}{L_\\mathrm{rail}} \\left[u_z^{(\\mathrm{rp})} + 
    (y-y^{(\\mathrm{rp})})\\phi_x^{(\\mathrm{rp})}\\right]
    
:math:`u_x^{(\\mathrm{c})}, u_y^{(\\mathrm{c})}, u_z^{(\\mathrm{c})}, u_x^{(\\mathrm{r})}, 
u_y^{(\\mathrm{r})}, u_z^{(\\mathrm{r})}` are the :math:`x`, :math:`y` and :math:`z` displacements of 
the constrained, :math:`(\\mathrm{c})`, and retained, :math:`(\\mathrm{r})`, degrees of freedom. 
:math:`x, y` are the :math:`x` and :math:`y` coordinates of the points, and :math:`z^{(\\mathrm{c})}` 
and :math:`z^{(\\mathrm{r})}` are the :math:`z`-coordinates of the constrained and retained points 
respectively. :math:`x^{(\\mathrm{rp})}, y^{(\\mathrm{rp})}, z^{(\\mathrm{rp})}` are the :math:`x,y,z` 
coordinates of the reference point. 
:math:`u_x^{(\\mathrm{rp})}, u_y^{(\\mathrm{rp})}, u_z^{(\\mathrm{rp})}` are the displacements of the 
reference point and 
:math:`\\phi_x^{(\\mathrm{rp})}, \\phi_y^{(\\mathrm{rp})}, \\phi_z^{(\\mathrm{rp})}` are its rotations 
around the :math:`x,y,z` axes. Finally, :math:`L_\\mathrm{rail}` is the length of the rail. 

The nodes at the bottom of the rail are constrained according to above, but with 
:math:`u_x^{(\\mathrm{r})} = u_y^{(\\mathrm{r})} = u_z^{(\\mathrm{r})} = 0` and 
:math:`z^{(\\mathrm{r})} = 0`

In summary, the height of the reference point determines the neutral line for bending. This will be 
up to the user to set, and then the load can be set accordingly. E.g. putting it at the top of the 
rail will give zero normal strains in the surface when prescribing the bending. Putting it in the 
neutral line of the rail profile will give a more natural bending and normal prescribation. 


.. codeauthor:: Knut Andreas Meyer
"""

import sys, os
import numpy as np

import abaqus
from abaqusConstants import *
import regionToolset, mesh

from rollover.utils import naming_mod as names

def create(the_model, rail_length, use_rail_rp, has_substructure=False):
    """Add the rail constraint sets and equations. 
    
    .. note:: `the_model` must fulfill the following requirements
    
              - Contain a part named names.rail_part that
                
                - Is a meshed part. 
                - Contains a set names.rail_bottom_nodes
                - Contains set pairs (equal node coords in xy-plane): 
                  names.rail_side_sets[0:2] and 
                  (names.rail_shadow_sets[0], names.rail_contact_surf),
                  and 
                  (names.rail_shadow_sets[1], names.rail_contact_surf)
              
              - Contains an instance of names.rail_part, named 
                names.rail_inst. 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param rail_length: The length of the rail (z-dimension)
    :type rail_length: float
    
    :param use_rail_rp: Should a reference point for the rail be used 
                        and included in the constraint equations?
    :type use_rail_rp: bool
    
    :param has_substructure: Does the model include a rail substructure?
    :type has_substructure: bool
    
    :returns: None
    :rtype: None

    """
    
    rail_part = the_model.parts[names.rail_part]
    
    sc_sets, sr_sets = create_sets(rail_part, names.rail_side_sets[0], names.rail_side_sets[1])
    shc_sets1, shr_sets1 = create_sets(rail_part, names.rail_shadow_sets[0], names.rail_contact_surf)
    shc_sets2, shr_sets2 = create_sets(rail_part, names.rail_shadow_sets[1], names.rail_contact_surf)
    
    constrained_sets_collection = [sc_sets, shc_sets1, shc_sets2]
    retained_sets_collection = [sr_sets, shr_sets1, shr_sets2]
    
    if use_rail_rp:
        if has_substructure:
            raise NotImplementedError('Combination of rail substructure and reference point not '
                                      + 'supported yet')
        rp_coord = add_ctrl_point(the_model, y_coord=0.0)
        rail_rp_set = names.rail_rp_set
        bc_sets, br_sets = create_sets(rail_part, names.rail_bottom_nodes)
        constrained_sets_collection.append(bc_sets)
        retained_sets_collection.append(br_sets)
    else:
        rail_rp_set = None
        rp_coord = None
    
    for c_sets, r_sets in zip(constrained_sets_collection, retained_sets_collection):
        for c_set, r_set in zip(c_sets, r_sets):
            add(the_model, rail_length, c_set, rail_rp_set, rp_coord, r_set)

def add_ctrl_point(the_model, y_coord):
    """Add the rail control point that is used to determine rail tension and bending 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param y_coord: The y-coordinate of the control point
    :type y_coord: float
    
    :returns: The coordinates of the reference point
    :rtype: list[ float ] (len=3)

    """
    rail_part = the_model.parts[names.rail_part]
    the_assy = the_model.rootAssembly
    rail_inst = the_assy.instances[names.rail_inst]
    
    rp_coord = (0.0, y_coord, 0.0)
    rp_node = rail_part.Node(coordinates=rp_coord)
    rail_part.Set(name=names.rail_rp_set, nodes=mesh.MeshNodeArray(nodes=(rp_node,)))
    # rail_rp = rail_part.ReferencePoint(point=rp_coord)
    #rp_key = rail_part.referencePoints.keys()[-1]
    
    #the_model.rootAssembly.regenerate()
    
    #the_assy.Set(name=names.rail_rp_set, 
    #             referencePoints=(rail_inst.referencePoints[rp_key],))
                 
    return rp_coord
    

def add(the_model, rail_length, c_set_name, rp_set_name=None, rp_coord=None, r_set_name=None):
    """Add the constraints to the node in the set c_set_name in the part rail. The constraints are 
    added on the model level. This function deducts the correct assembly set name using 
    names.rail_inst in combination with the set names given as input. The c_set_name and r_set_name
    must refer to sets belonging to the part. rp_set_name should refer to the set in the assembly.
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param rail_length: The length of the rail
    :type rail_length: float
    
    :param c_set_name: The name of the set in rail_part containing the node to be constrained
    :type c_set_name: str
    
    :param rp_set_name: The name of the set in rail_part containing the reference point node
    :type rp_set_name: str
    
    :param rp_coord: The coordinates of the rail reference point. (For some reason this is not 
                     included in the node properties)
    :type rp_coord: list[ float ] (len=3)
    
    :param r_set_name: The name of the set in rail_part containing the node participating in the 
                       constraint equation to be retained (appart from the reference point node)
    :type r_set_name: str
    
    :returns: None
    :rtype: None

    """
    the_assy = the_model.rootAssembly
    rail_part = the_model.parts[names.rail_part]
    
    def get_inst_set_name(part_set_name):
        return names.rail_inst + '.' + part_set_name
    
    c_node = rail_part.sets[c_set_name].nodes[0]
    xc, yc, zc = c_node.coordinates
    
    if rp_set_name is not None:
        xrp, yrp, zrp = rp_coord
        use_rp = True
    else:
        use_rp = False
    
    if r_set_name is not None:
        r_node = rail_part.sets[r_set_name].nodes[0]
        xr, yr, zr = r_node.coordinates
    else:
        zr = 0.0
    
    for dof, dirstr in zip([1, 2, 3], ['x', 'y', 'z']):
        # Add constrained dof first, this is removed
        terms = [ (-1.0, get_inst_set_name(c_set_name), dof) ]
        
        # Add retained dof if it should be added
        if r_set_name is not None:
            terms.append( (1.0, get_inst_set_name(r_set_name), dof) )
        
        # Add bending/extension constraints if z-dof
        # Note that dz / rail_length = +/- 1 except at bottom (when r_set_name is None)
        if dof == 3 and use_rp:    # z-dof. 
            # Extension
            dz = zc - zr
            terms.append( (dz / rail_length, get_inst_set_name(rp_set_name), dof) )
            # Bending, 4=ur1: Rotation around x-axis
            dy = yc - yrp
            terms.append( (dy * dz / rail_length, get_inst_set_name(rp_set_name), 4) )  
            
        if len(terms) > 1:  # Only add equation if required. If only one term (i.e. = 0), this 
                            # should be added as a regular boundary condition.
            the_model.Equation(name=c_set_name + '_' + dirstr, terms=tuple(terms))
       
       
def create_sets(rail_part, c_set_name, r_set_name=None):
    """Create individual sets for each matching node in the constrained set and retained set. If a 
    node is already constrained this set pair is not created. The retained set can contain nodes 
    that are not in the constrained set, but not the other way around. 
    
    :param rail_part: The rail part
    :type rail_part: Part object (Abaqus)
    
    :param c_set_name: The name of the set in rail_part containing the nodes to be constrained
    :type c_set_name: str
    
    :param r_set_name: The name of the set in rail_part containing the nodes participating in the 
                       constraint equation to be retained. If None, only sets for constrained nodes
                       are created, but the returned list of retained set names contains None to
                       have the same length
    :type r_set_name: str
    
    :returns: A list with two lists containing set names for the constrained and retained nodes
    :rtype: list[ list[ str ] ] (outer len=2, inner len=num_sets)

    """
    def get_c_set_name(c_node_label):
        return 'N' + str(c_node_label).zfill(8) + '_C'
    
    def get_r_set_name(c_node_label):
        return 'N' + str(c_node_label).zfill(8) + '_R'
        
    SEARCH_TOL = 1.e-3  # Tolerance for finding matching node
    c_node_set_names = []
    r_node_set_names = []
    
    c_nodes = rail_part.sets[c_set_name].nodes
    c_set_bb = c_nodes.getBoundingBox()
    
    if r_set_name is None:  # No matching nodes to be found, just create sets for constrained nodes
        for c_node in c_nodes:
            if get_c_set_name(c_node.label) not in rail_part.sets.keys():
                c_node_set_names.append(get_c_set_name(c_node.label))
                rail_part.Set(name=c_node_set_names[-1], nodes=mesh.MeshNodeArray(nodes=[c_node]))
                r_node_set_names.append(None)
        return c_node_set_names, r_node_set_names
    
    r_nodes = rail_part.sets[r_set_name].nodes
    r_set_bb = r_nodes.getBoundingBox()
    
    # Determine offset vec by which is longer. This constructs allow having a retained_region that 
    # contains more nodes than the constrained region. (i.e. there can be nodes in r_nodes without
    # corresponding nodes in c_nodes, but not the other way around)
    offset_vecs = [np.array(r_set_bb[side]) - np.array(c_set_bb[side]) for side in ['low', 'high']]
    offset_vec_norm = [np.linalg.norm(vec) for vec in offset_vecs]
    offset_vec = offset_vecs[0] if offset_vec_norm[0] > offset_vec_norm[1] else offset_vecs[1]
    
    for c_node in c_nodes:
        search_bb = {dim + side_str: pos + side*SEARCH_TOL + offset 
                     for side_str, side in zip(['Min', 'Max'], [-1,1]) 
                     for dim, pos, offset in zip(['x', 'y', 'z'], c_node.coordinates, offset_vec)}
        found_r_nodes = r_nodes.getByBoundingBox(**search_bb)
        if len(found_r_nodes) > 1:
            rail_part.Set(name='ERROR_MULTIPLE_NODES_FOUND', nodes=found_r_nodes)
            raise ValueError('Multiple nodes found, located in set "ERROR_MULTIPLE_NODES_FOUND"')
        if len(found_r_nodes) == 0:
            rail_part.Set(name='ERROR_NO_MATCHING_NODE', nodes=mesh.MeshNodeArray(nodes=[c_node]))
            raise ValueError('No matching node found to node in set "ERROR_NO_MATCHING_NODE". '
                             + 'Check that mesh is matching')
        
        if get_c_set_name(c_node.label) not in rail_part.sets.keys():
            c_node_set_names.append(get_c_set_name(c_node.label))
            # Using same node label and starting with the same letter to allow easy check of which 
            # nodes are constrained together
            r_node_set_names.append(get_r_set_name(c_node.label))
            r_node = found_r_nodes[0]
            rail_part.Set(name=c_node_set_names[-1], nodes=mesh.MeshNodeArray(nodes=[c_node]))
            rail_part.Set(name=r_node_set_names[-1], nodes=mesh.MeshNodeArray(nodes=[r_node]))
            
    return c_node_set_names, r_node_set_names


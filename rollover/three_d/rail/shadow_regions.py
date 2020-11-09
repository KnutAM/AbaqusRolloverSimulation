"""This module creates shadow regions

.. codeauthor:: Knut Andreas Meyer
"""
import sys, os
import numpy as np

import abaqus
from abaqusConstants import *
import regionToolset, mesh

from rollover.utils import naming_mod as names
from rollover.three_d.utils import mesh_tools as mt


def create(the_model, extend_lengths, Emod=1.0, nu=0.3, thickness=0.01):
    """Create a dummy region by extending the rail at each side. Assign 
    it a membrane section with thickness 0.01 and elastic material with
    E=1.0 and nu=0.3.
    
    .. note:: Requires that the meshed part, 
              the_model.parts[names.rail_part] contains a surface named 
              `names.rail_contact_surf`
    
    :param the_model: The model containing the rail part 
    :type rail_part: Model object (Abaqus)
    
    :param extend_lengths: The (absolute) distance with which the rail will be extended in each end 
                           `[z=0, z=L]`. If any is None, the full contact surface will be extended.
    :type extend_lengths: list[ float ], len=2
    
    :param Emod: Dummy stiffness - elastic modulus of shadow membrane
    :type Emod: float
    
    :param nu: Dummy Poisson's ratio of shaddow membrane
    :type nu: float
    
    :param thickness: Thickness of shadow membrane
    :type thickness: float
    
    :returns: None
    :rtype: None

    """
    rail_part = the_model.parts[names.rail_part]
    
    # Create shadow section
    the_model.Material(name='ShadowElastic')
    the_model.materials['ShadowElastic'].Elastic(table=((Emod, nu), ))
    the_model.MembraneSection(name=names.rail_shadow_sect, material='ShadowElastic', 
                              thickness=thickness)
    
    contact_surface = rail_part.surfaces[names.rail_contact_surf]
    
    cs_bounding_box = contact_surface.nodes.getBoundingBox()
    rail_length = cs_bounding_box['high'][2] - cs_bounding_box['low'][2]
    
    create_mesh(rail_part, contact_surface, z_shift=rail_length, 
                shadow_size=extend_lengths[0], set_name=names.rail_shadow_sets[0])
                                      
    create_mesh(rail_part, contact_surface, z_shift=-rail_length, 
                shadow_size=extend_lengths[1], set_name=names.rail_shadow_sets[1])
                                  
    shadow_region = rail_part.SetByBoolean(name=names.rail_shadow_set, 
                                           sets=tuple([rail_part.sets[name] 
                                                       for name in names.rail_shadow_sets]))
    
    rail_part.SectionAssignment(region=shadow_region, sectionName=names.rail_shadow_sect)
    
    
    
def create_mesh(rail_part, contact_surface, z_shift, shadow_size=None, set_name=None):
    """Create dummy elements by extending the rail on one side. 
    
    :param rail_part: The part containing the rail geometry with a surface: names.rail_contact_surf
    :type rail_part: Part object (Abaqus)
    
    :param contact_surface: The surface containing the mesh to be shifted
    :type contact_surface: Surface object (Abaqus)
    
    :param z_shift: How much the mesh will be shifted in the z-direction (typically +/- rail_length)
    :type z_shift: float
    
    :param shadow_size: How long part of the contact surface will be extended. (Measured from the 
                        opposite side. I.e. if we extend in positive z, how far from z=0 will be 
                        included. And contrarily, if negative z, how far from z=rail_length will be 
                        included). If None, the full length will be included (equivalent to setting
                        it to rail_length, but ensures no miss due to numerical tolerances. 
    :type shadow_size: float
    
    :param set_name: Name of set containing the created mesh. If None no set is created
    :type set_name: str
    
    :returns: None
    :rtype: None

    """
    shadow_elems = []
    shadow_nodes = []
    
    if shadow_size < abs(z_shift)*1.e-9:
        return shadow_elems
    
    if shadow_size is not None:
        zmax = abs(shadow_size) if z_shift > 0 else None
        zmin = - z_shift - abs(shadow_size) if z_shift < 0 else None
    else:
        zmax, zmin = (None, None)
        
    delete_elems = []
    tmpname = '1' if z_shift > 0 else '0'
    for source_face in contact_surface.faces:
        source_region = mt.get_source_region(source_face)
        shadow_elems_tmp, offset_vector = mt.create_offset_mesh(rail_part, source_face, source_region, 
                                                                offset_distance=0.0)
        for shadow_elem in shadow_elems_tmp:
            if zmax is not None:
                append_element = all([n.coordinates[2] < zmax for n in shadow_elem.getNodes()])
            elif zmin is not None:
                append_element = all([n.coordinates[2] > zmin for n in shadow_elem.getNodes()])
            else:
                append_element = True
            if append_element:                
                shadow_elems.append(shadow_elem)
                for node in shadow_elem.getNodes():
                    if node not in shadow_nodes:
                        shadow_nodes.append(node)
            else:
                delete_elems.append(shadow_elem)
    
    if set_name is not None:
        rail_part.Set(name=set_name, elements=mesh.MeshElementArray(elements=shadow_elems))
    
    delete_nodes = []
    for elem in delete_elems:
        for node in elem.getNodes():
            if node not in shadow_nodes:
                if node not in delete_nodes:
                    delete_nodes.append(node)
    
    rail_part.editNode(nodes=shadow_nodes, offset3=z_shift)
    if len(delete_nodes) > 0:
        rail_part.deleteNode(nodes=mesh.MeshNodeArray(nodes=delete_nodes))
    
    return shadow_elems
    
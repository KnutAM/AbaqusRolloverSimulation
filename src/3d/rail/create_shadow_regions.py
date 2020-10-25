"""This module creates shadow regions

.. codeauthor:: Knut Andreas Meyer
"""
import sys, os
import numpy as np

import abaqus
from abaqusConstants import *
import regionToolset, mesh

import naming_mod as names
import mesh_tools as mt


def create_shadow_region(rail_part, extend_lengths):
    """Create a dummy region by extending the rail at each side
    
    .. note:: Requires that `rail_part` contains a surface named `names.rail_contact_surf` and that
              the model contains a section definition named `names.rail_shadow_sect`
    
    :param rail_part: The part containing the rail geometry with a surface named 
                      `names.rail_contact_surf`
    :type rail_part: Part (Abaqus object)
    
    :param extend_lengths: The (absolute) distance with which the rail will be extended in each end 
                           `[z=0, z=L]`. If any is None, the full contact surface will be extended.
    :type extend_lengths: list[ float ], len=2
    
    :returns: None
    :rtype: None

    """
    
    contact_surface = rail_part.surfaces[names.rail_contact_surf]
    
    cs_bounding_box = contact_surface.nodes.getBoundingBox()
    rail_length = cs_bounding_box['high'][2] - cs_bounding_box['low'][2]
    
    shadow_elems = create_shadow_mesh(rail_part, contact_surface, z_shift=rail_length, 
                                      shadow_size=extend_lengths[0])
                                      
    shadow_eltmp = create_shadow_mesh(rail_part, contact_surface, z_shift=-rail_length, 
                                      shadow_size=extend_lengths[1])
    for etmp in shadow_eltmp:
        shadow_elems.append(etmp)
    
    shadow_region = regionToolset.Region(elements=mesh.MeshElementArray(elements=shadow_elems))
    
    rail_part.SectionAssignment(region=shadow_region, sectionName=names.rail_shadow_sect)
    
    
    
def create_shadow_mesh(rail_part, contact_surface, z_shift, shadow_size=None):
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
    
    :returns: A list of elements in the shadow mesh
    :rtype: list[ Element object (Abaqus) ]

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
        
    for source_face in contact_surface.faces:
        source_region = mt.get_source_region(source_face)
        shadow_elems_tmp, offset_vector = mt.create_offset_mesh(rail_part, source_face, source_region, 
                                                                offset_distance=0.0)
        delete_elems = []
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
        
        rail_part.deleteElement(elements=mesh.MeshElementArray(elements=delete_elems))
                    
    rail_part.editNode(nodes=shadow_nodes, offset3=z_shift)
    
    return shadow_elems
    
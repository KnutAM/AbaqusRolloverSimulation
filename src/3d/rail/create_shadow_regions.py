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


def create_shadow_mesh(rail_part):
    contact_surface = rail_part.surfaces[names.rail_contact_surf]
    
    cs_bounding_box = contact_surface.nodes.getBoundingBox()
    rail_length = np.abs(cs_bounding_box['high'][2] - cs_bounding_box['low'][2])
    
    shadow_elems = []
    shadow_nodes = []
    for source_face in contact_surface.faces:
        source_region = mt.get_source_region(source_face)
        shadow_elems_tmp, offset_vector = mt.create_offset_mesh(rail_part, source_face, source_region, 
                                                                offset_distance=0.0)
        for shadow_elem in shadow_elems_tmp:
            shadow_elems.append(shadow_elem)
            for node in shadow_elem.getNodes():
                if node not in shadow_nodes:
                    shadow_nodes.append(node)
                    
                    
    rail_part.editNode(nodes=shadow_nodes, offset3=rail_length)
    
    shadow_region = regionToolset.Region(elements=mesh.MeshElementArray(elements=shadow_elems))
    
    rail_part.SectionAssignment(region=shadow_region, sectionName=names.rail_shadow_sect)
    

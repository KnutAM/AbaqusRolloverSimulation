"""This module contains functions that helps when working with meshes

.. codeauthor:: Knut Andreas Meyer
"""
from __future__ import print_function
import numpy as np
import sys

from abaqus import *
from abaqusConstants import *
import regionToolset, mesh, part


def get_source_region(source_face):
    """Create a "surface-like" region, source_region, of elements on source_face
    
    :param source_face: A meshed face
    :type source_face: Face (Abaqus object)
    
    :returns: The "surface-like" region describing the meshed surface
        
    :rtype: Region (Abaqus object)

    """
    
    elems = get_elem_by_face_type(source_face)
            
    source_region = regionToolset.Region(**elems)
    
    return source_region


def get_elem_by_face_type(source_face, elems=None):
    """Get a dictionary with each elements of each face type, e.g. 
    face1Elements, face2Elements etc. (up to face6Elements) as keys.
    
    :param source_face: A meshed face
    :type source_face: Face (Abaqus object)
    
    :param elems: The dictionary to return, will add to it if not None
    :type elems: dict
    
    :returns: Dictionary keys as described above, containing MeshElement
              objects
    :rtype: dict

    """
    
    if elems is None:
        elems = {}
        
    elem_by_face_type = [[] for i in range(6)]
    f_elems = source_face.getElementFaces()
    for f_elem in f_elems:
        face_type_ind = int(str(f_elem.face)[4:]) - 1
        elem_by_face_type[face_type_ind].append(f_elem.getElements()[0])
    
    for i, e in enumerate(elem_by_face_type):
        if len(e)>0:
            key = 'face' + str(i+1) + 'Elements'
            if key in elems:
                els = [el for el in elems[key]]
                for el in e:
                    els.append(el)
            else:
                els = e
                
            elems[key] = mesh.MeshElementArray(elements=els)

    return elems
    

def create_offset_mesh(the_part, source_face, source_region, offset_distance=20.0):
    """Create an offsetted orphan mesh
    
    :param the_part: The part
    :type the_part: Part (Abaqus object)
    
    :param source_face: The meshed face whose mesh will be offset
    :type source_face: Face (Abaqus object)
    
    :param source_region: A "surface-like" mesh region describing the face whose mesh will be offset
    :type source_region: Region (Abaqus object)
    
    :param offset_distance: The distance to offset the mesh by, defaults to 20.0
    :type offset_distance: float, optional
    
    :returns: (shadow_elems, offset_vector)
        
        - shadow_elems: The created offsetted orphan elements
        - offset_vector: The vector with which the elements where offsetted
    :rtype: tuple(MeshElementArray (Abaqus object), np.array)

    """
    # Determine bounding box for offsetted mesh
    bounding_box = source_face.getNodes().getBoundingBox()
    offset_vector = offset_distance*np.array(source_face.getNormal())
    for key in bounding_box:
        bounding_box[key] = np.array(bounding_box[key]) + offset_vector
    
    # Convert bounding box to arguments understood by getByBoundingBox
    bb_to_get_by = convert_bounding_box(bounding_box)
    
    # Get mesh currently in that bounding box (e.g. from other faces in the set)
    old_elems = the_part.elements.getByBoundingBox(**bb_to_get_by)
    
    # Create the offsetted mesh
    the_part.generateMeshByOffset(region=source_region, initialOffset=offset_distance,
                                 meshType=SHELL, distanceBetweenLayers=0.0, numLayers=1)
    
    # Get all mesh that exist in the bounding box
    new_elems = the_part.elements.getByBoundingBox(**bb_to_get_by)
    
    # Extract only the parts of the mesh that is new with the offsetted mesh
    shadow_elems = mesh.MeshElementArray(elements=[e for e in new_elems if e not in old_elems])
    
    return shadow_elems, offset_vector
    
    
# Utility functions
def convert_bounding_box(bb_from_get):
    """Convert bounding box specified by by {'low': (x_min, y_min, z_min), 'high': (x_max, y_max, 
    z_max)} to {'xMin': x_min, 'yMin': y_min, ..., 'zMax': z_max}
    
    Input typically comes from Abaqus' function getBoundingBox. Output, bb_to_get_by, can be used in 
    Abaqus' function getByBoundingBox as getByBoundingBox(\*\*bb_to_get_by) (i.e. using kwargs)
    
    :param bb_from_get: Dictionary describing a bounding box by points 'low' and 'high'
    :type add_region: dict
    
    :returns: Dictionary describing a bounding box by values 'xMin', 'xMax', 'yMin', ..., 'zMax'
    :rtype: dict

    """
    
    bb_to_get_by = {x + side: bb_from_get[lh][i] for i, x in enumerate(['x', 'y', 'z']) 
                 for side, lh in zip(['Min', 'Max'], ['low', 'high'])}
    return bb_to_get_by

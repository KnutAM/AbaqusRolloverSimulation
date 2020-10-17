"""This module meshes a rail profile
.. codeauthor:: Knut Andreas Meyer
"""
# Python imports
from __future__ import print_function
import os, sys, inspect
import numpy as np

# Abaqus imports
from abaqusConstants import *
from abaqus import mdb

import naming_mod as names
import get_utils as get
import abaqus_python_tools as apt


def generate_mesh(rail_profile, rail_length):
    """Create a new model containing a simple rail geometry.
    
    The model is named 'RAIL' and the profile is created by importing the sketch rail_profile and 
    extruding it by rail_length. Two sets, one in each end of the rail are created.
    
    :param rail_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type rail_profile: str
    
    :param rail_length: Length of rail to be extruded
    :type rail_length: float
        
    :returns: The model database containing the rail part
    :rtype: Model (Abaqus object)

    """
    rail_model = apt.create_model('RAIL')
    profile_sketch = import_sketch(rail_profile, rail_model)
    rail_part = rail_model.Part(name=names.rail_part, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    rail_part.BaseSolidExtrude(sketch=profile_sketch, depth=rail_length)
    create_sets(rail_part, rail_length)
    
    return rail_model


def import_sketch(rail_profile, rail_model):
    """Import the sketch rail_profile and add it to the rail_model.
    
    :param rail_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type rail_profile: str
    
    :param rail_model: The model to which the sketch will be added
    :type rail_model: Model (Abaqus object)
    
    :returns: The added sketch
    :rtype: ConstrainedSketch (Abaqus object)

    """
    acis = mdb.openAcis(rail_profile, scaleFromFile=OFF)
    return rail_model.ConstrainedSketchFromGeometryFile(name='profile', geometryFile=acis)
    
    
def create_sets(rail_part, rail_length):
    """Create a set on each side of the rail. Set names based on names.rail_side_sets
    
    :param rail_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type rail_profile: str
    
    :param rail_length: Length of the extruded rail
    :type rail_length: float
    
    :returns: None
    :rtype: None

    """
    for z, set_name in zip([0, rail_length], names.rail_side_sets):
        faces = rail_part.faces.getByBoundingBox(xMin=-np.inf, xMax=np.inf, 
                                                 yMin=-np.inf, yMax=np.inf, 
                                                 zMax=z + 1.e-5, 
                                                 zMin=z - 1.e-5)
        rail_part.Set(name=set_name, faces=faces)
    
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Inputs:\n <path_to_rail_profile.sat> (str)\n <rail_length> (float)')
        raise IOError('rail profile file and rail length must be given as input')
    rail_profile = sys.argv[1]
    try:
        rail_length = float(sys.argv[2])
    except ValueError as ve:
        print('The rail length (second input) must be numeric')
        
    create_rail(rail_profile, rail_length)

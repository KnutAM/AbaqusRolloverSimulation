"""Tools to work with sketches

.. codeauthor:: Knut Andreas Meyer
"""
from __future__ import print_function
from abaqusConstants import *
from abaqus import mdb


def import_sketch(the_model, sketch_profile, name='profile'):
    """Import the sketch sketch_profile and add it to the_model.
    
    :param the_model: The model to which the sketch will be added
    :type the_model: Model (Abaqus object)
    
    :param sketch_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type sketch_profile: str
    
    :param name: Name of the created sketch, defaults to 'profile'
    :type name: str
    
    :returns: The added sketch
    :rtype: ConstrainedSketch (Abaqus object)

    """
    acis = mdb.openAcis(sketch_profile, scaleFromFile=OFF)
    return the_model.ConstrainedSketchFromGeometryFile(name=name, geometryFile=acis)

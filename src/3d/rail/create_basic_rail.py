"""Create a basic 3d rail based on an abaqus sketch saved as a .sat file

.. codeauthor:: Knut Andreas Meyer
"""
# Python imports
from __future__ import print_function
import os, sys, inspect
import numpy as np

# Abaqus imports
from abaqusConstants import *
from abaqus import mdb

# Project imports
import naming_mod as names
import get_utils as get
import abaqus_python_tools as apt


def create_rail(rail_profile, rail_length, refine_region=None):
    """Create a new model containing a simple rail geometry.
    
    The model is named 'RAIL' and the profile is created by importing the sketch rail_profile and 
    extruding it by rail_length. Two sets, one in each end of the rail are created.
    
    :param rail_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type rail_profile: str
    
    :param rail_length: Length of rail to be extruded
    :type rail_length: float
    
    :param refine_region: Rectangle specifying partition with mesh refinement in contact region, 
                          defaults to None implying no refined region
    :type refine_region: list(list(float)), optional
        
    :returns: The model database containing the rail part
    :rtype: Model (Abaqus object)

    """
    rail_model = apt.create_model('RAIL')
    profile_sketch = import_sketch(rail_model, rail_profile)
    rail_part = rail_model.Part(name=names.rail_part, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    rail_part.BaseSolidExtrude(sketch=profile_sketch, depth=rail_length)
    if refine_region is not None:
        create_partition(rail_model, rail_part, refine_region)
    
    create_sets(rail_part, rail_length)
    
    return rail_model


def import_sketch(rail_model, rail_profile):
    """Import the sketch rail_profile and add it to the rail_model.
    
    :param rail_model: The model to which the sketch will be added
    :type rail_model: Model (Abaqus object)
    
    :param rail_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type rail_profile: str
    
    :returns: The added sketch
    :rtype: ConstrainedSketch (Abaqus object)

    """
    acis = mdb.openAcis(rail_profile, scaleFromFile=OFF)
    return rail_model.ConstrainedSketchFromGeometryFile(name='profile', geometryFile=acis)
    
    
def create_sets(rail_part, rail_length):
    """Create a set on each side of the rail. Set names based on names.rail_side_sets
    
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param rail_length: Length of the extruded rail
    :type rail_length: float
    
    :returns: None
    :rtype: None

    """
    for z, set_name in zip([0, rail_length], names.rail_side_sets):
        faces = get_end_faces(rail_part, zpos=z)
        rail_part.Set(name=set_name, faces=faces)
    
    
def get_end_faces(rail_part, zpos):
    """Get the all faces at the end of the rail specified by zpos
        
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param zpos: The position of the end_faces
    :type zpos: float
    
    :returns: A FaceArray object containing all faces at zpos with z-normal direction
    :rtype: FaceArray (Abaqus object)

    """
    faces = rail_part.faces.getByBoundingBox(xMin=-np.inf, xMax=np.inf, 
                                                 yMin=-np.inf, yMax=np.inf, 
                                                 zMax=zpos + 1.e-5, 
                                                 zMin=zpos - 1.e-5)
    return faces
    
    
def create_partition(rail_model, rail_part, refine_region):
    """Create a partition by extruding the rectangle specified by refine_region
        
    :param rail_model: The model to which the sketch will be added
    :type rail_model: Model (Abaqus object)
        
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param refine_region: Rectangle specifying partition with mesh refinement in contact region
    :type refine_region: list(list(float))
    
    :returns: None
    :rtype: None

    """
    rail_cell = rail_part.cells[0]                      # Should only be 1 before partitioning
    rail_face = get_end_faces(rail_part, zpos=0.0)[0]   # Should only be 1 before partitioning
    
    extrude_axis = rail_part.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    extrude_axis = rail_part.datums[extrude_axis.id]
    vertical_axis = rail_part.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    vertical_axis = rail_part.datums[vertical_axis.id]
    
    sketch_position = rail_part.MakeSketchTransform(sketchPlane=rail_face, origin=(0.0, 0.0, 0.0), 
                                                    sketchUpEdge=vertical_axis, 
                                                    sketchPlaneSide=SIDE1)
                                                    
    partition_sketch = rail_model.ConstrainedSketch(name='partition_sketch', sheetSize=200.0,
                                                    transform=sketch_position)
    partition_sketch.rectangle(point1=refine_region[0], point2=refine_region[1])
    
    rail_part.PartitionFaceBySketch(faces=rail_face, sketch=partition_sketch,
                                    sketchUpEdge=vertical_axis, sketchOrientation=RIGHT)
    
    point_on_partitioned_face = (np.array(refine_region[0]) + np.array(refine_region[1]))/2.0
    point_on_partitioned_face = np.append(point_on_partitioned_face, 0.0)
    partition_edge_ids = rail_part.faces.findAt(tuple(point_on_partitioned_face)).getEdges()
    partition_edges = [rail_part.edges[i] for i in partition_edge_ids]
    
    rail_part.PartitionCellByExtrudeEdge(line=extrude_axis, cells=rail_cell, edges=partition_edges, 
                                         sense=FORWARD)

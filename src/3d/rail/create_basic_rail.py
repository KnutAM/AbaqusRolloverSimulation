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
import part

# Project imports
import naming_mod as names
import get_utils as get
import abaqus_python_tools as apt


def create_rail(rail_profile, rail_length, refine_region=None, sym_dir=None):
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
    
    :param sym_dir: Vector specifying the normal direction if symmetry is used in the rail profile
    :type sym_dir: list(float) (len=3)
        
    :returns: The model database containing the rail part
    :rtype: Model (Abaqus object)

    """
    rail_model = apt.create_model('RAIL')
    profile_sketch = import_sketch(rail_model, rail_profile)
    rail_part = rail_model.Part(name=names.rail_part, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    rail_part.BaseSolidExtrude(sketch=profile_sketch, depth=rail_length)
    if refine_region is not None:
        create_partition(rail_model, rail_part, refine_region)
    
    create_sets(rail_part, rail_length, refine_region, sym_dir)
    
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
    
    
def create_sets(rail_part, rail_length, refine_region=None, sym_dir=None):
    """Create (1) a set on each side of the rail with names from names.rail_side_sets, (2) the 
    contact surface and set on the top of the rail with name names.rail_contact_surf and (3) a set 
    on the bottom of the rail
    
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param rail_length: Length of the extruded rail
    :type rail_length: float
    
    :param refine_region: Rectangle specifying partition with mesh refinement in contact region, 
                          defaults to None implying no refined region
    :type refine_region: list(list(float)), optional
    
    :param sym_dir: Vector specifying the normal direction if symmetry is used in the rail profile
    :type sym_dir: list(float) (len=3)
    
    :returns: None
    :rtype: None

    """
    for z, set_name in zip([0, rail_length], names.rail_side_sets):
        faces = get_end_faces(rail_part, zpos=z)
        rail_part.Set(name=set_name, faces=faces)
        
    if refine_region is None:
        contact_cell = rail_part.cells[0]
    else:
        partition_face, point_on_partition_face = get_partition_face(rail_part, refine_region)
        contact_cell = rail_part.cells.findAt(point_on_partition_face)
    
    create_contact_face_set(rail_part, contact_cell, exclude_dir=sym_dir)
    
    bottom_faces = get_bottom_faces(rail_part)
    rail_part.Set(name=names.rail_bottom_nodes, faces=part.FaceArray(faces=bottom_faces))
    

def get_bottom_faces(rail_part):
    """Return a list of faces that are on the bottom of the rail profile. These are identified by 
    having their pointOn with an y-coordinate equal to the minimum of all faces and a normal 
    direction [0, -1, 0]
    
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part object (Abaqus)
    
    :returns: A list of faces that are located in the bottom of the rail
    :rtype: list[ Face object (Abaqus) ]

    """
    TOL_YMIN = 1.e-6
    TOL_YDIR = 1.e-3
    
    ymin = np.inf
    for face in rail_part.faces:
        ymin = min(ymin, face.pointOn[0][1])
    
    bottom_faces = []
    for face in rail_part.faces:
        if face.pointOn[0][1] < ymin + TOL_YMIN:
            if face.getNormal()[1] < -1.0 + TOL_YDIR:
                bottom_faces.append(face)
                
    return bottom_faces
    
    
def create_contact_face_set(rail_part, contact_cell, exclude_dir=None):
    # Get all faces on the contact cell
    contact_cell_faces = [rail_part.faces[f_ind] for f_ind in contact_cell.getFaces()]
    
    # Get all faces in the neighbouring cells
    neighbouring_cells = contact_cell.getAdjacentCells()
    if len(neighbouring_cells) > 0:        
        neighbouring_faces = []
        for nc in neighbouring_cells:
            for f_ind in nc.getFaces():
                neighbouring_faces.append(rail_part.faces[f_ind])
                
        # Get all faces in contact_cell that are external (i.e. not shared by neighbouring cells)
        external_faces = []
        for cf in contact_cell_faces:
            if cf not in neighbouring_faces:
                external_faces.append(cf)
    else:
        external_faces = contact_cell_faces
            
    # Get all external faces that do not have normal direction in z-direction
    contact_faces = []
    exclude_vec = np.array([0,0,0] if exclude_dir is None else exclude_dir)
    for ef in external_faces:
        n_vec = ef.getNormal()
        if np.abs(n_vec[2]) < 0.99 and np.dot(np.array(n_vec), exclude_vec) < 0.99:
            contact_faces.append(ef)
    
    rail_part.Surface(name=names.rail_contact_surf, side1Faces=part.FaceArray(contact_faces))
    rail_part.Set(name=names.rail_contact_surf, faces=part.FaceArray(contact_faces))
    
    
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
    
    partition_face, point_on_partition_face = get_partition_face(rail_part, refine_region)
    partition_edge_ids = partition_face.getEdges()
    partition_edges = [rail_part.edges[i] for i in partition_edge_ids]
    
    
    # rail_part.Set(name='partition_edges', edges=part.EdgeArray(edges=partition_edges))
    rail_part.PartitionCellByExtrudeEdge(line=extrude_axis, cells=rail_cell, edges=partition_edges, 
                                         sense=FORWARD)
                                         
    
def get_partition_face(rail_part, refine_region):
    rel_length = 0.001
    def get_face(pa, pb):
        point = p1 + rel_length*(p2-p1)
        return rail_part.faces.findAt(tuple(point)), point
        
    p1, p2 = [np.array([refine_region[i][0], refine_region[i][1], 0.0]) for i in [0, 1]]
    
    face, point = get_face(p1, p2)
    if face is not None:
        return face, point
    
    face, point = get_face(p2, p1)
    if face is not None:
        return face, point
        
    p1, p2 = [np.array([refine_region[i][0], refine_region[1-i][1], 0.0]) for i in [0, 1]]
    
    face, point = get_face(p1, p2)
    if face is not None:
        return face, point
        
    face, point = get_face(p2, p1)
    if face is not None:
        return face, point
    
    raise ValueError('Could not find the partition face')

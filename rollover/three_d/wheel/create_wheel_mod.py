"""Create a wheel super element

1) Create a 2-d wheel section mesh using abaqus cae
2) Based on this mesh, generate an input file for a full 3d-wheel 
3) Run the input file to obtain the substructure stiffness matrix
4) Add the stiffness matrix to a static library that can be referenced when creating the user 
   subroutine

.. codeauthor:: Knut Andreas Meyer
"""

# Python imports
import numpy as np
import uuid

# Abaqus imports
from abaqusConstants import *
import part, sketch, mesh

# Project imports
from rollover.three_d.utils import sketch_tools
from rollover.utils import abaqus_python_tools as apt
from rollover.utils import naming_mod as names
                 

def generate_2d_mesh(wheel_model, wheel_profile, mesh_sizes, wheel_contact_pos, partition_line, 
                     fine_mesh_edge_bb=None, quadratic_order=True):
    """Generate a mesh of the wheel profile
    
    :param wheel_model: The model containing the wheel part
    :type wheel_model: Model object (Abaqus)
    
    :param wheel_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type wheel_profile: str
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :param wheel_contact_pos: min and max x-coordinate for the wheel contact region (retained dofs)
    :type wheel_contact_pos: list[ float ] (len=2)
    
    :param partition_line: y-value for the line where the wheel profile will be partitioned to 
                           give a better mesh value.
    
    :param fine_mesh_edge_bb: Dictionary with bounding box parameters for determining which edges 
                              the fine mesh should be applied to. Keys are 'xMin', 'yMax', etc. 
                              If None, set h = partition_line*(1+1.e-6) and set 'yMax' to h if
                              partition_line < 0 or 'yMin' to h if partition_line > 0. The 
                              adjustment ensures that the partition line is not included amongst the 
                              fine mesh edges.
    :type fine_mesh_edge_bb: dict
    
    :param quadratic_order: Should quadratic elements be used, default is True
    :type quadratic_order: bool
    
    :returns: None
    :rtype: None

    """
    wheel_part = wheel_model.parts[names.wheel_part]
    
    # Create profile
    profile_sketch = sketch_tools.import_sketch(wheel_model, wheel_profile, 
                                                name='wheel_2d_profile')
    wheel_part.BaseShell(sketch=profile_sketch)
    
    # Create partition
    partition_sketch = wheel_model.ConstrainedSketch(name='partition', sheetSize=1.0)
    partition_sketch.Line(point1=(-1000.0, partition_line), point2=(1000.0, partition_line))
    wheel_part.PartitionFaceBySketch(faces=wheel_part.faces[0:1], sketch=partition_sketch)
    
    # Find edges to have fine mesh constraint
    if fine_mesh_edge_bb is None:
        fine_mesh_edge_bb = {('yMin' if partition_line > 0 else 'yMax'): partition_line*(1+1.e-6)}
    
    fine_mesh_edges = wheel_part.edges.getByBoundingBox(**fine_mesh_edge_bb)
    contact_edges = wheel_part.Set(name='contact_edges', edges=fine_mesh_edges)
    
    wheel_part.seedEdgeBySize(edges=fine_mesh_edges, size=mesh_sizes[0], constraint=FIXED)
    
    # Find edges to have coarse mesh constraint
    max_y = np.max([e.pointOn[0][1] for e in wheel_part.edges])
    coarse_mesh_edges = []
    for e in wheel_part.edges:
        if all([wheel_part.vertices[n].pointOn[0][1] > (max_y - 1.e-3) 
                for n in e.getVertices()]):
            coarse_mesh_edges.append(e)
    
    partition_line_edge = wheel_part.edges.getByBoundingBox(yMin=partition_line - 1.e-5,
                                                            yMax=partition_line + 1.e-5)[0]
    coarse_mesh_edges.append(partition_line_edge)
    wheel_part.seedEdgeBySize(edges=coarse_mesh_edges, size=mesh_sizes[1], constraint=FIXED)
    
    # Set mesh order
    if quadratic_order:
        elemType1 = mesh.ElemType(elemCode=S8R, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=STRI65, elemLibrary=STANDARD)
    else:
        elemType1 = mesh.ElemType(elemCode=S4R, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=S3, elemLibrary=STANDARD)
    
    wheel_part.setElementType(regions=(wheel_part.faces,), elemTypes=(elemType1, elemType2))
    
    # Mesh wheel
    wheel_part.generateMesh()


def generate_3d_mesh(wheel_model, mesh_sizes):
    """ Given a wheel_model containing a meshed planar 3d wheel section 
    (in the xy-plane with y the radial direction), create a 3d revolved
    mesh.
    
    :param wheel_model: The model containing the wheel part
    :type wheel_model: Model object (Abaqus)
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, 
                       mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :returns: None
    :rtype: None
    
    """
    wheel_part = wheel_model.parts[names.wheel_part]
    
    r_outer = np.max(np.abs([n.coordinates[1] for n in wheel_part.nodes]))
    num_angles = int(r_outer*2*np.pi/mesh_sizes[0])
    
    elem_faces_source_side = wheel_part.elementFaces
    x_axis =((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    wheel_part.generateBottomUpRevolvedMesh(elemFacesSourceSide=elem_faces_source_side, 
                                            axisOfRevolution=x_axis, 
                                            angleOfRevolution=360.0, 
                                            numberOfLayers=num_angles,
                                            extendElementSets=True)
    # Delete the meshed face (this does not delete the bottom up mesh
    wheel_part.deleteMesh()
    

def create_retained_set(wheel_part, wheel_angles):
    """Create a set for the retained dofs
    
    The wheel part should have a 3d-revolved mesh and a set 
    'contact_edges' containing the nodes in the section that should be 
    retained. This function will create a node set with the 
    corresponding nodes that are within the angular interval specified 
    by wheel_angles.
    
    :param wheel_part: The wheel part containing the orphan 3d mesh
    :type wheel_part: Part object (Abaqus)
    
    :param wheel_angles: Interval of angles (wrt. negative y-direction,
                         positive rotation around x-axis) for retained
                         nodes
    :type wheel_angles: list[ float ] (len=2)
    
    :returns: None
    :rtype: None

    """
    set_name = names.wheel_contact_nodes
    contact_line_nodes = wheel_part.sets['contact_edges'].nodes
    tmp_set = get_nodes_in_ang_int(wheel_part, wheel_angles, contact_line_nodes[0].coordinates)
    wheel_part.Set(name=set_name, objectToCopy=tmp_set)
    for node in contact_line_nodes[1:]:
        tmp_set = get_nodes_in_ang_int(wheel_part, wheel_angles, node.coordinates)
        wheel_part.SetByBoolean(name=set_name, sets=(wheel_part.sets[set_name], tmp_set))
    
    # Remove the final temporary set
    del wheel_part.sets['_contact_nodes']
    
    
def get_nodes_in_ang_int(wheel_part, wheel_angles, x0, considered_nodes=None):
    """Get the nodes that are within the interval specified by 
    wheel_angles that are revolved from coordinate x0
    
    :param wheel_part: The wheel part containing the orphan 3d mesh
    :type wheel_part: Part object (Abaqus)
    
    :param wheel_angles: Interval of angles (wrt. negative y-direction,
                         positive rotation around x-axis) for retained
                         nodes
    :type wheel_angles: list[ float ] (len=2)
    
    :param x0: Coordinates of the reference point for revolution
    :type x0: tuple[ float ] (len=3)
    
    :param considered_nodes: Which nodes to consider to possible be in 
                             the nodes to find. Can be used to speed up,
                             if None all nodes in wheel_part are used.
    
    :returns: The created set
    :rtype: Set object (Abaqus)

    """
    if any([abs(ang) > np.pi/2 for ang in wheel_angles]):
        raise NotImplementedError('Absolute wheel angles > pi/2 not supported')
    if wheel_angles[0] >= wheel_angles[1]:
        raise ValueError('The second wheel angle must be greater than the first')
        
    TOL = 1.e-2 # Tolerance, must be smaller than node spacing. But 
                # tolerances are not so good for bounding box...
    
    all_nodes = wheel_part.nodes if considered_nodes is None else considered_nodes
    
    c1 = (x0[0]-TOL, 0.0, 0.0)
    c2 = (x0[0]+TOL, 0.0, 0.0)
    r = np.sqrt(x0[1]**2 + x0[2]**2)
    
    sp = wheel_part.Set(name='_plane_nodes', 
                        nodes=all_nodes.getByBoundingCylinder(center1=c1, center2=c2, 
                                                              radius=r+TOL))
                                                              
    inner_nodes = all_nodes.getByBoundingCylinder(center1=c1, center2=c2, radius=r-TOL)
    if len(inner_nodes) > 0:
        si = wheel_part.Set(name='_inner_nodes', nodes=inner_nodes)
        so = wheel_part.SetByBoolean(name='_outer_nodes', sets=(sp, si), operation=DIFFERENCE)
    else:   # If no inner nodes found, all nodes in sp are outer nodes
        so = wheel_part.Set(name='_outer_nodes', objectToCopy=sp)
    
    bb = {}
    if abs(wheel_angles[0]) > abs(wheel_angles[1]):
        bb['yMax'] = -r*np.cos(wheel_angles[0])
        bb['zMax'] = r*np.sin(wheel_angles[1])
    else:
        bb['yMax'] = -r*np.cos(wheel_angles[1])
        bb['zMin'] = r*np.sin(wheel_angles[0])
        
    sc = wheel_part.Set(name='_contact_nodes', 
                        nodes=so.nodes.getByBoundingBox(**bb))
    
    # Delete temporary sets
    for help_set in ['_plane_nodes', '_inner_nodes', '_outer_nodes']:
        if help_set in wheel_part.sets.keys():
            del wheel_part.sets[help_set]
            
    return sc
    
    
    
    
    
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
from abaqus import mdb
import part, sketch, mesh, job

# Project imports
from rollover.three_d.utils import sketch_tools
from rollover.utils import abaqus_python_tools as apt
from rollover.utils import naming_mod as names


# Constants
BB_TOL = 1.e-2 # Tolerance for generating bounding boxes. It must be 
               # smaller than node spacing. However, tolerances are not 
               # so good for bounding boxes...
   
def generate(wheel_param):
    """Create the wheel substructure for a 3d wheel and return the job
    object. The job is not submitted. 
    
    :param wheel_param: The model containing the wheel part. The 
                        dictionary should contain arguments to
                        :py:func:`generate_2d_mesh`, except 
                        `wheel_model`. It should also contain
                        `wheel_angles`, see 
                        :py:func:`create_retained_set`. 
    :type wheel_param: dict
    
    :returns: The job object, allowing submission of job or writing to 
              input file if desired. 
    :rtype: Job object (Abaqus)

    """
    # Setup the wheel model and part
    wheel_model = apt.create_model('WHEEL_SUBSTRUCTURE')
    wheel_part = wheel_model.Part(name=names.wheel_part, dimensionality=THREE_D, 
                                  type=DEFORMABLE_BODY)
    
    # Create the 2d section mesh
    possible_section_param = list(wheel.generate_2d_mesh.__code__.co_varnames)
    possible_section_param.remove('wheel_model')
    wheel_section_param = {key: wheel_param[key] for key in wheel_param 
                           if key in possible_section_param}
    section_bb = wheel.generate_2d_mesh(wheel_model, **wheel_section_param)
    
    # Revolve 2d mesh to obtain 3d mesh
    wheel.generate_3d_mesh(wheel_model, wheel_param['mesh_sizes'])
    
    # Create retained node set
    wheel.create_retained_set(wheel_part, wheel_param['wheel_angles'])
    
    # Create inner node set
    wheel.create_inner_set(wheel_part, section_bb)
    
    # Setup mtx file output
    
    
    # Create job
    job = setup_simulation(wheel_model)
    
    return job
    

def generate_2d_mesh(wheel_model, wheel_profile, mesh_sizes, wheel_contact_pos, partition_line, 
                     fine_mesh_edge_bb=None, quadratic_order=True):
    """Generate a mesh of the wheel profile
    
    :param wheel_model: The model containing the wheel part
    :type wheel_model: Model object (Abaqus)
    
    :param wheel_profile: Path to an Abaqus sketch profile saved as .sat 
                          file (acis)
    :type wheel_profile: str
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, 
                       mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :param wheel_contact_pos: min and max x-coordinate for the wheel 
                              contact region (retained dofs)
    :type wheel_contact_pos: list[ float ] (len=2)
    
    :param partition_line: y-value for the line where the wheel profile 
                           will be partitioned to give a better mesh 
                           value.
    
    :param fine_mesh_edge_bb: Dictionary with bounding box parameters 
                              for determining which edges the fine mesh 
                              should be applied to. Keys are 'xMin', 
                              'yMax', etc. If None, set 
                              h = partition_line*(1+1.e-6) and set 
                              'yMax' to h if partition_line < 0 or 
                              'yMin' to h if partition_line > 0. The 
                              adjustment ensures that the partition line 
                              is not included amongst the fine mesh 
                              edges.
    :type fine_mesh_edge_bb: dict
    
    :param quadratic_order: Should quadratic elements be used, default 
                            is True
    :type quadratic_order: bool
    
    :returns: Bounding box for the generated mesh, given by points with 
              keys 'low' and 'high'
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
    
    return wheel_part.nodes.getBoundingBox()


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
        
    all_nodes = wheel_part.nodes if considered_nodes is None else considered_nodes
    
    c1 = (x0[0]-BB_TOL, 0.0, 0.0)
    c2 = (x0[0]+BB_TOL, 0.0, 0.0)
    r = np.sqrt(x0[1]**2 + x0[2]**2)
    
    sp = wheel_part.Set(name='_plane_nodes', 
                        nodes=all_nodes.getByBoundingCylinder(center1=c1, center2=c2, 
                                                              radius=r+BB_TOL))
                                                              
    inner_nodes = all_nodes.getByBoundingCylinder(center1=c1, center2=c2, radius=r-BB_TOL)
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
   
   
def create_inner_set(wheel_part, section_bb):
    
    """Create a set for the nodes on the inner shaft with name
    names.wheel_inner_set. This function assumes that the inner surface 
    is cylindrical.
    
    :param wheel_part: The wheel part containing the orphan 3d mesh
    :type wheel_part: Part object (Abaqus)
    
    :param section_bb: The bounding box for the section mesh in the 
                       xy-plane. Contains x, y, z coordinates given by 
                       keys 'low' and 'high'. 
    :type section_bb: dict
    
    :returns: None
    :rtype: None

    """
    
    r_inner = np.min(np.abs([section_bb['low'][1], section_bb['high'][1]]))
    x_min = section_bb['low'][0]
    x_max = section_bb['high'][0]
    
    inner_nodes = wheel_part.nodes.getByBoundingCylinder(center1=(x_min-1.0, 0.0, 0.0), 
                                                         center2=(x_max+1.0, 0.0, 0.0),
                                                         radius=r_inner + BB_TOL)
                                                         
    wheel_part.Set(name=names.wheel_inner_set, nodes=inner_nodes)
    

def setup_simulation(wheel_model):

    wheel_part = wheel_model.parts[names.wheel_part]
    
    # Setup material with unit elasticity modulus
    unit_elastic_material = wheel_model.Material(name='UnitElastic')
    unit_elastic_material.Elastic(table=((1.0, 0.3), ))
    # Setup section for all elements
    wheel_model.HomogeneousSolidSection(name='SolidWheel', material='UnitElastic')
    
    all_elements = wheel_part.Set(name='ALL_ELEMENTS', elements=wheel_part.elements)
    
    wheel_part.SectionAssignment(region=all_elements, sectionName='SolidWheel')
    
    # Create assembly
    assy = wheel_model.rootAssembly
    wheel_inst = assy.Instance(name=names.wheel_inst, part=wheel_part, dependent=ON)
    
    # Create substructure step
    wheel_model.SubstructureGenerateStep(name='SUBSTRUCTURE', previous='Initial', 
                                         substructureIdentifier=1, recoveryMatrix=NONE)
    
    # Setup retained nodes (contact and reference point)
    contact_set = wheel_inst.sets[names.wheel_contact_nodes]
    wheel_model.RetainedNodalDofsBC(name='BC-1', createStepName='SUBSTRUCTURE', region=contact_set, 
                                    u1=ON, u2=ON, u3=ON, ur1=OFF, ur2=OFF, ur3=OFF)
    
    assy.ReferencePoint(point=(0.0, 0.0, 0.0))
    ref_point_tuple = (assy.referencePoints[assy.referencePoints.keys()[0]],)
    rp_set = assy.Set(referencePoints=ref_point_tuple, name=names.wheel_rp_set)
    
    wheel_model.RetainedNodalDofsBC(name='BC-2', createStepName='SUBSTRUCTURE', region=rp_set, 
                                    u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    inner_set = wheel_inst.sets[names.wheel_inner_set]
    wheel_model.Tie(name='Constraint-1', master=rp_set, slave=inner_set, 
                    positionToleranceMethod=COMPUTED, adjust=ON, 
                    tieRotations=ON, constraintEnforcement=NODE_TO_SURFACE, thickness=ON)
                    
    return mdb.Job(name='WHEEL_SUBSTRUCTURE', model='WHEEL_SUBSTRUCTURE', type=ANALYSIS, numCpus=1)


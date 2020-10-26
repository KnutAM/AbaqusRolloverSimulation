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

# Abaqus imports
from abaqusConstants import *
import part, sketch, mesh

# Project imports
import sketch_tools
import abaqus_python_tools as apt


def create_wheel(wheel_profile, mesh_sizes, wheel_angles, wheel_contact_pos, sym_dir=None):
    """Create a wheel super element
    
    :param wheel_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type wheel_profile: str
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :param wheel_angles: Start and end angle for the wheel wrt. negative y-axis
    :type wheel_angles: list[ float ] (len=2)
    
    :param wheel_contact_pos: min and max x-coordinate for the wheel contact region (retained dofs)
    :type wheel_contact_pos: list[ float ] (len=2)
    
    :param sym_dir: Vector specifying the normal direction if symmetry is used in the wheel profile.
                    If not None, symmetry boundary conditions will be applied. 
    :type sym_dir: list(float) (len=3)
    
    :returns: The model database containing the rail part
    :rtype: Model (Abaqus object)

    """
    pass
    
    
def generate_2d_mesh(wheel_profile, mesh_sizes, wheel_contact_pos, partition_line, 
                     fine_mesh_edge_bb=None, quadratic_order=True):
    """Generate a 2d-mesh of the wheel profile
    
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
    
    :returns: A list of mesh specification as follows:
    
              - Node coordinates (num_nodes x 2)
              - Tri element node numbers (num_tri_elements, 3/6)
              - Quad element node numbers (num_quad_elements, 4/8)
              - Node numbers for contact nodes
              - Node numbers for inner nodes
              
    :rtype: list[ np.array ] (len=5)

    """
    wheel_2d_model = apt.create_model('WHEEL_2D')
    wheel_2d_part = wheel_2d_model.Part(name='WHEEL_2D', dimensionality=TWO_D_PLANAR, 
                                        type=DEFORMABLE_BODY)
    # Create profile
    profile_sketch = sketch_tools.import_sketch(wheel_2d_model, wheel_profile, 
                                                name='wheel_2d_profile')
    wheel_2d_part.BaseShell(sketch=profile_sketch)
    # Create part
    partition_sketch = wheel_2d_model.ConstrainedSketch(name='partition', sheetSize=1.0)
    partition_sketch.Line(point1=(-1000.0, partition_line), point2=(1000.0, partition_line))
    wheel_2d_part.PartitionFaceBySketch(faces=wheel_2d_part.faces[0:1], sketch=partition_sketch)
    
    # Find edges to have fine mesh constraint
    if fine_mesh_edge_bb is None:
        fine_mesh_edge_bb = {('yMin' if partition_line > 0 else 'yMax'): partition_line*(1+1.e-6)}
    
    fine_mesh_edges = wheel_2d_part.edges.getByBoundingBox(**fine_mesh_edge_bb)
    contact_edges = wheel_2d_part.Set(name='contact_edges', edges=fine_mesh_edges)
    wheel_2d_part.seedEdgeBySize(edges=fine_mesh_edges, size=mesh_sizes[0], constraint=FIXED)
    
    # Find edges to have coarse mesh constraint
    max_y = np.max([e.pointOn[0][1] for e in wheel_2d_part.edges])
    coarse_mesh_edges = []
    for e in wheel_2d_part.edges:
        if all([wheel_2d_part.vertices[n].pointOn[0][1] > (max_y - 1.e-3) 
                for n in e.getVertices()]):
            coarse_mesh_edges.append(e)
    
    wheel_2d_part.Set(name='inner_edges', edges=part.EdgeArray(edges=coarse_mesh_edges))
    
    partition_line_edge = wheel_2d_part.edges.getByBoundingBox(yMin=partition_line - 1.e-5,
                                                               yMax=partition_line + 1.e-5)[0]
    coarse_mesh_edges.append(partition_line_edge)
    wheel_2d_part.Set(name='coarse_mesh_edges', edges=part.EdgeArray(edges=coarse_mesh_edges))
    wheel_2d_part.seedEdgeBySize(edges=coarse_mesh_edges, size=mesh_sizes[1], constraint=FIXED)
    
    # Set mesh order
    if quadratic_order:
        elemType1 = mesh.ElemType(elemCode=CPS8R, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=CPS6, elemLibrary=STANDARD)
    else:
        elemType1 = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=CPS3, elemLibrary=STANDARD)
    
    wheel_2d_part.setElementType(regions=(wheel_2d_part.faces,), elemTypes=(elemType1, elemType2))
    
    # Mesh wheel
    wheel_2d_part.generateMesh()
    
    # Add set of contact_nodes
    contact_nodes = contact_edges.nodes.getByBoundingBox(xMin=wheel_contact_pos[0], 
                                                         xMax=wheel_contact_pos[1])
    wheel_2d_part.Set(name='contact_nodes', nodes=contact_nodes)
    
    return get_2d_mesh(wheel_2d_part)
    
    
def get_2d_mesh(meshed_wheel_part):
    """Extract the 2d-mesh from a meshed 2d Abaqus part. Keeping this separate allows the user to 
    manually mesh a wheel using Abaqus cae (or another tool) if this is desired. 
    
    The part must contain two sets, 'contact_nodes' and 'inner_edges'.
    
    :param meshed_wheel_part: A 2d Abaqus part of a wheel that has been meshed
    :type meshed_wheel_part: Part object (Abaqus)
    
    :returns: A list of mesh specification as follows:
    
              - Node coordinates (num_nodes x 2)
              - Tri element node numbers (num_tri_elements, 3/6)
              - Quad element node numbers (num_quad_elements, 4/8)
              - Node numbers for contact nodes
              - Node numbers for inner nodes
              
    :rtype: list[ np.array ] (len=5)

    """
    
    node_coords = []
    contact_nodes = []
    inner_nodes = []
    for i, n in enumerate(meshed_wheel_part.nodes):
        node_coords.append(n.coordinates)
        if n in meshed_wheel_part.sets['contact_nodes'].nodes:
            contact_nodes.append(i)
        elif n in meshed_wheel_part.sets['inner_edges'].nodes:
            inner_nodes.append(i)
    node_coords = np.array(node_coords, dtype=np.float)
    contact_nodes = np.array(contact_nodes, dtype=np.int)
    inner_nodes = np.array(inner_nodes, dtype=np.int)
    
    tri_elems = []
    quad_elems = []
    if len(meshed_wheel_part.elements[0].connectivity) in [3, 4]:
        NUM_TRI = 3
        NUM_QUAD = 4
    elif len(meshed_wheel_part.elements[0].connectivity) in [6, 8]:
        NUM_TRI = 6
        NUM_QUAD = 8
    else:
        raise ValueError('Cannot determine element order')
        
    for e in meshed_wheel_part.elements:
        nodes = e.connectivity
        if len(nodes)==NUM_TRI:
            tri_elems.append(nodes)
        elif len(nodes)==NUM_QUAD:
            quad_elems.append(nodes)
        else:
            if len(nodes) in [3,4,6,8]:
                raise ValueError('Looks like there is a varying element order in the mesh')
            else:
                raise ValueError('Element with ' + str(len(nodes)) + ' nodes is not supported')
    
    tri_elems = np.array(tri_elems, dtype=np.int)
    quad_elems = np.array(quad_elems, dtype=np.int)
    
    return node_coords, tri_elems, quad_elems, contact_nodes, inner_nodes
    
    
def revolve_mesh(nodes_2d, elements_2d, contact_nodes_2d, inner_nodes_2d, mesh_fine):
    """Given a 2d mesh, create a 3d revolved mesh
    
    :param nodes_2d: Node coordinates for the 2d-mesh
    :type nodes_2d: np.array(dtype=np.int)
    
    :param elements_2d: Element node numbers for the 2d-mesh
    :type elements_2d: np.array(dtype=np.int)
    
    :param contact_nodes_2d: Indices for nodes that will be in contact
    :type contact_nodes_2d: np.array(dtype=np.int)
    
    :param inner_nodes_2d: Indices for nodes that will be constrained to the control point
    :type inner_nodes_2d: np.array(dtype=np.int)
    
    :param mesh_fine: The mesh size to be used when revolving the mesh
    :type mesh_fine: float
    
    :returns: A list of mesh specification as follows:
    
              - Node coordinates (num_nodes x 3)
              - WEDGE element node numbers (num_tri_elements, 6/15)
              - HEX element node numbers (num_quad_elements, 8/20)
              - Node numbers for contact nodes
              - Node numbers for inner nodes
              
    :rtype: list[ np.array(dtype=np.float), np.array(dtype=np.int) ]

    """
    pass
    
    
def write_input(nodes_3d, elements_3d, retained_nodes):
    pass
    

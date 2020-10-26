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
import part
import sketch

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
    
    
def generate_2d_mesh(wheel_profile, mesh_sizes, partition_line, fine_mesh_edge_bb=None):
    """Generate a 2d-mesh of the wheel profile
    
    :param wheel_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type wheel_profile: str
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :param partition_line: y-value for the line where the wheel profile will be partitioned to 
                           give a better mesh value.
    
    :param fine_mesh_edge_bb: Dictionary with bounding box parameters for determining which edges 
                              the fine mesh should be applied to. Keys are 'xMin', 'yMax', etc. 
                              If None, set h = partition_line*(1+1.e-6) and set 'yMax' to h if
                              partition_line < 0 or 'yMin' to h if partition_line > 0. The 
                              adjustment ensures that the partition line is not included amongst the 
                              fine mesh edges.
    :type fine_mesh_edge_bb: dict
    
    :returns: Node coordinates (num_nodes x 3) and 
              element node numbers (num_elements x num_element_nodes)
    :rtype: list[ np.array(dtype=np.float), np.array(dtype=np.int) ]

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
    
    print fine_mesh_edge_bb
    fine_mesh_edges = wheel_2d_part.edges.getByBoundingBox(**fine_mesh_edge_bb)
    wheel_2d_part.Set(name='fine_mesh_edges', edges=fine_mesh_edges)
    wheel_2d_part.seedEdgeBySize(edges=fine_mesh_edges, size=mesh_sizes[0], constraint=FIXED)
    
    # Find edges to have coarse mesh constraint
    max_y = np.max([e.pointOn[0][1] for e in wheel_2d_part.edges])
    coarse_mesh_edges = []
    for e in wheel_2d_part.edges:
        if all([wheel_2d_part.vertices[n].pointOn[0][1] > (max_y - 1.e-3) 
                for n in e.getVertices()]):
            coarse_mesh_edges.append(e)
    partition_line_edge = wheel_2d_part.edges.getByBoundingBox(yMin=partition_line - 1.e-5,
                                                               yMax=partition_line + 1.e-5)[0]
    coarse_mesh_edges.append(partition_line_edge)
    wheel_2d_part.Set(name='coarse_mesh_edges', edges=part.EdgeArray(edges=coarse_mesh_edges))
    wheel_2d_part.seedEdgeBySize(edges=coarse_mesh_edges, size=mesh_sizes[1], constraint=FIXED)
    
    # Mesh wheel
    wheel_2d_part.generateMesh()
    
    
    

def get_2d_mesh(meshed_wheel_part):
    """Extract the 2d-mesh from a meshed 2d Abaqus part. Keeping this separate allows the user to 
    manually mesh a wheel using Abaqus cae (or another tool) if this is desired. 
    
    :param meshed_wheel_part: A 2d Abaqus part of a wheel that has been meshed
    :type meshed_wheel_part: Part object (Abaqus)
    
    :returns: Node coordinates (num_nodes x 2) and 
              element node numbers (num_elements x num_element_nodes)
    :rtype: list[ np.array(dtype=np.float), np.array(dtype=np.int) ]

    """
    
    
def revolve_mesh(nodes_2d, elements_2d, mesh_fine):
    """Given a 2d mesh, create a 3d revolved mesh
    
    :param nodes_2d: Node coordinates for the 2d-mesh
    :type nodes_2d: np.array(dtype=np.int)
    
    :param elements_2d: Element node numbers for the 2d-mesh
    :type elements_2d: np.array(dtype=np.int)
    
    :param mesh_fine: The mesh size to be used when revolving the mesh
    :type mesh_fine: float
    
    :returns: Node coordinates (num_nodes x 3) and 
              element node numbers (num_elements x num_element_nodes)
    :rtype: list[ np.array(dtype=np.float), np.array(dtype=np.int) ]

    """
    pass
    
    
def write_input(nodes_3d, elements_3d, retained_nodes):
    pass
    

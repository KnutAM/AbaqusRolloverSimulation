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
    
       
def revolve_mesh(nodes_2d, elements_2d, contact_nodes_2d, inner_nodes_2d, mesh_fine):
    """Given a 2d mesh, create a 3d revolved mesh
    
    :param nodes_2d: Node coordinates for the 2d-mesh
    :type nodes_2d: np.array() (shape=[nnod x 3])
    
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
    

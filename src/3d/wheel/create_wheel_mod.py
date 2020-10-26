"""Create a wheel super element

1) Create a 2-d wheel section mesh using abaqus cae
2) Based on this mesh, generate an input file for a full 3d-wheel 
3) Run the input file to obtain the substructure stiffness matrix
4) Add the stiffness matrix to a static library that can be referenced when creating the user 
   subroutine

.. codeauthor:: Knut Andreas Meyer
"""

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
    
    
def generate_2d_mesh(wheel_profile, mesh_sizes):
    """Generate a 2d-mesh of the wheel profile
    
    :param wheel_profile: Path to an Abaqus sketch profile saved as .sat file (acis)
    :type wheel_profile: str
    
    :param mesh_sizes: Mesh sizes, mesh_sizes[0]=fine mesh in contact, mesh_sizes[1] coarse mesh
    :type mesh_sizes: list[ float ] (len=2)
    
    :returns: Node coordinates (num_nodes x 3) and 
              element node numbers (num_elements x num_element_nodes)
    :rtype: list[ np.array(dtype=np.float), np.array(dtype=np.int) ]

    """
    pass
    

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
    

"""This module is used to include a wheel super element in the analysis

.. codeauthor:: Knut Andreas Meyer
"""

import shutil
import numpy as np

from abaqus import mdb
from abaqusConstants import *
import regionToolset, mesh

from rollover.utils import naming_mod as names
from rollover.utils import inp_file_edit as inp_edit


def from_folder(the_model, folder, translation, stiffness=210.e3, symmetric=False):
    """Include a wheel super element from a folder.
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param folder: The path to the folder containing the wheel super 
                   element. The folder must contain
                   
                   - names.uel_coordinates_file
                   - names.uel_elements_file
                   - names.uel_stiffness_file
                   
    :type folder: str
    
    :param translation: Translation on the wheel part when adding the 
                        instance to the assembly.
    :type translation: list[ float ] (len=3)
    
    :param stiffness: The wheel's modulus of elasticity
    :type stiffness: float
    
    :param symmetric: Should a symmetry set in the yz-plane be created?
    :type symmetric: bool
    
    :returns: stiffness
    :rtype: float
    
    """
    
    wheel_stiffness = stiffness
    
    coords = np.load(folder + '/' + names.uel_coordinates_file)
    element_connectivity = np.load(folder + '/' + names.uel_elements_file)
    
    wheel_part = the_model.Part(name=names.wheel_part, dimensionality=THREE_D, 
                                type=DEFORMABLE_BODY)
    # Add wheel control (center) reference point
    rp_node = wheel_part.Node(coordinates=(0.0, 0.0, 0.0))
    
    # Add wheel contact mesh
    nodes = [wheel_part.Node(coordinates=coord) for coord in coords]
    elems = []
    for ec in element_connectivity:
        enodes = [nodes[i] for i in ec]
        elems.append(wheel_part.Element(nodes=enodes, elemShape=QUAD4))
    
    # Set element type to membrane elements
    membrane_element_type = mesh.ElemType(elemCode=M3D4, elemLibrary=STANDARD)
    wheel_part.setElementType(regions=(wheel_part.elements, ), elemTypes=(membrane_element_type, ))
    
    # Create sets and surfaces
    wheel_part.Set(name=names.wheel_rp_set, nodes=mesh.MeshNodeArray(nodes=(rp_node,)))
    wheel_part.Set(name=names.wheel_contact_nodes, nodes=mesh.MeshNodeArray(nodes=nodes))
    wheel_part.Surface(name=names.wheel_contact_surf, side2Elements=wheel_part.elements)
    if symmetric:
        wheel_part.Set(name=names.wheel_sym_set, nodes=wheel_part.nodes.getByBoundingBox(xMin=-1.e-6, xMax=1.e-6))
    
    # Add a zero stiffness section and very thin section.
    region = regionToolset.Region(elements=wheel_part.elements)
    the_model.Material(name='WheelDummyElastic')
    the_model.materials['WheelDummyElastic'].Elastic(table=((1.0, 0.3)    , ))
    the_model.MembraneSection(name=names.wheel_dummy_contact_sect, 
                              material='WheelDummyElastic', thickness=1.e-9)
    wheel_part.SectionAssignment(region=region, sectionName=names.wheel_dummy_contact_sect)
    
    
    assy = the_model.rootAssembly
    assy.Instance(name=names.wheel_inst, part=wheel_part, dependent=ON)
    
    assy.translate(instanceList=(names.wheel_inst, ), vector=translation)
    
    shutil.copy(folder + '/' + names.uel_stiffness_file, '.')
    
    return stiffness
    

def add_wheel_super_element_to_inp(the_model, stiffness):
    """
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param stiffness: The wheel's modulus of elasticity
    :type stiffness: float
    
    """
    
    wheel_part = the_model.parts[names.wheel_part]
    
    assy = the_model.rootAssembly
    if assy.isOutOfDate:
        assy.regenerate()
    
    kwb = the_model.keywordBlock
    
    kwb.synchVersions(storeNodesAndElements=True)
    
    # Add element definition at beginning of input file
    inp_edit.add_after(kwb, get_inp_str_element_definition(wheel_part))
    
    # Search 
    find_strings = ['*Part', 'name='+names.wheel_part]
    inp_edit.add_at_end_of_cat(kwb, get_inp_str_element_connectivity(wheel_part), 
                               category='Part', name=names.wheel_part)
    
    inp_edit.add_at_end_of_cat(kwb, get_inp_str_element_property(stiffness), 
                               category='Part', name=names.wheel_part)
    
    

def get_inp_str_element_definition(wheel_part):
    num_nodes = len(wheel_part.nodes)
    inp_str = '*USER ELEMENT, TYPE=U1, NODES=%u, COORDINATES=3, PROPERTIES=1\n' % num_nodes
    inp_str = inp_str + '1, 2, 3, 4, 5, 6\n2, 1, 2, 3'
    return inp_str
    

def get_inp_str_element_connectivity(wheel_part):
    """ Return the string used in the Abaqus input file to define how
    the user element is connected to the wheel nodes. 
    
    .. note:: The nodes in the set 
              `wheel_part.sets[names.wheel_contact_nodes]` must be 
              ordered in the same order as for the nodes in the 
              `names.uel_coordinates_file`. Currently, this is assumed.
              An alternative approach could be to read that file and 
              get the label from each node matching those coordinates. 
    
    Excerpt from Abaqus manual:

    Data lines to define the elements:

    - First line

      - Element number.
      - First node number forming the element.
      - Second node number forming the element.
      - Etc., up to 15 node numbers on this line.

    - Continuation lines (only needed if the previous line ends with a comma)

      - Node numbers forming the element.

    Repeat this set of data lines as often as necessary, with up to 16 integer values per line (maximum 80 characters).

    """ 
    rp_node = wheel_part.sets[names.wheel_rp_set].nodes[0]
    contact_nodes = wheel_part.sets[names.wheel_contact_nodes].nodes
    element_number = len(wheel_part.elements) + 1
    
    inp_str = '*Element, type=U1, ELSET=WHEEL_SUPER_ELEMENT\n'
    
    inp_str = inp_str + '%u, ' % element_number
    inp_str = inp_str + '%u, ' % rp_node.label
    num_per_line = 2    # Already 2 items placed
    for node in contact_nodes:
        # Check if line has become too long, use 70 chars as limit for
        # safety against 80. This allows node label value up to 10^8-1
        if num_per_line >= 16 or len(inp_str.split('\n')[-1]) > 70:
            inp_str = inp_str + '\n'
            num_per_line = 0
            
        inp_str = inp_str + '%u, ' % node.label
        num_per_line = num_per_line + 1
        
    return inp_str[:-2] # Remove last comma and space
    

def get_inp_str_element_property(stiffness):
    inp_str = '*UEL PROPERTY, ELSET=WHEEL_SUPER_ELEMENT\n'
    inp_str = inp_str + str(stiffness)
    return inp_str
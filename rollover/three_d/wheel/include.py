"""This module is used to include a wheel super element in the analysis

.. codeauthor:: Knut Andreas Meyer
"""

from __future__ import print_function

import shutil
import numpy as np

from abaqus import mdb
from abaqusConstants import *
import regionToolset, mesh

from rollover.utils import naming_mod as names
from rollover.utils import inp_file_edit as inp_edit
from rollover.local_paths import data_path
from rollover.utils import abaqus_python_tools as apt

def from_folder(the_model, folder, translation, start_labels=[1,1], 
                stiffness=210.e3, symmetric=False):
    """Include a wheel super element from a folder.
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param folder: The path to the folder containing the wheel super 
                   element. A path starting with ':/' is equivalent to 
                   the full path starting from the data folder. The 
                   folder must contain
                   
                   - names.uel_coordinates_file
                   - names.uel_elements_file
                   - names.uel_stiffness_file
                   
    :type folder: str
    
    :param translation: Translation on the wheel part when adding the 
                        instance to the assembly.
    :type translation: list[ float ] (len=3)
    
    :param start_labels: The node and element labels from which the 
                         wheel node/element labeling start.
    :type start_labels: list[ int ]
    
    :param stiffness: The wheel's modulus of elasticity
    :type stiffness: float
    
    :param symmetric: Should a symmetry set in the yz-plane be created?
    :type symmetric: bool
    
    :returns: stiffness
    :rtype: float
    
    """
    
    node_lab0 = start_labels[0]
    elem_lab0 = start_labels[1]
    wheel_stiffness = stiffness
    
    if folder.startswith(':/'):
        folder = data_path + folder[1:]
        
    coords = np.load(folder + '/' + names.uel_coordinates_file)
    element_connectivity = np.load(folder + '/' + names.uel_elements_file)
    
    wheel_part = the_model.Part(name=names.wheel_part, dimensionality=THREE_D, 
                                type=DEFORMABLE_BODY)
    # Add wheel control (center) reference point
    rp_node = wheel_part.Node(coordinates=(0.0, 0.0, 0.0), label=node_lab0)
    
    # Add wheel contact mesh
    nodes = [wheel_part.Node(coordinates=coord, label=node_lab0+i+1) 
             for i, coord in enumerate(coords)]
    elems = []
    elem_shape = QUAD4 if len(element_connectivity[0])==4 else QUAD8
    for i, ec in enumerate(element_connectivity):
        enodes = [nodes[i] for i in ec]
        elems.append(wheel_part.Element(nodes=enodes, elemShape=elem_shape,
                                        label=elem_lab0+i))
    
    # Set element type to membrane elements
    elem_code = M3D4 if elem_shape==QUAD4 else M3D8
    membrane_element_type = mesh.ElemType(elemCode=elem_code, elemLibrary=STANDARD)
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
    

def add_wheel_super_element_to_inp(the_model, stiffness, wheel_folder,
                                   wheel_translation):
    """
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param stiffness: The wheel's modulus of elasticity
    :type stiffness: float
    
    :param wheel_folder: The folder containing the wheel information
    :type wheel_folder: str
    
    :param wheel_translation: Translation of wheel when added to assy.
    :type wheel_translation: list[ float ] (len=3)
    
    """
    print('start add_wheel_super_element_to_inp...')
    wheel_part = the_model.parts[names.wheel_part]
    
    assy = the_model.rootAssembly
    if assy.isOutOfDate:
        print('Regenerating...')
        assy.regenerate()
        print('assy regenerated')
    
    kwb = the_model.keywordBlock
    print('syncing...')
    kwb.synchVersions(storeNodesAndElements=True)
    print('sync done')
    
    # Add element definition at beginning of input file
    inp_edit.add_after(kwb, get_inp_str_element_definition(wheel_part))
    print('elem def added')
    # Search 
    find_strings = ['*Part', 'name='+names.wheel_part]
    elem_conn = get_inp_str_element_connectivity(wheel_part, wheel_folder)
    try:
        inp_edit.add_at_end_of_cat(kwb, elem_conn, 
                                   category='Part', name=names.wheel_part)
        inp_edit.add_at_end_of_cat(kwb, get_inp_str_element_property(stiffness), 
                                   category='Part', name=names.wheel_part)
    except: # If no parts exists, then try to add for case without parts
            # In that case only instances are put in, and labels should
            # be taken from those. 
        print('Could not add wheel as part, trying as instance')
        wheel_inst = assy.instances[names.wheel_inst]
        find_strings = ['*Nset, nset=' + names.wheel_inst + '_' + names.wheel_rp_set]
        elem_conn = get_inp_str_element_connectivity(wheel_inst, wheel_folder, wheel_translation)
        inp_edit.add_before(kwb, get_inp_str_element_property(stiffness), find_strings)
        inp_edit.add_before(kwb, elem_conn, find_strings)
        print('Wheel element added as instance')
        
    print('elem connectivity added')

    
    

def get_inp_str_element_definition(wheel_part):
    num_nodes = len(wheel_part.nodes)
    inp_str = '*USER ELEMENT, TYPE=U1, NODES=%u, COORDINATES=3, PROPERTIES=1\n' % num_nodes
    inp_str = inp_str + '1, 2, 3, 4, 5, 6\n2, 1, 2, 3'
    return inp_str
    

def get_inp_str_element_connectivity(wheel, wheel_folder, translation=[0.0, 0.0, 0.0]):
    """ Return the string used in the Abaqus input file to define how
    the user element is connected to the wheel nodes. 
    
    :param wheel: Meshed wheel part or instance
    :type wheel: Part object (Abaqus) or Instance object (Abaqus)
    
    :param wheel_folder: Folder with wheel specification
    :type wheel_folder: str
    
    :returns: The string used in the Abaqus input file
    :rtype: str
    
    Excerpt from Abaqus manual:

    Data lines to define the elements:

    - First line

      - Element number.
      - First node number forming the element.
      - Second node number forming the element.
      - Etc., up to 15 node numbers on this line.

    - Continuation lines (only needed if the previous line ends with a 
      comma)

      - Node numbers forming the element.

    Repeat this set of data lines as often as necessary, with up to 16 
    integer values per line (maximum 80 characters).

    """ 
    
    rp_node = wheel.sets[names.wheel_rp_set].nodes[0]
    contact_nodes = get_contact_nodes(wheel, wheel_folder, translation)
    element_number = len(wheel.elements) + 1
    
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

    
def get_contact_nodes(wheel, wheel_folder, translation=[0.0, 0.0, 0.0]):
    """ Get the contact nodes in the order described by coordinates in 
    names.uel_coordinates_file in the wheel_folder. 
    
    :param wheel: Meshed wheel part or instance
    :type wheel: Part object (Abaqus) or Instance object (Abaqus)
    
    :param wheel_folder: Folder with wheel specification
    :type wheel_folder: str
    
    :returns: A list of contact nodes, with the order from 
              names.uel_coordinates_file.
    :rtype: list[ Mesh node object (Abaqus) ]
    
    """
    
    tol = 1.e-6
    
    cn_from_set = wheel.sets[names.wheel_contact_nodes].nodes
    if wheel_folder.startswith(':/'):
        wheel_folder = data_path + wheel_folder[1:]
    coords = np.load(wheel_folder + '/' + names.uel_coordinates_file)
    
    contact_nodes = []
    def get_bb(the_coord):
        return {axis + side: translate + value + d*tol
                for axis, value, translate in zip(['x', 'y', 'z'], the_coord, translation)
                for side, d in zip(['Min', 'Max'], [-1, 1])}
                
    print(wheel.nodes.getBoundingBox())
    for coord in coords:
        contact_node = wheel.nodes.getByBoundingBox(**get_bb(coord))
        if len(contact_node) == 0:
            raise ValueError('Could not find the correct node')
        elif len(contact_node) > 1:
            raise ValueError('Multiple contact nodes found')
        contact_nodes.append(contact_node[0])

    return contact_nodes


def get_inp_str_element_property(stiffness):
    inp_str = '*UEL PROPERTY, ELSET=WHEEL_SUPER_ELEMENT\n'
    inp_str = inp_str + str(stiffness)
    return inp_str
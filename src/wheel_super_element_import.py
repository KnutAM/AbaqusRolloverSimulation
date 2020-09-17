# System imports
import sys, os, inspect, json, time
import numpy as np
from shutil import copyfile

# Abaqus imports 
from abaqusConstants import *
import abaqus
import assembly
import part
import sketch
import mesh
import section
import regionToolset

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)

import naming_mod as names
import user_settings
import get_utils as get
import abaqus_python_tools as apt
import inp_file_edit_module as inpmod


def add_wheel_super_element_to_inp():
    # Add add the super_element to the input file.
    # 1) Add element definition
    # 2) Add element nodal connectivity
    # 3) Add element properties
    the_model = get.model()
    assy = get.assy()
    if assy.isOutOfDate:
        assy.regenerate()
    
    kwb = the_model.keywordBlock
    
    inpmod.add_after(kwb, get_inp_str_element_definition())
    find_strings = ['*Part', 'name='+names.wheel_part]
    inpmod.add_after(kwb, get_inp_str_element_connectivity(), find_strings)
    inpmod.add_after(kwb, get_inp_str_element_property(), find_strings)


def get_inp_str_element_definition():
    winfo = get_wheel_info()
    num_nodes = winfo['num_nodes']
    inp_str = '*USER ELEMENT, TYPE=U1, NODES=%u, COORDINATES=3, PROPERTIES=1\n' % num_nodes
    inp_str = inp_str + '1, 2, 6\n2, 1, 2'
    return inp_str
    

def get_inp_str_element_connectivity():
    winfo = get_wheel_info()
    num_nodes = winfo['num_nodes']
    inp_str = '*Element, type=U1, ELSET=WHEEL_SUPER_ELEMENT\n'
    con_parts = ['%u' % num_nodes]*2
    inp_str = inp_str + ', '.join(['%u' % num_nodes]*2 + ['%u' % i for i in range(1, num_nodes)])
    apt.log('get_inp_str_element_connectivity returns:')
    apt.log(inp_str)
    return inp_str
    

def get_inp_str_element_property():
    inp_str = '*UEL PROPERTY, ELSET=WHEEL_SUPER_ELEMENT\n'
    inp_str = inp_str + str(user_settings.materials['wheel']['mpar']['E'])
    return inp_str
    

def setup_wheel():
    # Move super_element data (compiled routine, uel_coords.npy) to cwd
    # Create contact part (with dummy elements for contact) and reference point for control
    #   Also create sets allowing these nodes to be found later when editing the input file
    
    move_super_element_to_cwd()
    
    define_contact_surface_mesh_part()
    
    rp_node_set = get_rp_node_set()


def move_super_element_to_cwd():
    se_path = user_settings.super_element_path
    filenames = ['uel_coords.npy', 'uel_info.json']
    uel_lib = 'uel.for' if os.name=='nt' else 'uel.f'
    filenames.append(uel_lib)
    for filename in filenames:
        try:
            copyfile(se_path + '/' + filename, os.getcwd() + '/' + filename)
        except:
            apt.log('Could not find ' + filename + ' in ' + se_path)
            raise
    
    
def define_contact_surface_mesh_part():
    the_model = get.model()
    assy = get.assy()
    
    x0 = 0.0
    y0 = 0.0
    
    winfo = get_wheel_info()
    
    xrel = winfo['xrel']
    yrel = winfo['yrel']
    radius = winfo['outer_diameter']/2.0
    
    angles = np.arctan2(xrel,-yrel)
    minang = np.min(angles)
    maxang = np.max(angles)
    num_nodes =len(angles)
    
    # Create part and add instance to assembly
    wheel_part = the_model.Part(name=names.wheel_part, dimensionality=TWO_D_PLANAR, 
                                  type=DEFORMABLE_BODY)
    wheel_inst = assy.Instance(name=names.wheel_inst, part=wheel_part, dependent=ON)
    
    the_sketch = the_model.ConstrainedSketch(name='__contact_surface__', sheetSize=200.0)
    the_sketch.setPrimaryObject(option=STANDALONE)
    
    # Note: If this direction is changed, the contact_surface definition must be updated accordingly
    the_sketch.ArcByCenterEnds(center=(0.0, y0), direction=COUNTERCLOCKWISE,
                               point1=(x0 + radius*np.sin(minang), y0 - radius * np.cos(minang)), 
                               point2=(x0 + radius*np.sin(maxang), y0 - radius * np.cos(maxang)))
    wheel_part.BaseWire(sketch=the_sketch)
    
    # Generate mesh
    edge = wheel_part.edges.findAt(((xrel[0], yrel[0], 0.0),))
    wheel_part.seedEdgeByNumber(edges=edge, number=num_nodes-1, constraint=FIXED)
    truss_element = mesh.ElemType(elemCode=T2D2, elemLibrary=STANDARD)
    wheel_part.setElementType(regions=(edge,), elemTypes=(truss_element, ))
    wheel_part.generateMesh()
    
    region = regionToolset.Region(edges=edge)
    wheel_part.SectionAssignment(region=region, 
                                   sectionName=names.wheel_dummy_contact_sect, 
                                   offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', 
                                   thicknessAssignment=FROM_SECTION)
    
    # Note: side2Edges should be used as direction in definition in sketch is COUNTERCLOCKWISE
    #       This ensures that the normal is pointing towards the wheel.
    contact_surface = assy.Surface(side2Edges=wheel_inst.edges.findAt(((xrel[0], yrel[0], 0.),),),
                                   name=names.wheel_contact_surf)
    contact_nodes = wheel_part.Set(edges=wheel_part.edges.findAt(((xrel[0], yrel[0], 0.),),),
                                     name=names.wheel_contact_nodes)
    
def get_wheel_info():
    coords = np.load('uel_coords.npy')
    with open('uel_info.json', 'r') as fid:
        wheel_info = json.load(fid)
    
    wheel_info['xrel'] = coords[0, :]
    wheel_info['yrel'] = coords[1, :]
    wheel_info['num_nodes'] = coords.shape[1]+1
    
    return wheel_info
    
    
def get_rp_node_set():
    assy = get.assy()
    wheel_part = get.part(names.wheel_part)
    wheel_inst = get.inst(names.wheel_inst)
    
    rp = wheel_part.ReferencePoint(point=(0.0, 0.0, 0.0))
    rp_key = wheel_part.referencePoints.keys()[-1]
    assy.regenerate()

    # Make a set that can be accessed later
    wheel_refpoint = assy.Set(referencePoints=(wheel_inst.referencePoints[rp_key],), 
                              name=names.wheel_rp_set)
    
    return wheel_refpoint
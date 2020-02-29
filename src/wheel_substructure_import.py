# System imports
import sys
import os
import numpy as np
import inspect
from shutil import copyfile

# Abaqus imports 
from abaqusConstants import *
import assembly
import part
import sketch
import mesh
import section
import regionToolset

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
sys.path.append(os.path.dirname(src_file_path))

import wheel_toolbox as wtb
import user_settings

def test_script():
    # Settings
    wheel_geometry = user_settings.wheel_geometry
    wheel_mesh = user_settings.wheel_mesh
    wheel_naming = user_settings.wheel_naming   

    the_model = mdb.models.values(0)[0] # Get first model just for testing
    
    assy = the_model.rootAssembly
    substructureFile = user_settings.substructureFile
    odbFile = user_settings.odbFile
    import_wheel_substructure(the_model, assy, wheel_naming, substructureFile, odbFile, wheel_geometry, wheel_mesh)
    

def import_wheel_substructure(the_model, assy, wheel_naming, geometry, the_mesh):
    # Input
    #   the_model   The full abaqus model section_name
    #   assy        The full assembly (for all parts)
    #   geometry    Dictionary describing the geometry
    #    req.        'outer_diameter', 'inner_diameter', 'max_contact_length'
    #   the_mesh    Dictionary describing the mesh parameters
    #    req.        'fine'
    #   naming      Dictionary containing the names for part, section etc.
    #    req.        'part', 'section', 'shadow_section'
    #   
    # Output
    #   the_part            The wheel part
    #   contact_surface     Surface
    #   control_point_reg   Control point (reference point region) to apply boundary conditions for controlling wheel
    #   
    # Modified
    #   the_model       The wheel parts, sketches etc. will be added
    #   assy            Adding surfaces, the wheel part, etc. 
    # -------------------------------------------------------------------------
    
    move_substructure_to_cwd()
    substructureFile = user_settings.substructure_name + '_Z1.sim'
    odbFile = user_settings.substructure_name + '.odb'
    
    the_part = the_model.PartFromSubstructure(name=wheel_naming['part']+'_substr', substructureFile=substructureFile, 
                                              odbFile=odbFile)
    the_inst = assy.Instance(name=wheel_naming['part']+'_substr', part=the_part, dependent=ON)
    
    contact_nodes, contact_nodes_set_name = wtb.define_contact_nodes(the_part, geometry, the_mesh)
    
    contact_part, contact_inst, contact_surface = define_contact_surface_mesh_part(the_model, assy, geometry, the_mesh, contact_nodes, wheel_naming)
    
    the_model.Tie(name='substr_to_contact_surf', master=contact_surface, slave=the_inst.sets[contact_nodes_set_name], 
                  positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
    
    rp_node_set = get_rp_node_set(the_part, the_inst, geometry)
    
    return the_part, contact_surface, rp_node_set


def move_substructure_to_cwd():
    substr_id = 1
    ss_name = user_settings.substructure_name
    ss_path = user_settings.substructure_path
    
    for suffix in ['.odb', '.sup']:
        filename = ss_name + suffix
        copyfile(ss_path + '/' + filename, os.getcwd() + '/' + filename)
    
    for suffix in ['.sim', '.prt', '.stt', '.mdl']:
        filename = ss_name + '_Z' + str(substr_id) + suffix
        copyfile(ss_path + '/' + filename, os.getcwd() + '/' + filename)
    

def define_contact_surface_mesh_part(the_model, assy, geometry, the_mesh, contact_node_set, wheel_naming):
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    radius = geometry['outer_diameter']/2.0
    
    xrel = np.array([n.coordinates[0] - x0 for n in contact_node_set.nodes])
    yrel = np.array([n.coordinates[1] - y0 for n in contact_node_set.nodes])
    
    # radius = np.sqrt(xrel**2 + yrel**2)
    angles = np.arctan2(xrel,-yrel)
    minang = np.min(angles)
    maxang = np.max(angles)
    num_nodes =len(angles)
    
    # Create part and add instance to assembly
    contact_part = the_model.Part(name='contact_part', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    contact_inst = assy.Instance(name='contact_part', part=contact_part, dependent=ON)
    
    the_sketch = the_model.ConstrainedSketch(name='__contact_surface__', sheetSize=200.0)
    the_sketch.setPrimaryObject(option=STANDALONE)
    
    # Note: If this direction is changed, the contact_surface definition must be updated accordingly
    the_sketch.ArcByCenterEnds(center=(0.0, y0), direction=COUNTERCLOCKWISE,
                               point1=(x0 + radius*np.sin(minang), y0 - radius * np.cos(minang)), 
                               point2=(x0 + radius*np.sin(maxang), y0 - radius * np.cos(maxang)))
    contact_part.BaseWire(sketch=the_sketch)
    
    # Generate mesh
    edge = contact_part.edges.findAt(((0.0, 0.0, 0.0),))
    contact_part.seedEdgeByNumber(edges=edge, number=num_nodes-1, constraint=FIXED)
    truss_element = mesh.ElemType(elemCode=T2D2, elemLibrary=STANDARD)
    contact_part.setElementType(regions=(edge,), elemTypes=(truss_element, ))
    contact_part.generateMesh()
    
    region = regionToolset.Region(edges=edge)
    contact_part.SectionAssignment(region=region, sectionName=wheel_naming['contact_section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    # Note: side2Edges should be used as direction in definition in sketch is COUNTERCLOCKWISE
    #       This ensures that the normal is pointing towards the wheel.
    contact_surface = assy.Surface(side2Edges=contact_inst.edges.findAt((( 0., 0., 0.),),),
                                   name='wheel_substr_contact_surface')
    
    return contact_part, contact_inst, contact_surface
    

def get_rp_node_set(the_part, the_inst, geometry):
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    all_nodes = the_part.nodes
    rp_node = None
    for n in all_nodes:
        xrel = n.coordinates[0] - x0
        yrel = n.coordinates[1] - y0
        radius = np.sqrt(xrel**2 + yrel**2)
        if radius < 1.e-6:
            rp_node = n
            break
    
    rp_nodes = mesh.MeshNodeArray([rp_node])
    rp_node_set_name = 'rp_node'
    rp_node_set = the_part.Set(name=rp_node_set_name, nodes=rp_nodes)
    
    rp_node_inst_set = the_inst.sets[rp_node_set_name]
    
    return rp_node_inst_set        

if __name__ == '__main__':
    test_script()

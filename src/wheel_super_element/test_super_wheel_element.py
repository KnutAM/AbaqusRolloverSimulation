# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset, mesh
from abaqusConstants import *

this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)
if not src_path in sys.path:
    sys.path.append(src_path)
if not this_path in sys.path:
    sys.path.append(this_path)

import material_and_section_module as matmod
import contact_module as contactmod
import naming_mod as names
import user_settings
import rail_setup as railmod

reload(matmod)
reload(contactmod)
reload(names)
reload(user_settings)
reload(railmod)

def test_super_wheel():
    model_name = names.get_model(cycle_nr=1)
    if model_name in mdb.models:    # Delete old model if exists
            del(mdb.models[model_name])
        
    the_model = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    the_model.StaticStep(name=names.step1, previous=names.step0, nlgeom=ON)

    matmod.setup_sections(the_model, section_names={'contact': 'contact_section'})
    
    matmod.setup_sections(the_model, 
                          section_names={'wheel': user_settings.wheel_naming['section'],
                                         'rail': user_settings.rail_naming['section'], 
                                         'shadow': user_settings.rail_naming['shadow_section'],
                                         'contact': user_settings.wheel_naming['contact_section']})
    
    contact_part, contact_inst, wheel_contact_surf = define_contact_surface_mesh_part(the_model, 
                                                                                      assy)
    rp = contact_part.ReferencePoint(point=(0.0, 0.0, 0.0))
    rp_key = contact_part.referencePoints.keys()[0]
    assy.regenerate()

    # Make a set that can be accessed later
    wheel_refpoint = assy.Set(referencePoints=(contact_inst.referencePoints[rp_key],), name='RP')
    
    # contact_inst.translate((0., 200., 0.))
    
    # rail_geometry = {'length': 30.0, 'height': 30.0, 
                     # 'max_contact_length': 15}
    # rail_mesh = {'fine': 2.0, 'coarse': 5.0}
    # rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 
                   # 'shadow_section': 'RAIL_SHADOW_SECTION'}
    # rail_part, rail_contact_surf, bottom_reg = railmod.setup_rail(the_model, assy, rail_geometry, 
                                                                  # rail_mesh, rail_naming)
    
    # contactmod.setup_contact(rail_contact_surf, wheel_contact_surf)
    
    # rail_contact_nodes = the_model.rootAssembly.instances['RAIL'].sets['BOTTOM_NODES']
    # the_model.DisplacementBC(name='BC-1', createStepName=names.step0, 
        # region=rail_contact_nodes, u1=SET, u2=SET, ur3=UNSET)
    
    # BC for wheel
    ctrl_bc = the_model.DisplacementBC(name='ctrl_bc', createStepName=names.step1, 
                                       region=wheel_refpoint, u1=0.0, ur3=0.0, 
                                       u2=-0.0)
    

def define_contact_surface_mesh_part(the_model, assy, super_wheel_element='uel'):
    x0 = 0.0
    y0 = 0.0
    
    coords = np.load(super_wheel_element + '_coords.npy')
    xrel = coords[0, :]
    yrel = coords[1, :]
    radius = np.sqrt(xrel[0]**2 + yrel[0]**2)
    
    # radius = np.sqrt(xrel**2 + yrel**2)
    angles = np.arctan2(xrel,-yrel)
    minang = np.min(angles)
    maxang = np.max(angles)
    num_nodes =len(angles)
    
    # Create part and add instance to assembly
    contact_part = the_model.Part(name='contact_part', dimensionality=TWO_D_PLANAR, 
                                  type=DEFORMABLE_BODY)
    contact_inst = assy.Instance(name='contact_part', part=contact_part, dependent=ON)
    
    the_sketch = the_model.ConstrainedSketch(name='__contact_surface__', sheetSize=200.0)
    the_sketch.setPrimaryObject(option=STANDALONE)
    
    # Note: If this direction is changed, the contact_surface definition must be updated accordingly
    the_sketch.ArcByCenterEnds(center=(0.0, y0), direction=COUNTERCLOCKWISE,
                               point1=(x0 + radius*np.sin(minang), y0 - radius * np.cos(minang)), 
                               point2=(x0 + radius*np.sin(maxang), y0 - radius * np.cos(maxang)))
    contact_part.BaseWire(sketch=the_sketch)
    
    # Generate mesh
    edge = contact_part.edges.findAt(((xrel[0], yrel[0], 0.0),))
    contact_part.seedEdgeByNumber(edges=edge, number=num_nodes-1, constraint=FIXED)
    truss_element = mesh.ElemType(elemCode=T2D2, elemLibrary=STANDARD)
    contact_part.setElementType(regions=(edge,), elemTypes=(truss_element, ))
    contact_part.generateMesh()
    
    region = regionToolset.Region(edges=edge)
    contact_part.SectionAssignment(region=region, 
                                   sectionName=user_settings.wheel_naming['contact_section'], 
                                   offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', 
                                   thicknessAssignment=FROM_SECTION)
    
    # Note: side2Edges should be used as direction in definition in sketch is COUNTERCLOCKWISE
    #       This ensures that the normal is pointing towards the wheel.
    contact_surface = assy.Surface(side2Edges=contact_inst.edges.findAt(((xrel[0], yrel[0], 0.),),),
                                   name='wheel_substr_contact_surface')
    
    return contact_part, contact_inst, contact_surface

test_super_wheel()

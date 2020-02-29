# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
from abaqus import mdb
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
from material_and_section_module import setup_sections

import wheel_toolbox as wtb

def test_script():
    # Settings
    wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
    wheel_mesh = {'fine': 40.0, 'coarse': 50.0, 'refine_thickness': 50.0}
    wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER'}
    rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}
    
    substructureFile, odbFile = create_wheel_substructure(wheel_geometry, wheel_mesh, wheel_naming, 'wheel_substr1')
    
    
def create_wheel_substructure(geometry, the_mesh, naming, substructure_name, wait_for_completion=False):
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
    
    # Setup model
    the_model = mdb.Model(name=substructure_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    setup_sections(the_model, naming={'wheel': naming['section']})
    
    # Create part and add instance to assembly
    the_part = the_model.Part(name=naming['part'], dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    inst = assy.Instance(name=naming['part'], part=the_part, dependent=ON)
    
    # Sketch the wheel profile
    sketch = sketch_wheel(the_model, geometry, the_mesh)
    the_part.BaseShell(sketch=sketch)
    sketch.unsetPrimaryObject()
    
    # Partitioning
    partition_sketch = partition_wheel(the_model, geometry, the_mesh)
    the_part.PartitionFaceBySketch(faces=the_part.faces.findAt(((0.0, 1.0, 0.0),)), sketch=partition_sketch)
    
    mesh_wheel(the_part, geometry, the_mesh)
    
    # Assign sections
    define_sections(the_part, geometry, the_mesh, naming)
    
    # Setup control point
    control_point_reg = setup_control_point(the_model, assy, inst, the_part, geometry)
    
    # Define contact surface
    contact_nodes, contact_nodes_set_name = wtb.define_contact_nodes(the_part, geometry, the_mesh)
    
    substr_id = 1
    create_submodel(the_model, inst, contact_nodes_set_name, control_point_reg, substr_id)
    
    the_job = mdb.Job(name=substructure_name, model=substructure_name, type=ANALYSIS, resultsFormat=ODB)
    mdb.jobs[substructure_name].submit()
    if wait_for_completion:
        the_job.waitForCompletion()
    
    cwd = os.getcwd().replace('\\', '/') # Use unix path as this is simpler (and abaqus seem to use this)
    substructureFile = cwd + '/' + substructure_name + '_Z' + str(substr_id) + '.sim'
    odbFile = cwd + '/' + substructure_name + '.odb'
    
    return substructureFile, odbFile
    
            
def sketch_wheel(the_model, geometry, the_mesh):
    sketch = the_model.ConstrainedSketch(name='__wheel_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    sketch.CircleByCenterPerimeter(center=(0.0, geometry['outer_diameter']/2.0), point1=(0.0, 0.0))
    sketch.CircleByCenterPerimeter(center=(0.0, geometry['outer_diameter']/2.0), point1=(0.0, geometry['outer_diameter']/2.0 - geometry['inner_diameter']/2.0))
    
    return sketch


def partition_wheel(the_model, geometry, the_mesh):
    partition_sketch = the_model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    
    split_angles = get_split_angles(geometry, the_mesh)
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    r = geometry['outer_diameter']/2.0 + 1
    for sa in split_angles:
        partition_sketch.Line(point1=(-r * np.sin(sa) + x0, -r * np.cos(sa) + y0), 
                              point2=(r * np.sin(sa) + x0, r * np.cos(sa) + y0))
    
    return partition_sketch
    
    
def mesh_wheel(the_part, geometry, the_mesh):
    split_angles = get_split_angles(geometry, the_mesh)
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    # Define r as average radius of outer and inner
    r = (geometry['outer_diameter'] + geometry['inner_diameter'])/4.0
    for sa in split_angles:
        for sign in [-1, 1]:
            edge = the_part.edges.findAt(((sign * r * np.sin(sa) + x0, sign * r * np.cos(sa) + y0, 0.0),))
            verts = [the_part.vertices[vert_nr] for vert_nr in edge[0].getVertices()]
            dist = [np.linalg.norm(np.array(v.pointOn[0])-np.array([x0, y0, 0.0])) for v in verts]
            if dist[0] < dist[1]:   # Use end1Edges (smallest close to first vertex)
                the_part.seedEdgeByBias(biasMethod=SINGLE, end1Edges=edge, 
                            minSize=the_mesh['fine']*geometry['inner_diameter']/geometry['outer_diameter'], 
                            maxSize=the_mesh['fine'], constraint=FIXED)
            else:                   # Use end2Edges (smallest close to last vertex)
                the_part.seedEdgeByBias(biasMethod=SINGLE, end2Edges=edge, 
                            minSize=the_mesh['fine']*geometry['inner_diameter']/geometry['outer_diameter'], 
                            maxSize=the_mesh['fine'], constraint=FIXED)
                            

    the_part.generateMesh()
    
    
def define_sections(the_part, geometry, the_mesh, naming):
    # Section assignment
    #faces = the_part.faces.findAt(((0., the_mesh['refine_thickness']/2.0, 0.),),((0., 1.5*the_mesh['refine_thickness'], 0.),))
    faces = the_part.faces
    region = the_part.Set(faces=faces, name='wheel')
    the_part.SectionAssignment(region=region, sectionName=naming['section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
        
        
def setup_control_point(the_model, assy, inst, the_part, geometry):
    rp = the_part.ReferencePoint(point=the_part.InterestingPoint(edge=the_part.edges.findAt(((0.,0.,0.),))[0], rule=CENTER))
    rp_key = the_part.referencePoints.keys()[0]
    assy.regenerate()
    
    ## Tie using rigid body reference point to inner diameter of wheel
    # Determine geometry to select only the the inner point. For this to work, the outer diameter must be large enough:
    if geometry['outer_diameter'] < np.sqrt(2)*1.01*geometry['inner_diameter']:
        print('WARNING: Tie constraint for wheel reference point may be wrong.\n' + 
              '         Too small difference between inner and outer diameter')
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    r = geometry['inner_diameter']/2.0 + 0.01 * (geometry['outer_diameter']-geometry['inner_diameter'])/2.0
    
    inner_circle = inst.edges.getByBoundingBox(x0-r,y0-r,0,x0+r,y0+r,0)
    
    wheel_center=assy.Set(edges=inner_circle, name='WheelCenter')
    rp_region=regionToolset.Region(referencePoints=(inst.referencePoints[rp_key],))
    the_model.RigidBody(name='Center', refPointRegion=rp_region, tieRegion=wheel_center)
    
    return rp_region


def get_split_angles(geometry, the_mesh):
    num_el_half_circum = int(0.5 * np.round(np.pi*geometry['outer_diameter']/the_mesh['fine']))
    split_angles = np.linspace(0, np.pi, num_el_half_circum+1)[:-1]
    
    return split_angles


def create_submodel(the_model, inst, contact_node_set_name, rp_ctrl_region, substr_id):
    the_model.SubstructureGenerateStep(name='Step-1', 
        previous='Initial', description='Wheel', substructureIdentifier=substr_id)
    
    the_model.RetainedNodalDofsBC(name='BC-1', createStepName='Step-1', 
        region=inst.sets[contact_node_set_name], u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    
    the_model.RetainedNodalDofsBC(name='BC-2', createStepName='Step-1', 
        region=rp_ctrl_region, u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=ON)
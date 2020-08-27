# System imports
import sys
import os
import numpy as np
import inspect

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
# adapted solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))

from material_and_section_module import setup_sections
import wheel_toolbox as wtools
import user_settings

def test_script():
    # Settings
    wheel_geometry = user_settings.wheel_geometry
    wheel_mesh = user_settings.wheel_mesh
    wheel_naming = user_settings.wheel_naming    
    
    # Setup model
    model = mdb.models.values()[0]
    assy = model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    setup_sections(model, naming={'wheel': wheel_naming['section']})
    
    wheel_part, wheel_contact_surf = setup_wheel(model, assy, wheel_geometry, wheel_mesh, wheel_naming)
    
    
def setup_wheel(model, assy, geometry, mesh, naming):
    # Input
    #   model       The full abaqus model section_name
    #   assy        The full assembly (for all parts)
    #   geometry    Dictionary describing the geometry
    #    req.        'outer_diameter', 'inner_diameter', 'max_contact_length'
    #   mesh        Dictionary describing the mesh parameters
    #    req.        'fine'
    #   naming      Dictionary containing the names for part, section etc.
    #    req.        'part', 'section', 'shadow_section'
    #   
    # Output
    #   part                The rail part
    #   contact_surface     Surface
    #   control_point_reg   Control point (reference point region) to apply boundary conditions for controlling wheel
    #   
    # Modified
    #   model       The rail parts, sketches etc. will be added
    #   assy        adding surfaces, the rail part, etc. 
    # -------------------------------------------------------------------------
    
    # Create part and add instance to assembly
    part = model.Part(name=naming['part'], dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    inst = assy.Instance(name=naming['part'], part=part, dependent=ON)
    
    # Sketch the wheel profile
    sketch = sketch_wheel(model, geometry, mesh)
    part.BaseShell(sketch=sketch)
    sketch.unsetPrimaryObject()
    
    # Partitioning
    partition_sketch = partition_wheel(model, geometry, mesh)
    part.PartitionFaceBySketch(faces=part.faces.findAt(((0.0, 1.0, 0.0),)), sketch=partition_sketch)
    
    mesh_wheel(part, geometry, mesh)
    
    wtools.define_contact_nodes(part, geometry, mesh)
    
    # Assign sections
    define_sections(part, geometry, mesh, naming)
    
    # Define contact surface
    contact_surf = define_contact_surface(assy, inst, part, geometry, mesh)
    
    # Setup control point
    control_point_reg = setup_control_point(model, assy, inst, part, geometry)
        
    return part, contact_surf, control_point_reg
    
    
def partition_wheel(model, geometry, mesh):
    partition_sketch = model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    dias = np.array([geometry['outer_diameter'], geometry['outer_diameter'] - 2*mesh['refine_thickness']])
    refine_angle = geometry['rolling_angle']/2.0 + geometry['max_contact_length']/geometry['outer_diameter']
    dx = dias*np.sin(refine_angle)/2.0
    dy = dias*(1.0 - np.cos(refine_angle))/2.0
    dy[1] = dy[1] + mesh['refine_thickness']
    partition_sketch.ArcByCenterEnds(center=(0.0, geometry['outer_diameter']/2.0), point1=(dx[1], dy[1]), point2=(-dx[1], dy[1]), direction=CLOCKWISE)
    partition_sketch.Line(point1=(-dx[0], dy[0]), point2=(-dx[1], dy[1]))
    partition_sketch.Line(point1=(dx[0], dy[0]), point2=(dx[1], dy[1]))
    
    return partition_sketch
    
        
def sketch_wheel(model, geometry, mesh):
    sketch = model.ConstrainedSketch(name='__wheel_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    sketch.CircleByCenterPerimeter(center=(0.0, geometry['outer_diameter']/2.0), point1=(0.0, 0.0))
    sketch.CircleByCenterPerimeter(center=(0.0, geometry['outer_diameter']/2.0), point1=(0.0, geometry['outer_diameter']/2.0 - geometry['inner_diameter']/2.0))
    
    return sketch

    
def mesh_wheel(part, geometry, mesh):
    part.seedEdgeBySize(edges=part.edges.findAt(((0.0, 0.0, 0.0),)), size=mesh['fine'], deviationFactor=0.1, constraint=FINER)
    part.seedEdgeByBias(biasMethod=DOUBLE, endEdges=part.edges.findAt(((0.0, geometry['outer_diameter'], 0.0),)), minSize=mesh['fine'], maxSize=mesh['coarse'], constraint=FINER)
    part.generateMesh()
    
    
def define_sections(part, geometry, mesh, naming):
    # Section assignment
    faces = part.faces.findAt(((0., mesh['refine_thickness']/2.0, 0.),),((0., 1.5*mesh['refine_thickness'], 0.),))
    region = part.Set(faces=faces, name='wheel')
    part.SectionAssignment(region=region, sectionName=naming['section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
        
        
def define_contact_surface(assy, inst, part, geometry, mesh):
    dx = geometry['max_contact_length']/2.0
    r = geometry['outer_diameter']/2.0
    dy = r - np.sqrt(r**2 - dx**2)
    contact_surface = assy.Surface(side1Edges=inst.edges.findAt((( dx, dy, 0.),),((-dx, dy, 0.),)),
                                   name='wheel_contact_surface')
    return contact_surface
        
        
def setup_control_point(model, assy, inst, part, geometry):
    rp = part.ReferencePoint(point=part.InterestingPoint(edge=part.edges.findAt(((0.,0.,0.),))[0], rule=CENTER))
    rp_key = part.referencePoints.keys()[0]
    assy.regenerate()
    
    ## Tie using rigid body reference point to inner diameter of wheel
    inner_circle = inst.edges.findAt(((0.0, (geometry['outer_diameter']-geometry['inner_diameter'])/2.0, 0.),))
    wheel_center=assy.Set(edges=inner_circle, name='WheelCenter')
    rp_set = part.Set(name='RP_NODE', referencePoints=(part.referencePoints[rp_key],))
    rp_region=regionToolset.Region(referencePoints=(inst.referencePoints[rp_key],))
    model.RigidBody(name='Center', refPointRegion=rp_region, tieRegion=wheel_center)
    
    return rp_region


if __name__ == '__main__':
    test_script()

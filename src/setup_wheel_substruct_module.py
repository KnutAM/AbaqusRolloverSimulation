# System imports
import sys
import os
import numpy as np

# Abaqus imports 
# import abaqusConstants as abaconst
from abaqusConstants import *
#from abaqus import *
import assembly
import part
import sketch
import mesh
import section
import regionToolset

# Custom imports (from present project)
# Should find better way of including by automating the path, however, __file__ doesn't seem to work...
sys.path.append(r'C:\Box Sync\PhD\MyArticles\RolloverSimulationMethodology\AbaqusRolloverSimulation\src')
from material_and_section_module import setup_sections

def test_script_import():
    # Settings
    wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
    wheel_mesh = {'fine': 40.0, 'coarse': 50.0, 'refine_thickness': 50.0}
    wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER'}
    rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}

    
    the_model = mdb.models['rollover']
    assy = the_model.rootAssembly
    substructureFile='c:/work/Abaqus/2017/Temp/Job-1_Z1.sim'
    odbFile='c:/work/Abaqus/2017/Temp/Job-1.odb'
    import_wheel_substructure(the_model, assy, wheel_naming, substructureFile, odbFile, wheel_geometry, wheel_mesh)
    
    
def test_script():
    # Settings
    wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
    wheel_mesh = {'fine': 40.0, 'coarse': 50.0, 'refine_thickness': 50.0}
    wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER'}
    rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}
    
    substructureFile, odbFile = create_wheel_substructure(wheel_geometry, wheel_mesh, wheel_naming, 'wheel_substr1')
    
    
    
def setup_wheel():
    pass
    

def import_wheel_substructure(the_model, assy, wheel_naming, substructureFile, odbFile, geometry, the_mesh):
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
    
    the_part = the_model.PartFromSubstructure(name=wheel_naming['part']+'_substr', substructureFile=substructureFile, 
                                              odbFile=odbFile)
    the_inst = assy.Instance(name=wheel_naming['part']+'_substr', part=the_part, dependent=ON)
    
    contact_nodes, contact_nodes_set_name = define_contact_nodes(the_part, geometry, the_mesh)
    
    contact_part, contact_inst, contact_surface = define_contact_surface_mesh_part(the_model, assy, geometry, the_mesh, contact_nodes, wheel_naming)
    
    # TIE contact surface to nodes!
    
    rp_node_set = get_rp_node_set(the_part, the_inst, geometry)
    
    return the_part, contact_surface, rp_node_set


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
    the_sketch.ArcByCenterEnds(center=(0.0, y0), direction=COUNTERCLOCKWISE,
                               point1=(x0 + radius*np.sin(minang), y0 - radius * np.cos(minang)), 
                               point2=(x0 + radius*np.sin(maxang), y0 - radius * np.cos(maxang)))
    contact_part.BaseWire(sketch=the_sketch)
    
    edge = contact_part.edges.findAt(((0.0, 0.0, 0.0),))
    contact_part.seedEdgeByNumber(edges=edge, number=num_nodes-1, constraint=FIXED)
    contact_part.generateMesh()
    
    region = regionToolset.Region(edges=edge)
    contact_part.SectionAssignment(region=region, sectionName=wheel_naming['contact_section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    contact_surface = assy.Surface(side1Edges=contact_inst.edges.findAt((( 0., 0., 0.),),),
                                   name='wheel_substr_contact_surface')
    
    return contact_part, contact_inst, contact_surface
    

def get_contact_nodes(geometry, the_mesh, nodes):
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    min_radius = geometry['outer_diameter']/2.0 - the_mesh['fine']/100
    max_angle = geometry['rolling_angle']/2.0
    
    node_list = []
    for n in nodes:
        # Coordinates relative wheel center
        xrel = n.coordinates[0] - x0
        yrel = n.coordinates[1] - y0
        radius = np.sqrt(xrel**2 + yrel**2)
        if radius > min_radius:
            angle = np.arccos(-yrel/radius)
            if  angle < max_angle:
                node_list.append(n)
    
    return mesh.MeshNodeArray(node_list)
    
    
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
    setup_sections(the_model, naming={'wheel': naming['section'], 
                                  'rail': 'rail_section',       # Not used in current analysis
                                  'shadow': 'shadow_section'})  # Not used in current analysis
    
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
    contact_nodes, contact_nodes_set_name = define_contact_nodes(the_part, geometry, the_mesh)
    # contact_surf = define_contact_surface(assy, inst, geometry, the_mesh)
    
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
        
        
def define_contact_surface(assy, inst, geometry, the_mesh):
    dx = geometry['max_contact_length']/2.0
    r = geometry['outer_diameter']/2.0
    dy = r - np.sqrt(r**2 - dx**2)
    contact_surface = assy.Surface(side1Edges=inst.edges.findAt((( dx, dy, 0.),),((-dx, dy, 0.),)),
                                   name='wheel_contact_surface')
    return contact_surface
        
        
def define_contact_nodes(the_part, geometry, the_mesh):    
    nodes = get_contact_nodes(geometry, the_mesh, the_part.nodes)
    contact_nodes_set_name = 'contact_nodes'
    contact_nodes = the_part.Set(name=contact_nodes_set_name, nodes=nodes)
    
    return contact_nodes, contact_nodes_set_name
    
        
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
        

if __name__ == '__main__':
    test_script_import()
    #test_script()

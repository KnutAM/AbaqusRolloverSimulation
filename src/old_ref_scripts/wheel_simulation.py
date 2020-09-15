# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset
from abaqusConstants import *
import mesh, interaction, step

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)
if not src_path in sys.path:
    sys.path.append(src_path)

if not this_path in sys.path:
    sys.path.append(this_path)
    
import user_settings
import wheel_super_element_import as wheelmod
import wheel_mesh_tb
reload(user_settings)
reload(wheelmod)

model_name = 'SUPER_WHEEL'
part_name = model_name
inst_name = model_name
job_name = model_name

def create_mesh(the_part, id, od, elsize):
    # Calculate number of elements around circumference. Multiple of 4 to ensure symmetry.
    nel_circumf = 4*int(od*np.pi/(4.0*elsize))
    angles = np.linspace(0, 2*np.pi, nel_circumf + 1)[:-1]  # Remove last element that is duplicated
    radii, nel_radial = wheel_mesh_tb.get_radial_node_pos(id, od, elsize)
    
    for ir, r in zip(range(nel_radial+1), radii):
        for ic, a in zip(range(nel_circumf), angles):
            x = r*np.cos(a)
            y = r*np.sin(a)
            node_nr = wheel_mesh_tb.get_node_nr(ir, ic, nel_radial, nel_circumf)
            the_part.Node(coordinates=(x, y, 0.0), label=node_nr + 1)
    
    for ir in range(nel_radial):
        for ic in range(nel_circumf):
            enodes = [the_part.nodes[i] for i in 
                      wheel_mesh_tb.get_elem_node_nrs(ir, ic, nel_radial, nel_circumf)]
            the_part.Element(nodes=enodes, elemShape=QUAD4, 
                             label=wheel_mesh_tb.get_elem_nr(ir, ic, nel_radial, nel_circumf) + 1)
    
    inner_nodes = [the_part.nodes[wheel_mesh_tb.get_node_nr(nel_radial, ic, nel_radial, nel_circumf)] 
                   for ic in range(nel_circumf)]
    outer_nodes = [the_part.nodes[wheel_mesh_tb.get_node_nr(0, ic, nel_radial, nel_circumf)] 
                   for ic in range(nel_circumf)]
    n1_node = [the_part.nodes[wheel_mesh_tb.get_node_nr(0, 0, nel_radial, nel_circumf)]]
    outer_nodes_without_n1 = [the_part.nodes[wheel_mesh_tb.get_node_nr(0, ic, nel_radial, nel_circumf)] 
                              for ic in range(1,nel_circumf)]
                   
    the_part.Set(nodes=mesh.MeshNodeArray(nodes=inner_nodes), name='INNER_CIRCLE')
    the_part.Set(nodes=mesh.MeshNodeArray(nodes=outer_nodes), name='OUTER_CIRCLE')
    the_part.Set(nodes=mesh.MeshNodeArray(nodes=n1_node), name='N1')
    the_part.Set(nodes=mesh.MeshNodeArray(nodes=outer_nodes_without_n1), name='OUTER_CIRCLE_NOT_N1')

def setup_control_point(the_model, assy, inst, the_part):
    rp = the_part.ReferencePoint(point=(0.0, 0.0, 0.0))
    rp_key = the_part.referencePoints.keys()[0]
    assy.regenerate()

    wheel_inner_circle=inst.sets['INNER_CIRCLE']
    rp_region=regionToolset.Region(referencePoints=(inst.referencePoints[rp_key],))
    the_model.RigidBody(name='Center', refPointRegion=rp_region, tieRegion=wheel_inner_circle)
    
    # Make a set that can be accessed later
    rp_set = assy.Set(referencePoints=(inst.referencePoints[rp_key],), name='RP')
    
    return rp_region


def create_wheel():
    if model_name in mdb.models:    # Delete old model if exists
        del(mdb.models[model_name])
        
    the_model = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    the_part = the_model.Part(name=part_name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    
    od = user_settings.wheel_geometry['outer_diameter']
    id = user_settings.wheel_geometry['inner_diameter']
    elsize = user_settings.wheel_mesh['fine']
    #elsize = od*np.pi/16.1   # For debug
    
    # Create mesh describing the geometry
    create_mesh(the_part, id, od, elsize)
    
    # Apply material
    the_material = the_model.Material(name='Elastic')
    the_material.Elastic(table=((1.0, 0.3), ))
    the_model.HomogeneousSolidSection(name='Section', material='Elastic', thickness=None)
    all_elements_set = the_part.Set(elements=the_part.elements, name='AllElements')
    the_part.SectionAssignment(region=all_elements_set, sectionName='Section')
    
    # Create assembly
    the_inst = assy.Instance(name=inst_name, part=the_part, dependent=ON)
    
    # Create control point and apply tie condition to inner circle of wheel
    setup_control_point(the_model, assy, the_inst, the_part)
    
    
def get_angle_to_minus_y(nodes):
    ang = []
    for n in nodes:
        ang.append(np.arctan2(-n.coordinates[0], -n.coordinates[1]))
    
    return np.array(ang)


def save_node_coords(nodes):
    coords = np.transpose([n.coordinates for n in nodes])
    np.save('uel_coords_tmp.npy', coords)
    

def create_substructure():
    create_wheel()
    
    the_model = mdb.models[model_name]
    the_part = the_model.parts[part_name]
    assy = the_model.rootAssembly
    the_inst = assy.instances[inst_name]
    
    outer_nodes = the_part.sets['OUTER_CIRCLE'].nodes
    angles = get_angle_to_minus_y(outer_nodes)
    
    rolling_angle = user_settings.wheel_geometry['rolling_angle']
    
    contact_nodes = []
    for n, a in zip(outer_nodes, angles):
        if np.abs(a) < np.abs(rolling_angle):
            contact_nodes.append(n)
    
    save_node_coords(contact_nodes)
    
    the_part.Set(nodes=mesh.MeshNodeArray(nodes=contact_nodes), name='CONTACT_NODES')
    
    the_model.SubstructureGenerateStep(name='Step-1', previous='Initial', 
                                       description='Wheel', substructureIdentifier=1,
                                       #recoveryMatrix=NONE,
                                       )
    
    the_model.RetainedNodalDofsBC(name='BC-1', createStepName='Step-1', 
        region=the_inst.sets['CONTACT_NODES'], u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    
    the_model.RetainedNodalDofsBC(name='BC-2', createStepName='Step-1', 
        region=assy.sets['RP'], u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=ON)
    
    if assy.isOutOfDate:
        assy.regenerate()
    kwb = the_model.keywordBlock
    kwb.synchVersions(storeNodesAndElements=False)
    linenum = wheelmod.find_strings_in_iterable(kwb.sieBlocks, ['*End Step'])
    if linenum:
        kwb.insert(linenum-1, '*SUBSTRUCTURE MATRIX OUTPUT, STIFFNESS=YES, ' + 
                   'OUTPUT FILE=USER DEFINED, FILE NAME=' + job_name)
    else:
        print('could not find "*End Step"')
        
    the_job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS, resultsFormat=ODB)
    mdb.jobs[job_name].submit()
    the_job.waitForCompletion()
    
    return job_name
    
    
def simulate():
    create_wheel()
    
    the_model = mdb.models[model_name]
    assy = the_model.rootAssembly
    the_inst = assy.instances[inst_name]
    
    # Setup load steps
    previous = 'Initial'
    for nr in range(1, 5):
        step_name = 'u' + str(nr)
        the_model.StaticStep(name=step_name, previous=previous, maxNumInc=1, 
                             timeIncrementationMethod=FIXED)
        previous = step_name
    
    # Setup loading
    the_model.DisplacementBC(name='FIXED_NODES', createStepName='Initial', 
                             region=the_inst.sets['OUTER_CIRCLE_NOT_N1'], u1=SET, u2=SET)
    # Load u1: Radial (horizontal) loading of node at (x, y) = (od/2, 0)
    bc_n1 = the_model.DisplacementBC(name='N1', createStepName='u1', region=the_inst.sets['N1'], 
                                     u1=1.0, u2=0.0)
    bc_rp = the_model.DisplacementBC(name='RP', createStepName='u1', region=assy.sets['RP'], 
                                     u1=0.0, u2=0.0, ur3=0.0)
    
    # Load u2: Circumferential (vertical) loading of node at (x, y) = (od/2, 0)
    bc_n1.setValuesInStep(stepName='u2', u1=0.0, u2=1.0)
    
    # Load u3: Horizontal loading of reference point
    bc_n1.setValuesInStep(stepName='u3', u1=0.0, u2=0.0)
    bc_rp.setValuesInStep(stepName='u3', u1=1.0, u2=0.0, ur3=0.0)
    
    # Load u4: Rotational loading of reference point
    bc_rp.setValuesInStep(stepName='u4', u1=0.0, u2=0.0, ur3=1.0)
    
    # Setup history outputs
    the_model.HistoryOutputRequest(name='OUTER_CIRCLE', createStepName='u1', 
                                   variables=('RF1', 'RF2'), region=the_inst.sets['OUTER_CIRCLE'])
    the_model.HistoryOutputRequest(name='RP', createStepName='u1', 
                                   variables=('RF1', 'RF2', 'RM3'), region=assy.sets['RP'])
                                   
    # Run analysis
    if job_name in mdb.jobs:
       del(mdb.jobs[job_name])
        
    the_job = mdb.Job(name=job_name, model=model_name, nodalOutputPrecision=FULL)
    the_job.submit(consistencyChecking=OFF)
    the_job.waitForCompletion()
    
    return job_name
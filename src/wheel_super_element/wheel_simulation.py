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

src_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(lambda: None))))
if not src_path in sys.path:
    sys.path.append(src_path)
    
import user_settings
reload(user_settings)

def get_node_nr(inod_radial, inod_circumf, nel_radial, nel_circumf):
    return inod_radial*nel_circumf + inod_circumf 
    
    
def get_elem_nr(iel_radial, iel_circumf, nel_radial, nel_circumf):
    return iel_radial*nel_circumf + iel_circumf
    
    
def get_elem_node_nrs(iel_radial, iel_circumf, nel_radial, nel_circumf):
    # Given the element position, return the number for the 4 nodes that build up the element.
    node_indices_radial = np.array([iel_radial,
                                    iel_radial,
                                    iel_radial + 1,
                                    iel_radial + 1], dtype=np.int)
    node_indices_circumf= np.array([iel_circumf,
                                    iel_circumf + 1 if iel_circumf < (nel_circumf - 1) else 0,
                                    iel_circumf + 1 if iel_circumf < (nel_circumf - 1) else 0,
                                    iel_circumf], dtype=np.int)
    
    return get_node_nr(node_indices_radial, node_indices_circumf, nel_radial, nel_circumf)


def get_radial_node_pos(id, od, elsize):
    # Distribute radial node positions to get elsize element length at outer diameter (od) and then 
    # approx square elements while going to inner diameter (id)
    radii = [od/2.0, od/2.0 - elsize]
    while radii[-1] > id/2:
        radii.append(radii[-1] - radii[-1]*elsize/(od/2.0))
    radii = np.array(radii)
    sfac = 1 + (id/(2*radii[-1]) - 1)*(radii[0] - radii)/(radii[0]-radii[-1])
    radii = radii*sfac
    nel_radial = radii.size - 1
    return radii, nel_radial


def create_mesh(the_part, id, od, elsize):
    # Calculate number of elements around circumference. Multiple of 4 to ensure symmetry.
    nel_circumf = 4*int(od*np.pi/(4.0*elsize))
    angles = np.linspace(0, 2*np.pi, nel_circumf + 1)[:-1]  # Remove last element that is duplicated
    radii, nel_radial = get_radial_node_pos(id, od, elsize)
    
    for ir, r in zip(range(nel_radial+1), radii):
        for ic, a in zip(range(nel_circumf), angles):
            x = r*np.cos(a)
            y = r*np.sin(a)
            node_nr = get_node_nr(ir, ic, nel_radial, nel_circumf)
            the_part.Node(coordinates=(x, y, 0.0), label=node_nr + 1)
    
    for ir in range(nel_radial):
        for ic in range(nel_circumf):
            enodes = [the_part.nodes[i] for i in get_elem_node_nrs(ir, ic, nel_radial, nel_circumf)]
            the_part.Element(nodes=enodes, elemShape=QUAD4, 
                             label=get_elem_nr(ir, ic, nel_radial, nel_circumf) + 1)
    
    inner_nodes = [the_part.nodes[get_node_nr(nel_radial, ic, nel_radial, nel_circumf)] 
                   for ic in range(nel_circumf)]
    outer_nodes = [the_part.nodes[get_node_nr(0, ic, nel_radial, nel_circumf)] 
                   for ic in range(nel_circumf)]
    n1_node = [the_part.nodes[get_node_nr(0, 0, nel_radial, nel_circumf)]]
    outer_nodes_without_n1 = [the_part.nodes[get_node_nr(0, ic, nel_radial, nel_circumf)] 
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

def simulate():
    model_name = 'SUPER_WHEEL'
    part_name = model_name
    inst_name = model_name
    job_name = model_name
    if model_name in mdb.models:    # Delete old model if exists
        del(mdb.models[model_name])
        
    the_model = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    the_part = the_model.Part(name=part_name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    
    od = user_settings.wheel_geometry['outer_diameter']
    id = user_settings.wheel_geometry['inner_diameter']
    elsize = user_settings.wheel_mesh['fine'] # Should be fine, but use coarse for testing
    elsize = od*np.pi/16.1   # For debug
    
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
        
    the_job = mdb.Job(name=job_name, model=model_name)
    the_job.submit(consistencyChecking=OFF)
    the_job.waitForCompletion()
    
    return job_name
# System imports
import sys
import os
import numpy as np
import inspect
import time

# Abaqus imports 
from abaqus import mdb
import assembly
from abaqusConstants import *

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))


import material_and_section_module as matmod
import rail_setup as railmod
import wheel_setup as wheelmod
import wheel_substructure_create as wheel_ssc_mod
import wheel_substructure_import as wheel_ssi_mod
import loading_module as loadmod
import contact_module as contactmod
import user_settings
import abaqus_python_tools as apt
import wheel_toolbox

# Reload to account for script updates when running from inside abaqus CAE
reload(matmod)
reload(railmod)
reload(wheelmod)
reload(wheel_ssc_mod)
reload(wheel_ssi_mod)
reload(loadmod)
reload(contactmod)
reload(user_settings)
reload(apt)
reload(wheel_toolbox)

def main():
    t0 = time.time()
    the_model = setup_initial_model()
    setup_time = time.time() - t0
    job_name, run_time = run_cycle(the_model, cycle_nr=1)
    #job_name = get_cycle_name(1)
    #run_time=t0
    t0 = time.time()
    save_results(the_model, cycle_nr=1)
    result_time = time.time() - t0
    apt.print_message('Setup time:  ' + str(setup_time) + 's \n' + 
                      'Run time:    ' + str(run_time) + ' s \n' + 
                      'Result time: ' + str(result_time) + ' s')
    
    t0 = time.time()
    the_model=setup_next_rollover(old_model=the_model, old_job_name=job_name, new_cycle_nr=2)
    setup_time = time.time() - t0
    job_name, run_time = run_cycle(the_model, cycle_nr=2)
    apt.print_message('Setup time:  ' + str(setup_time) + 's \n' + 
                      'Run time:    ' + str(run_time) + ' s \n' + 
                      'Result time: ' + str(result_time) + ' s')
    
    
def get_cycle_name(cycle_nr):
    return 'rollover_' + str(cycle_nr).zfill(6)
    
    
def run_cycle(model,
             cycle_nr,
             n_proc=1,
             ):
    
    # mdb.saveAs(pathName=job_name + '.cae')
    
    # Checks written by Martin Pletz, unsure what these does, but should read up about these
    # __get_model_nodes_elem(model)
    # __make_ip_out(model)
    #
    job_name = get_cycle_name(cycle_nr)
    job_type = ANALYSIS if cycle_nr == 1 else RESTART
    
    if job_name in mdb.jobs:
        del(mdb.jobs[job_name])
        
    job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                  model=model.name, name=job_name, nodalOutputPrecision=SINGLE,
                  multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                  type=job_type)
    
    time_before = time.time()
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    run_time = time.time() - time_before
    
    return job_name, run_time

def setup_initial_model():
    # Settings
    ## Overall settings
    model_name = get_cycle_name(cycle_nr=1)
    
    ## Rail settings
    rail_geometry = user_settings.rail_geometry
    rail_mesh = user_settings.rail_mesh
    rail_naming = user_settings.rail_naming 
    
    ## Wheel settings
    use_substructure = user_settings.use_substructure
    new_substructure = user_settings.new_substructure
    
    wheel_geometry = user_settings.wheel_geometry
    wheel_mesh = user_settings.wheel_mesh
    wheel_naming = user_settings.wheel_naming
    
    # Create wheel substructure model
    if new_substructure:
        wheel_ssc_mod.create_wheel_substructure(wheel_geometry, wheel_mesh, wheel_naming)
    
    # Setup model
    if model_name in mdb.models:    # Delete old model if exists
        del(mdb.models[model_name])
    
    the_model = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    matmod.setup_sections(the_model, section_names={'wheel': wheel_naming['section'],
                                                    'rail': rail_naming['section'], 
                                                    'shadow': rail_naming['shadow_section'],
                                                    'contact': wheel_naming['contact_section']})
    
    # Setup rail
    rail_part, rail_contact_surf, bottom_reg = railmod.setup_rail(the_model, assy, rail_geometry, rail_mesh, rail_naming)
    
    # Setup wheel
    if use_substructure:
        wheel_part, wheel_contact_surf, ctrl_pt_reg = wheel_ssi_mod.import_wheel_substructure(the_model, assy, wheel_naming, 
                                                                                              wheel_geometry, wheel_mesh)
    else:
        wheel_part, wheel_contact_surf, ctrl_pt_reg = wheelmod.setup_wheel(the_model, assy, wheel_geometry, wheel_mesh, wheel_naming)

    # Position wheel
    loadmod.preposition(assy)

    # Setup loading
    loadmod.initial_bc(the_model, assy, ctrl_pt_reg, bottom_reg)
    
    # Setup contact conditions
    contactmod.setup_contact(the_model, assy, rail_contact_surf, wheel_contact_surf)
    
    # Setup output requests
    loadmod.setup_outputs(the_model, ctrl_pt_reg)
       
    return the_model
    
def save_results(the_model, cycle_nr):
    # Save the results required for continued simulation
    # - Wheel contact node displacements (only those in contact required)
    # - Wheel reference node displacements
    # - Rail contact node displacements (only those in contact should be required). 
    odb_name = get_cycle_name(cycle_nr)
    odb = session.openOdb(odb_name + '.odb')
    inst_name = odb.rootAssembly.instances.keys()[0]
    inst = odb.rootAssembly.instances[inst_name]
    
    rp_node = inst.nodeSets['WHEEL_RP_NODE'].nodes[0]
    wheel_contact_surf_nodes = inst.nodeSets['WHEEL_CONTACT_NODES'].nodes
    rail_contact_surf_nodes = inst.nodeSets['RAIL_CONTACT_NODES'].nodes
    
    # Make dictionary containing node label as key and history region for that node as data. 
    step_name = odb.steps.keys()[-1]
    history_regions = odb.steps[step_name].historyRegions
    node_hr = {int(label.split('.')[-1]):hr for label, hr in history_regions.items() if 'Node' in label}
    
    save_node_results([rp_node], node_hr, filename=odb_name + '_rp', variable_keys=['U1', 'U2', 'UR3'])
    save_node_results(wheel_contact_surf_nodes, node_hr, filename=odb_name + '_wheel', variable_keys=['U1', 'U2'])
    save_node_results(rail_contact_surf_nodes, node_hr, filename=odb_name + '_rail', variable_keys=['U1', 'U2'])
    # Save the results asked for for post-processing
    # Results for x in middle of rail:
    # - ux(y,z)
    # - sigma(y,z,t) and epsilon(y,z,t)
    # 
    
    
def save_node_results(nodes, node_hr, filename, variable_keys=[]):
    # Save <filename>.npy containing one row per node. The first column contain 
    # the node label, and the three following columns the x, y, z coordinates.
    # Then the variables described by variable_keys follow. 
    # nodes:         List of nodes from which to save results
    # node_hr:       Dictionary with history region with node label as key
    # filename:      Name (excluding suffix) of .npy file to save to
    # variable_keys: List of keys (e.g. 'U1', 'UR2', 'RF1', etc.) that should be saved
    n_cols = 4 if not variable_keys else 4 + len(variable_keys)
    
    result_data = np.zeros((len(nodes), n_cols))
    row = 0
    for node in nodes:
        result_data[row, 0] = node.label
        result_data[row, 1:4] = np.array(node.coordinates)
        col = 4
        for key in variable_keys:
            result_data[row, col] = node_hr[node.label].historyOutputs[key].data[-1][-1]
            col = col + 1
        row = row + 1
    
    np.save(filename + '.npy', result_data)
            
    
def setup_next_rollover(old_model, old_job_name, new_cycle_nr):
    # copy the old model and add new steps. Restart from the previous job
    new_model_name = get_cycle_name(new_cycle_nr)
    new_model = mdb.Model(name=new_model_name, objectToCopy=old_model)
    
    # Setup restart parameters
    last_step_in_old_job = old_model.steps.keys()[-1]
    new_model.setValues(restartJob=old_model.name, restartStep=last_step_in_old_job)
    
    # Read in old state
    rp_old = np.load(old_model.name + '_rp.npy')
    wheel_old = np.load(old_model.name + '_wheel.npy')
    u2_end = rp_old[0, 5]
    ur3_end = rp_old[0, 6]
    
    # Load parameters
    wheel_load = user_settings.load_parameters['normal_load']
    slip_ratio = user_settings.load_parameters['slip']
    rolling_length = -user_settings.rail_geometry['length']
    nominal_radius = user_settings.wheel_geometry['outer_diameter']/2.0
    rolling_angle = -(1+slip_ratio)*rolling_length/nominal_radius
    
    # Mesh parameters
    wheel_node_angles = wheel_ssi_mod.get_split_angles(user_settings.wheel_geometry, 
                                                       user_settings.wheel_mesh)
    wheel_node_angle_increment = wheel_node_angles[1] - wheel_node_angles[0]
    
    # Boundary conditions and loads to be modified
    ctrl_bc = new_model.boundaryConditions['ctrl_bc']
    ctrl_load = new_model.loads['ctrl_load']
    
    # Move wheel to start
    return_step_name = 'return_' + str(new_cycle_nr)
    new_model.StaticStep(name=return_step_name, previous=last_step_in_old_job,
                         timeIncrementationMethod=FIXED, initialInc=1, 
                         maxNumInc=1, amplitude=STEP)
                         
    num_element_rolled = np.round(rolling_angle/wheel_node_angle_increment)
    return_angle = rolling_angle - num_element_rolled*wheel_node_angle_increment
    
    ctrl_bc.setValuesInStep(stepName=return_step_name, ur3=return_angle, u1=0, u2=u2_end)
    
    # Determine which nodes are in contact at the end of previous step
    # Sort all wheel nodes by angle (apart from rp)
    # Identify the new nodes in contact by shifting the sorted list by num_element_rolled
    # Apply the old displacements to the new contact nodes
    # Disable this boundary condition in the next step
    
    # Continue rolling
    rolling_step_name = 'rolling_' + str(new_cycle_nr)
    new_model.StaticStep(name=rolling_step_name, previous=return_step_name, maxNumInc=1000, 
                         initialInc=0.01, minInc=1e-06, maxInc=0.01)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, u1=rolling_length, 
                            ur3=rolling_angle, u2=FREED)
    
    ctrl_load.setValuesInStep(stepName=rolling_step_name, cf3=-wheel_load)
    
    new_model.steps[rolling_step_name].Restart(numberIntervals=1)
    
    return new_model
    
    
    
if __name__ == '__main__':
    main()

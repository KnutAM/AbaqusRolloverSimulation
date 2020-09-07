# System imports
import sys
import os
import numpy as np
import inspect
import time
import subprocess

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset
from abaqusConstants import *

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)


import material_and_section_module as matmod
import rail_setup as railmod
import wheel_super_element_import as wheelmod
import loading_module as loadmod
import contact_module as contactmod
import user_settings
import abaqus_python_tools as apt
import naming_mod as names
import get_utils as get

# Reload to account for script updates when running from inside abaqus CAE
reload(matmod)
reload(railmod)
reload(wheelmod)
reload(loadmod)
reload(contactmod)
reload(user_settings)
reload(apt)
reload(names)
reload(get)

def main():
    num_cycles = user_settings.num_cycles
    t0 = time.time()
    setup_initial_model()
    run_cycle(cycle_nr=1)
    
    
    for nr in range(2, num_cycles+1):
        t0 = time.time()
        setup_next_rollover(new_cycle_nr=nr)
        setup_time = time.time() - t0
        # if nr == 2:
            # FiOpRe = mdb.models['rollover_00002'].FieldOutputRequest(name='F-Output-2', 
               # createStepName='return_00002', variables=('S', 'U'), substructures=(
                # 'WHEEL.Entire Substructure', 'WHEEL.WHEEL-REFPT_', 'WHEEL.WHEELCENTER', 
                # 'WHEEL.WHEEL_CONTACT_NODES', 'WHEEL.WHEEL_WHEEL'), sectionPoints=DEFAULT, 
                # rebar=EXCLUDE)
            # FiOpRe.deactivate(stepName='rolling_start_00002')
        run_time = run_cycle(cycle_nr=nr)
        apt.print_message('Setup time:  ' + str(setup_time) + 's \n' + 
                          'Run time:    ' + str(run_time) + ' s \n' + 
                          'Result time: ' + str(result_time) + ' s')
        save_results(cycle_nr=nr)
    
    join_odb_files([names.get_odb(cycle_nr=i+1) for i in range(num_cycles)])
    
    
def join_odb_files(odb_file_list):
    try:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abaqus restartjoin originalodb=' + odb_file_list[0] + ' restartodb='+odb_i, shell=True)
    except:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abq2017 restartjoin originalodb=' + odb_file_list[0] + ' restartodb='+odb_i, shell=True)
    
def get_cycle_name(cycle_nr):
    return 'rollover_' + str(cycle_nr).zfill(6)
    
    
def run_cycle(cycle_nr, n_proc=1, run=True):
    job_name = names.get_job(cycle_nr)
    model_name = names.get_model(cycle_nr)
    job_type = ANALYSIS if cycle_nr == 1 else RESTART
    
    if user_settings.materials['rail']['material_model']=='user':
        usub = user_settings.materials['rail']['mpar']['umat']
    else:
        usub = ''
    usub=''
    if job_name in mdb.jobs:
        del(mdb.jobs[job_name])
    
    job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                  model=model_name, name=job_name, nodalOutputPrecision=SINGLE,
                  multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                  type=job_type,userSubroutine=usub)
    
    time_before = time.time()
    if run:
        job.submit(consistencyChecking=OFF)
        job.waitForCompletion()
    else:
        job.writeInput()
    run_time = time.time() - time_before
    
    return run_time


def setup_initial_model():
    # Settings
    ## Overall settings
    model_name = names.get_model(cycle_nr=1)
    
    ## Rail settings
    rail_geometry = user_settings.rail_geometry
    rail_mesh = user_settings.rail_mesh
    rail_naming = user_settings.rail_naming 
    
    
    # Setup model
    if model_name in mdb.models:    # Delete old model if exists
        del(mdb.models[model_name])
    
    the_model = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    assy = get.assy()
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    matmod.setup_sections(the_model, section_names={'rail': names.rail_sect, 
                                                    'shadow': names.rail_shadow_sect,
                                                    'contact': names.wheel_dummy_contact_sect})
    
    # Setup rail
    # rail_part, rail_contact_surf, bottom_reg = railmod.setup_rail(the_model, assy, rail_geometry, rail_mesh)
    
    # Setup wheel
    wheelmod.setup_wheel()
    
    # Position wheel
    loadmod.preposition()

    # Setup loading
    # loadmod.initial_bc()
    
    wheel_inst = get.inst(names.wheel_inst)
    wheel_refpoint = assy.sets[names.wheel_rp_set]
    
    the_model.StaticStep(name=names.step1, previous=names.step0, nlgeom=ON)
    
    # BC for wheel
    ctrl_bc = the_model.DisplacementBC(name=names.rp_ctrl_bc, createStepName=names.step1, 
                                       region=wheel_refpoint, u1=0.0, ur3=1.0, 
                                       u2=0)
                                       
    # Edit input directly to add user element
    wheelmod.add_wheel_super_element_to_inp()
    
    return the_model
    
def save_results(cycle_nr):
    # Save the results required for continued simulation
    # - Wheel contact node displacements (only those in contact required)
    # - Wheel reference node displacements
    # - Rail contact node displacements (only those in contact should be required). 
    
    the_model = get.model(cycle_nr)
    odb_name = names.get_odb(cycle_nr)
    odb = session.openOdb(odb_name + '.odb')
    
    if False: #  user_settings.use_substructure: (old code)
        inst_name = odb.rootAssembly.instances.keys()[0]
        inst = odb.rootAssembly.instances[inst_name]
        
        rp_node = inst.nodeSets['WHEEL_RP_NODE'].nodes[0]
        wheel_contact_surf_nodes = inst.nodeSets['WHEEL_CONTACT_NODES'].nodes
        rail_contact_surf_nodes = inst.nodeSets['RAIL_CONTACT_NODES'].nodes
    else:
        winst = get.inst(names.wheel_inst, odb=odb)
        rinst = get.inst(names.rail_inst, odb=odb)
        rp_node = winst.nodeSets[names.wheel_rp_set].nodes[0]
        wheel_contact_surf_nodes = winst.nodeSets[names.wheel_contact_nodes].nodes
        rail_contact_surf_nodes = rinst.nodeSets[names.rail_contact_nodes].nodes
    
    # Make dictionary containing node label as key and history region for that node as data. 
    step_name = odb.steps.keys()[-1]
    history_regions = odb.steps[step_name].historyRegions
    node_hr = {int(label.split('.')[-1]):hr for label, hr in history_regions.items() if 'Node' in label}
    
    save_node_results([rp_node], node_hr, variable_keys=['U1', 'U2', 'UR3'],
                      filename=names.get_model(cycle_nr) + '_rp', )
    save_node_results(wheel_contact_surf_nodes, node_hr, variable_keys=['U1', 'U2'], 
                      filename=names.get_model(cycle_nr) + '_wheel')
    save_node_results(rail_contact_surf_nodes, node_hr, variable_keys=['U1', 'U2'],
                      filename=names.get_model(cycle_nr) + '_rail')
    # Save the results asked for for post-processing
    # Results for x in middle of rail:
    # - ux(y,z)
    # - sigma(y,z,t) and epsilon(y,z,t)
    # 
    odb.close()
    
    
def save_node_results(nodes, node_hr, filename, variable_keys=[]):
    # Save <filename>.npy containing one row per node. The first column contain 
    # the node label, and the three following columns the x, y, z coordinates.
    # Then the variables described by variable_keys follow. 
    # nodes:         List of nodes from which to save results
    # node_hr:       Dictionary with history region with node label as key
    # filename:      Name (excluding suffix) of .npy file to save to
    # variable_keys: List of keys (e.g. 'U1', 'UR2', 'RF1', etc.) that should be saved
    #                Also the rate of change of these variables will be saved in the following col.
    n_cols = 4 if not variable_keys else 4 + 2*len(variable_keys)
    
    result_data = np.zeros((len(nodes), n_cols))
    row = 0
    for node in nodes:
        result_data[row, 0] = node.label
        result_data[row, 1:4] = np.array(node.coordinates)
        col = 4
        for key in variable_keys:
            ndata = node_hr[node.label].historyOutputs[key].data
            result_data[row, col] = ndata[-1][1]
            dt = ndata[-1][0] - ndata[-2][0]
            result_data[row, col+1] = (ndata[-1][1] - ndata[-2][1])/dt
            col = col + 2
            
        row = row + 1
    
    np.save(filename + '.npy', result_data)
            
    
def setup_next_rollover(new_cycle_nr):
    old_model = get.model(stepnr=new_cycle_nr-1)
    old_job_name = names.get_job(new_cycle_nr-1)
    # copy the old model and add new steps. Restart from the previous job
    new_model_name = names.get_model(new_cycle_nr)
    new_model = mdb.Model(name=new_model_name, objectToCopy=old_model)
    
    # Setup restart parameters
    last_step_in_old_job = old_model.steps.keys()[-1]
    new_model.setValues(restartJob=old_model.name, restartStep=last_step_in_old_job)
    
    # Read in old state
    rp_old = np.load(old_model.name + '_rp.npy')
    wheel_old = np.load(old_model.name + '_wheel.npy')
    u2_end = rp_old[0, 6]
    ur3_end = rp_old[0, 8]
    
    # Load parameters
    ntpar = user_settings.numtrick
    ipar = user_settings.time_incr_param
    rol_par = loadmod.get_rolling_parameters()
    
    wheel_load = rol_par['load']
    slip_ratio = user_settings.load_parameters['slip']
    rolling_length = rol_par['length']
    rolling_time = rol_par['time']
    rolling_angle = rol_par['angle']
    
    end_stp_frac = abs(ntpar['extrap_roll_length']/rolling_length)
    
    # Mesh parameters
    wheel_node_angles = wheel_ssc_mod.get_split_angles(user_settings.wheel_geometry, 
                                                       user_settings.wheel_mesh)
    wheel_node_angle_increment = wheel_node_angles[1] - wheel_node_angles[0]
    
    # Boundary conditions and loads to be modified
    ctrl_bc = new_model.boundaryConditions[names.rp_ctrl_bc]
    ctrl_load = new_model.loads[names.rp_vert_load]
    
    # Move wheel to start
    return_step_name = names.get_step_return(new_cycle_nr)
    new_model.StaticStep(name=return_step_name, previous=last_step_in_old_job,
                         timeIncrementationMethod=FIXED, initialInc=1, 
                         maxNumInc=1, amplitude=STEP)
                         
    num_element_rolled = int(np.round(rolling_angle/wheel_node_angle_increment))
    rot_angle = num_element_rolled*wheel_node_angle_increment
    return_angle = rolling_angle - rot_angle
    
    ctrl_bc.setValuesInStep(stepName=return_step_name, ur3=return_angle, u1=0, u2=u2_end)
    
    # Sort all wheel nodes by angle (apart from rp)
    node_angles = get_node_angles(wheel_old, rp_old)
    sort_inds = np.argsort(node_angles)
    sorted_wheel_node_info = wheel_old[sort_inds, :]
    node_angles_sort = node_angles[sort_inds]
    
    # The node labels from above are given from odb. Due to renumbering these may have been changed. 
    # Therefore, we need to get the node labels from the instance and use those instead when setting boundary conditions
    wheel_part = get.part(names.wheel_part, cyclenr=new_cycle_nr)
    contact_nodes = wheel_part.sets[names.wheel_contact_nodes]
    
    new_node_info = np.array([[node.label, node.coordinates[0], node.coordinates[1]] 
                                 for node in contact_nodes])
    
    sort_inds = np.argsort(get_node_angles(new_node_info, rp_old))
    sorted_new_node_info = new_node_info[sort_inds, :]
    sorted_wheel_node_info[:, 0] = sorted_new_node_info[:, 0]   # Add correct node labels
    
    # Determine which nodes are in contact at the end of previous step
    old_contact_node_indices = get_contact_nodes(sorted_wheel_node_info, rp_old)
    
    # Identify the new nodes in contact by shifting the sorted list by num_element_rolled
    new_contact_node_indices = old_contact_node_indices + num_element_rolled
    
    # Apply the old displacements to the new contact nodes
    disp_rel_rp = np.transpose([sorted_wheel_node_info[old_contact_node_indices, 4+i]    
                                - rp_old[0, 4+2*i] for i in range(2)])
    
    x_rp_old = rp_old[0, 1:3] + rp_old[0, 4:7:2]
    x_rp_new = rp_old[0, 1:3] + np.array([0, u2_end])
    
    node_bc = []
    wheel_nodes = new_model.rootAssembly.instances['WHEEL'].sets['CONTACT_NODES'].nodes
    
    for old_node, new_node in zip(sorted_wheel_node_info[old_contact_node_indices], 
                                  sorted_wheel_node_info[new_contact_node_indices]):
        
        new_node_id = int(new_node[0])
        
        # Node positions
        xold = old_node[1:3] + old_node[4:7:2]  # Deformed old position
        Xnew = new_node[1:3]                    # Undeformed new position
        
        # Old position relative old rp is same as new position relative new rp
        xnew = x_rp_new + (xold - x_rp_old)
        
        unew = xnew - Xnew                      # Displacement is relative undeformed pos
                    
        node_bc_name = return_step_name + '_' + str(new_node_id)
        region = new_model.rootAssembly.Set(name=node_bc_name, 
                                            nodes=wheel_nodes[(new_node_id-1):(new_node_id)])
                                            # number due to nodes numbered from 1 but python from 0
        node_bc.append(new_model.DisplacementBC(name=node_bc_name,
                                                createStepName=return_step_name, 
                                                region=region, u1=unew[0], u2=unew[1]))
        
    # Lock all rail contact node displacements
    rail_contact_nodes = new_model.rootAssembly.instances['RAIL'].sets['CONTACT_NODES']
    lock_rail_bc = new_model.VelocityBC(name=names.get_lock_rail_bc(new_cycle_nr),
                                        createStepName=return_step_name,
                                        region=rail_contact_nodes,
                                        v1=0., v2=0., v3=0.)
    
    # Continue rolling
    rolling_start_step_name = names.get_step_roll_start(new_cycle_nr)
    time = rolling_time*end_stp_frac
    new_model.StaticStep(name=rolling_start_step_name, previous=return_step_name, timePeriod=time, 
                         maxNumInc=3, initialInc=time, minInc=time/2.0, maxInc=time)
    ctrl_load.setValuesInStep(stepName=rolling_start_step_name, cf3=-wheel_load)
    ctrl_bc.setValuesInStep(stepName=rolling_start_step_name, u1=rolling_length*end_stp_frac, 
                            ur3=rolling_angle*end_stp_frac, u2=FREED)
    
    for bc in node_bc:
        # bc.setValuesInStep(stepName=rolling_step_name, u1=FREED, u2=FREED)
        bc.deactivate(stepName=rolling_start_step_name)
        
    lock_rail_bc.deactivate(stepName=rolling_start_step_name)
    
    rolling_step_name = names.get_step_rolling(new_cycle_nr)
    time = rolling_time*(1.0 - 2.0*end_stp_frac)
    dt0 = time/ipar['nom_num_incr_rolling']
    dtmin = time/(ipar['max_num_incr_rolling']+1)
    new_model.StaticStep(name=rolling_step_name, previous=rolling_start_step_name, timePeriod=time, 
                         maxNumInc=ipar['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, u1=rolling_length*(1.0 - end_stp_frac), 
                            ur3=rolling_angle*(1.0 - end_stp_frac), u2=FREED)
    
    ctrl_load.setValuesInStep(stepName=rolling_step_name, cf3=-wheel_load)
    
    rolling_step_end_name = names.get_step_roll_end(new_cycle_nr)
    time = rolling_time*end_stp_frac
    new_model.StaticStep(name=rolling_step_end_name, previous=rolling_step_name, timePeriod=time, 
                         maxNumInc=3, initialInc=time, minInc=time/2.0, maxInc=time)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_end_name, 
                            u1=rolling_length, u2=FREED,
                            ur3=rolling_angle)
    
    new_model.steps[rolling_step_end_name].Restart(numberIntervals=1)
    
    # contactmod.renew_contact(new_cycle_nr)
    
    
def get_contact_nodes(wheel_node_info, rp_info):
    xpos = wheel_node_info[:, 1] + wheel_node_info[:, 4]
    # ypos = wheel_node_info[:, 2] + wheel_node_info[:, 5]
    rp_x = rp_info[0, 1] + rp_info[0, 4]
    contact_length = user_settings.max_contact_length
    all_indices = np.arange(wheel_node_info.shape[0])
    contact_indices = all_indices[np.abs(xpos-rp_x) < contact_length/2.0]
    
    return contact_indices[1:-1]    # Remove the first and last to avoid taking one too many on either side
    
    
def get_node_angles(wheel_node_info, rp_info):
    dx = np.transpose([wheel_node_info[:, 1+i] - rp_info[0, 1+i] for i in range(2)])
    
    # Get angle wrt. y-axis
    angles = np.arctan2(dx[:, 0], -dx[:, 1])
    return angles
    
    
if __name__ == '__main__':
    main()

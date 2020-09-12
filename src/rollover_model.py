# System imports
import sys
import os
import numpy as np
import inspect
import time
import pickle
import subprocess
from shutil import copyfile

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
    setup_time = time.time() - t0
    if num_cycles > 0:
        #run_time = -1.0
        run_time = run_cycle(cycle_nr=1)
    else:
        run_time = run_cycle(cycle_nr=1, n_proc=1, run=False)
        return
    
    t0 = time.time()
    save_results(cycle_nr=1)
    result_time = time.time() - t0
    apt.print_message('Setup time:  ' + str(setup_time) + 's \n' + 
                      'Run time:    ' + str(run_time) + ' s \n' + 
                      'Result time: ' + str(result_time) + ' s')
    
    
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
    joined_odb_file_name = 'rollover_joined'
    copyfile(odb_file_list[0] + '.odb', joined_odb_file_name + '.odb')
    try:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abaqus restartjoin originalodb=' + joined_odb_file_name + ' restartodb='+odb_i, shell=True)
    except:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abq2017 restartjoin originalodb=' + joined_odb_file_name + ' restartodb='+odb_i, shell=True)
    
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
    rail_part, rail_contact_surf, bottom_reg = railmod.setup_rail(the_model, assy, rail_geometry, rail_mesh)
    
    # Setup wheel
    wheelmod.setup_wheel()
    
    # Position wheel
    loadmod.preposition()

    # Setup loading
    loadmod.initial_bc()
    
    # Setup contact conditions
    contactmod.setup_contact(rail_contact_surf)
    
    # Setup output requests
    loadmod.setup_outputs()
    
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
        rinst_name = inst_name
        winst_name = inst_name
    else:
        winst_name = names.wheel_inst
        rinst_name = names.rail_inst
        winst = get.inst(winst_name, odb=odb)
        rinst = get.inst(rinst_name, odb=odb)
        rp_node = get.assy(odb=odb).nodeSets[names.wheel_rp_set].nodes[0][0]
        wheel_contact_surf_nodes = winst.nodeSets[names.wheel_contact_nodes].nodes
        rail_contact_surf_nodes = rinst.nodeSets[names.rail_contact_nodes].nodes
    
    # Make dictionaries containing node label as key and history region for that node as data. 
    # Make different dictionaries for wheel and rail to avoid label confusion!
    step_name = odb.steps.keys()[-1]
    history_regions = odb.steps[step_name].historyRegions
    node_hr_wheel = {int(label.split('.')[-1]):hr for label, hr in history_regions.items() 
                     if ('Node' in label and winst_name in label)}
    
    node_hr_rail  = {int(label.split('.')[-1]):hr for label, hr in history_regions.items() 
                     if ('Node' in label and rinst_name in label)}
    
    save_node_results([rp_node], winst_name, history_regions, incl_rot=True, ndim=2,
                      filename=names.get_model(cycle_nr) + '_rp')
    save_node_results(wheel_contact_surf_nodes, winst_name, history_regions, incl_rot=False, ndim=2,
                      filename=names.get_model(cycle_nr) + '_wheel')
    save_node_results(rail_contact_surf_nodes, rinst_name, history_regions, incl_rot=False, ndim=2, 
                      filename=names.get_model(cycle_nr) + '_rail')
    # Save the results asked for for post-processing
    # Results for x in middle of rail:
    # - ux(y,z)
    # - sigma(y,z,t) and epsilon(y,z,t)
    # 
    odb.close()
    
    
def save_node_results_old(nodes, node_hr, filename, variable_keys=[]):
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
            
def save_node_results(nodes, inst_name, history_reg, filename, incl_rot=False, ndim=2):
    # Save <filename>.pickle containing a dictionary with array for each node in each field.
    # Input
    # nodes:        List of nodes from which to save results
    # inst_name:    To which instance the node labels apply
    # history_reg:  History regions (step.historyRegion)
    # filename:     Name (excluding suffix) of .pickle file to save to
    # incl_rot:     Should rotational output be saved?
    # ndim:         Number of dimensions (2 or 3)
    lin_key_ind = [i+1 for i in range(ndim)]
    
    hr_keys = {'U': ['U' + str(i) for i in lin_key_ind]}
    vel_keys = {'U': 'V', 'UR': 'VR'}   # Translate from static to velocity values
    
    if incl_rot:
        rot_key_ind = [1,2,3] if ndim==3 else [3]
        hr_keys['UR'] = ['UR' + str(i) for i in rot_key_ind]
        
    all_keys = (['label', 'X'] + [type_key for type_key in hr_keys] + 
                [vel_keys[type_key] for type_key in hr_keys])
    result_dict = {}
    for type_key in all_keys:
        result_dict[type_key] = []
        
    for node in nodes:
        result_dict['label'].append(node.label)
        result_dict['X'].append(node.coordinates[:ndim])
        hist_outp = history_reg['Node ' + inst_name + '.' + str(node.label)].historyOutputs
        for type_key in hr_keys:    # type_key is e.g. 'U', 'UR', etc.
            dt = (hist_outp[hr_keys[type_key][0]].data[-1][0] - 
                  hist_outp[hr_keys[type_key][0]].data[-2][0])
            old_val = np.array([hist_outp[key].data[-2][1] for key in hr_keys[type_key]])
            new_val = np.array([hist_outp[key].data[-1][1] for key in hr_keys[type_key]])
            vel_val = (new_val - old_val)/dt    # Velocity
            result_dict[type_key].append(new_val)
            result_dict[vel_keys[type_key]].append(vel_val)
    
    for key in all_keys:
        result_dict[key] = np.array(result_dict[key])
        
    pickle.dump(result_dict, open(filename + '.pickle', 'wb'))
    
    
# def get_wheel_angle_incr():
    # coords = np.load('uel_coords.npy')
    # v1 = coords[:,0]    # First node
    # v2 = coords[:,1]    # Second node
    # ang = np.arccos(np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2)))
    # return ang
    

def sort_dict(dict_unsrt, array_to_sort):
    # Sort a dictionary containing arrays of equal first dimension
    # Input
    # dict_unsrt        A dictionary containing arrays (of shapes [n, m] or [n])
    # array_to_sort     An array of length n. Corresponding to the arrays in dict_unsrt
    #                   This array will be sorted and the indices will be used to reorder dict_unsrt
    # Output
    # dict_srt          The sorted variant of dict_unsrt. 
    
    sort_inds = np.argsort(array_to_sort)
    dict_srt = {}
    for key in dict_unsrt:
        if len(dict_unsrt[key].shape) > 1:
            dict_srt[key] = dict_unsrt[key][sort_inds, :] 
        else:
            dict_srt[key] = dict_unsrt[key][sort_inds]
    
    return dict_srt
    

def get_old_node_data(filename, new_cycle_nr):
    # Read in results from previous cycle. Sort node data and ensure that node labels match that in the odb file
    # Reference point data
    rp_data = pickle.load(open(filename + '_rp.pickle', 'rb'))
    # Saved as 2-d array, but for simplicity remove the "first" unneccessary dimension
    for key in rp_data:
        rp_data[key] = rp_data[key][0]
    
    # Wheel data
    wheel_data_unsrt = pickle.load(open(filename + '_wheel.pickle', 'rb'))
    node_angles = get_node_angles(wheel_data_unsrt['X'], rp_data['X'])
    
    wheel_data = sort_dict(wheel_data_unsrt, node_angles)   # Sort by angle
    
    # The node labels from above are given from odb. Due to renumbering these may have been changed. 
    # Therefore, we need to get the node labels from the part and use those instead when setting boundary conditions
    wheel_part = get.part(names.wheel_part, stepnr=new_cycle_nr)
    contact_nodes = wheel_part.sets[names.wheel_contact_nodes].nodes
    
    new_node_labels = np.array([node.label for node in contact_nodes])
    new_node_coords = np.array([node.coordinates[0:2] for node in contact_nodes])
    
    sort_inds = np.argsort(get_node_angles(new_node_coords, rp_data['X']))
    wheel_data['label'] = new_node_labels[sort_inds]   # Add correct node labels
    
    wheel_data['angle_incr'] = node_angles[sort_inds[1]]-node_angles[sort_inds[0]]
    
    # Rail data
    rail_data_unsrt = pickle.load(open(filename + '_rail.pickle', 'rb'))
    rail_data = sort_dict(rail_data_unsrt, rail_data_unsrt['X'][:,0])   # Sort by x-coordinate
    
    # As for the wheel, labels should be updated to ensure conformance to odb labels
    rail_part = get.part(names.rail_part, stepnr=new_cycle_nr)
    contact_nodes = rail_part.sets[names.rail_contact_nodes].nodes
    
    new_node_labels = np.array([node.label for node in contact_nodes])
    new_node_coords = np.array([node.coordinates[0:2] for node in contact_nodes])
    
    sort_inds = np.argsort(new_node_coords[:,0])        # Sort by x-coordinate
    rail_data['label'] = new_node_labels[sort_inds]     # Add correct node labels
    
    return rp_data, wheel_data, rail_data

    
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
    rp_data, wheel_data, rail_data = get_old_node_data(old_model.name, new_cycle_nr)
    u2_end = rp_data['U'][1]
    ur3_end = rp_data['UR'][-1]
    
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
    
    # Boundary conditions and loads to be modified
    ctrl_bc = new_model.boundaryConditions[names.rp_ctrl_bc]
    # ctrl_load = new_model.loads[names.rp_vert_load]
    
    # Define steps
    return_step_name = names.get_step_return(new_cycle_nr)
    new_model.StaticStep(name=return_step_name, previous=last_step_in_old_job,
                         timeIncrementationMethod=FIXED, initialInc=0.1, 
                         maxNumInc=10, 
                         #amplitude=STEP
                         )
    
    rolling_start_step_name = names.get_step_roll_start(new_cycle_nr)
    rs_time = rolling_time*end_stp_frac
    new_model.StaticStep(name=rolling_start_step_name, previous=return_step_name, timePeriod=rs_time, 
                         #maxNumInc=3, initialInc=rs_time, minInc=rs_time/2.0, maxInc=rs_time)
                         maxNumInc=30, initialInc=rs_time/10, minInc=rs_time/20, maxInc=rs_time/10)
                         
    rolling_step_name = names.get_step_rolling(new_cycle_nr)
    r_time = rolling_time*(1.0 - 2.0*end_stp_frac)
    dt0 = r_time/ipar['nom_num_incr_rolling']
    dtmin = r_time/(ipar['max_num_incr_rolling']+1)
    new_model.StaticStep(name=rolling_step_name, previous=rolling_start_step_name, timePeriod=r_time, 
                         maxNumInc=ipar['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
                         
    rolling_step_end_name = names.get_step_roll_end(new_cycle_nr)
    re_time = rolling_time*end_stp_frac
    new_model.StaticStep(name=rolling_step_end_name, previous=rolling_step_name, timePeriod=re_time, 
                         #maxNumInc=3, initialInc=re_time, minInc=re_time/2.0, maxInc=re_time)
                         maxNumInc=30, initialInc=re_time/10, minInc=re_time/20, maxInc=re_time/10)
                         
    num_element_rolled = int(np.round(ur3_end/wheel_data['angle_incr']))
    rot_angle = num_element_rolled*wheel_data['angle_incr']
    return_angle = ur3_end - rot_angle
    
    print 'step               = ', new_cycle_nr
    print 'w_node_angle_incr. = ', wheel_data['angle_incr']
    print 'num_element_rolled = ', num_element_rolled
    print 'rot_angle          = ', rot_angle
    print 'ur3_end            = ', ur3_end
    print 'return_angle       = ', return_angle
    
    ctrl_bc.setValuesInStep(stepName=return_step_name, ur3=return_angle, u1=0, u2=u2_end)
    
    # Determine which nodes are in contact at the end of previous step
    old_contact_node_indices = get_contact_nodes(wheel_data, rp_data)
    
    # Identify the new nodes in contact by shifting the sorted list by num_element_rolled
    new_contact_node_indices = old_contact_node_indices + num_element_rolled
    
    x_rp_old = rp_data['X'] + rp_data['U']
    x_rp_new = rp_data['X'] + np.array([0, u2_end])
    
    wheel_nodes = new_model.rootAssembly.instances['WHEEL'].sets['CONTACT_NODES'].nodes
    
    for iold, inew in zip(old_contact_node_indices, new_contact_node_indices):
        
        new_node_id = int(wheel_data['label'][inew])
        
        # Node positions
        #  Deformed old position
        xold = wheel_data['X'][iold] + wheel_data['U'][iold]
        #  Undeformed new position
        Xnew = wheel_data['X'][inew]
        
        # Old position relative old rp is same as new position relative new rp
        xnew = x_rp_new + (xold - x_rp_old)
        
        unew = xnew - Xnew                      # Displacement is relative undeformed pos
                    
        wnode_bc_name = return_step_name + '_wheel_' + str(new_node_id)
        region = new_model.rootAssembly.Set(name=wnode_bc_name, 
                                            nodes=wheel_nodes[(new_node_id-1):(new_node_id)])
                                            # number due to nodes numbered from 1 but python from 0
        
        # Prescribe the displacements of the old nodes to the new node, but moved back to start point
        node_bc = new_model.DisplacementBC(name=wnode_bc_name,
                                                createStepName=return_step_name, 
                                                region=region, u1=unew[0], u2=unew[1])
        # Prescribe the same velocity in a the rolling_start_step as in the last step of the previous sim
        vel = wheel_data['V'][iold] # Take velocity from old node
        unext = unew + vel*rs_time
        node_bc.setValuesInStep(stepName=rolling_start_step_name, u1=unext[0], u2=unext[1])
        # Free the prescribed displacements of the nodes in the general rolling step
        node_bc.deactivate(stepName=rolling_step_name)
        
    # Lock all rail contact node displacements
    rail_contact_nodes = new_model.rootAssembly.instances['RAIL'].sets['CONTACT_NODES'].nodes
    rcn_sortinds = np.argsort([node.coordinates[0] for node in rail_contact_nodes])
        
    for i, rcn_ind in enumerate(rcn_sortinds):
        node = rail_contact_nodes[rcn_ind]
        node_id = int(node.label)
        rnode_bc_name = return_step_name + '_rail_' + str(node_id)
        region = new_model.rootAssembly.Set(name=rnode_bc_name, nodes=mesh.MeshNodeArray([node]))
        lock_rail_bc = new_model.VelocityBC(name=rnode_bc_name,
                                            createStepName=return_step_name,
                                            region=region,
                                            v1=0., v2=0., v3=0.)
        vel = rail_data['V'][i]
        lock_rail_bc.setValuesInStep(stepName=rolling_start_step_name, 
                                     v1=vel[0], v2=vel[1], v3=0.0)
        lock_rail_bc.deactivate(stepName=rolling_step_name)
    
    # Set values for wheel center
    ctrl_bc.setValuesInStep(stepName=rolling_start_step_name, u1=rolling_length*end_stp_frac, 
                            ur3=rolling_angle*end_stp_frac + return_angle, u2=FREED)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, u1=rolling_length*(1.0 - end_stp_frac), 
                            ur3=rolling_angle*(1.0 - end_stp_frac) + return_angle, u2=FREED)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_end_name, 
                            u1=rolling_length, u2=FREED,
                            ur3=rolling_angle + return_angle)
    
    # Add restart capability to the last rolling step
    new_model.steps[rolling_step_end_name].Restart(numberIntervals=1)
    
    
def get_contact_nodes(wheel_data, rp_data):
    xpos = wheel_data['X'][:,0] + wheel_data['U'][:,0]
    rp_x = rp_data['X'][0] + rp_data['U'][0]
    contact_length = user_settings.max_contact_length
    all_indices = np.arange(wheel_data['X'].shape[0])
    contact_indices = all_indices[np.abs(xpos-rp_x) < contact_length/2.0]
    
    return contact_indices[1:-1]    # Remove the first and last to avoid taking one too many on either side
    
    
def get_node_angles(wheel_node_coord, rp_coord):
    dx = np.transpose([wheel_node_coord[:, i] - rp_coord[i] for i in range(2)])
    
    # Get angle wrt. y-axis
    angles = np.arctan2(dx[:, 0], -dx[:, 1])
    return angles
    
    
if __name__ == '__main__':
    main()

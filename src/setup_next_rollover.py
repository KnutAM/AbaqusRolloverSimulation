# System imports
import sys
import os
import numpy as np
import inspect
import pickle

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset, mesh
from abaqusConstants import *

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)

import loading_module as loadmod
import user_settings
import naming_mod as names
import get_utils as get

# Reload to account for script updates when running from inside abaqus CAE
reload(loadmod)
reload(user_settings)
reload(names)
reload(get)

   
def get_roll_back_info(rp_data, wheel_data):
    ur3_end = rp_data['UR'][-1]
    num_element_rolled = int(np.round(ur3_end/wheel_data['angle_incr']))
    rot_angle = num_element_rolled*wheel_data['angle_incr']
    return_angle = ur3_end - rot_angle
    
    return num_element_rolled, return_angle
    
   
def setup_next_rollover(new_cycle_nr):
    old_model = get.model(cycle_nr=new_cycle_nr-1)
    old_job_name = names.get_job(new_cycle_nr-1)
    # copy the old model and add new steps. Restart from the previous job
    new_model_name = names.get_model(new_cycle_nr)
    new_model = mdb.Model(name=new_model_name, objectToCopy=old_model)
    
    # Setup restart parameters
    last_step_in_old_job = old_model.steps.keys()[-1]
    new_model.setValues(restartJob=old_model.name, restartStep=last_step_in_old_job)
    
    moveback_reapply_load(new_cycle_nr, last_step_in_old_job)
    
    # Add restart capability to the last rolling step
    last_step = new_model.steps.keys()[-1]
    new_model.steps[last_step].Restart(numberIntervals=1)
    
    
def moveback_reapply_load(new_cycle_nr, last_step_in_old_job, lock_rail=True):
    # Move straight back. Add step to reapply load.
    # Input
    # new_cycle_nr          Cycle number for the analysis to be set up
    # last_step_in_old_job  Name of the last step in the job from which the current continues from
    # lock_rail             Should the nodes on the rail be locked during moving back?
    
    # Model
    new_model = get.model(new_cycle_nr)
    # Load parameters
    inc_par = user_settings.time_incr_param
    rol_par = loadmod.get_rolling_parameters()
    
    # Roll back info
    rp_data, wheel_data, rail_data = get_old_node_data(new_cycle_nr)
    u1_end = rp_data['U'][0]
    u2_end = rp_data['U'][1]
    ur3_end = rp_data['UR'][-1]
    
    num_element_rolled, ret_ang = get_roll_back_info(rp_data, wheel_data)
    
    # Determine which nodes are in contact at the end of previous step
    old_contact_node_indices = get_contact_nodes(wheel_data, rp_data)
    
    # Identify the new nodes in contact by shifting the sorted list by num_element_rolled
    new_contact_node_indices = old_contact_node_indices + num_element_rolled
    
    # Boundary conditions and loads to be modified
    ctrl_bc = new_model.boundaryConditions[names.rp_ctrl_bc]
    
    # Define steps
    return_step_name = names.get_step_return(new_cycle_nr)
    time = user_settings.numtrick['move_back_time']
    new_model.StaticStep(name=return_step_name, previous=last_step_in_old_job, 
                         maxNumInc=2, timePeriod=time, initialInc=time,
                         amplitude=STEP
                         )
    
    reapply_step_name = 'reapply' + names.cycle_str(new_cycle_nr)
    new_model.StaticStep(name=reapply_step_name, previous=return_step_name,
                         timeIncrementationMethod=FIXED, initialInc=time, 
                         maxNumInc=2, timePeriod=time, 
                         amplitude=STEP
                         )
                         
    release_nodes_step_name = 'release' + names.cycle_str(new_cycle_nr)
    new_model.StaticStep(name=release_nodes_step_name, previous=reapply_step_name,
                         timeIncrementationMethod=FIXED, initialInc=time, 
                         maxNumInc=2, timePeriod=time, 
                         amplitude=STEP
                         )
    
    rolling_step_name = names.get_step_rolling(new_cycle_nr)
    r_time = rol_par['time']
    dt0 = r_time/inc_par['nom_num_incr_rolling']
    dtmin = r_time/(inc_par['max_num_incr_rolling']+1)
    new_model.StaticStep(name=rolling_step_name, previous=release_nodes_step_name, timePeriod=r_time, 
                         maxNumInc=inc_par['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
                         
    # Set values for wheel center
    ctrl_bc.setValuesInStep(stepName=return_step_name, ur3=ret_ang, u1=0, u2=u2_end)
    ctrl_bc.setValuesInStep(stepName=reapply_step_name, ur3=ret_ang, u1=0, u2=FREED)
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, u1=rol_par['length'], 
                            ur3=rol_par['angle'] + ret_ang, u2=FREED)
    
    fid = open('bc_python.txt', 'w')
    fid.write('%u %25.15E %25.15E %25.15E\n' % (1, 0.0, u2_end, ret_ang))
    # Set values for wheel
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

        # Free the prescribed displacements of the nodes in the general rolling step
        node_bc.deactivate(stepName=rolling_step_name)
        fid.write('%u %25.15E %25.15E\n' % (wheel_nodes[new_node_id-1].label, unew[0], unew[1]))
        
    fid.close()
    
    
    # Set values for rail
    if lock_rail:
        # Lock all rail contact node displacements
        rail_contact_node_set = new_model.rootAssembly.instances['RAIL'].sets['CONTACT_NODES']
        lock_rail_bc = new_model.VelocityBC(name=return_step_name + '_lockrail',
                                                createStepName=return_step_name,
                                                region=rail_contact_node_set,
                                                v1=0., v2=0., v3=0.)
        lock_rail_bc.deactivate(stepName=release_nodes_step_name)
    
    
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
    

def get_old_node_data(new_cycle_nr):
    # Read in results from previous cycle. Sort node data and ensure that node labels match that in the odb file
    filename = names.get_model(new_cycle_nr-1)
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
    wheel_part = get.part(names.wheel_part, cycle_nr=new_cycle_nr)
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
    rail_part = get.part(names.rail_part, cycle_nr=new_cycle_nr)
    contact_nodes = rail_part.sets[names.rail_contact_nodes].nodes
    
    new_node_labels = np.array([node.label for node in contact_nodes])
    new_node_coords = np.array([node.coordinates[0:2] for node in contact_nodes])
    
    sort_inds = np.argsort(new_node_coords[:,0])        # Sort by x-coordinate
    rail_data['label'] = new_node_labels[sort_inds]     # Add correct node labels
    
    return rp_data, wheel_data, rail_data
    
    
def get_contact_nodes(wheel_data, rp_data):
    xpos = wheel_data['X'][:,0] + wheel_data['U'][:,0]
    rp_x = rp_data['X'][0] + rp_data['U'][0]
    contact_length = user_settings.max_contact_length
    all_indices = np.arange(wheel_data['X'].shape[0])
    contact_indices = all_indices[np.abs(xpos-rp_x) < (contact_length/2.0)]
    
    return contact_indices[1:-1]    # Remove the first and last to avoid taking one too many on either side
    
    
def get_node_angles(wheel_node_coord, rp_coord):
    dx = np.transpose([wheel_node_coord[:, i] - rp_coord[i] for i in range(2)])
    
    # Get angle wrt. y-axis
    angles = np.arctan2(dx[:, 0], -dx[:, 1])
    return angles
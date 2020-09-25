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
import assembly, regionToolset, mesh
from abaqusConstants import *

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not this_path in sys.path:
    sys.path.append(this_path)


import material_and_section_module as matmod
import rail_setup as railmod
import wheel_super_element_import as wheelmod
import loading_module as loadmod
import contact_module as contactmod
import user_settings
import abaqus_python_tools as apt
import naming_mod as names
import get_utils as get
import setup_next_rollover as next_rollover
import user_subroutine as usub
import move_back_module as movebackmod

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
reload(next_rollover)


def main():
    apt.setup_log_file()
    usub.setup()
    num_cycles = user_settings.num_cycles
    t0 = time.time()
    if user_settings.use_restart:
        setup_initial_model()
        #return None
        setup_time = time.time() - t0
        if num_cycles > 0:
            run_time = run_cycle(cycle_nr=1, run=user_settings.run_simulation)
        
        t0 = time.time()
        save_results(cycle_nr=1)
        result_time = time.time() - t0
        apt.log('Setup time:  ' + str(setup_time) + 's \n' + 
                'Run time:    ' + str(run_time) + ' s \n' + 
                'Result time: ' + str(result_time) + ' s')
        
        
        for nr in range(2, num_cycles+1):
            t0 = time.time()
            next_rollover.setup_next_rollover(new_cycle_nr=nr)
            setup_time = time.time() - t0
            run_time = run_cycle(cycle_nr=nr)
            apt.log('Setup time:  ' + str(setup_time) + 's \n' + 
                    'Run time:    ' + str(run_time) + ' s \n' + 
                    'Result time: ' + str(result_time) + ' s')
            save_results(cycle_nr=nr)
        
        join_odb_files([names.get_odb(cycle_nr=i+1) for i in range(num_cycles)])
    else:
        setup_full_model()
        setup_time = time.time() - t0
        run_time = run_cycle(cycle_nr=1, run=user_settings.run_simulation)
        
        apt.log('Setup time: ' + str(setup_time) + 's \n' + 
                'Run time:   ' + str(run_time) + 's')
    
    
def join_odb_files(odb_file_list):
    joined_odb_file_name = 'rollover_joined'
    copyfile(odb_file_list[0] + '.odb', joined_odb_file_name + '.odb')
    try:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abaqus restartjoin originalodb=' + joined_odb_file_name + ' restartodb='+odb_i, shell=True)
    except:
        for odb_i in odb_file_list[1:]:
            subprocess.call('abq2017 restartjoin originalodb=' + joined_odb_file_name + ' restartodb='+odb_i, shell=True)
 
    
def run_cycle(cycle_nr, n_proc=1, run=True):
    job_name = names.get_job(cycle_nr)
    model_name = names.get_model(cycle_nr)
    job_type = ANALYSIS if cycle_nr == 1 else RESTART
    
    if job_name in mdb.jobs:
        del(mdb.jobs[job_name])
    
    usub_path = 'usub/usub-std.' + ('obj' if os.name == 'nt' else 'o')

    job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                  model=model_name, name=job_name, nodalOutputPrecision=SINGLE,
                  multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                  type=job_type, userSubroutine=usub_path)
    
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
    matmod.setup_sections()
    
    # Setup rail
    railmod.setup_rail()
    
    # Setup wheel
    wheelmod.setup_wheel()
    
    # Position wheel
    loadmod.preposition()

    # Setup loading
    loadmod.initial_bc()
    
    # Setup contact conditions
    contactmod.setup_contact()
    
    # Setup output requests
    loadmod.setup_outputs()
    
    # Generate user subroutine unless object file given in input
    if user_settings.usub_object_path:
        usub.copy_to_usub_dir(user_settings.usub_object_path)
    else:
        usub.generate()
    
    # Direct editing of input file (should be done last)
    the_model.keywordBlock.synchVersions(storeNodesAndElements=True)
    
    ## Add user element 
    wheelmod.add_wheel_super_element_to_inp()
    
    if not user_settings.use_restart:            
        ## Add output to .fil file
        movebackmod.add_output(cycle_nr=1)
    
    return the_model
    
def setup_full_model():
    setup_initial_model()   # Should potentially edit input file at end of setup_full_model and not
                            # at the end of setup_initial_model. But for now, that should be ok.
    
    if user_settings.num_cycles > 1:
        setup_remaining_rolling_cycles()


def setup_steps(the_model, cycle_nr, rol_par, inc_par):
    previous_step_name = names.get_step_rolling(cycle_nr-1)
    return_step_name = names.get_step_return(cycle_nr)
    time = user_settings.numtrick['move_back_time']
    the_model.StaticStep(name=return_step_name, previous=previous_step_name, 
                         initialInc=time, maxNumInc=11, timePeriod=time, minInc=time/10,
                         amplitude=STEP
                         )
    
    reapply_step_name = 'reapply' + names.cycle_str(cycle_nr)
    the_model.StaticStep(name=reapply_step_name, previous=return_step_name,
                         initialInc=time, maxNumInc=11, timePeriod=time, minInc=time/10,
                         amplitude=STEP
                         )
                         
    release_nodes_step_name = 'release' + names.cycle_str(cycle_nr)
    the_model.StaticStep(name=release_nodes_step_name, previous=reapply_step_name,
                         initialInc=time, maxNumInc=11, timePeriod=time, minInc=time/10,
                        #amplitude=STEP
                         )
    
    rolling_step_name = names.get_step_rolling(cycle_nr)
    r_time = rol_par['time']
    dt0 = r_time/inc_par['nom_num_incr_rolling']
    dtmin = r_time/(inc_par['max_num_incr_rolling']+1)
    the_model.StaticStep(name=rolling_step_name, previous=release_nodes_step_name, timePeriod=r_time, 
                         maxNumInc=inc_par['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
                         
    return return_step_name, reapply_step_name, release_nodes_step_name, rolling_step_name
    
    
def setup_remaining_rolling_cycles():
    the_model = get.model()
    # Setup steps for second cycle
    inc_par = user_settings.time_incr_param
    rol_par = loadmod.get_rolling_parameters()
    
    step_names = setup_steps(the_model, cycle_nr=2, rol_par=rol_par, inc_par=inc_par)
    # returns: return_step_name, reapply_step_name, release_nodes_step_name, rolling_step_name
    
    # Determine which nodes that should be controlled by moving back boundary conditions
    winst = get.inst(names.wheel_inst)
    w_info = wheelmod.get_wheel_info()
    wheel_contact_region_angle = w_info['contact_angle'] - w_info['rolling_angle']
    
    rp = loadmod.get_preposition_motion()  # For some unknown reason, rp_node has no coords?
    
    # To ensure correct node numbers, we use the coordinates from the node set. This is as the node 
    # label order could be different the order in the coordinate list from wheel_info
    wn = winst.sets[names.wheel_contact_nodes].nodes
    wn_rel_coords = np.array([np.array(n.coordinates[0:2])-np.array(rp[0:2]) for n in wn])
    wn_angels = np.arctan2(wn_rel_coords[:,0], -wn_rel_coords[:,1])
    
    bc_nodes = wn.sequenceFromLabels([n.label for a, n in zip(wn_angels, wn)
                                      if np.abs(a) < wheel_contact_region_angle/2.0])
    
    # Setup boundary condition for those nodes
    bc_cnod_region = regionToolset.Region(nodes=bc_nodes)
    cnod_bc = get.model().DisplacementBC(name='contact_node_bc', createStepName=step_names[0], 
                                         region=bc_cnod_region, distributionType=USER_DEFINED)
    
    # Get boundary condition for rp
    ctrl_bc = the_model.boundaryConditions[names.rp_ctrl_bc]
    
    # Setup boundary condition for rail contact nodes
    rinst = get.inst(names.rail_inst)
    rail_contact_node_set = rinst.sets[names.rail_contact_nodes]
    lock_rail_bc = the_model.VelocityBC(name='lock_rail_contact_surface',
                                        createStepName=step_names[0],
                                        region=rail_contact_node_set)
    
    for cycle_nr in range(2, user_settings.num_cycles+1):
        if cycle_nr > 2:
            step_names = setup_steps(the_model, cycle_nr, rol_par, inc_par)
        
        # Set boundary conditions for controlled contact nodes
        cnod_bc.setValuesInStep(stepName=step_names[0], u1=0.0, u2=0.0)
        cnod_bc.setValuesInStep(stepName=step_names[3], u1=FREED, u2=FREED)
        
        # Set boundary condition for rp
        ctrl_bc.setValuesInStep(stepName=step_names[0], 
                                u1=0.0, u2=0.0, ur3=0.0)    # DISP routine to set all (u1,u2,ur3)
        ctrl_bc.setValuesInStep(stepName=step_names[1], 
                                u1=0.0, u2=FREED, ur3=0.0)  # DISP routine to set u1 and ur3
    
        # Set boundary condition for rail contact nodes
        lock_rail_bc.setValuesInStep(stepName=step_names[0], v1=0.0, v2=0.0)
        lock_rail_bc.setValuesInStep(stepName=step_names[2], v1=FREED, v2=FREED)
    
    
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

    
if __name__ == '__main__':
    main()

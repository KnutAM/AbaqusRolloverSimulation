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
import setup_next_rollover as next_rollover
import user_subroutine as usub

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
    setup_initial_model()
    usub.generate()
    setup_time = time.time() - t0
    if num_cycles > 0:
        # If debugging continuation, can comment run_cycle(..) and uncomment run_time = -1.0
        # to avoid simulating the first cycle if result files already exist. 
        #run_time = -1.0
        run_time = run_cycle(cycle_nr=1)
    else:
        run_time = run_cycle(cycle_nr=1, n_proc=1, run=False)
        return
    
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
        # if nr == 2:
            # FiOpRe = mdb.models['rollover_00002'].FieldOutputRequest(name='F-Output-2', 
               # createStepName='return_00002', variables=('S', 'U'), substructures=(
                # 'WHEEL.Entire Substructure', 'WHEEL.WHEEL-REFPT_', 'WHEEL.WHEELCENTER', 
                # 'WHEEL.WHEEL_CONTACT_NODES', 'WHEEL.WHEEL_WHEEL'), sectionPoints=DEFAULT, 
                # rebar=EXCLUDE)
            # FiOpRe.deactivate(stepName='rolling_start_00002')
        run_time = run_cycle(cycle_nr=nr)
        apt.log('Setup time:  ' + str(setup_time) + 's \n' + 
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
    
    # Edit input directly to add user element (should be done last)
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

# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import load
import regionToolset
import step

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)
import user_settings
import wheel_super_element_import as wsei
import naming_mod as names
import get_utils as get


def setup_outputs(is_3d=False):
    the_model = get.model()
    assy = get.assy()
    wheel_inst = get.inst(names.wheel_inst)
    rail_inst = get.inst(names.rail_inst)
    wheel_refpoint = assy.sets[names.wheel_rp_set]
    if is_3d:
        vars_rp = [var + str(i) for i in range(1,4) for var in ['U', 'UR', 'RF', 'RM']]
        vars_nods = [var + str(i) for i in range(1,4) for var in ['U', 'RF']]
    else:
        vars_nods = [var + str(i) for i in range(1,3) for var in ['U', 'RF']]
        vars_rp = vars_nods[:]  # make a copy of vars_nods
        vars_rp.append('UR3')
        vars_rp.append('RM3')
        
    step_name = names.step1
    
    # WHEEL CONTROL POINT
    the_model.HistoryOutputRequest(name='RP', createStepName=step_name, 
                                   region=wheel_refpoint, variables=vars_rp,
                                   frequency=100)
    
    # WHEEL CONTACT AREA
    wheel_contact_region = wheel_inst.sets[names.wheel_contact_nodes]
    the_model.HistoryOutputRequest(name='wheel', createStepName=step_name, 
                                   region=wheel_contact_region, variables=vars_nods,
                                   frequency=LAST_INCREMENT)
                        
    # RAIL CONTACT AREA
    rail_contact_region = rail_inst.sets[names.rail_contact_nodes]
    the_model.HistoryOutputRequest(name='rail', createStepName=step_name, 
                                   region=rail_contact_region, variables=vars_nods,
                                   frequency=LAST_INCREMENT)
    
    
def get_preposition_motion():
    rolling_par = get_rolling_parameters()
    radius = rolling_par['radius']
    rolling_angle = -0.5*rolling_par['angle']
    rgeom = user_settings.rail_geometry
    
    vector = ((rgeom['length'] - rgeom['max_contact_length'])/2.0, radius, 0.0)
    
    return rolling_angle, vector
    

def preposition():
    wheel_inst = get.inst(names.wheel_inst)
    
    rotation_angle, translation_vector = get_preposition_motion()
    
    # Rotate wheel to correct starting angle
    wheel_inst.rotateAboutAxis(axisPoint=(0.0, 0.0, 0.0), 
                               axisDirection=(0.0, 0.0, 1.0), 
                               angle= 180.0 * rotation_angle/np.pi)
    
    # Move wheel to correct starting position
    wheel_inst.translate(vector=translation_vector)
    
    
def get_rolling_parameters():
    wheel_info = wsei.get_wheel_info()
    nominal_radius = wheel_info['r']
    
    lpar = user_settings.load_parameters
    rolling_length = -user_settings.rail_geometry['length']
    rolling_time = abs(rolling_length)/lpar['speed']
    rolling_angle = -(1+lpar['slip'])*rolling_length/nominal_radius
    
    rpar = {'length': rolling_length,
            'time': rolling_time,
            'angle': rolling_angle,
            'radius': nominal_radius,
            'load': lpar['normal_load']
            }
            
    return rpar
    
    
def initial_bc():
    the_model = get.model()
    assy = get.assy()
    wheel_inst = get.inst(names.wheel_inst)
    rail_inst = get.inst(names.rail_inst)
    wheel_refpoint = assy.sets[names.wheel_rp_set]
    
    lpar = user_settings.load_parameters
    ntpar = user_settings.numtrick
    ipar = user_settings.time_incr_param
    
    the_model.StaticStep(name=names.step1, previous=names.step0, nlgeom=ON)
    
    # BC for rail (bottom)
    rail_contact_nodes = rail_inst.sets[names.rail_bottom_nodes]
    the_model.DisplacementBC(name=names.fix_rail_bc, createStepName=names.step0, 
        region=rail_contact_nodes, u1=SET, u2=SET, ur3=UNSET)
    
    # BC for wheel
    ctrl_bc = the_model.DisplacementBC(name=names.rp_ctrl_bc, createStepName=names.step1, 
                                       region=wheel_refpoint, u1=0.0, ur3=0.0, 
                                       u2=-lpar['initial_depression'])
    
    #the_model.StaticStep(name=names.step2, previous=names.step1)
    #ctrl_bc.setValuesInStep(stepName=names.step2, u2=FREED)
    #the_model.ConcentratedForce(name='ctrl_load', createStepName=names.step2, 
    #                            region=wheel_refpoint, cf2=-lpar['normal_load'])

    rpar = get_rolling_parameters()
    rolling_length = rpar['length']
    rolling_time = rpar['time']
    rolling_angle = rpar['angle']
    
    end_stp_frac = abs(ntpar['extrap_roll_length']/rolling_length)
    
    rolling_step_name = names.get_step_rolling(1)
    time = rolling_time*(1.0 - end_stp_frac)
    dt0 = time/ipar['nom_num_incr_rolling']
    dtmin = time/(ipar['max_num_incr_rolling']+1)
    the_model.StaticStep(name=rolling_step_name, previous=names.step1, timePeriod=time,
                         maxNumInc=ipar['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
    
    the_model.ConcentratedForce(name=names.rp_vert_load, createStepName=rolling_step_name, 
                                region=wheel_refpoint, cf2=-lpar['normal_load'])
    
    
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, 
                            u1=rolling_length*(1.0 - end_stp_frac), u2=FREED,
                            ur3=rolling_angle*(1.0 - end_stp_frac))
    
    rolling_step_end_name = names.get_step_roll_end(1)
    time = rolling_time*end_stp_frac
    the_model.StaticStep(name=rolling_step_end_name, previous=rolling_step_name, timePeriod=time,
                         maxNumInc=3, initialInc=time, minInc=time/2.0, maxInc=time)
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_end_name, 
                            u1=rolling_length, u2=FREED, ur3=rolling_angle)
    
    the_model.steps[rolling_step_end_name].Restart(numberIntervals=1)
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
import abaqus_python_tools as apt


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
                                   frequency=LAST_INCREMENT)
    
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
    rgeom = user_settings.rail_geometry
    
    vector = ((rgeom['length'] - rgeom['max_contact_length'])/2.0, radius, 0.0)
    
    return vector
    

def preposition():
    wheel_inst = get.inst(names.wheel_inst)
    
    translation_vector = get_preposition_motion()
    
    # Move wheel to correct starting position
    wheel_inst.translate(vector=translation_vector)
    
    
def get_rolling_parameters():
    wheel_info = wsei.get_wheel_info()
    nominal_radius = wheel_info['outer_diameter']/2.0
    
    lpar = user_settings.load_parameters
    rolling_length = -user_settings.rail_geometry['length']
    rolling_time = abs(rolling_length)/lpar['speed']
    rolling_angle = -(1+lpar['slip'])*rolling_length/nominal_radius
    
    # Check that rolling angle is not too large for wheel
    w_contact_angle = wheel_info['contact_angle']
    w_rolling_angle = wheel_info['rolling_angle']
    
    if np.abs(rolling_angle) > w_contact_angle:
        apt.log('Rolling angle (abs value) too large for chosen wheel')
        apt.log('Rolling angle = %6.2f deg' % (rolling_angle*180/np.pi))
        apt.log('Contact angle = %6.2f deg (max abs rolling angle)' % (w_contact_angle*180/np.pi))
        raise ValueError
    
    max_contact_length_as_angle = 0.5*user_settings.max_contact_length/nominal_radius
    if max_contact_length_as_angle > (w_contact_angle-w_rolling_angle):
        apt.log('max_contact_length too large for chosen wheel')
        apt.log('Wheel rolling angle = %6.2f deg' % (w_rolling_angle*180/np.pi))
        apt.log('Wheel contact angle = %6.2f deg' % (w_contact_angle*180/np.pi))
        apt.log('Settings max contact length = %6.2f mm' % (user_settings.max_contact_length))
        apt.log('Require wheel contact-rolling angle = %6.2f deg > %6.2f deg' % 
                ((w_contact_angle-w_rolling_angle)*180/np.pi, max_contact_length_as_angle*180/np.pi))
        raise ValueError
    
    rpar = {'length': rolling_length,
            'time': rolling_time,
            'angle': rolling_angle,
            'radius': nominal_radius,
            'load': lpar['normal_load'],
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
    step1_time = 1.0
    the_model.StaticStep(name=names.step1, previous=names.step0, nlgeom=ON, timePeriod=step1_time,
                         initialInc=step1_time, minInc=step1_time/100, maxInc=step1_time,
                         maxNumInc=101)
    
    # BC for rail (bottom)
    rail_contact_nodes = rail_inst.sets[names.rail_bottom_nodes]
    the_model.DisplacementBC(name=names.fix_rail_bc, createStepName=names.step0, 
        region=rail_contact_nodes, u1=SET, u2=SET, ur3=UNSET)
    
    # BC for wheel
    distribution = UNIFORM if user_settings.use_restart else USER_DEFINED
    
    ctrl_bc = the_model.DisplacementBC(name=names.rp_ctrl_bc, createStepName=names.step1, 
                                       region=wheel_refpoint, u1=0.0, ur3=0.0, 
                                       u2=-lpar['initial_depression'],
                                       distributionType=distribution)
    
    rpar = get_rolling_parameters()
    
    if not user_settings.use_restart:
        # Save initial depression and time for that cycle
        with open('initial_depression.txt', 'w') as fid:
            fid.write('%25.15e %25.15e' % (step1_time, -lpar['initial_depression']))
            
        # Save rolling parameters for each cycle to file. The user subroutine DISP will read this file
        # and use the data for the previous step number if current not defined. 
        with open('rolling_parameters.txt', 'w') as fid:
            fid.write('%10.0f %25.15e %25.15e %25.15e\n' % 
                      (1, rpar['time'], rpar['length'], rpar['angle']))
    
    rolling_step_name = names.get_step_rolling(1)
    time = rpar['time']
    dt0 = time/ipar['nom_num_incr_rolling']
    dtmin = time/(ipar['max_num_incr_rolling']+1)
    the_model.StaticStep(name=rolling_step_name, previous=names.step1, timePeriod=time,
                         maxNumInc=ipar['max_num_incr_rolling'], 
                         initialInc=dt0, minInc=dtmin, maxInc=dt0)
    
    the_model.ConcentratedForce(name=names.rp_vert_load, createStepName=rolling_step_name, 
                                region=wheel_refpoint, cf2=-lpar['normal_load'])
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, 
                            u1=rpar['length'], u2=FREED, ur3=rpar['angle'])
    
    the_model.steps[rolling_step_name].Restart(numberIntervals=1)
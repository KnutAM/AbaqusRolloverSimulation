# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import load

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))
import user_settings


def setup_outputs(the_model, ctrl_pt_reg, is_3d=False):
    if is_3d:
        vars_rp = [var + str(i) for i in range(1,4) for var in ['U', 'UR', 'RF', 'RM']]
        vars_nods = [var + str(i) for i in range(1,4) for var in ['U', 'RF']]
    else:
        vars_nods = [var + str(i) for i in range(1,3) for var in ['U', 'RF']]
        vars_rp = vars_nods[:]  # make a copy of vars_nods
        vars_rp.append('UR3')
        vars_rp.append('RM3')
        
    step_name = the_model.steps.keys()[1]   # First step after the initial step
     
    # WHEEL CONTROL POINT
    the_model.HistoryOutputRequest(name='RP', createStepName=step_name, 
                                    region=ctrl_pt_reg, variables=vars_rp,
                                    frequency=100)
    
    # WHEEL CONTACT AREA
    wheel_inst = the_model.rootAssembly.instances['WHEEL']
    wheel_contact_region = wheel_inst.sets['CONTACT_NODES']
    the_model.HistoryOutputRequest(name='wheel', createStepName=step_name, 
                                    region=wheel_contact_region, variables=vars_nods,
                                    frequency=LAST_INCREMENT)
                        
    # RAIL CONTACT AREA
    rail_inst = the_model.rootAssembly.instances['RAIL']
    rail_contact_region = rail_inst.sets['CONTACT_NODES']
    the_model.HistoryOutputRequest(name='rail', createStepName=step_name, 
                                    region=rail_contact_region, variables=vars_nods,
                                    frequency=LAST_INCREMENT)
    

def preposition(assy):
    # Find instances to move (if substructure used, two instances for the wheel 
    # must be moved...
    names = [user_settings.wheel_naming['part'], 
             user_settings.wheel_naming['contact_part']]
    insts = tuple([name for name in names if name in assy.instances])
    
    wgeom = user_settings.wheel_geometry
    rgeom = user_settings.rail_geometry
    
    # Rotate wheel to correct starting angle
    assy.rotate(instanceList=insts, 
             axisPoint=(0, wgeom['outer_diameter']/2.0, 0.0), 
             axisDirection=(0.0, 0.0, 1.0), 
             angle= - 180.0 * wgeom['rolling_angle']/(2 * np.pi))
    
    # Move wheel to correct starting position
    assy.translate(instanceList=insts, 
                   vector=((rgeom['length'] - rgeom['max_contact_length'])/2.0, 
                           0.0, 0.0))
    

def initial_bc(the_model, assy, wheel_refpoint, rail_bottom):
    lpar = user_settings.load_parameters
    preload_step_name = 'preload'
    the_model.StaticStep(name=preload_step_name, previous='Initial', nlgeom=ON)
    
    # BC for rail (bottom)
    the_model.DisplacementBC(name='BC-1', createStepName='Initial', 
        region=rail_bottom, u1=SET, u2=SET, ur3=UNSET)
    
    # BC for wheel
    ctrl_bc = the_model.DisplacementBC(name='ctrl_bc', createStepName=preload_step_name, 
                                       region=wheel_refpoint, u1=0.0, ur3=0.0, 
                                       u2=-lpar['initial_depression'])
    
    load_step_name = 'load_application'
    the_model.StaticStep(name=load_step_name, previous=preload_step_name)
    ctrl_bc.setValuesInStep(stepName=load_step_name, u2=FREED)
    the_model.ConcentratedForce(name='ctrl_load', createStepName=load_step_name, 
                                region=wheel_refpoint, cf2=-lpar['normal_load'])
                                
    rolling_step_name = 'rolling_0'
    the_model.StaticStep(name=rolling_step_name, previous=load_step_name, maxNumInc=1000, 
                         initialInc=0.01, minInc=1e-06, maxInc=0.01)
    
    rolling_length = -user_settings.rail_geometry['length']
    nominal_radius = user_settings.wheel_geometry['outer_diameter']/2.0
    rolling_angle = -(1+lpar['slip'])*rolling_length/nominal_radius
    
    ctrl_bc.setValuesInStep(stepName=rolling_step_name, u1=rolling_length, 
                            ur3=rolling_angle)
    
    the_model.steps[rolling_step_name].Restart(numberIntervals=1)

# def add_rolling_step(model, wheel_refpoint
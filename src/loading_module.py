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
sys.path.append(os.path.dirname(src_file_path))
import user_settings

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
    the_model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    
    # BC for rail (bottom)
    the_model.DisplacementBC(name='BC-1', createStepName='Initial', 
        region=rail_bottom, u1=SET, u2=SET, ur3=UNSET)
    
    # BC for wheel
    ctrl_bc = the_model.DisplacementBC(name='ctrl_BC', createStepName='Step-1', 
                                       region=wheel_refpoint, u1=0.0, ur3=0.0, 
                                       u2=-lpar['initial_depression'])
    
    the_model.StaticStep(name='Step-2', previous='Step-1')
    ctrl_bc.setValuesInStep(stepName='Step-2', u2=FREED)
    the_model.ConcentratedForce(name='Load-1', createStepName='Step-2', 
                                region=wheel_refpoint, cf2=-lpar['normal_load'])
                                
    
    the_model.StaticStep(name='Step-3', previous='Step-2', maxNumInc=1000, 
                         initialInc=0.01, minInc=1e-06, maxInc=0.01)
    
    rolling_length = -user_settings.rail_geometry['length']
    nominal_radius = user_settings.wheel_geometry['outer_diameter']/2.0
    rolling_angle = -(1+lpar['slip'])*rolling_length/nominal_radius
    
    ctrl_bc.setValuesInStep(stepName='Step-3', u1=rolling_length, 
                            ur3=rolling_angle)
    

# def add_rolling_step(model, wheel_refpoint
from __future__ import print_function

from abaqusConstants import *
import step, load

from rollover.utils import naming_mod as names


def setup(the_model, initial_depression=0.1, inbetween_step_time=1.e-6, inbetween_max_incr=100,
          rolling_length=30.0, max_incr=1000, min_incr=60,
          cycles=[1], vertical_load=[150.e3], speed=[30.0], slip=[0.01511335013], rail_ext=[0.0]):
    
    assy = the_model.rootAssembly
    rail_inst = assy.instances[names.rail_inst]
    wheel_inst = assy.instances[names.wheel_inst]
    
    # Setup boundary conditions valid from the beginning
    if names.rail_rp_set in assy.sets.keys():
        the_model.DisplacementBC(name=names.rail_rp_bc, createStepName=names.step0, 
                                 u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
                                 region=assy.sets[names.rail_rp_set])
        bottom_u3=UNSET
    else:
        bottom_u3=0.0
    
    the_model.DisplacementBC(name=names.rail_bottom_bc, createStepName=names.step0, 
                             region=rail_inst.sets[names.rail_bottom_nodes],
                             u1=0.0, u2=0.0, u3=bottom_u3)
    
    # Setup the initial depression step
    the_model.StaticStep(name=names.step1, previous=names.step0, nlgeom=ON, 
                         timePeriod=inbetween_step_time,
                         initialInc=inbetween_step_time/min(5, inbetween_max_incr), 
                         minInc=inbetween_step_time/inbetween_max_incr, 
                         maxInc=inbetween_step_time,
                         maxNumInc=inbetween_max_incr)
    
    wheel_rp_bc = the_model.DisplacementBC(name=names.wheel_rp_bc, createStepName=names.step1, 
                                           region=wheel_inst.sets[names.wheel_rp_set], 
                                           u2=-initial_depression,
                                           u1=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)
                             
                             
    # Setup the load application step
    the_model.StaticStep(name=names.step2, previous=names.step1,
                         timePeriod=inbetween_step_time,
                         initialInc=inbetween_step_time/min(5, inbetween_max_incr), 
                         minInc=inbetween_step_time/inbetween_max_incr, 
                         maxInc=inbetween_step_time,
                         maxNumInc=inbetween_max_incr)
    
    the_model.ConcentratedForce(name=names.wheel_vert_load, createStepName=names.step2, 
                                region=wheel_inst.sets[names.wheel_rp_set], 
                                cf2=-vertical_load[0])
    
    wheel_rp_bc.setValuesInStep(stepName=names.step2, u2=FREED)
    
    


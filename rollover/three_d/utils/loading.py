from __future__ import print_function
import numpy as np

from abaqusConstants import *
import step, load

from rollover.utils import naming_mod as names


def setup(the_model, rolling_length, rolling_radius, vertical_load, 
          cycles=[1], speed=1.0, slip=0.0, rail_ext=0.0, num_cycles=1, 
          initial_depression=0.1, inbetween_step_time=1.e-6, inbetween_max_incr=100,
          max_incr=1000, min_incr=100):
    """Setup the loading for the rollover simulation
    
    "cycle data type": If value is scalar, the same value will be 
                       applied to all cycles. If list, it should have 
                       the same length as `cycles`, and the value will 
                       be applied from the corresponding cycle and 
                       onwards.
    
    :param the_model: The model to which the contact settings should be
                      applied
    :type the_model: Model object (Abaqus)
    
    :param rolling_length: The length the wheel shall roll (not 
                           accounting for rail extensions)
    :type rolling_length: float
    
    :param rolling_radius: The rolling radius used to calculate wheel 
                           rotation as function of slip.
    :type rolling_radius: float
    
    :param vertical_load: Vertical wheel load. See "cycle data type".
    :type vertical_load: float / list[ float ]
    
    :param cycles: List of cycle numbers where new load parameters are
                   specified.
    :type cycles: list[ int ]
    
    :param speed: The linear speed of the wheel. See "cycle data type".
    :type speed: float / list[ float ]
    
    :param slip: The slip ratio of the rolling. See "cycle data type".
    :type slip: float / list[ float ]
    
    :param rail_ext: The rail extension length. See "cycle data type".
    :type rail_ext: float / list[ float ]
    
    :param num_cycles: Number of rollover cycles
    :type num_cycles: int
    
    :param initial_depression: The amount to lower the wheel (in y-dir)
                               before changing to load control.
    :type initial_depression: float
    
    :param inbetween_step_time: The step time used for initial 
                                depression, first load application,
                                moving back step, reapplication of load,
                                and release of node steps.
    :type inbetween_step_time: float
    
    :param inbetween_max_incr: Max number of increments for steps for 
                               which inbetween_step_time applies
    :type inbetween_max_incr: int
    
    :param max_incr: Max number of increments during the rolling step
    :type max_incr: int
    
    :param min_incr: Min number of increments during the rolling step
    :type min_incr: int
    
    
    :returns: Number of cycles used
    :rtype: int
    
    """
    
    # Change floats to lists
    vertical_load = [vertical_load] if isinstance(vertical_load, (int, float)) else vertical_load
    speed = [speed] if isinstance(speed, (int, float)) else speed
    slip = [slip] if isinstance(slip, (int, float)) else slip
    rail_ext = [rail_ext] if isinstance(rail_ext, (int, float)) else rail_ext
    
    # Write loading file
    write_loading_file(initial_depression/inbetween_step_time, rolling_length, 
                       rolling_radius, cycles, vertical_load, speed, slip, rail_ext)
    
    # Define regions
    assy = the_model.rootAssembly
    rail_inst = assy.instances[names.rail_inst]
    
    rail_cn = rail_inst.sets[names.rail_contact_nodes]
    rail_bot = rail_inst.sets[names.rail_bottom_nodes]
    
    wheel_inst = assy.instances[names.wheel_inst]
    wheel_rp = wheel_inst.sets[names.wheel_rp_set]
    wheel_cn = wheel_inst.sets[names.wheel_contact_nodes]
    
    # .Optional regions
    # ..Rail reference point
    if names.rail_rp_set in rail_inst.sets.keys():
        rail_rp = rail_inst.sets[names.rail_rp_set]  
        rail_rp_exists = True
        bottom_u3=UNSET
    else:
        rail_rp_exists = False
        bottom_u3=0.0
        
    # ..Check if symmetry bc should be applied and if so get symmetry plane sets
    rail_sym_exists = names.rail_sym_set in rail_inst.sets.keys()
    rail_sym_set = rail_inst.sets[names.rail_sym_set] if rail_sym_exists else None
    
    wheel_sym_exists = names.wheel_sym_set in wheel_inst.sets.keys()
    wheel_sym_set = wheel_inst.sets[names.wheel_sym_set] if wheel_sym_exists else None
    
    if rail_sym_exists != wheel_sym_exists:
        raise Exception('Either both or none of wheel and rail must be symmetric')
    else:
        sym_bc = rail_sym_exists
    if sym_bc:
        rail_cn, rail_cn_sym_edge = make_sym_sets(the_model)
    
    # Setup boundary conditions valid from the beginning
    if rail_rp_exists:
        rail_rp_bc = the_model.DisplacementBC(name=names.rail_rp_bc, 
                                              createStepName=names.step0, 
                                              u1=SET, u2=SET, u3=SET, 
                                              ur1=SET, ur2=SET, ur3=SET,
                                              region=rail_rp,
                                              distributionType=USER_DEFINED)
    
    if not names.rail_substructure in the_model.parts.keys():
        the_model.DisplacementBC(name=names.rail_bottom_bc, createStepName=names.step0, 
                                 region=rail_bot, u1=0.0, u2=0.0, u3=bottom_u3)
    
    if sym_bc:
        rail_sym_bc = the_model.DisplacementBC(name=names.rail_sym_bc,
                                               createStepName=names.step0,
                                               u1=SET, region=rail_sym_set)
        wheel_sym_bc = the_model.DisplacementBC(name=names.wheel_sym_bc,
                                                createStepName=names.step0,
                                                u1=SET, region=wheel_sym_set)
                                                
    # Setup the initial depression step
    step_name = setup_step(the_model, names.step1, names.step0, 
                           inbetween_step_time, min(5,inbetween_max_incr),
                           inbetween_max_incr)
    
    wheel_rp_bc = the_model.DisplacementBC(name=names.wheel_rp_bc, 
                                           createStepName=step_name, 
                                           region=wheel_rp, 
                                           u1=0.0, u2=0.0,u3=0.0, 
                                           ur1=0.0, ur2=0.0, ur3=0.0,
                                           distributionType=USER_DEFINED)
                             
    # Setup the load application step
    step_name = setup_step(the_model, names.step2, step_name, 
                           inbetween_step_time, min(5,inbetween_max_incr),
                           inbetween_max_incr)
    
    wheel_rp_fz = the_model.ConcentratedForce(name=names.wheel_vert_load, 
                                              createStepName=step_name, 
                                              region=wheel_rp, 
                                              cf2=-vertical_load[0])
    
    wheel_rp_bc.setValuesInStep(stepName=step_name, u2=FREED)
    
    # Setup the remaining steps
    for cycle_nr in range(1, num_cycles+1):
        # 1: ROLLING STEP ----------------------------------------------
        fz, v = get_cycle_data(cycle_nr, cycles, [vertical_load, speed])
        step_time = rolling_length/v
        new_step_name = names.get_step_rolling(cycle_nr)
        step_name = setup_step(the_model, new_step_name, step_name,
                               step_time, min_incr, max_incr)
                               
        wheel_rp_fz.setValuesInStep(stepName=step_name, cf2=-fz)
        
        # 2: MOVE BACK STEP --------------------------------------------
        step_name = setup_step(the_model, names.get_step_return(cycle_nr+1), step_name, 
                               inbetween_step_time, min_num=1, max_num=inbetween_max_incr,
                               amp=STEP)
        wheel_rp_bc.setValuesInStep(stepName=step_name, u2=0.0)
        
        if cycle_nr == 1:   # Setup bc for first time
            wheel_cn_bc = the_model.DisplacementBC(name='WHEEL_CN_BC', createStepName=step_name,
                                                   region=wheel_cn, distributionType=USER_DEFINED)
            rail_cn_bcs = [the_model.VelocityBC(name='RAIL_CN_BC', createStepName=step_name,
                                                  region=rail_cn)]
            if sym_bc:
                rail_cn_bcs.append(the_model.VelocityBC(name='RAIL_CN_EDGE_BC', 
                                                        createStepName=step_name,
                                                        region=rail_cn_sym_edge))
        
        # All wheel contact nodes controlled by DISP subroutine:
        wheel_cn_bc.setValuesInStep(stepName=step_name, u1=0.0, u2=0.0, u3=0.0)
        # All rail contact nodes locked:
        rail_cn_bcs[0].setValuesInStep(stepName=step_name, v1=0.0, v2=0.0, v3=0.0)
        if sym_bc:
            rail_cn_bcs[1].setValuesInStep(stepName=step_name, v2=0.0, v3=0.0)
        
        # 3: REAPPLY WHEEL RP LOAD STEP --------------------------------
        step_name = setup_step(the_model, names.get_step_reapply(cycle_nr+1), step_name, 
                               inbetween_step_time, min_num=1, max_num=inbetween_max_incr,
                               amp=STEP)
        # Release u2 for wheel reference point changing to force control
        wheel_rp_bc.setValuesInStep(stepName=step_name, u2=FREED)
        
        # 4: RELEASE CONTACT NODES STEP --------------------------------
        step_name = setup_step(the_model, names.get_step_release(cycle_nr+1), step_name, 
                               inbetween_step_time, min_num=1, max_num=inbetween_max_incr)
        
        # All wheel contact nodes free (no longer ctrl by DISP subroutine):
        wheel_cn_bc.setValuesInStep(stepName=step_name, u1=FREED, u2=FREED, u3=FREED)
        
        # All rail contact nodes free:
        for rail_cn_bc in rail_cn_bcs:
            rail_cn_bc.setValuesInStep(stepName=step_name, v1=FREED, v2=FREED, v3=FREED)
        
        # next cycle ---------------------------------------------------
    
    return num_cycles
    
def write_loading_file(initial_depression_speed, rolling_length, rolling_radius,
                       cycles, load, speed, slip, rail_ext):
    """Write the loading file, `names.loading_file`, used by the user 
    subroutine DISP.
    
    :param initial_depression_speed: The speed at which the wheel is 
                                     lowered during the initial 
                                     depression step
    :type initial_depression_speed: float
    
    :param rolling_length: The length the wheel shall roll (not 
                           accounting for rail extensions)
    :type rolling_length: float
    
    :param rolling_radius: The rolling radius used to calculate wheel 
                           rotation as function of slip.
    :type rolling_radius: float
    
    :param cycles: List of cycle numbers where new load parameters are
                   specified.
    :type cycles: list[ int ]
    
    :param load: List of vertical wheel loads for each cycle in cycles.
    :type load: list[ float ]
    
    :param speed: List of linear wheel speeds for each cycle in cycles.
    :type speed: list[ float ]
    
    :param slip: List of wheel slips for each cycle in cycles.
    :type slip: float / list[ float ]
    
    :param rail_ext: List of rail extension length for each cycle in 
                     cycles.
    :type rail_ext: list[ float ]
    
    :returns: None
    :rtype: None
    
    """
    
    with open(names.loading_file, 'w') as fid:
        fid.write('%25.15e\n' % (rolling_length))
        fid.write('%25.15e\n' % (-initial_depression_speed))
        fid.write('%0.0f\n' % (len(cycles)))
        for c, v, s, rext in zip(cycles, speed, slip, rail_ext):
            rolling_time = rolling_length/v
            rot_per_length = (1+s)/rolling_radius
            fid.write(('%0.0f' + 3*', %25.15e' + '\n') % (c, rolling_time, rot_per_length, rext))
    
    
def get_cycle_data(cycle_nr, cycles, cycle_data):
    """ Given a list of cycle data, give the relevant data for 
    `cycle_nr`
    
    :param cycle_nr: The cycle number for which the cycle data should be 
                     extracted
    :type cycle_nr: int
    
    :param cycles: List of cycles for which the items in cycle data are
                   specified for.
    :type cycles: list[ int ]
    
    :param cycle_data: List of cycle data. 
    
                       Each cycle data is a list with the same length as
                       cycles.
    :type cycle_data: list[ list [float/int] ]
    
    :returns: A list containing the items in each list in cycle data on 
              the position `i` in cycle_nr before `cycle_nr < cycles[i]`
    :rtype: list[ float/int ]
    
    """
    search_cycles = cycles[:]
    search_cycles.append(np.iinfo(np.int).max)  # Append max int possible
    
    ind = np.argmax(cycle_nr < np.array(search_cycles))-1
    
    return [data[ind] for data in cycle_data]

    
def setup_step(the_model, name, prev_name, step_time, min_num, max_num, amp=RAMP):
    """ Setup a new step.
    
    :param the_model:
    :type the_model:
    
    :param name:
    :type name:
    
    :param prev_name:
    :type prev_name:
    
    :param step_time:
    :type step_time:
    
    :param min_num:
    :type min_num: 
    
    :param max_num:
    :type max_num: 
    
    :param amp:
    :type amp: 
    
    """
    the_model.StaticStep(name=name, previous=prev_name,
                         timePeriod=step_time,
                         initialInc=step_time/min_num,
                         minInc=step_time/max_num,
                         maxInc=step_time/min_num,
                         maxNumInc=max_num,
                         amplitude=amp,
                         nlgeom=ON)
    return name
    
def make_sym_sets(the_model):
    """ Based on the contact node set and the symmetric node set, create 
    2 new sets: 
    
    - One set that contains all nodes in the contact node set, except 
      those that also are in the symmetric node set
    - One set that contains the nodes in both the contact node set and
      the symmetric node set.
    
    :param the_model: The model containing the rail part with the sets 
                      initial sets and to which the new sets are added
    :type the_model: Model object (Abaqus)
    
    :returns: A list of the created sets, see list above. The sets 
              belong to the rail instance.
    :rtype: list[ Set object (Abaqus) ]
    
    """
    
    rail_part = the_model.parts[names.rail_part]
    cn_set = rail_part.sets[names.rail_contact_nodes]
    sym_set = rail_part.sets[names.rail_sym_set]
    
    # Find node in the contact node set and in the yz-plane:
    TOL = 1.e-6
    cn_nodes = cn_set.nodes
    contact_sym_edge_nodes = cn_nodes.getByBoundingBox(xMin=-TOL, xMax=TOL)
    contact_sym_edge_set_p = rail_part.Set(name='RAIL_CONTACT_SYM_EDGE',
                                           nodes=contact_sym_edge_nodes)
    
    contact_set_bb = cn_nodes.getBoundingBox()
    cn_x_min = contact_set_bb['low'][0]
    cn_x_max = contact_set_bb['high'][0]
    if abs(cn_x_min) < TOL: # Rail in positive x direction
        contact_set_reduced_nodes = cn_nodes.getByBoundingBox(xMin=TOL)
    elif abs(cn_x_max) < TOL: # Rail in negative x direction
        contact_set_reduced_nodes = cn_nodes.getByBoundingBox(xMax=-TOL)
    else:
        raise ValueError('A symmetric rail should be soley on one side of the yz-plane')
    
    contact_set_reduced_p = rail_part.Set(name='RAIL_CONTACT_SET_REDUCED',
                                        nodes=contact_set_reduced_nodes)
    
    # Return the instance sets:
    the_model.rootAssembly.regenerate()
    rail_inst = the_model.rootAssembly.instances[names.rail_inst]
    contact_set_reduced = rail_inst.sets['RAIL_CONTACT_SET_REDUCED']
    contact_sym_edge_set = rail_inst.sets['RAIL_CONTACT_SYM_EDGE']
    
    
    return contact_set_reduced, contact_sym_edge_set
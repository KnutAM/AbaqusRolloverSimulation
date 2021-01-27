""" Functions to be called from plugins

"""
from __future__ import print_function
import os, shutil

from abaqus import mdb
from abaqusConstants import *

from rollover import local_paths
from rollover.utils import naming_mod as names
from rollover.utils import abaqus_python_tools as apt
from rollover.three_d.rail import basic as rail_basic
from rollover.three_d.rail import mesher as rail_mesh
from rollover.three_d.utils import symmetric_mesh_module as sm

from rollover.three_d.wheel import substructure as wheel_substr
from rollover.three_d.wheel import super_element as super_wheel

from rollover.three_d.rail import include as rail_include
from rollover.three_d.wheel import include as wheel_include
from rollover.three_d.utils import contact
from rollover.three_d.utils import loading
from rollover.three_d.utils import odb_output
from rollover.three_d.utils import fil_output



def get_csv(csv, type):
    """ Convert a comma separated string of values to list of given type
    :param csv: Comma separated string
    :type csv: str
    
    :param type: a type casting function, e.g. float, int, str
    :type type: function
    
    :returns: A list of values of type type
    :rtype: list[type]
    """
    
    if type==str:
        return [str(itm).strip() for itm in csv.split(',')]
    else:
        return [type(itm) for itm in csv.split(',')]

def create_rail(profile, name, length, mesh_size, pt_min, pt_max, pt, 
                sym_sign=0):
    """Create a rail model from plugin input
    
    :param profile: Path to an Abaqus sketch profile saved as .sat file 
                    (acis)
    :type profile: str
    
    :param name: Name of file to save rail as
    :type name: str
    
    :param length: Length of rail to be extruded
    :type length: float
    
    :param mesh_size: Mesh size to be used: fine, coarse (csv data)
    :type mesh_size: str
    
    :param pt_min: point 1 in refine rectangle, csv data
    :type pt_min: str
    
    :param pt_max: point 2 in refine rectangle, csv data
    :type pt_max: str
    
    :param pt: point inside refine rectangle (overlapping rail geom),
               csv data
    :type pt: str
    
    :param sym_sign: Direction of symmetry normal (along x-axis), if 0
                     no symmetry is applied.
    :type sym_sign: int
    
    """
    
    refinement_cell = [get_csv(pt_min, float), get_csv(pt_max, float)]
    point_in_refine_cell = get_csv(pt, float)
    point_in_refine_cell.append(length/2.0) # Append z coordinate
    sym_dir = None if sym_sign == 0 else [sym_sign, 0, 0]
    rail_model = rail_basic.create(profile, length, 
                                   refine_region=refinement_cell, 
                                   sym_dir=sym_dir)
    rail_part = rail_model.parts[names.rail_part]
    fine_mesh, coarse_mesh = get_csv(mesh_size, float)
    
    rail_mesh.create_basic(rail_part, point_in_refine_cell, 
                           fine_mesh=fine_mesh, coarse_mesh=coarse_mesh)

    mdb.saveAs(pathName=name)
    
    
def periodicize_mesh():
    """ Attempt to make the mesh periodic between the sides.
    """
    the_model = mdb.models[names.rail_model]
    rail_part = the_model.parts[names.rail_part]
    
    sm.make_periodic_meshes(rail_part, 
                            source_sets=[rail_part.sets[names.rail_side_sets[0]]], 
                            target_sets=[rail_part.sets[names.rail_side_sets[1]]])
    
    rail_part.generateMesh()
    
    
def create_wheel(profile, name, mesh, quadratic, ang_int, x_int, 
                 partition_y):
    """Create a wheel super element from plugin input
    
    :param profile: Path to an Abaqus sketch profile saved as .sat file 
                    (acis)
    :type profile: str
    
    :param name: Name of file to save wheel as
    :type name: str
    
    :param mesh: Mesh size, fine, coarse (csv data)
    :type mesh_fine: str
    
    :param quadratic: Use quadratic elements? (0=false, 1=true)
    :type quadratic: int
    
    :param ang_int: Angular interval to retain (min, max) csv data
    :type ang_int: str
        
    :param x_int: x interval to retain (min, max) (csv data)
    :type x_int: str
    
    :param partition_y: Y-coordinate outside which to use the fine mesh
    :type partition_y: float
    
    """
    
    # Create wheel parameter dictionary 
    wheel_param = {'wheel_profile': profile, 
                   'mesh_sizes': get_csv(mesh, float),
                   'quadratic_order': quadratic == 1,
                   'wheel_contact_pos': get_csv(x_int, float),
                   'wheel_angles': get_csv(ang_int, float),
                   'partition_line': partition_y}
    
    # Create wheel substructure
    job = wheel_substr.generate(wheel_param)
    job.submit()
    job.waitForCompletion()
    
    # Save resulting file
    mdb.saveAs(pathName=name + '.cae')
    
    # Check that analysis succeeded
    if job.status != COMPLETED:
        raise Exception('Abaqus job failed, please see ' + job.name + '.log')
        
    # Create super element files
    super_wheel.get_uel_mesh(wheel_param['quadratic_order'])
    
    # Copy all relevant files to specified directory (name)
    if os.path.exists(name):
        shutil.rmtree(name)
    os.mkdir(name)

    for file_name in [names.uel_stiffness_file, 
                      names.uel_coordinates_file, 
                      names.uel_elements_file,
                      name + '.cae']:
        shutil.copy(file_name, name)

def create_rollover(rail, shadow, use_rp, wheel, trans, stiffness,
                    mu, k_c, uz_init, t_ib, n_inc_ib, L_roll, R_roll, 
                    max_incr, min_incr, N,
                    cycles, load, speed, slip, rail_ext, output_table):
    """
    :param rail: path to rail .cae file 
    :type rail: str
    
    :param shadow: How far to extend shadow region in negative/positive
                   direction. Given as csv
    :type shadow: str
    
    :param use_rp: Use a rail reference point? (0:false,1:true)
    :type use_rp: int
    
    :param wheel: path to wheel folder
    :type wheel: str
    
    :param trans: wheel translation to position before starting (csv)
    :type trans: str
    
    :param stiffness: Young's modulus for wheel
    :type stiffness: float
    
    :param mu: friction coefficient
    :type mu: float
    
    :param k_c: contact stiffness (N/mm^3)
    :type k_c: float
    
    :param uz_init: Initial depression, before changing to load control
    :type uz_init: float
    
    :param t_ib: Step time inbetween rolling steps
    :type t_ib: float
    
    :param n_inc_ib: Maximum number of increments for inbetween steps
    :type n_inc_ib: int
    
    :param L_roll: Rolling length / rail length
    :type L_roll: float
    
    :param R_roll: Rolling radius (used to convert slip to rot. speed)
    :type R_roll: float
    
    :param max_incr: Maximum number of increments
    :type max_incr: int
    
    :param min_incr: Minimum number of increments
    :type min_incr: int
    
    :param N: Number of cycles to simulate
    :type N: int
    
    :param cycles: Which cycles load parameters are specified for. 1 
                   must be included, given as csv
    :type cycles: str
    
    :param load: Wheel load, one value for each specified cycle in 
                 cycles. Given as csv.
    :type load: str
    
    load, speed, slip, rail_ext, output_table
    
    :param speed: Wheel speed, one value for each specified cycle in 
                  cycles. Given as csv.
    :type speed: str
    
    :param slip: Wheel slip, one value for each specified cycle in 
                 cycles. Given as csv.
    :type slip: str
    
    :param rail_ext: Rail extension, one value for each specified cycle
                     in cycles. Given as csv.
    :type rail_ext: str
    
    :param output_table: Field output data specification. Each item 
                         should contain: tuple(field output name, set,
                         variables, frequency, cycle) where the two last
                         are integers and the former are strings. 
    :type output_table: tuple
    
    :returns: None
    
    """
    rp = {'model_file': rail,
          'shadow_extents': get_csv(shadow, float),
          'use_rail_rp': use_rp==1}
    wp = {'folder': wheel,
          'translation': get_csv(trans, float),
          'stiffness': stiffness}
          
    cp = {'friction_coefficient': mu,
          'contact_stiffness': k_c}
            
    lp = {'initial_depression': uz_init,
          'inbetween_step_time': t_ib,
          'inbetween_max_incr': n_inc_ib,
          'rolling_length': L_roll,
          'rolling_radius': R_roll,
          'max_incr': max_incr,
          'min_incr': min_incr,
          'num_cycles': N,
          'cycles': get_csv(cycles, int),
          'vertical_load': get_csv(load, float),
          'speed': get_csv(speed, float),
          'slip': get_csv(slip, float),
          'rail_ext': get_csv(rail_ext, float)}
          
        
    # Create model
    rollover_model = apt.create_model(names.model)
    
    # Include rail
    num_nodes, num_elems = rail_include.from_file(rollover_model, **rp)
    
    # Include wheel
    start_lab = (num_nodes+1, num_elems+1)
    wheel_stiffness = wheel_include.from_folder(rollover_model, 
                                                start_labels=start_lab,
                                                **wp)
    # Setup contact
    contact.setup(rollover_model, **cp)
    
    # Setup loading
    num_cycles = loading.setup(rollover_model, **lp)
    
    # Setup field outputs (if requested)
    if len(output_table) > 0:
        heads = ['set', 'var', 'freq', 'cycle']
        op = {}
        for row in output_table:
            op[row[0]] = {}
            for head, val in zip(heads, row[1:]):
                if head == 'var':
                    op[row[0]][head] = get_csv(val, str)
                else:
                    op[row[0]][head] = val
                
        #op = {row[0]: {head:val for head, val in zip(heads, row[1:])} 
        #      for row in output_table}
        odb_output.add(rollover_model, op, num_cycles)
    
    # Add wheel uel to input file
    wheel_include.add_wheel_super_element_to_inp(rollover_model, 
                                                 wheel_stiffness, 
                                                 wp['folder'],
                                                 wp['translation'])
    # Add output to .fil file
    fil_output.add(rollover_model, num_cycles)
    
    # Write reference point coordinates to file:
    with open(names.rp_coord_file, 'w') as fid:
        rail_rp_coord = [0,0,0]
        wheel_rp_coord = wp['translation']
        fid.write(('%25.15e'*3 + '\n') % tuple(wheel_rp_coord))
        fid.write(('%25.15e'*3 + '\n') % tuple(rail_rp_coord))
    
    # Write input file
    obj_suff = '.o' if os.name == 'posix' else '.obj'
    usub = local_paths.data_path + '/usub/usub_rollover' + obj_suff
    
    the_job = mdb.Job(name=names.job, model=names.model,
                      userSubroutine=usub)
    the_job.writeInput(consistencyChecking=OFF)
    
    # Save model database
    mdb.saveAs(pathName=names.model)
    


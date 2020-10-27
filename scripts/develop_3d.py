"""This module is used to test during development
.. codeauthor:: Knut Andreas Meyer
"""
# System imports
from __future__ import print_function
import sys, os, inspect
import numpy as np

if sys.version_info.major == 3:
    if sys.version_info.minor < 4:
        from imp import reload
    else:
        from importlib import reload

from abaqus import mdb

# Add all paths here, should not be required in called modules
def add_subfolders_to_path(folder):
    if not folder in sys.path:
        sys.path.append(folder)
    for f in os.listdir(folder):
        if os.path.isdir(folder + '/' + f):
            add_subfolders_to_path(folder + '/' + f)
        
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)
add_subfolders_to_path(this_path)
add_subfolders_to_path(src_path + '/utils')


import naming_mod as names
import create_basic_rail as cbr
import mesh_rail as mr
import symmetric_mesh_module as sm
import create_shadow_regions as csr
import rail_constraints as rc
import sketch_tools as st
import create_wheel_mod as wheel

# Reload should only be used here, so need to import any module used down the import directory here if reload is required (i.e. when developing via abaqus cae)
reload(names)
reload(cbr)
reload(mr)
reload(sm)
reload(csr)
reload(rc)
reload(st)
reload(wheel)


def main():
    setup_wheel()

def setup_wheel():
    wheel_profile = src_path + '/../data/wheel_profiles/rs200_ro460_ri300.sat'
    
    mesh_2d = wheel.generate_2d_mesh(wheel_profile, mesh_sizes=[1.0, 10.0], 
                                     wheel_contact_pos = [-10.0, 1.0], partition_line= -450.0)
                           
    node_coords, tri_elems, quad_elems, contact_nodes, inner_nodes = mesh_2d
    for output in [node_coords, tri_elems, quad_elems, contact_nodes, inner_nodes]:
        print(output.shape)
    

def setup_rail():
    rail_material = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
    rail_sketch = src_path + '/../data/rail_profiles/BV50_half.sat'
    rail_length = 50.0
    rail_model = cbr.create_rail(rail_sketch, rail_length, refine_region=[[-20, 145],[20,160]],
                                 sym_dir = [1, 0, 0], material=rail_material)
    rail_part = rail_model.parts[names.rail_part]
    mr.create_basic_mesh(rail_part=rail_part, 
                         point_in_refine_cell = [0.0, 150.0, 1.0], 
                         fine_mesh=1.0, coarse_mesh=10.0)
    return
    # Need to setup material and section
    
    # Done creating the part. It should be saved to file and user can edit the file at will
    # mdb.saveAs(pathName='rail')
    
    # At this point the created file should be opened, the 'RAIL' model copied and the rollover 
    # model should be created. 
    
    the_model = rail_model
    
    # Create shadow section:
    the_model.Material(name='ShadowElastic')
    the_model.materials['ShadowElastic'].Elastic(table=((1.0, 0.3), ))
    the_model.MembraneSection(name=names.rail_shadow_sect, material='ShadowElastic', thickness=0.01)
    
    csr.create_shadow_region(rail_part, extend_lengths=[40, 40])
    
    bc_sets, br_sets = rc.create_constraint_sets(rail_part, names.rail_bottom_nodes)
    sc_sets, sr_sets = rc.create_constraint_sets(rail_part, names.rail_side_sets[0], names.rail_side_sets[1])
    shc_sets1, shr_sets1 = rc.create_constraint_sets(rail_part, names.rail_shadow_sets[0], names.rail_contact_surf)
    shc_sets2, shr_sets2 = rc.create_constraint_sets(rail_part, names.rail_shadow_sets[1], names.rail_contact_surf)
    
    the_model.rootAssembly.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    rp_coord = rc.add_ctrl_point(the_model, y_coord=0.0)
    
    for c_sets, r_sets in zip([bc_sets, sc_sets, shc_sets1, shc_sets2], 
                              [br_sets, sr_sets, shr_sets1, shr_sets2]):
        for c_set, r_set in zip(c_sets, r_sets):
            rc.add_constraint(the_model, rail_length, c_set, names.rail_rp_set, rp_coord, r_set)
    
    
    
if __name__ == '__main__':
    main()

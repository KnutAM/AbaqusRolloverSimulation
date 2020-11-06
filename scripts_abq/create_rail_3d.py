"""Running this abaqus script creates a wheel super element. 

The dictionary described by the 'wheel_settings.json' file should
contain the keywords according to 
:py:func:`rollover.three_d.wheel.create.substructure` as well as
`'wheel_name'` giving the name of the folder to which the user element
files will be saved along with a copy of the `'wheel_settings.json'` 
file

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
import sys, os, shutil, inspect

# Abaqus imports
from abaqusConstants import *
from abaqus import mdb
import part, sketch, mesh, job

# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.three_d.rail import basic as rail_basic
from rollover.three_d.rail import mesher as rail_mesh
from rollover.three_d.rail import shadow_regions as rail_shadow_regions
from rollover.three_d.rail import constraints as rail_constraints

this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)    

def main():
    # Read in wheel section parameters
    rail_param = json_io.read(names.rail_settings_file)
    rail_model = rail_basic.create_from_param(rail_param)
    rail_mesh.create_basic_from_param(rail_model.parts[names.rail_part], rail_param)
    
    mdb.saveAs(pathName=rail_param['rail_name'])
    
    setup_rail(rail_model, rail_param)
    
    mdb.saveAs(pathName='done_develop.cae')


def setup_rail(the_model, rail_param):
    '''
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
    '''
    # Need to setup material and section
    
    # Done creating the part. It should be saved to file and user can edit the file at will
    # mdb.saveAs(pathName='rail')
    
    # At this point the created file should be opened, the 'RAIL' model copied and the rollover 
    # model should be created. 
    
    # the_model = rail_model
    
    # Create shadow section:
    rail_part = the_model.parts[names.rail_part]
    the_model.Material(name='ShadowElastic')
    the_model.materials['ShadowElastic'].Elastic(table=((1.0, 0.3), ))
    the_model.MembraneSection(name=names.rail_shadow_sect, material='ShadowElastic', thickness=0.01)
    
    rail_shadow_regions.create(rail_part, extend_lengths=[40, 40])
    
    bc_sets, br_sets = rail_constraints.create_sets(rail_part, names.rail_bottom_nodes)
    sc_sets, sr_sets = rail_constraints.create_sets(rail_part, names.rail_side_sets[0], names.rail_side_sets[1])
    shc_sets1, shr_sets1 = rail_constraints.create_sets(rail_part, names.rail_shadow_sets[0], names.rail_contact_surf)
    shc_sets2, shr_sets2 = rail_constraints.create_sets(rail_part, names.rail_shadow_sets[1], names.rail_contact_surf)
    
    the_model.rootAssembly.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    rp_coord = rail_constraints.add_ctrl_point(the_model, y_coord=0.0)
    
    for c_sets, r_sets in zip([bc_sets, sc_sets, shc_sets1, shc_sets2], 
                              [br_sets, sr_sets, shr_sets1, shr_sets2]):
        for c_set, r_set in zip(c_sets, r_sets):
            rail_constraints.add(the_model, rail_param['rail_length'], c_set, names.rail_rp_set, rp_coord, r_set)
    
    
    
if __name__ == '__main__':
    main()

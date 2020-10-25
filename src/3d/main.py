"""This module is used to test during development
.. codeauthor:: Knut Andreas Meyer
"""
# System imports
from __future__ import print_function
import sys, os, inspect

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

# Reload should only be used here, so need to import any module used down the import directory here if reload is required (i.e. when developing via abaqus cae)
reload(names)
reload(cbr)
reload(mr)
reload(sm)
reload(csr)

def main():
    rail_sketch = src_path + '/../data/rail_profiles/BV50_half.sat'
    rail_model = cbr.create_rail(rail_sketch, rail_length=50.0, refine_region=[[-20, 145],[20,160]],
                                 sym_dir = [1, 0, 0])
    rail_part = rail_model.parts[names.rail_part]
    mr.create_basic_mesh(rail_part=rail_part, 
                         point_in_refine_cell = [0.0, 150.0, 1.0], 
                         fine_mesh=1.0, coarse_mesh=10.0)
    
    # Need to create section:
    rail_model.Material(name='ShadowElastic')
    rail_model.materials['ShadowElastic'].Elastic(table=((1.0, 0.3), ))
    rail_model.MembraneSection(name=names.rail_shadow_sect, material='ShadowElastic', thickness=0.01)
    
    csr.create_shadow_region(rail_part, extend_lengths=[30, 10])
    
    mdb.saveAs(pathName='rail')
    # mdb.close()
    
    
if __name__ == '__main__':
    main()

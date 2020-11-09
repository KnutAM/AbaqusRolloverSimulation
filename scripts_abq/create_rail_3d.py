"""Running this abaqus script creates a basic rail .cae file

The dictionary described by the rail settings .json file with name
rollover.utils.naming_mod.rail_settings_file should contain keywords 
according to :py:func:`rollover.three_d.rail.basic.create_from_param` 
and :py:func:`rollover.three_d.rail.mesher.create_basic_from_param` as 
well as `'rail_name'` giving the name of the cae file to which the model 
is saved. 

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
# import sys, os, shutil, inspect

# Abaqus imports
# from abaqusConstants import *
# from abaqus import mdb
# import part, sketch, mesh, job

# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.three_d.rail import basic as rail_basic
from rollover.three_d.rail import mesher as rail_mesh


def main():
    # Read in wheel section parameters
    rail_param = json_io.read(names.rail_settings_file)
    rail_model = rail_basic.create_from_param(rail_param)
    rail_mesh.create_basic_from_param(rail_model.parts[names.rail_part], rail_param)
    
    mdb.saveAs(pathName=rail_param['rail_name'])
    
    
if __name__ == '__main__':
    main()

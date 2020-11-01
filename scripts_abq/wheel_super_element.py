"""Running this abaqus script creates a wheel super element. 

The dictionary described by the 'wheel_settings.json' file should
contain the keywords according to 
:py:func:`rollover.three_d.wheel.create.substructure`

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
import sys
import numpy as np

# Abaqus imports
from abaqusConstants import *
from abaqus import mdb
import part, sketch, mesh, job

# Project library imports
from rollover.utils import json_io
from rollover.utils import naming_mod as names
from rollover.three_d.wheel import substructure as wheel_substr
from rollover.three_d.wheel import super_element as super_wheel

try:
    reload(wheel_substr)
    reload(super_wheel)
    reload(names)
except NameError as ne:   # Will fail for Python 3, but that is ok:
    if sys.version_info.major == 3:
        pass    # Only required from cae which use Python 2
    else:
        raise ne
    

def main():
    # Read in wheel section parameters
    wheel_param = json_io.read('wheel_settings.json')
    
    # create_substructure(wheel_param)
    create_user_element(wheel_param)
    
        
    
    
def create_substructure(wheel_param):
    job = wheel_substr.generate(wheel_param)
    
    #job.submit()
    #job.waitForCompletion()
    
    
def create_user_element(wheel_param):
    coords, elems = super_wheel.get_uel_mesh()
    super_wheel.create_test_part(coords, elems)
    
    
if __name__ == '__main__':
    main()

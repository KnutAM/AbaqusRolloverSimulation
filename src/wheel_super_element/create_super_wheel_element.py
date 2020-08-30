# System imports
import sys
import os
import numpy as np
import inspect
import time
import subprocess

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset
from abaqusConstants import *
import mesh

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)
if not src_path in sys.path:
    sys.path.append(src_path)
if not this_path in sys.path:
    sys.path.append(this_path)
    
import user_settings
import wheel_simulation
reload(user_settings)

# Steps
# 1) Simulate unit deformations on wheel
job_name = wheel_simulation.simulate()

# 2) Read the odb file and save the forces, moments and corresponding coordinates required to build 
#    up the stiffness matrix in the next step


# 3) Built up the stiffness matrix for the wheel
# 4) Reduce the stiffness matrix to only the kept degrees of freedom.
# 5) Write a fortran file containing the data to calculate the superelement.



    
    
    


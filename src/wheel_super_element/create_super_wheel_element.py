# System imports
import sys
import os
import numpy as np
import inspect

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
import get_results
import stiffness_matrix
import uel
reload(user_settings)
reload(wheel_simulation)
reload(get_results)
reload(stiffness_matrix)
reload(uel)

# Steps
# 1) Simulate unit deformations on wheel
job_name = wheel_simulation.simulate()
# job_name = 'SUPER_WHEEL'

# 2) Read the odb file and save the forces, moments and corresponding coordinates required to build 
#    up the stiffness matrix in the next step
outer_node_coord, outer_node_RF, rp_node_RF = get_results.get_nodal_results(odb_name=job_name)

# 3) Built up the stiffness matrix for the wheel
Kfull = stiffness_matrix.create_stiffness_matrix(outer_node_coord, outer_node_RF, rp_node_RF)
np.savetxt('Kfull.txt', Kfull, fmt='%25.16e')

# 4) Reduce the stiffness matrix to only the kept degrees of freedom.
# angle_to_keep = 2*user_settings.wheel_geometry['rolling_angle']
angle_to_keep = np.pi/1.9
Kred, coords = stiffness_matrix.reduce_stiffness_matrix(Kfull, outer_node_coord, angle_to_keep)

# 5) Write a fortran file containing the data to calculate the superelement.
uel.create_uel(Kred, coords)


    
    
    


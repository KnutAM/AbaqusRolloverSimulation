# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import load

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
sys.path.append(os.path.dirname(src_file_path))
import user_settings


def loading(model, assy, wheel_refpoint, rail_bottom):
    
    model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    
    # BC for rail (bottom)
    model.DisplacementBC(name='BC-1', createStepName='Initial', 
        region=rail_bottom, u1=SET, u2=SET, ur3=UNSET, amplitude=UNSET, 
        distributionType=UNIFORM, fieldName='', localCsys=None)
    
    # BC for wheel
    model.DisplacementBC(name='BC-2', createStepName='Step-1', 
        region=wheel_refpoint, u1=0.0, u2=-1.0, ur3=0.0, amplitude=UNSET, fixed=OFF, 
        distributionType=UNIFORM, fieldName='', localCsys=None)
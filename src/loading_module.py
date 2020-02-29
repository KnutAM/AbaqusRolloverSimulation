# System imports
import sys
import os
import numpy as np

# Abaqus imports 
from abaqusConstants import *
import load


def loading(model, assy, wheel_refpoint, rail_bottom):
    
    assy.translate(instanceList=('WHEEL', ), vector=(-60.0, 0.0, 0.0))
    
    model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    
    # BC for rail (bottom)
    model.DisplacementBC(name='BC-1', createStepName='Initial', 
        region=rail_bottom, u1=SET, u2=SET, ur3=UNSET, amplitude=UNSET, 
        distributionType=UNIFORM, fieldName='', localCsys=None)
    
    # BC for wheel
    model.DisplacementBC(name='BC-2', createStepName='Step-1', 
        region=wheel_refpoint, u1=0.0, u2=-1.0, ur3=0.0, amplitude=UNSET, fixed=OFF, 
        distributionType=UNIFORM, fieldName='', localCsys=None)
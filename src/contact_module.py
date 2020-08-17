# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import interaction

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))
    
import user_settings

def setup_contact(model, assy, rail_contact_surface, wheel_contact_surface):
    create_step_name = 'Initial'
    model.ContactProperty('Contact')
    model.interactionProperties['Contact'].NormalBehavior(pressureOverclosure=LINEAR, contactStiffness=1.e6)
    model.interactionProperties['Contact'].TangentialBehavior(formulation=FRICTIONLESS)

    model.SurfaceToSurfaceContactStd(name='Contact', 
        createStepName=create_step_name, slave=rail_contact_surface, master=wheel_contact_surface, sliding=FINITE, 
        thickness=ON, interactionProperty='Contact', adjustMethod=NONE, 
        initialClearance=OMIT, datumAxis=None, clearanceRegion=None)

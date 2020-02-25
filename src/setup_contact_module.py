# System imports
import sys
import os
import numpy as np

# Abaqus imports 
from abaqusConstants import *
import interaction


def setup_contact(model, assy, rail_contact_surface, wheel_contact_surface):
    create_step_name = 'Initial'
    model.ContactProperty('Contact')
    model.interactionProperties['Contact'].NormalBehavior(pressureOverclosure=LINEAR, contactStiffness=1.e6)
    model.interactionProperties['Contact'].TangentialBehavior(formulation=FRICTIONLESS)

    model.SurfaceToSurfaceContactStd(name='Contact', 
        createStepName=create_step_name, master=rail_contact_surface, slave=wheel_contact_surface, sliding=FINITE, 
        thickness=ON, interactionProperty='Contact', adjustMethod=NONE, 
        initialClearance=OMIT, datumAxis=None, clearanceRegion=None)

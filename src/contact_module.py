# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
from abaqus import mdb
import interaction

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)
    
import user_settings
import naming_mod as names
import get_utils as get

def setup_contact(rail_contact_surface):
    the_model = get.model()
    assy = get.assy()
    wheel_contact_surface = assy.surfaces[names.wheel_contact_surf]
    
    cpar = user_settings.contact_parameters
    create_step_name = names.step0
    contact_prop = the_model.ContactProperty('Contact')
    contact_prop.NormalBehavior(pressureOverclosure=LINEAR, 
                                contactStiffness=cpar['penalty_stiffness'])
    contact_prop.TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, 
                                    slipRateDependency=OFF, pressureDependency=OFF, 
                                    temperatureDependency=OFF, dependencies=0, 
                                    table=((cpar['friction'], ), ), shearStressLimit=None, 
                                    maximumElasticSlip=FRACTION, fraction=0.005, 
                                    elasticSlipStiffness=None)

    the_model.SurfaceToSurfaceContactStd(name=names.get_contact(cycle_nr=1), 
                                         createStepName=create_step_name, 
                                         slave=rail_contact_surface, master=wheel_contact_surface, 
                                         sliding=FINITE, thickness=ON, 
                                         interactionProperty=contact_prop.name, adjustMethod=NONE, 
                                         initialClearance=OMIT, datumAxis=None, 
                                         clearanceRegion=None)

def renew_contact(cycle_nr):
    the_model = mdb.models[names.get_model(cycle_nr)]
    deactivation_step = names.get_step_return(cycle_nr)
    activation_step = names.get_step_roll_start(cycle_nr)
    old_interaction = the_model.interactions[the_model.interactions.keys()[-1]]
    the_model.Interaction(name=names.get_contact(cycle_nr), 
                          objectToCopy=old_interaction, toStepName=activation_step)
    old_interaction.deactivate(stepName=deactivation_step)
    

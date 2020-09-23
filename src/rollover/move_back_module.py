# move_back_module - This module provides functionality to setup output etc. to provide boundary 
# 					 conditions for wheel nodes when moving it back for the next cycle
# System imports
import sys, os, inspect

# Abaqus imports 
from abaqusConstants import *
import abaqus

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not this_path in sys.path:
    sys.path.append(this_path)

import naming_mod as names
import user_settings
import get_utils as get
import abaqus_python_tools as apt
import inp_file_edit_module as inpmod

def get_output_string(nset, variable='U', frequency=10000000):
    output_str = ('*NODE FILE, NSET=' + nset + 
                  ', FREQUENCY=%0.0f \n'
                  + variable) % (frequency)
    return output_str


def add_output(cycle_nr=1):
    the_model = get.model()
    assy = get.assy()
    if assy.isOutOfDate:
        assy.regenerate()
        
    kwb = the_model.keywordBlock
    
    # Add output for wheel contact nodes
    nset = names.wheel_inst + '.' + names.wheel_contact_nodes
    inpmod.add_at_end_of_cat(kwb, get_output_string(nset, variable='COORD'), category='Step', 
                             name=names.get_step_rolling(cycle_nr))
                             
    inpmod.add_at_end_of_cat(kwb, get_output_string(nset, variable='U'), category='Step', 
                             name=names.get_step_rolling(cycle_nr))
    
    # Add outputs for wheel reference point
    nset = names.wheel_rp_set   # This is created on assembly level, hence no instance prefix
    inpmod.add_at_end_of_cat(kwb, get_output_string(nset, variable='U'), category='Step', 
                             name=names.get_step_rolling(cycle_nr))
    
    inpmod.add_at_end_of_cat(kwb, get_output_string(nset, variable='COORD'), category='Step', 
                             name=names.get_step_rolling(cycle_nr))

# Define functions that allow to get things such as the model, instances etc. 
# Recommended to import as "import get_utils as get"
# Hence, the functions can be called by e.g. "get.model(cycle_nr)"
# Functions in this file should therefore not include the word get as this is implicit when the 
# proper import is used. 

from abaqus import mdb
import assembly, regionToolset, odbAccess
from abaqusConstants import *

import naming_mod as names

def model(cycle_nr=1):
	return mdb.models[names.get_model(cycle_nr)]
	

def assy(cycle_nr=1, odb=None):
    if odb:
        return odb.rootAssembly
    else:
        return model(cycle_nr).rootAssembly
    

def inst(inst_name, cycle_nr=1, odb=None):
    return assy(cycle_nr, odb).instances[inst_name]


def part(part_name, cycle_nr=1):
	return model(cycle_nr).parts[part_name]


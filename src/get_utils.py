# Define functions that allow to get things such as the model, instances etc. 
# Recommended to import as "import get_utils as get"
# Hence, the functions can be called by e.g. "get.model(stepnr)"
# Functions in this file should therefore not include the word get as this is implicit when the 
# proper import is used. 

from abaqus import mdb
import assembly, regionToolset
from abaqusConstants import *

import naming_mod as names

def model(stepnr=1):
	return mdb.models[names.get_model(stepnr)]
	

def assy(stepnr=1):
    return model(stepnr).rootAssembly
    

def inst(inst_name, stepnr=1, odb=None):
    if odb:
        return odb.rootAssembly[inst_name]
    else:
        return assy(stepnr).instances[inst_name]


def part(part_name, stepnr=1):
	return model(stepnr).parts[part_name]


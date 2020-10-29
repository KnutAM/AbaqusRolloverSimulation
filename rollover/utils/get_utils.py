# Define functions that allow to get things such as the model, instances etc. 
# Recommended to import as "import get_utils as get"
# Hence, the functions can be called by e.g. "get.model()"
# Functions in this file should therefore not include the word get as this is implicit when the 
# suggested import structure is used. 

from abaqus import mdb
import assembly, regionToolset, odbAccess
from abaqusConstants import *

from rollover.utils import naming_mod as names

def model():
	return mdb.models[names.model]
	

def assy(odb=None):
    if odb:
        return odb.rootAssembly
    else:
        return model().rootAssembly
    

def inst(inst_name, odb=None):
    return assy(odb).instances[inst_name]


def part(part_name):
	return model().parts[part_name]


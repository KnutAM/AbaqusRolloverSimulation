 """Running this abaqus script makes a substructure from part of the 
 rail

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function

# Project library imports
from rollover.utils import naming_mod as names
from rollover.three_d.rail import substructure


def main():
    substructure.create(mdb.models[names.rail_model], regenerate=True)
    
    
if __name__ == '__main__':
    main()

"""Running this abaqus script creates a wheel super element. 

The dictionary described by the 'wheel_settings.json' file should
contain the keywords according to 
:py:func:`rollover.three_d.wheel.create.substructure`

.. codeauthor:: Knut Andreas Meyer
"""

# System imports
from __future__ import print_function
import sys


# Project library imports
from rollover.utils import json_io
from rollover.three_d.wheel import substructure as wheel_substr


def main():
    # Read in wheel section parameters
    wheel_param = json_io.read('wheel_settings.json')
    
    job = wheel_substr.generate(wheel_param)
    
        
    
if __name__ == '__main__':
    main()

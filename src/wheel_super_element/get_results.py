# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqus import mdb
import assembly, regionToolset
from abaqusConstants import *
import mesh

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":

src_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(lambda: None))))
if not src_path in sys.path:
    sys.path.append(src_path)
    
import user_settings
reload(user_settings)


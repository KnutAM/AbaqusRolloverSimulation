# Python imports
from __future__ import print_function
import os, sys, inspect

# Abaqus imports
from abaqusConstants import *

# Project paths and imports
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(os.path.dirname(this_path))
util_path = src_path + '/utils'
[sys.path.append(p) for p in [this_path, util_path] if p not in sys.path]

import naming_mod as names
import get_utils as get
import abaqus_python_tools as apt


def create_rail(rail_profile, rail_length):
    rail_model = atp.create_model('RAIL')
    profile_sketch = import_sketch(rail_profile, rail_model)
    rail_part = rail_model.Part(name=names.rail_part, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    rail_part.BaseSolidExtrude(sketch=profile_sketch, depth=rail_length)
    create_sets(rail_part, rail_length)


def import_sketch(rail_profile, rail_model):
    acis = mdb.openAcis(rail_profile, scaleFromFile=OFF)
    return rail_model.ConstrainedSketchFromGeometryFile(name='profile', geometryFile=acis)
    
    
def create_sets(rail_part, rail_length):
    for z, side in zip([0, rail_length], ['1', '2']):
        faces = rail_part.faces.getByBoundingBox(xMin=-np.inf, xMax=np.inf, 
                                                 yMin=-np.inf, yMax=np.inf, 
                                                 zMax=1.e-5, zMin=-1.e-5)
        rail_part.Set(name='SIDE' + side + '_SET', faces=faces)
    
    
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Inputs:\n <path_to_rail_profile.sat> (str)\n <rail_length> (float)')
        raise IOError('rail profile file and rail length must be given as input')
    rail_profile = sys.argv[1]
    try:
        rail_length = float(sys.argv[2])
    except ValueError as ve:
        print('The rail length (second input) must be numeric')
        
    create_rail(rail_profile, rail_length)

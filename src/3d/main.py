"""This module is used to test during development
.. codeauthor:: Knut Andreas Meyer
"""
# System imports
from __future__ import print_function
import sys, os, inspect

if sys.version_info.major == 3:
    if sys.version_info.minor < 4:
        from imp import reload
    else:
        from importlib import reload

# Add all paths here, should not be required in called modules
def add_subfolders_to_path(folder):
    if not folder in sys.path:
        sys.path.append(folder)
    for f in os.listdir(folder):
        if os.path.isdir(folder + '/' + f):
            add_subfolders_to_path(folder + '/' + f)
        
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
src_path = os.path.dirname(this_path)
add_subfolders_to_path(this_path)
add_subfolders_to_path(src_path + '/utils')

import create_basic_rail as cbr

reload(cbr)

def main():
    rail_sketch = src_path + '/../data/rail_profiles/BV50.sat'
    rail_model = cbr.create_rail(rail_sketch, rail_length=50.0, refine_region=[[-20, 105],[20,160]])
    
    
if __name__ == '__main__':
    main()

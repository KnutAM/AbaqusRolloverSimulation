# System imports
import sys
import os
import numpy as np

# Abaqus imports 
import assembly
from abaqusConstants import *

# Custom imports (from present project)
# Should find better way of including by automating the path, however, __file__ doesn't seem to work...
sys.path.append(r'C:\Box Sync\PhD\MyArticles\RolloverSimulationMethodology\AbaqusRolloverSimulation\src')
import material_and_section_module as material_module
import setup_rail_module as rail_module
import setup_wheel_substruct_module as wheel_module
#import setup_wheel_module as wheel_module
import setup_loading_module as loading_module
import setup_contact_module as contact_module

#Reload to allow multiple runs from abaqus (not neccessary for cluster runs)
if sys.platform.startswith('win'):
    reload(material_module)
    reload(rail_module)
    reload(wheel_module)
    reload(loading_module)
    reload(contact_module)


def main():
    # Settings
    simulation_name = 'rollover'
    
    rail_geometry = {'length': 100.0, 'height': 30.0, 'max_contact_length': 25.}
    rail_mesh = {'fine': 1.0, 'coarse': 5.0}
    rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}
    
    wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
    wheel_mesh = {'fine': 5.0, 'coarse': 20.0, 'refine_thickness': 10.0}
    wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER', 
                    'contact_section': 'WHEEL_CONTACT_SECTION'}
    
    # Create wheel substructure model
    # substructureFile, odbFile = wheel_module.create_wheel_substructure(wheel_geometry, wheel_mesh, wheel_naming, 'wheel_substr1')
    
    # Setup model
    if simulation_name in mdb.models:    # Delete old model if exists
        del(mdb.models[simulation_name])
    
    the_model = mdb.Model(name=simulation_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    material_module.setup_sections(the_model, naming={'wheel': wheel_naming['section'], 
                                                  'rail': rail_naming['section'], 
                                                  'shadow': rail_naming['shadow_section'],
                                                  'contact': wheel_naming['contact_section']})
    
    # Setup rail
    rail_part, rail_contact_surf, bottom_reg = rail_module.setup_rail(the_model, assy, rail_geometry, rail_mesh, rail_naming)
    
    # Setup wheel
    #wheel_part, wheel_contact_surf, ctrl_pt_reg = wheel_module.setup_wheel(the_model, assy, wheel_geometry, wheel_mesh, wheel_naming)
    substructureFile='c:/work/Abaqus/2017/Temp/Job-1_Z1.sim'
    odbFile='c:/work/Abaqus/2017/Temp/Job-1.odb'
    wheel_part, wheel_contact_surf, ctrl_pt_reg = wheel_module.import_wheel_substructure(the_model, assy, wheel_naming, 
                                                                                         substructureFile, odbFile, 
                                                                                         wheel_geometry, wheel_mesh)
    
    # Setup loading
    loading_module.loading(the_model, assy, ctrl_pt_reg, bottom_reg)
    
    # Setup contact conditions
    contact_module.setup_contact(the_model, assy, rail_contact_surf, wheel_contact_surf)

    if simulation_name in mdb.jobs:
        del(mdb.jobs[simulation_name])
        
    the_job = mdb.Job(name=simulation_name, model=simulation_name)
    

if __name__ == '__main__':
    main()
